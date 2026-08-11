#!/usr/bin/env python3
"""
QQ音乐歌词下载器
用法: python3 qqmusic_lyrics.py <QQ音乐歌曲链接或songmid>
示例: python3 qqmusic_lyrics.py https://y.qq.com/n/ryqq_v2/songDetail/004HfOir4Jxe0W
"""

import sys
import urllib.request
import urllib.parse
import json
import base64
import re
import os


def extract_songmid(url_or_id):
    """从链接或ID提取songmid"""
    # 如果是完整URL
    match = re.search(r'/songDetail/([a-zA-Z0-9]+)', url_or_id)
    if match:
        return match.group(1)
    # 如果直接是songmid
    if re.match(r'^[a-zA-Z0-9]{10,}$', url_or_id):
        return url_or_id
    return None


def search_song(keyword):
    """搜索歌曲获取songmid"""
    encoded = urllib.parse.quote(keyword)
    url = f'https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={encoded}&format=json&p=1&n=5&cr=1'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Referer': 'https://y.qq.com/'
    })
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read().decode('utf-8'))

    if data.get('data') and data['data'].get('song') and data['data']['song'].get('list'):
        return data['data']['song']['list']
    return []


def fetch_song_info(songmid):
    """通过QQ音乐页面获取歌曲信息"""
    try:
        url = f'https://y.qq.com/n/ryqq_v2/songDetail/{songmid}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept': 'text/html'
        })
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode('utf-8')

        # 从页面提取歌曲信息
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
        if title_match:
            title_text = title_match.group(1)
            # 格式通常是 "歌名 - 歌手 - QQ音乐"
            parts = title_text.split(' - ')
            if len(parts) >= 2:
                return parts[0].strip(), parts[1].strip()
            return title_text.strip(), ''
    except Exception:
        pass
    return None, None


def fetch_lyrics(songmid):
    """获取歌词"""
    url = 'https://u.y.qq.com/cgi-bin/musicu.fcg'
    payload = {
        'comm': {'ct': 24, 'cv': 0},
        'lyric': {
            'module': 'music.musichallSong.PlayLyricInfo',
            'method': 'GetPlayLyricInfo',
            'param': {
                'songMID': songmid,
                'songID': 0
            }
        }
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Content-Type': 'application/json',
        'Referer': 'https://y.qq.com/'
    })
    resp = urllib.request.urlopen(req, timeout=10)
    result = json.loads(resp.read().decode('utf-8'))

    if result.get('lyric') and result['lyric'].get('data') and result['lyric']['data'].get('lyric'):
        lyrics = base64.b64decode(result['lyric']['data']['lyric']).decode('utf-8')
        return lyrics
    return None


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
        print('请输入QQ音乐歌曲链接、songmid或搜索关键词')
        sys.exit(1)

    input_val = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'

    # 尝试提取songmid
    songmid = extract_songmid(input_val)

    title = None
    artist = None

    if not songmid:
        # 当作搜索关键词
        print(f'搜索: {input_val}')
        songs = search_song(input_val)
        if not songs:
            print('未找到歌曲')
            sys.exit(1)

        print('搜索结果:')
        for i, s in enumerate(songs[:5]):
            singer = s.get('singer', [{}])[0].get('name', '')
            print(f"  {i+1}. {s.get('songname')} - {singer} (mid: {s.get('songmid')})")

        # 使用第一个结果
        songmid = songs[0]['songmid']
        title = songs[0].get('songname', '未知歌曲')
        artist = songs[0].get('singer', [{}])[0].get('name', '')
        print(f'\n选择: {title}')
    else:
        # 直接用songmid，尝试搜索获取标题
        print(f'获取歌曲信息: {songmid}')
        # 尝试从歌词提取标题
        pass

    print(f'获取歌词: {songmid}')
    lyrics = fetch_lyrics(songmid)

    if not lyrics:
        print('未找到歌词')
        sys.exit(1)

    # 尝试从歌词提取歌名
    if not title:
        title_match = re.search(r'\[ti:(.*?)\]', lyrics)
        if title_match and title_match.group(1).strip():
            title = title_match.group(1)
        else:
            # 使用songmid作为文件名
            title = songmid

    # 组合文件名
    display_title = f'{title} - {artist}' if artist else title
    filepath = save_lrc(display_title, lyrics, output_dir)
    print(f'✅ 歌词已保存: {filepath}')
    print(f'   歌曲: {display_title}')
    print()
    print('歌词预览:')
    print('-' * 40)
    lines = lyrics.split('\n')
    for line in lines[:10]:
        print(line)
    if len(lines) > 10:
        print(f'... 共 {len(lines)} 行')


if __name__ == '__main__':
    main()
