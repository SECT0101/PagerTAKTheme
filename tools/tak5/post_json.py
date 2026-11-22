#!/usr/bin/env python3
"""Apply TAK5 JSON changes (palette, dashboard, boot frames) on top of the copied layout."""
import json, re, os, sys
T = sys.argv[1]
os.chdir(T)
p = 'theme.json'; s = open(p).read()
pal = {"black": (0, 0, 0), "blue": (128, 224, 255), "red": (255, 64, 80), "dark_red": (120, 18, 30), "yellow": (255, 200, 40), "gray": (120, 138, 150),
       "green": (64, 255, 140), "dark_green": (0, 96, 56), "disabled_light_gray": (150, 160, 168), "disabled_dark_gray": (52, 60, 66), "medium_gray": (92, 104, 112),
       "orange": (255, 140, 40), "dark_orange": (140, 70, 20), "light_blue": (190, 240, 255), "cyan": (0, 240, 255), "dark_cyan": (0, 90, 110), "purple": (182, 154, 112),
       "dark_purple": (104, 82, 54), "magenta": (206, 164, 104), "dark_magenta": (110, 82, 48), "light_green": (150, 255, 180), "olive": (140, 150, 60), "dark_olive": (70, 80, 30),
       "brown": (120, 80, 40), "tan": (205, 180, 130), "teal": (0, 170, 160), "dark_teal": (0, 80, 80), "navy": (6, 20, 40), "light_yellow": (255, 232, 140), "soft_white": (225, 240, 245)}
SCHEME = os.environ.get("TAK5_SCHEME", "coyote")
prim, bright = {"cyan": ((128, 224, 255), (0, 240, 255)), "nvg": ((132, 232, 150), (90, 255, 160)),
                "coyote": ((216, 186, 134), (240, 212, 156)), "white": ((214, 220, 216), (250, 252, 250))}[SCHEME]
pal["blue"] = prim
pal["cyan"] = bright
pal["light_blue"] = tuple(min(255, int(c * 1.12) + 20) for c in prim)
pal["dark_cyan"] = tuple(int(c * 0.4) for c in prim)
pal["navy"] = tuple(int(c * 0.12) for c in prim)
for k, (r, g, b) in pal.items():
    s, n = re.subn(r'"%s":\{ "r":\d+, "g":\d+, "b":\d+ \}' % k, '"%s":{ "r":%d, "g":%d, "b":%d }' % (k, r, g, b), s); assert n == 1, k
s = s.replace('"author": "Hak5"', '"author": "SECT0101"').replace('"theme_version": "2.0.0"', '"theme_version": "1.0.0"')
s = s.replace('components/dashboards/wargames_dashboard.json', 'components/dashboards/tak5_dashboard.json')
json.loads(s); open(p, 'w').write(s)
os.rename('components/dashboards/wargames_dashboard.json', 'components/dashboards/tak5_dashboard.json')
p = 'components/dashboards/tak5_dashboard.json'; j = json.load(open(p))
j['background']['layers'][0]['image_path'] = 'assets/dashboard/tak5_bg.png'
for m in j['menu_items']:
    for l in m['layers']:
        if 'recolor_palette' in l: l['recolor_palette'] = 'blue'
    for l in m['selected_layers']:
        if l.get('image_path', '').endswith('item_bg.png'): l['recolor_palette'] = 'yellow'
        elif 'recolor_palette' in l: l['recolor_palette'] = 'black'
        if 'text' in l: l['text_color_palette'] = 'yellow'
json.dump(j, open(p, 'w'), indent=2)
p = 'components/boot_animation.json'; j = json.load(open(p))
j['animation']['frames'] = [{"image_path": "assets/boot_animation/init-%d.png" % i, "x": 0, "y": 0} for i in range(1, 9)]
json.dump(j, open(p, 'w'), indent=2)
os.remove('assets/dashboard/wargames_bg_updated.png')
os.remove('README')
print("json done")
