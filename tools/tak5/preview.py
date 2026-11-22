import json,sys
from PIL import Image,ImageDraw,ImageFont
import os
T=os.environ.get('TAK5_THEME','../../themes/tak5').rstrip('/')+'/'
pal={k:(v['r'],v['g'],v['b']) for k,v in json.load(open(T+'theme.json'))['color_palette'].items()}
def recolor(im,c):
    im=im.convert('RGBA'); a=im.split()[3]; s=Image.new('RGBA',im.size,c+(255,)); s.putalpha(a); return s
def font(sz): return ImageFont.truetype(os.path.join(os.environ.get('TAK5_FONTS','fonts'),'ShareTechMono-Regular.ttf'),sz)
SZ={'large':24,'medium':18,'small':13}
def layer(img,l,ox,oy):
    x=ox+l.get('x',0); y=oy+l.get('y',0)
    if 'image_path' in l:
        im=Image.open(T+l['image_path']).convert('RGBA')
        if 'recolor_palette' in l: im=recolor(im,pal[l['recolor_palette']])
        img.alpha_composite(im,(x,y))
    elif 'text' in l:
        ImageDraw.Draw(img).text((x,y),l['text'],font=font(SZ.get(l.get('text_size','medium'),18)),fill=pal[l.get('text_color_palette','blue')])
def statusbar(img,col='blue'):
    d=ImageDraw.Draw(img); d.text((400,4),'14:37',font=font(16),fill=pal[col])
    img.alpha_composite(recolor(Image.open(T+'assets/statusbar/dashboard_battery_text.png'),pal[col]),(350,5))
    img.alpha_composite(recolor(Image.open(T+'assets/statusbar/gps.png'),pal['green']),(318,4))
def dashboard(sel):
    j=json.load(open(T+'components/dashboards/tak5_dashboard.json'))
    img=Image.new('RGBA',(480,222),(0,0,0,255))
    for l in j['background']['layers']: layer(img,l,0,0)
    for m in j['menu_items']:
        for l in (m['selected_layers'] if m['id']==sel else m['layers']): layer(img,l,m['x'],m['y'])
    statusbar(img); return img
def screen(bg, layers=(), sb=True):
    img=Image.new('RGBA',(480,222),(0,0,0,255)); img.alpha_composite(Image.open(T+bg).convert('RGBA'))
    for l in layers: layer(img,l,0,0)
    if sb: statusbar(img)
    return img
