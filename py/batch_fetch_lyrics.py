#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# --------------------------------------------
# 批量获取原创歌曲歌词（网易云优先，QQ音乐兜底）
# 从 music_list_songs.json 读取歌曲列表，
# 对没有歌词的歌曲，优先从网易云获取，网易云没有则用QQ音乐。
# 用法: python ./py/batch_fetch_lyrics.py
# --------------------------------------------

import json
import os
import sys
import re
import time

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_LIST = os.path.join(WORK_DIR, "static", "music_list_songs.json")
sys.path.insert(0, os.path.join(WORK_DIR, "py"))

import netease_lyrics as netease
import qqmusic_lyrics as qq

LYRIC_SUFFIX = ".lrc"
RETRY_TIMES = 3
RETRY_SLEEP = 2


def clean_name(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def find_lrc_path(item):
    url = item.get("url", "")
    rel_dir = os.path.dirname(url)
    music_name = os.path.splitext(os.path.basename(url))[0]
    return os.path.join(WORK_DIR, rel_dir, clean_name(music_name) + LYRIC_SUFFIX)


def clean_metadata(lyrics):
    """清理歌词头部元信息（保留 作曲/作词 行）"""
    lines = []
    for line in lyrics.split('\n'):
        if re.match(r'^\[(ti|ar|al|by|offset|total|length)\s*[:：]', line.strip()):
            continue
        lines.append(line)
    return '\n'.join(lines).strip() + '\n'


def fetch_from_netease(name):
    """从网易云获取歌词，返回 LRC 字符串或 None"""
    # 先从歌手列表找
    artist_songs = netease.fetch_artist_songs()
    song_id = artist_songs.get(name)
    if not song_id:
        # 搜索
        song_id = netease.search_song(name)
    if not song_id:
        return None

    for attempt in range(1, RETRY_TIMES + 1):
        try:
            lrc = netease.fetch_lyrics(song_id)
            if lrc:
                return clean_metadata(lrc)
        except Exception as e:
            print(f"    网易云第{attempt}次异常: {e}")
        if attempt < RETRY_TIMES:
            time.sleep(RETRY_SLEEP)
    return None


def fetch_from_qq(name):
    """从QQ音乐获取歌词，返回 LRC 字符串或 None"""
    for attempt in range(1, RETRY_TIMES + 1):
        try:
            songs = qq.search_song(name)
            if not songs:
                return None
            # 优先匹配悟小宝
            chosen = None
            for s in songs:
                singer = s.get('singer', [{}])[0].get('name', '')
                if singer in ['悟小宝', '悟为行', '神坦祖师', '百小生']:
                    chosen = s
                    break
            if not chosen:
                return None

            songmid = chosen.get('songmid', '')
            lyrics = qq.fetch_lyrics(songmid)
            if lyrics:
                return clean_metadata(lyrics)
        except Exception as e:
            print(f"    QQ音乐第{attempt}次异常: {e}")
        if attempt < RETRY_TIMES:
            time.sleep(RETRY_SLEEP)
    return None


def main():
    with open(MUSIC_LIST, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data[0]['item']
    missing = [it for it in items if not it.get('lyric')]
    print(f"共 {len(items)} 首歌，缺歌词 {len(missing)} 首")

    # 预加载网易云歌手列表
    print("正在加载网易云歌手列表...")
    try:
        netease_songs = netease.fetch_artist_songs()
        print(f"  网易云共 {len(netease_songs)} 首歌")
    except Exception as e:
        print(f"  网易云歌手列表获取失败: {e}，将全部使用QQ音乐")
        netease_songs = {}

    success = []
    failed = []

    for idx, item in enumerate(missing, 1):
        name = item.get('name', '')
        lrc_path = find_lrc_path(item)
        print(f"\n[{idx}/{len(missing)}] 处理: {name}")

        if os.path.exists(lrc_path):
            print(f"  已存在，跳过")
            success.append((name, lrc_path))
            continue

        lyrics = None

        # 1. 优先网易云
        if name in netease_songs:
            print(f"  网易云匹配: id={netease_songs[name]}")
            lyrics = fetch_from_netease(name)
            if lyrics:
                print(f"  ✅ 网易云获取成功")
            else:
                print(f"  ⚠ 网易云无歌词，尝试QQ音乐")
        else:
            print(f"  网易云无此歌，尝试QQ音乐")

        # 2. 兜底QQ音乐
        if not lyrics:
            lyrics = fetch_from_qq(name)
            if lyrics:
                print(f"  ✅ QQ音乐获取成功")

        if not lyrics:
            print(f"  ❌ 所有源均无歌词")
            failed.append((name, "无歌词"))
            continue

        os.makedirs(os.path.dirname(lrc_path), exist_ok=True)
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write(lyrics)
        print(f"  已保存: {os.path.relpath(lrc_path, WORK_DIR)}")
        success.append((name, lrc_path))

    print("\n" + "=" * 50)
    print(f"成功 {len(success)} 首:")
    for name, path in success:
        print(f"  ✅ {name}")
    if failed:
        print(f"失败 {len(failed)} 首:")
        for name, reason in failed:
            print(f"  ❌ {name}: {reason}")


if __name__ == '__main__':
    main()
