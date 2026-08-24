# Shing Player

> 悟小宝原创音乐播放器 · [player.weshing.com](https://player.weshing.com)

纯静态 GitHub Pages 音乐播放器，托管悟小宝原创歌曲、伴奏与剪辑版。无需后端，上传 mp3 即可播放。

## 功能

- 歌词同步显示（全屏 LRC 歌词）
- 多平台标签（汽水音乐、视频号），按平台显示发布日期
- 歌曲搜索
- PC / 移动端自适应
- GitHub Actions 自动更新歌单（push 即生效）

## 歌曲库

| 歌单 | 数量 | 说明 |
|------|------|------|
| 原创音乐 | 53 首 | 悟小宝原创，文件名无前缀，显示名带 ` - 悟小宝` |
| 伴奏 | 42 首 | 带汽水/视频号平台标签 |
| 剪辑版 | 8 首 | 带汽水/视频号平台标签 |

歌曲目录在 [`static/`](./static/) 下，每个子目录包含 mp3、封面（png/jpeg）、歌词（lrc）、可选片段 wav。

## 快速开始

### GitHub Pages（线上）

1. Fork 或推送到本仓库
2. 启用 GitHub Pages（部署 `main` 分支）
3. 访问分配的域名，填入登录账密（默认 `admin / 123456`）

推送新歌曲到 `static/` 后，[update_music_list.yml](./.github/workflows/update_music_list.yml) 自动重新生成歌单。

### Docker（本地调试）

```bash
./bin/build.sh
./bin/run.sh
# 访问 http://127.0.0.1:7080
```

## 工具脚本

在 [`py/`](./py/) 目录下，需 Python 3.9+：

| 脚本 | 用途 |
|------|------|
| `gen_music_list.py` | 扫描 `static/` 生成三份歌单 JSON |
| `update_song_meta.py` | 给歌曲打发布日期（支持 `--platform 汽水\|视频号`） |
| `qishui_lyrics.py` | 从汽水音乐抓取 LRC 歌词（标准库，无需依赖） |
| `qqmusic_lyrics.py` | 从 QQ 音乐抓取歌词 |
| `kugou_lyrics.py` | 从酷狗音乐抓取歌词 |
| `batch_fetch_lyrics.py` | 批量抓取缺失歌词 |
| `fix_metadata.py` | 修复 mp3 元数据 |

## 项目结构

```
├── index.html              # 播放器页面
├── js/
│   ├── player.js           # 播放器核心
│   ├── functions.js        # UI 渲染（歌单列表/平台标签/日期列）
│   ├── ajax.js             # 数据加载与搜索
│   └── musicList.js        # 歌单配置
├── css/
│   ├── player.css          # 主样式
│   └── small.css           # 移动端适配
├── static/
│   ├── song_meta.json      # 原创歌曲日期标签
│   ├── song_meta_qishui.json      # 汽水平台日期
│   ├── song_meta_shipinhao.json   # 视频号平台日期
│   ├── music_list_songs.json       # 原创歌单
│   ├── music_list_accompaniment.json # 伴奏歌单
│   ├── music_list_clip.json        # 剪辑版歌单
│   └── <编号>-<歌名>/             # 歌曲目录（mp3/lrc/png/wav）
├── py/                     # 工具脚本
├── images/                 # 平台图标等静态资源
└── .github/workflows/
    └── update_music_list.yml  # 自动更新歌单
```

## 技术栈

- 前端：HTML + CSS + jQuery
- 歌单生成：Python
- CI/CD：GitHub Actions
- 部署：GitHub Pages + Cloudflare DNS
- 自定义域名：player.weshing.com

## License

[Apache License 2.0](./LICENSE)
