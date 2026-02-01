import os, glob, tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp")

RAW_NAME_CHOICES = [
"000el","001el","002el","003el","004el","005el","006el","007el",
"000pl","001pl","002pl","003pl","004pl","005pl","006pl","007pl",
"000kn","001kn","002kn","003kn","004kn","005kn","006kn","007kn",
"008cl","009cl","010cl","011cl","012cl","013cl","014cl","015cl",
"016rn","017rn","018rn","019rn","020rn","021rn","022rn","023rn",
"024dr","025dr","026dr","027dr","028dr","029dr","030dr","031dr",
"032al","033al","034al","035al","036al","037al","038al","039al",
"056hr","057hr","058hr","059hr","060hr","061hr","062hr","063hr",
"048dm","049dm","050dm","051dm","052dm","053dm","054dm","055dm",
"072nc","073nc","074nc","075nc","076nc","077nc","078nc","079nc",
"080ov","081ov","082ov","083ov","084ov","085ov","086ov","087ov",
"088wl","089wl","090wl","091wl","092wl","093wl","094wl","095wl",
"096br","097br","098br","099br","100br","101br","102br","103br",
"104bm","105bm","106bm","107bm","108bm","109bm","110bm","111bm",
"112bs","113bs","114bs","115bs","116bs","117bs","118bs","119bs",
"120wh","121wh","122wh","123wh","124wh","125wh","126wh","127wh",
]

def dedupe_preserve_order(xs):
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out

class Cropper(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pan/Zoom Cropper")
        self.geometry("1000x800")
        self.canvas = tk.Canvas(self, bg="#111", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.steps = [(58, 64), (48, 32)]
        self.step_i = 0
        self.crops = {}

        self.img = None
        self.img_path = None
        self.tkimg = None
        self.scale = 1.0
        self.tx = 0.0
        self.ty = 0.0
        self.dragging = False
        self.last_x = 0
        self.last_y = 0

        self.cwd = os.getcwd()
        self.originals_dir = os.path.join(self.cwd, "Heroes_Portraits", "Originals")
        self.png_dir = os.path.join(self.cwd, "Heroes_Portraits", "pixelated_portraits")
        self.pcx_dir = os.path.join(self.cwd, "Heroes_Portraits", "pcx_files")

        self.name_choices = dedupe_preserve_order(RAW_NAME_CHOICES)
        self.used_names = set()

        self.image_paths = []
        self.image_i = 0

        self.bind_events()
        self.after(50, self.load_queue_and_start)

    def bind_events(self):
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.on_down)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_up)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.on_wheel_linux(1, e))
        self.canvas.bind("<Button-5>", lambda e: self.on_wheel_linux(-1, e))

        self.bind("<KeyPress-plus>", lambda e: self.zoom_at(1.1, self.canvas.winfo_width()/2, self.canvas.winfo_height()/2))
        self.bind("<KeyPress-equal>", lambda e: self.zoom_at(1.1, self.canvas.winfo_width()/2, self.canvas.winfo_height()/2))
        self.bind("<KeyPress-minus>", lambda e: self.zoom_at(1/1.1, self.canvas.winfo_width()/2, self.canvas.winfo_height()/2))
        self.bind("<KeyPress-underscore>", lambda e: self.zoom_at(1/1.1, self.canvas.winfo_width()/2, self.canvas.winfo_height()/2))

        self.bind("<KeyPress-Left>", lambda e: self.pan(20, 0))
        self.bind("<KeyPress-Right>", lambda e: self.pan(-20, 0))
        self.bind("<KeyPress-Up>", lambda e: self.pan(0, 20))
        self.bind("<KeyPress-Down>", lambda e: self.pan(0, -20))

        self.bind("<KeyPress-r>", lambda e: self.reset_view())
        self.bind("<KeyPress-R>", lambda e: self.reset_view())
        self.bind("<KeyPress-s>", lambda e: self.capture_and_advance())
        self.bind("<KeyPress-S>", lambda e: self.capture_and_advance())

        self.bind("<KeyPress-n>", lambda e: self.skip_image())
        self.bind("<KeyPress-N>", lambda e: self.skip_image())

        self.bind("<Escape>", lambda e: self.destroy())

    def load_queue_and_start(self):
        if not os.path.isdir(self.originals_dir):
            messagebox.showerror("Missing folder", f"Could not find:\n{self.originals_dir}\n\nCreate it and put images inside.")
            self.destroy()
            return

        paths = []
        for ext in SUPPORTED_EXTS:
            paths.extend(glob.glob(os.path.join(self.originals_dir, f"*{ext}")))
            paths.extend(glob.glob(os.path.join(self.originals_dir, f"*{ext.upper()}")))
        paths = sorted(set(paths), key=lambda p: os.path.basename(p).lower())

        if not paths:
            messagebox.showerror("No images found", f"No supported images found in:\n{self.originals_dir}")
            self.destroy()
            return

        os.makedirs(self.png_dir, exist_ok=True)
        os.makedirs(self.pcx_dir, exist_ok=True)

        self.image_paths = paths
        self.image_i = 0
        self.load_image(self.image_paths[self.image_i])

    def load_image(self, path):
        self.img_path = path
        self.img = Image.open(path)
        self.step_i = 0
        self.crops = {}
        self.reset_view()

    def compute_crop_rect(self):
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            return (0, 0, 1, 1)
        out_w, out_h = self.steps[self.step_i]
        ar = out_w / out_h
        margin = 60
        avail_w = max(50, cw - 2*margin)
        avail_h = max(50, ch - 2*margin)
        if avail_w / avail_h > ar:
            rect_h = avail_h
            rect_w = rect_h * ar
        else:
            rect_w = avail_w
            rect_h = rect_w / ar
        x0 = (cw - rect_w) / 2
        y0 = (ch - rect_h) / 2
        x1 = x0 + rect_w
        y1 = y0 + rect_h
        return (x0, y0, x1, y1)

    def reset_view(self):
        if self.img is None:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            self.after(50, self.reset_view)
            return
        x0, y0, x1, y1 = self.compute_crop_rect()
        rect_w = x1 - x0
        rect_h = y1 - y0
        iw, ih = self.img.size
        self.scale = max(rect_w / iw, rect_h / ih)
        disp_w = iw * self.scale
        disp_h = ih * self.scale
        self.tx = (cw - disp_w) / 2
        self.ty = (ch - disp_h) / 2
        self.redraw()

    def on_down(self, e):
        self.dragging = True
        self.last_x, self.last_y = e.x, e.y

    def on_drag(self, e):
        if not self.dragging:
            return
        dx = e.x - self.last_x
        dy = e.y - self.last_y
        self.last_x, self.last_y = e.x, e.y
        self.tx += dx
        self.ty += dy
        self.redraw()

    def on_up(self, e):
        self.dragging = False

    def pan(self, dx, dy):
        self.tx += dx
        self.ty += dy
        self.redraw()

    def on_wheel_linux(self, direction, e):
        factor = 1.1 if direction > 0 else 1/1.1
        self.zoom_at(factor, e.x, e.y)

    def on_wheel(self, e):
        factor = 1.1 if e.delta > 0 else 1/1.1
        self.zoom_at(factor, e.x, e.y)

    def zoom_at(self, factor, cx, cy):
        if self.img is None:
            return
        new_scale = self.scale * factor
        new_scale = max(0.02, min(50.0, new_scale))
        factor = new_scale / self.scale
        self.tx = cx - factor * (cx - self.tx)
        self.ty = cy - factor * (cy - self.ty)
        self.scale = new_scale
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")
        if self.img is None:
            return
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            return

        iw, ih = self.img.size
        disp_w = max(1, int(round(iw * self.scale)))
        disp_h = max(1, int(round(ih * self.scale)))
        img_resized = self.img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
        self.tkimg = ImageTk.PhotoImage(img_resized)
        self.canvas.create_image(self.tx, self.ty, image=self.tkimg, anchor="nw")

        x0, y0, x1, y1 = self.compute_crop_rect()
        self.canvas.create_rectangle(x0, y0, x1, y1, outline="#00E5FF", width=3)
        self.draw_overlay(x0, y0, x1, y1)

        out_w, out_h = self.steps[self.step_i]
        total = len(self.image_paths)
        fname = os.path.basename(self.img_path) if self.img_path else ""
        remaining = len(self.name_choices) - len(self.used_names)
        text = f"[{self.image_i+1}/{total}] {fname}   Step {self.step_i+1}/2  Output: {out_w}x{out_h}px   S=capture/next  R=reset  N=skip  Esc=quit   Names left: {remaining}"
        self.canvas.create_text(12, 10, text=text, anchor="nw", fill="#ddd", font=("Segoe UI", 11))

    def draw_overlay(self, x0, y0, x1, y1):
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        shade = "#000"
        stip = "gray50"
        self.canvas.create_rectangle(0, 0, cw, y0, fill=shade, stipple=stip, outline="")
        self.canvas.create_rectangle(0, y1, cw, ch, fill=shade, stipple=stip, outline="")
        self.canvas.create_rectangle(0, y0, x0, y1, fill=shade, stipple=stip, outline="")
        self.canvas.create_rectangle(x1, y0, cw, y1, fill=shade, stipple=stip, outline="")

    def canvas_to_image_affine(self, crop_canvas):
        x0, y0, x1, y1 = crop_canvas
        left = (x0 - self.tx) / self.scale
        top = (y0 - self.ty) / self.scale
        right = (x1 - self.tx) / self.scale
        bottom = (y1 - self.ty) / self.scale
        return (left, top, right, bottom)

    def render_current_crop(self, out_w, out_h):
        x0, y0, x1, y1 = self.compute_crop_rect()
        left, top, right, bottom = self.canvas_to_image_affine((x0, y0, x1, y1))
        crop_w = right - left
        crop_h = bottom - top

        a = crop_w / out_w
        e = crop_h / out_h
        c = left
        f = top

        mode = "RGBA" if ("A" in self.img.getbands()) else "RGB"
        base = self.img.convert(mode)
        fill = (0, 0, 0, 0) if mode == "RGBA" else (0, 0, 0)

        out = base.transform(
            (out_w, out_h),
            Image.Transform.AFFINE,
            (a, 0.0, c, 0.0, e, f),
            resample=Image.Resampling.BICUBIC,
            fillcolor=fill
        )
        return out

    def prompt_name_and_save(self):
        remaining = [n for n in self.name_choices if n not in self.used_names]
        if not remaining:
            messagebox.showerror("No names left", "You have no unused names remaining.")
            self.destroy()
            return

        win = tk.Toplevel(self)
        win.title("Choose output name")
        win.geometry("360x520")
        win.transient(self)
        win.grab_set()

        label = tk.Label(win, text="Select an unused name (double-click or OK):")
        label.pack(padx=10, pady=(10, 6), anchor="w")

        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=6)

        sb = tk.Scrollbar(frame)
        sb.pack(side="right", fill="y")

        lb = tk.Listbox(frame, exportselection=False, yscrollcommand=sb.set)
        lb.pack(side="left", fill="both", expand=True)
        sb.config(command=lb.yview)

        for n in remaining:
            lb.insert("end", n)
        lb.selection_set(0)
        lb.activate(0)

        btn_row = tk.Frame(win)
        btn_row.pack(fill="x", padx=10, pady=10)

        result = {"name": None}

        def do_ok():
            sel = lb.curselection()
            if not sel:
                return
            result["name"] = lb.get(sel[0])
            win.destroy()

        def do_cancel():
            result["name"] = None
            win.destroy()

        okb = tk.Button(btn_row, text="OK", command=do_ok)
        okb.pack(side="left", padx=(0, 8))

        cb = tk.Button(btn_row, text="Cancel", command=do_cancel)
        cb.pack(side="left")

        lb.bind("<Double-Button-1>", lambda e: do_ok())

        self.wait_window(win)

        chosen = result["name"]
        if chosen is None:
            return False

        self.used_names.add(chosen)

        large = self.crops.get(0)
        small = self.crops.get(1)
        if large is None or small is None:
            messagebox.showerror("Internal error", "Missing crops to save.")
            return False

        base_large = "Hpl" + chosen
        base_small = "Hps" + chosen

        png_large = os.path.join(self.png_dir, base_large + ".png")
        png_small = os.path.join(self.png_dir, base_small + ".png")
        pcx_large = os.path.join(self.pcx_dir, base_large + ".pcx")
        pcx_small = os.path.join(self.pcx_dir, base_small + ".pcx")

        large.save(png_large, "PNG")
        small.save(png_small, "PNG")

        large_rgb = large.convert("RGB")
        small_rgb = small.convert("RGB")

        large_p = large_rgb.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
        small_p = small_rgb.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)

        large_p.save(pcx_large, "PCX")
        small_p.save(pcx_small, "PCX")

        return True

    def advance_to_next_image(self):
        self.image_i += 1
        if self.image_i >= len(self.image_paths):
            messagebox.showinfo("Done", f"Finished all images.\n\nPNG:\n{self.png_dir}\n\nPCX:\n{self.pcx_dir}")
            self.destroy()
            return
        self.load_image(self.image_paths[self.image_i])

    def capture_and_advance(self):
        if self.img is None:
            return

        out_w, out_h = self.steps[self.step_i]
        crop = self.render_current_crop(out_w, out_h)
        self.crops[self.step_i] = crop
        self.step_i += 1

        if self.step_i >= len(self.steps):
            saved = self.prompt_name_and_save()
            if saved:
                self.advance_to_next_image()
            else:
                self.step_i = len(self.steps) - 1
        else:
            self.reset_view()

    def skip_image(self):
        if self.img is None:
            return
        self.advance_to_next_image()

if __name__ == "__main__":
    Cropper().mainloop()
