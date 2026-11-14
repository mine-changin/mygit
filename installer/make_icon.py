#!/usr/bin/env python3
"""설치 프로그램·바로가기용 아이콘(app.ico) 생성: 'M↓' 모양의 단순한 문서 아이콘"""
import sys
from PIL import Image, ImageDraw
S = 256
im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle((24, 12, 232, 244), radius=28, fill=(11, 110, 110, 255))
d.polygon([(168, 12), (232, 76), (168, 76)], fill=(223, 241, 240, 255))
d.rectangle((60, 120, 76, 196), fill='white'); d.rectangle((108, 120, 124, 196), fill='white')
d.polygon([(60, 120), (92, 160), (76, 160)], fill='white'); d.polygon([(124, 120), (92, 160), (108, 160)], fill='white')
d.rectangle((152, 120, 168, 176), fill='white'); d.polygon([(136, 172), (184, 172), (160, 204)], fill='white')
im.save(sys.argv[1], sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
