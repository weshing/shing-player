#!/usr/bin/env python3
"""从悟小宝歌手列表获取缺歌词歌曲（用 QQ 音乐正确 songmid）"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qqmusic_lyrics import fetch_lyrics

SONG_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static'))

TARGETS = {
    '16-三道茶': None,  # 已有
    '20-玻璃珠': '001pyVr63DbIKR',
    '23-水往低处流': '0006aGvi1JkmY5',
    '34-轻轻落下': '002XZnsF1ZEyqf',
    '39-还是那条路': '001L8k9822sgb2',
    '4602-小算盘': '001fvEDO2RnsJt',
}

def clean_metadata(lyrics):
    lines = []
    for line in lyrics.split('\n'):
        if re.match(r'^\[(ti|ar|al|by|offset|total|length|t_time|sign|qq)\s*[:：]', line.strip()):
            continue
        lines.append(line)
    return '\n'.join(lines).strip() + '\n'

for folder, mid in TARGETS.items():
    if mid is None:
        continue
    path = os.path.join(SONG_DIR, folder)
    if not os.path.isdir(path):
        print(f'跳过（目录不存在）: {folder}')
        continue
    name = folder.split('-', 1)[1]
    out = os.path.join(path, f'{name}.lrc')
    if os.path.exists(out):
        print(f'已存在，跳过: {out}')
        continue
    print(f'获取: {name} (mid={mid})')
    lyrics = fetch_lyrics(mid)
    if not lyrics:
        print(f'  无歌词')
        continue
    content = clean_metadata(lyrics)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  ✅ 已保存: {out}')
