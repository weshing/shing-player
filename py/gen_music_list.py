#!/usr/bin/env python
# -*- coding: utf-8 -*-
# env: python3
# --------------------------------------------
# 生成仓库所有音乐文件的路径，供播放器读取（ajax.js loadLocalMusicList）
#  （可人工执行、亦可通过 Github Action 在 PR 时触发）
# --------------------------------------------
# usage: 
#   python ./py/gen_music_list.py -i {ignore_dir_keyword1,ignore_dir_keyword2,ignore_dir_keyword3,...}
# --------------------------------------------
# 分列表规则：
#   文件名含“伴奏/前奏/间奏/尾奏”等关键词 → 伴奏列表（accompaniment）
#   文件名含“主歌/副歌/剪辑版”等关键词 → 剪辑版列表（clip）
#   其余 → 歌曲列表（songs）
# 分别生成 static/music_list_songs.json、static/music_list_accompaniment.json 与 static/music_list_clip.json
# 平台标签：文件名末尾形如 “-汽水”“-视频号”（可多个）会被剥离展示，作为 platform 标签；
#           纯歌曲文件不附加平台标签。
# 更新日期：读取 static/song_meta.json（键为歌曲显示名，值为 YYYY-MM-DD），
#           生成时格式化为 YYYY.MM.DD 写入 update 字段；无记录则为空。


import argparse
import glob
import os
import re
import json
import hashlib
from mutagen.easyid3 import EasyID3
from color_log.clog import log

DEFAULT_ENCODING = "utf-8"
WORK_DIR = "."
MUSIC_DIR = f"{WORK_DIR}/static"
MUSIC_LIST_PERFIX = "music_list"
MUSIC_LIST = f"{MUSIC_DIR}/{MUSIC_LIST_PERFIX}_%s.json"
MUSIC_LIST_JS = "js/player.js"
MUSIC_SUFFIXES = [ ".mp3", ".wma", ".m4a", ".aac", ".ogg", ".flac", ".wav" ]
LYRIC_SUFFIX = ".lrc"
PIC_SUFFIXES = [ ".jpg", ".jpeg", ".png", ".PNG", ".JPG", ".JPEG" ]
BGM_KEYWORDS = [ "伴奏", "前奏", "尾奏", "间奏" ]
CLIP_KEYWORDS = [ "主歌", "副歌", "剪辑版" ]
# 平台标签后缀：文件名末尾附加（可叠加多个），显示时会剥离并作为 platform 标签
PLATFORM_SUFFIXES = [ "-汽水", "-视频号", "-抖音" ]
# 歌曲更新日期元数据文件：{显示名: "YYYY-MM-DD"}
SONG_META = f"{MUSIC_DIR}/song_meta.json"


def args() :
    parser = argparse.ArgumentParser(
        prog='', # 会被 usage 覆盖
        usage='python ./py/gen_music_list.py -i {ignore_dir_keyword1,ignore_dir_keyword2,ignore_dir_keyword3,...}',  
        description='生成 static 目录下的音乐歌单，允许跳过一些目录',  
        epilog='\r\n'.join([
            '更多参数执行', 
            '  python ./py/gen_music_list.py -h', 
            '查看', 
        ])
    )
    parser.add_argument('-i', '--ignores', dest='ignores', type=str, default="", help='忽略目录列表（关键字即可），多个用英文逗号分隔')
    return parser.parse_args()


def main(args) :
    if args.ignores :
        ignores = [x.strip() for x in args.ignores.split(',')]
    else :
        ignores = []

    # 读取歌曲更新日期元数据 {显示名: "YYYY-MM-DD"}
    song_meta = {}
    if os.path.exists(SONG_META) :
        with open(SONG_META, 'r', encoding=DEFAULT_ENCODING) as f :
            try:
                song_meta = json.load(f)
            except Exception as e:
                log.error(f"读取 {SONG_META} 失败：{e}，将忽略更新日期")

    # 创建歌曲列表
    musiclist = MusicList(
        id="9527",
        name="原创音乐",
        cover="images/album.png",
        creatorName="EXP",
        creatorAvatar="images/avatar.jpg"
    )
    # 创建伴奏列表
    bgmlist = MusicList(
        id="9528",
        name="伴奏",
        cover="images/album.png",
        creatorName="EXP",
        creatorAvatar="images/avatar.jpg"
    )
    # 创建剪辑版列表
    cliplist = MusicList(
        id="9529",
        name="剪辑版",
        cover="images/album.png",
        creatorName="EXP",
        creatorAvatar="images/avatar.jpg"
    )
    log.info(f"开始生成歌单：【{musiclist.name}】、【{bgmlist.name}】与【{cliplist.name}】")

    # 先构建"同名 mp3"集合：{目录: {文件名主干, ...}}
    # 用于规则：同一目录下若存在同名 mp3，则其余格式（wav/m4a等）视为备份，不进播放列表
    mp3_names = {}
    for root, _, files in os.walk(MUSIC_DIR):
        if any(kw in root.lower() for kw in ignores):
            continue
        mp3_names[root] = set()
        for file in files:
            if file.lower().endswith(".mp3"):
                mp3_names[root].add(os.path.splitext(file)[0])

    # 遍历所有文件
    for root, _, files in os.walk(MUSIC_DIR):

        if any(kw in root.lower() for kw in ignores) :
            log.warn(f"跳过目录： {root}")
            continue
        
        for file in files:
            if not file.lower().endswith(tuple(MUSIC_SUFFIXES)) :
                continue

            if any(kw in file.lower() for kw in ignores) :
                log.warn(f"跳过文件： {file}")
                continue

            music_name = os.path.splitext(file)[0]

            # 同名 mp3 优先：该目录下存在同名 mp3 时，跳过非 mp3 的备份文件（如 wav/m4a）
            if root in mp3_names and music_name in mp3_names[root] and not file.lower().endswith(".mp3"):
                log.warn(f"存在同名 MP3，跳过备份文件： {file}")
                continue

            # 剥离末尾平台标签后缀（可多个，如 “-汽水-视频号”），得到显示名与平台列表
            display_name, platforms = split_platform(music_name)

            absolute_path = os.path.join(root, file)
            rel_path = os.path.relpath(absolute_path, WORK_DIR).replace("\\", "/")
            rel_dir = os.path.dirname(rel_path)

            # 判断列表归属：伴奏（纯伴奏/前奏/间奏/尾奏）→ 伴奏，片段（主歌/副歌/剪辑版）→ 剪辑版，其余 → 歌曲
            is_bgm = any(kw in file for kw in BGM_KEYWORDS)
            is_clip = any(kw in file for kw in CLIP_KEYWORDS)

            lyric_path = f"{rel_dir}/{music_name}{LYRIC_SUFFIX}"
            pic_path = ""
            for pic_suffix in PIC_SUFFIXES :
                candidate = f"{rel_dir}/{music_name}{pic_suffix}"
                if os.path.exists(os.path.join(WORK_DIR, candidate)) :
                    pic_path = candidate
                    break

            # 检查歌词文件是否存在
            if not os.path.exists(os.path.join(WORK_DIR, lyric_path)) :
                lyric_path = ""

            # 获取 MP3 文件的元数据
            try:
                audio = EasyID3(absolute_path)
                artist = audio.get('artist', [''])[0]
                album = audio.get('album', [''])[0]
            except:
                artist = ""
                album = ""

            # 创建 Music 对象
            music = Music(
                id=calculate_md5(absolute_path),
                name=display_name,
                artist=artist,
                album=album,
                pic=pic_path,
                url=rel_path,
                lyric=lyric_path,
                platform=platforms,
                update=format_update(song_meta.get(display_name, ""))
            )
            if is_bgm :
                bgmlist.add(music)
            elif is_clip :
                cliplist.add(music)
            else :
                musiclist.add(music)

    del_music_lists()
    musiclist.save_to_file(MUSIC_LIST % "songs")
    bgmlist.save_to_file(MUSIC_LIST % "accompaniment")
    cliplist.save_to_file(MUSIC_LIST % "clip")
    to_js()
    log.info(f"完成，共收录 歌曲 {musiclist.size()} 首、伴奏 {bgmlist.size()} 首、剪辑版 {cliplist.size()} 首")


def split_platform(stem):
    """从文件主干末尾剥离平台标签后缀（可多个，如“-汽水-视频号”）。

    返回 (显示名, 平台标签列表)，如 ("只是错觉（间奏）", ["汽水", "视频号"])。
    """
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


def format_update(date_str):
    """把元数据里的 YYYY-MM-DD 格式化为界面展示的 YYYY.MM.DD；空值原样返回。"""
    if not date_str:
        return ""
    return date_str.replace("-", ".")


def calculate_md5(file_path):
    return hashlib.md5(file_path.encode()).hexdigest().lower()
def now() :
    return datetime.now().strftime('%Y%m%d%H%M%S')


def del_music_lists() :
    path = f"{MUSIC_DIR}/{MUSIC_LIST_PERFIX}*"  # 使用 glob 来找到所有以'music_list'开头的文件
    files = glob.glob(path)
    for file in files:
        try:
            os.remove(file)
        except:
            pass


def to_js() :
    with open(MUSIC_LIST_JS, 'r', encoding=DEFAULT_ENCODING) as file:
        content = file.read()

    # 默认歌单（歌曲列表）写入 player.js 的 githubAPI
    songs_path = MUSIC_LIST % "songs"
    content = re.sub(
        r'githubAPI:\s*"' + MUSIC_DIR + r'/' + MUSIC_LIST_PERFIX + r'.*"', 
        f'githubAPI: "{songs_path}"', 
        content
    )

    with open(MUSIC_LIST_JS, 'w', encoding=DEFAULT_ENCODING) as file:
        file.write(content)


class MusicList:
    def __init__(self, id, name, cover, creatorName, creatorAvatar):
        self.id = id
        self.name = name
        self.cover = cover
        self.creatorName = creatorName
        self.creatorAvatar = creatorAvatar
        self.item = []

    def add(self, music):
        self.item.append(music.__dict__)

    def size(self) :
        return len(self.item)

    def save_to_file(self, file_path):
        # 根据 url 字段排序歌曲列表
        sorted_items = sorted(self.item, key=lambda x: x.get('url', ''))
        self.item = sorted_items
        
        with open(file_path, 'w+', encoding=DEFAULT_ENCODING) as file:
            json.dump([self.__dict__], file, ensure_ascii=False, indent=4)

class Music:
    def __init__(self, id, name, artist, album, pic, url, lyric, platform=None, update="", source="local", url_id=None, pic_id=None, lyric_id=None):
        self.id = id
        self.name = name
        self.artist = artist
        self.album = album
        self.url = url
        self.pic = pic
        self.lyric = lyric
        self.platform = platform if platform else []
        self.update = update
        self.source = source
        self.url_id = "" if not url else id
        self.pic_id = "" if not pic else id
        self.lyric_id = "" if not lyric else id


if __name__ == "__main__" :
    main(args())
