#!/usr/bin/env python3
"""Check a Pager theme: JSON parses, every referenced asset exists, sizes match the wargames reference."""
import json, glob, os, re, sys
from PIL import Image
T, R = sys.argv[1], sys.argv[2]
os.chdir(T); bad = 0
for f in glob.glob('**/*.json', recursive=True):
    s = open(f).read()
    try: json.loads(s)
    except Exception as e: print('JSON ERR', f, e); bad += 1; continue
    for ref in re.findall(r'"((?:assets|components)/[^"]+\.(?:png|json))"', s):
        if not os.path.exists(ref): print('MISSING', f, ref); bad += 1
for f in glob.glob('assets/**/*.png', recursive=True):
    r = os.path.join(R, f)
    if os.path.exists(r) and Image.open(r).size != Image.open(f).size: print('SIZE', f); bad += 1
    if Image.open(f).mode not in ('P', 'RGBA', 'RGB', 'LA', 'L'): print('MODE', f); bad += 1
print('errors:', bad); sys.exit(1 if bad else 0)
