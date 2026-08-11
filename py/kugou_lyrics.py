#!/usr/bin/env python3
"""
酷狗音乐歌词下载器（用于 QQ 音乐无歌词的歌曲）
用法: python3 kugou_lyrics.py <歌名> <歌手>
或:   python3 kugou_lyrics.py <hash> [输出目录]
"""

import sys
import os
import re
import base64
import json
import urllib.request
import urllib.parse


def search_song(keyword, pagesize=5):
    """搜索歌曲获取 FileHash"""
    kw = urllib.parse.quote(keyword)
    url = f'https://songsearch.kugou.com/song_search_v2?keyword={kw}&page=1&pagesize={pagesize}&userid=-1&clientver=&platform=WebFilter&tag=em&filter=2&iscorrection=1&privilege_filter=0'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.kugou.com/'
    })
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return data.get('data', {}).get('lists', [])


def get_lyric_candidates(files_hash):
    """获取歌词候选"""
    url = f'https://lyrics.kugou.com/search?ver=1&man=yes&client=web&hash={files_hash}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)'
    })
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    return data.get('candidates', [])


def download_lyric(cand_id, accesskey):
    """下载歌词"""
    url = f'https://lyrics.kugou.com/download?ver=1&client=web&id={cand_id}&accesskey={accesskey}&fmt=lrc&charset=utf8'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)'
    })
    data = json.loads(urllib.request.urlopen(req, timeout=15).read())
    if data.get('status') != 200 or not data.get('content'):
        return None
    return base64.b64decode(data['content']).decode('utf-8')


def clean_metadata(lyrics):
    """清理元数据标签"""
    lines = []
    for line in lyrics.split('\n'):
        if re.match(r'^\[(ti|ar|al|by|offset|total|length|t_time|sign|qq)\s*[:：]', line.strip()):
            continue
        lines.append(line)
    return '\n'.join(lines).strip() + '\n'


def fetch_lyrics(files_hash):
    """通过 hash 获取歌词"""
    candidates = get_lyric_candidates(files_hash)
    if not candidates:
        return None
    cand = candidates[0]
    return download_lyric(cand['id'], cand['accesskey'])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    output_dir = '.'
    keyword = None
    files_hash = None

    # 判断输入是 hash 还是关键词
    # 用法: kugou_lyrics.py <hash> [输出目录]
    #   或  kugou_lyrics.py "歌名 歌手" [输出目录]
    if re.match(r'^[0-9A-F]{32}$', sys.argv[1], re.I):
        files_hash = sys.argv[1].upper()
        if len(sys.argv) > 2:
            output_dir = sys.argv[2]
    else:
        keyword = sys.argv[1]
        if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]):
            output_dir = sys.argv[2]

    if keyword:
        print(f'搜索: {keyword}')
        songs = search_song(keyword)
        if not songs:
            print('未找到歌曲')
            sys.exit(1)
        for i, s in enumerate(songs[:5]):
            name = re.sub(r'</?em>', '', s.get('SongName', ''))
            singer = re.sub(r'</?em>', '', s.get('SingerName', ''))
            print(f"  {i+1}. {name} - {singer} (hash: {s.get('FileHash')})")
        files_hash = songs[0]['FileHash']
        name = re.sub(r'</?em>', '', songs[0].get('SongName', '未知'))
        print(f'\n选择: {name}')
    else:
        name = files_hash

    print(f'获取歌词: {files_hash}')
    lyrics = fetch_lyrics(files_hash)
    if not lyrics:
        print('未找到歌词')
        sys.exit(1)

    content = clean_metadata(lyrics)
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
    filepath = os.path.join(output_dir, f'{safe_name}.lrc')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'✅ 歌词已保存: {filepath}')
    print()
    print('歌词预览:')
    print('-' * 40)
    for line in content.split('\n')[:10]:
        print(line)
    print(f'... 共 {len(content.splitlines())} 行')


if __name__ == '__main__':
    main()
