#!/usr/bin/env python3
"""
汽水音乐歌词下载器
用法: python3 qishui_lyrics.py <汽水音乐分享链接>
示例: python3 qishui_lyrics.py https://qishui.douyin.com/s/iC8orPUu/
"""

import sys
import urllib.request
import json
import re
import os


def fetch_lyrics(url):
    """从汽水音乐分享链接获取歌词"""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)',
        'Accept': 'text/html'
    })
    resp = urllib.request.urlopen(req, timeout=15)
    html = resp.read().decode('utf-8')

    # 提取 _ROUTER_DATA
    match = re.search(r'_ROUTER_DATA\s*=\s*({[\s\S]*?});', html)
    if not match:
        return None, None, None

    data = json.loads(match.group(1))

    # 提取歌曲信息
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html)
    title = title_match.group(1).strip() if title_match else '未知歌曲'
    title = title.replace('@汽水音乐', '').strip()
    title = title.strip('《》')

    # 递归查找歌词
    def find_lyrics(obj, depth=0):
        if depth > 40:
            return None
        if isinstance(obj, dict):
            # 优先命中 "lyrics" 容器（其内含 sentences）
            if 'lyrics' in obj and isinstance(obj['lyrics'], dict) and 'sentences' in obj['lyrics']:
                return obj['lyrics']
            if 'sentences' in obj and isinstance(obj['sentences'], list):
                return obj
            for v in obj.values():
                result = find_lyrics(v, depth + 1)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = find_lyrics(item, depth + 1)
                if result:
                    return result
        return None

    lyrics_data = find_lyrics(data)
    if not lyrics_data:
        return title, None, None

    # 转换为 LRC 格式
    if 'sentences' in lyrics_data:
        lrc_lines = []
        for s in lyrics_data['sentences']:
            start_ms = int(s.get('startMs', 0))
            mins = start_ms // 60000
            secs = (start_ms % 60000) // 1000
            ms = start_ms % 1000
            text = ''.join([w.get('text', '') for w in s.get('words', [])])
            lrc_lines.append(f'[{mins:02d}:{secs:02d}.{ms:03d}]{text}')
        return title, '\n'.join(lrc_lines), lyrics_data

    return title, str(lyrics_data), lyrics_data


def save_lrc(title, lrc_content, output_dir='.'):
    """保存 LRC 文件"""
    # 清理文件名
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    filename = f'{safe_title}.lrc'
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(lrc_content)

    return filepath


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print('请输入汽水音乐分享链接')
        sys.exit(1)

    url = sys.argv[1]

    # 支持输出目录参数
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'

    print(f'正在获取: {url}')
    title, lrc_content, raw_data = fetch_lyrics(url)

    if not lrc_content:
        print('未找到歌词数据')
        sys.exit(1)

    filepath = save_lrc(title, lrc_content, output_dir)
    print(f'✅ 歌词已保存: {filepath}')
    print(f'   歌曲: {title}')
    print()
    print('歌词预览:')
    print('-' * 40)
    lines = lrc_content.split('\n')
    for line in lines[:10]:
        print(line)
    if len(lines) > 10:
        print(f'... 共 {len(lines)} 行')


if __name__ == '__main__':
    main()
