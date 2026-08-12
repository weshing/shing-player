#!/usr/bin/env python
# -*- coding: utf-8 -*-
# env: python3
# --------------------------------------------
# 更新歌曲的“更新日期”元数据（static/song_meta.json）
#   python ./py/update_song_meta.py <歌名>
#   python ./py/update_song_meta.py --all
#   python ./py/update_song_meta.py <歌名> --date 2026-08-12
# 默认只修改本地文件，不推送；推送由你正常发起。
# 歌名匹配规则：支持显示名或完整文件名（含/不含扩展名、含/不含平台后缀均可）。
# --------------------------------------------

import argparse
import json
import os
import sys
import datetime

DEFAULT_ENCODING = "utf-8"
WORK_DIR = "."
MUSIC_DIR = f"{WORK_DIR}/static"
SONG_META = f"{MUSIC_DIR}/song_meta.json"
MUSIC_SUFFIXES = [ ".mp3", ".wma", ".m4a", ".aac", ".ogg", ".flac", ".wav" ]
PLATFORM_SUFFIXES = [ "-汽水", "-视频号" ]


def split_platform(stem):
    platforms = []
    rest = stem
    while True:
        matched = None
        for sfx in PLATFORM_SUFFIXES:
            if rest.endswith(sfx):
                matched = sfx
                break
        if matched is None:
            break
        platforms.insert(0, matched.lstrip("-"))
        rest = rest[: -len(matched)]
    return rest, platforms


def collect_songs():
    """扫描 static 目录，返回 {显示名: 完整文件名主干}（同名 mp3 优先，纯 mp3 歌曲不带平台后缀）。"""
    result = {}
    for root, _, files in os.walk(MUSIC_DIR):
        for file in files:
            if not file.lower().endswith(tuple(MUSIC_SUFFIXES)):
                continue
            stem = os.path.splitext(file)[0]
            display_name, _ = split_platform(stem)
            cur = result.get(display_name)
            if cur is None or (file.lower().endswith(".mp3") and not cur.lower().endswith(".mp3")):
                result[display_name] = stem
    return result


def load_meta():
    if os.path.exists(SONG_META):
        with open(SONG_META, "r", encoding=DEFAULT_ENCODING) as f:
            try:
                return json.load(f)
            except Exception as e:
                print(f"警告：{SONG_META} 解析失败（{e}），将重建空元数据")
                return {}
    return {}


def save_meta(meta):
    with open(SONG_META, "w", encoding=DEFAULT_ENCODING) as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"已写入 {SONG_META}")


def normalize(query):
    """对查询词做归一化：剥离目录/扩展名/平台后缀，方便匹配。"""
    q = query.replace("\\", "/").replace(os.sep, "/")
    q = os.path.basename(q)
    for sfx in MUSIC_SUFFIXES:
        if q.lower().endswith(sfx):
            q = q[: -len(sfx)]
            break
    display_name, _ = split_platform(q)
    return display_name


def main(args):
    meta = load_meta()

    if args.all:
        songs = collect_songs()
        for display_name in songs:
            meta[display_name] = args.date
        print(f"已更新全部 {len(songs)} 首歌曲的更新日期为 {args.date}")
        save_meta(meta)
        return

    query = normalize(args.name)
    songs = collect_songs()

    # 先精确匹配显示名
    if query in songs:
        matched = {query: songs[query]}
    else:
        # 否则模糊匹配（显示名包含查询词）
        matched = {k: v for k, v in songs.items() if query in k}

    if not matched:
        print(f"未找到匹配“{args.name}”的歌曲。可用显示名或完整文件名。")
        print("可用的歌曲名（节选）：")
        for name in sorted(songs):
            print(f"  {name}")
        sys.exit(1)

    for display_name, stem in matched.items():
        meta[display_name] = args.date
        print(f"更新 {display_name}（{stem}）→ {args.date}")

    save_meta(meta)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="",
        usage="python ./py/update_song_meta.py <歌名> [--date YYYY-MM-DD] [--all]",
        description="更新歌曲的更新日期元数据（static/song_meta.json），默认只改本地文件。",
    )
    parser.add_argument("name", nargs="?", default="", help="歌曲显示名或完整文件名")
    parser.add_argument("--date", dest="date", default=datetime.date.today().strftime("%Y-%m-%d"), help="更新日期，默认今天")
    parser.add_argument("--all", dest="all", action="store_true", help="更新所有歌曲")
    main(parser.parse_args())
