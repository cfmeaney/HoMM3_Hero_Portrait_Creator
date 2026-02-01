# HoMM3 Hero Portrait Creator

A small Python program for creating custom **Heroes of Might and Magic III** hero portraits for creation of custom maps with user-inputted hero portraits.

The tool lets you pan/zoom/crop each source image and automatically exports both required HoMM3 portrait sizes and formats.

It batch-processes images and saves:

- Large portrait: 58×64
- Small portrait: 48×32
- PNG and PCX versions
- Correct HoMM3 filenames (Hpl###xx / Hps###xx)

## Folder Structure

Place your images and run the script from this layout:

```
Heroes_Portraits/
  Originals/            put source images here
  pixelated_portraits/  PNG output (auto-created)
  pcx_files/            PCX output (auto-created)
```

## Usage

1. Put your raw images into:

```
Heroes_Portraits/Originals/
```

2. Run:

```bash
python HoMM3_Hero_Portrait_Creator.py
```

3. For each image:
- frame the portrait
- capture both sizes
- choose an unused HoMM3 portrait code
- files are saved automatically

4. After the images have been created, paste the outputted `.pcx` files into the `Data/` subdirectory in the install folder of HoMM3.

## Controls

```
Mouse drag     pan
Mouse wheel    zoom
Arrow keys     fine pan
R              reset view
S              capture / next step
N              skip image
Esc            quit
```

Each image requires two captures:
1) 58×64  
2) 48×32

## Output Files

PNG:

```
Heroes_Portraits/pixelated_portraits/
  HplXXXX.png
  HpsXXXX.png
```

PCX:

```
Heroes_Portraits/pcx_files/
  HplXXXX.pcx
  HpsXXXX.pcx
```

## Notes

The name for the large portrait will be `Hpl###xx.pcx` where ### is a 3-digit code for the specific hero and xx is a two-digit code for the hero type.

The name for the small portrait will be `Hps###xx.pcx`.

The hero code and number range is:

```
sh = special heroes (000-008)
el = elementalist (000-007)
pl = planeswalker (000-007)
kn = knight (000-007)
cl = cleric (008-015)
rn = ranger (016-023)
dr = druid (024-031)
al = alchemist (032-039)
hr = demoniac (056-063)
dm = heretic (048-055)
nc = necromancer (072-079)
ov = overlord (080-087)
wl = warlock (088-095)
br = barbarian (096-103)
bm = battlemage (104-111)
bs = beastmaster (112-119)
wh = witch (120-127)
```
