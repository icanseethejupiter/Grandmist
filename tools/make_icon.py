"""Generate assets/grandmist.ico (app and .gm file icon). Run once: python tools/make_icon.py"""
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'grandmist.ico')
SIZE = 256
BG, ACCENT = (11, 14, 18, 255), (61, 220, 151, 255)

img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([8, 8, SIZE - 8, SIZE - 8], radius=48, fill=BG, outline=ACCENT, width=10)
font = ImageFont.truetype(r'C:\Windows\Fonts\seguisym.ttf', 190)
d.text((SIZE / 2, SIZE / 2 + 6), '\u265e', font=font, fill=ACCENT, anchor='mm')  # black knight glyph

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
img.save(OUT.replace('.ico', '.png'))
print('wrote', OUT)
