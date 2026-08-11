#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# env: python3
# --------------------------------------------
# 批量获取原创歌曲歌词（QQ音乐）
# 从 music_list_songs.json 读取歌曲列表，
# 对没有歌词的歌曲，按歌名搜索 QQ 音乐并下载歌词，
# 保存为 <歌曲名>.lrc 到对应歌曲目录。
# 优先选择歌手为"悟小宝"的结果。
# 用法: python ./py/batch_fetch_lyrics.py
# --------------------------------------------

import json
import os
import sys
import re
import glob
import time

WORK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_LIST = os.path.join(WORK_DIR, "static", "music_list_songs.json")
sys.path.insert(0, os.path.join(WORK_DIR, "py"))
import qqmusic_lyrics as qq

PREFERRED_ARTISTS = ["悟小宝", "悟为行", "神坦祖师", "百小生"]
LYRIC_SUFFIX = ".lrc"
RETRY_TIMES = 3
RETRY_SLEEP = 3


def clean_name(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def find_lrc_path(item):
    """根据歌曲 url 推断歌词应存放的路径（与 gen_music_list.py 规则一致）"""
    url = item.get("url", "")
    rel_dir = os.path.dirname(url)
    music_name = os.path.splitext(os.path.basename(url))[0]
    return os.path.join(WORK_DIR, rel_dir, clean_name(music_name) + LYRIC_SUFFIX)


def choose_best(songs):
    """从搜索结果中选择最合适的（优先指定歌手，其次第一个）"""
    for s in songs:
        singer = s.get('singer', [{}])[0].get('name', '')
        if singer in PREFERRED_ARTISTS:
            return s
    # 没有匹配到指定歌手，返回 None 表示"不采用"（避免错配他人歌曲）
    return None


def main():
    with open(MUSIC_LIST, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data[0]['item']
    missing = [it for it in items if not it.get('lyric')]
    print(f"共 {len(items)} 首歌，缺歌词 {len(missing)} 首")

    success = []
    failed = []

    for idx, item in enumerate(missing, 1):
        name = item.get('name', '')
        lrc_path = find_lrc_path(item)
        print(f"\n[{idx}/{len(missing)}] 处理: {name}")

        # 若目标文件已存在则跳过
        if os.path.exists(lrc_path):
            print(f"  已存在，跳过: {lrc_path}")
            success.append((name, lrc_path))
            continue

        try:
            songs = qq.search_song(name)
            if not songs:
                print("  未找到歌曲")
                failed.append((name, "无搜索结果"))
                continue

            chosen = choose_best(songs)
            if not chosen:
                singer_names = [s.get('singer', [{}])[0].get('name', '') for s in songs[:3]]
                print(f"  无原创歌手匹配（其他结果: {singer_names}），跳过")
                failed.append((name, "未匹配到原创歌手"))
                continue

            singer = chosen.get('singer', [{}])[0].get('name', '')
            songmid = chosen.get('songmid', '')
            print(f"  匹配: {chosen.get('songname')} - {singer} (mid: {songmid})")

            # 获取歌词，带重试
            lyrics = None
            for attempt in range(1, RETRY_TIMES + 1):
                try:
                    lyrics = qq.fetch_lyrics(songmid)
                    if lyrics:
                        break
                except Exception as e:
                    print(f"  第{attempt}次获取异常: {e}")
                if attempt < RETRY_TIMES:
                    time.sleep(RETRY_SLEEP)

            if not lyrics:
                print("  获取歌词失败（多次重试）")
                failed.append((name, "无歌词数据"))
                continue

            # 清理歌词头部的元信息（[ti:]/[ar:]/[al:]/[by:]/[offset:]）
            lines = lyrics.split('\n')
            keep = [l for l in lines if not re.match(r'^\[(ti|ar|al|by|offset):', l.strip())]
            lyrics = '\n'.join(keep).strip() + '\n'

            # 保存到歌曲目录
            os.makedirs(os.path.dirname(lrc_path), exist_ok=True)
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write(lyrics)
            print(f"  ✅ 已保存: {os.path.relpath(lrc_path, WORK_DIR)}")
            success.append((name, lrc_path))

        except Exception as e:
            print(f"  错误: {e}")
            failed.append((name, str(e)))

    print("\n" + "=" * 50)
    print(f"成功 {len(success)} 首:")
    for name, path in success:
        print(f"  ✅ {name} -> {os.path.relpath(path, WORK_DIR)}")
    if failed:
        print(f"失败 {len(failed)} 首:")
        for name, reason in failed:
            print(f"  ❌ {name}: {reason}")


if __name__ == '__main__':
    main()
