#!/usr/bin/env python
# -*- coding: utf-8 -*-
# env: python3
# --------------------------------------------
# 将 .srt 字幕转换为 .lrc 歌词（取每句开始时间）
# usage:
#   python ./py/srt2lrc.py <input.srt> [output.lrc]
# --------------------------------------------

import os
import re
import sys


def srt_time_to_lrc(t):
    # 00:00:22,270 -> 00:22.27
    m = re.match(r'(\d+):(\d+):(\d+)[,.](\d+)', t)
    if not m:
        return ''
    h, mi, s, ms = m.groups()
    total_min = int(h) * 60 + int(mi)
    return '%02d:%02d.%02d' % (total_min, int(s), int(ms) // 10)


def convert(srt_path, lrc_path):
    with open(srt_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    out = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # 时间轴行
        if '-->' in line:
            start = line.split('-->')[0].strip()
            lrc_t = srt_time_to_lrc(start)
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip() and '-->' not in lines[i]:
                text_lines.append(lines[i].strip())
                i += 1
            text = ' '.join(text_lines)
            if text and lrc_t:
                out.append('[%s]%s' % (lrc_t, text))
        else:
            i += 1

    with open(lrc_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')

    print('converted %d lines -> %s' % (len(out), lrc_path))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python srt2lrc.py <input.srt> [output.lrc]')
        sys.exit(1)
    srt_file = sys.argv[1]
    if len(sys.argv) >= 3:
        lrc_file = sys.argv[2]
    else:
        lrc_file = os.path.splitext(srt_file)[0] + '.lrc'
    convert(srt_file, lrc_file)
