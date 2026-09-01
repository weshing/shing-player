#!/usr/bin/env python3
"""
网易云音乐歌词下载器（默认歌词源）
用法:
  python3 netease_lyrics.py <歌曲ID或链接> [输出目录]
  python3 netease_lyrics.py --name <歌名> [输出目录]
示例:
  python3 netease_lyrics.py 3425622350 static/6000-两个果/
  python3 netease_lyrics.py https://music.163.com/song?id=3425622350 static/6000-两个果/
  python3 netease_lyrics.py --name 两个果 static/6000-两个果/
"""

import sys
import urllib.request
import json
import re
import os

ARTIST_ID = 127800568  # 悟小宝
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'


def extract_song_id(url_or_id):
    """从链接或ID提取歌曲ID"""
    match = re.search(r'id=(\d+)', url_or_id)
    if match:
        return int(match.group(1))
    if url_or_id.isdigit():
        return int(url_or_id)
    return None


def fetch_artist_songs(artist_id=ARTIST_ID):
    """获取歌手所有歌曲 {歌名: 歌曲ID}"""
    url = f'https://music.163.com/api/artist/{artist_id}'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read().decode('utf-8'))
    songs = data.get('hotSongs', [])
    return {s['name']: s['id'] for s in songs}


def search_song(name, artist_id=ARTIST_ID):
    """按歌名搜索，返回歌曲ID（优先匹配指定歌手）"""
    url = 'https://music.163.com/api/search/get'
    payload = f's={urllib.parse.quote(name)}&type=1&limit=10&offset=0'.encode()
    req = urllib.request.Request(url, data=payload, headers={
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/x-www-form-urlencoded',
    })
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read().decode('utf-8'))
    songs = data.get('result', {}).get('songs', [])
    # 优先匹配悟小宝
    for s in songs:
        artists = [a.get('name', '') for a in s.get('artists', [])]
        if '悟小宝' in artists:
            return s['id']
    return None


def fetch_lyrics(song_id):
    """从网易云API获取LRC歌词"""
    url = f'https://music.163.com/api/song/lyric?id={song_id}&lv=1'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    resp = urllib.request.urlopen(req, timeout=15)
    data = json.loads(resp.read().decode('utf-8'))
    lrc = data.get('lrc', {}).get('lyric', '')
    return lrc if lrc else None


def clean_metadata(lrc):
    """清理歌词头部元信息（保留 作曲/作词 行）"""
    lines = []
    for line in lrc.split('\n'):
        # 保留 [mm:ss.xxx] 开头的行（歌词+作曲/作词）
        # 删除 [ti:]/[ar:]/[al:]/[by:]/[offset:] 等元数据标签
        if re.match(r'^\[(ti|ar|al|by|offset|total|length)\s*[:：]', line.strip()):
            continue
        lines.append(line)
    return '\n'.join(lines).strip() + '\n'


def save_lrc(title, lrc_content, output_dir='.'):
    """保存LRC文件"""
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    filename = f'{safe_title}.lrc'
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(lrc_content)
    return filepath


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    output_dir = '.'
    song_id = None
    title = None

    if sys.argv[1] == '--name':
        # 按歌名搜索
        if len(sys.argv) < 3:
            print('用法: python3 netease_lyrics.py --name <歌名> [输出目录]')
            sys.exit(1)
        name = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else '.'
        print(f'正在搜索: {name}')
        # 先从歌手列表找
        try:
            artist_songs = fetch_artist_songs()
            if name in artist_songs:
                song_id = artist_songs[name]
                print(f'  从歌手列表匹配: id={song_id}')
        except Exception as e:
            print(f'  歌手列表获取失败: {e}')
        if not song_id:
            song_id = search_song(name)
            if song_id:
                print(f'  搜索匹配: id={song_id}')
        if not song_id:
            print(f'  未找到歌曲: {name}')
            sys.exit(1)
        title = name
    else:
        # 按ID或链接
        song_id = extract_song_id(sys.argv[1])
        output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
        if not song_id:
            print(f'无法解析歌曲ID: {sys.argv[1]}')
            sys.exit(1)

    print(f'正在获取歌词: id={song_id}')
    lrc = fetch_lyrics(song_id)
    if not lrc:
        print('❌ 该歌曲在网易云上没有歌词')
        sys.exit(1)

    lrc = clean_metadata(lrc)

    # 如果没有歌名，从歌手列表反查
    if not title:
        try:
            artist_songs = fetch_artist_songs()
            for name, sid in artist_songs.items():
                if sid == song_id:
                    title = name
                    break
        except Exception:
            pass
    if not title:
        title = f'song_{song_id}'

    os.makedirs(output_dir, exist_ok=True)
    filepath = save_lrc(title, lrc, output_dir)
    print(f'✅ 歌词已保存: {filepath}')
    print(f'   歌曲: {title}')
    print()
    print('歌词预览:')
    print('-' * 40)
    lines = lrc.split('\n')
    for line in lines[:10]:
        print(line)
    if len(lines) > 10:
        print(f'... 共 {len(lines)} 行')


if __name__ == '__main__':
    main()
