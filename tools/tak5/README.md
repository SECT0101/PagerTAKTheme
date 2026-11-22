# TAK5 build tools

Scripts that draw every TAK5 image on top of Hak5's `wargames` reference theme: the theme art, the TAK.5 wordmark, the 3D Tac-Pine character and the Pineapple Edition shield.

```
git clone https://github.com/hak5/wifipineapplepager-themes
tools/tak5/build.sh /path/to/wifipineapplepager-themes          # rebuild themes/tak5
tools/tak5/build.sh /path/to/wifipineapplepager-themes --logo   # also rebuild the art/tak5 logos
```

Needs python3 with pillow and numpy, jq, and the SIL OFL fonts listed at the top of `build.sh` saved in `tools/tak5/fonts/`.
`TAK5_SCHEME` picks the color scheme: `coyote` (default), `cyan`, `nvg` or `white`.

| Script | What it does |
|---|---|
| `build_tak5.py` | Draws the theme images (same names and sizes as `wargames`) |
| `post_json.py` | Palette, dashboard and boot-frame JSON changes |
| `brand.py` | Camo patterns and the TAK.5 wordmark |
| `character.py`, `character3d.py`, `shade.py` | Tac-Pine geometry and 3D lighting |
| `logo.py`, `logo3d.py` | The TAK.5 Pineapple Edition shield |
| `family.py` | The PagerTAK, OpenWrt-TAK and LiveU-TAK project shields (`art/family/`) |
| `selector.py` | The small shield menu cursors (`payloads_dashboard/arrow.png`, `alerts_dashboard/sub.png`) |
| `icons.py` | Repaints the home-menu icons coyote tan (the stock files are magenta) |
| `planet.py` | TAK THE PLANET! slogan, glitch color split and the globe (Natural Earth coastlines in `data/`) |
| `planet_logos.py` | The TAK THE PLANET! tab, shield and patch (`art/tak5/`) |
| `validate.py` | Checks JSON, referenced assets and image sizes |
| `preview.py` | Renders the README preview screenshots |
