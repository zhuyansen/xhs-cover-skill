# xhs-cover

给 Claude Code 等支持 Agent Skills 的工具用的技能：做小红书风的视频封面。

把两行标题、一个数字、两三样证据和（可选的）一张人像抠图交给它，它用自带的脚本排出三张：3:4（小红书）、16:9（B 站）、9:16（抖音、视频号）。脚本只依赖 Pillow，不联网，不调用任何模型。

| 3:4（小红书） | 16:9（B 站） |
|---|---|
| ![3:4 示例](examples/example-p.jpg) | ![16:9 示例](examples/example-h.jpg) |

上面是自带示例的输出，没有用人像和底图。加上你自己的人像抠图和一张底图，效果会完整得多。

## 安装

克隆到技能目录下，文件夹名用 `xhs-cover`：

```bash
git clone https://github.com/zhuyansen/xhs-cover-skill ~/.claude/skills/xhs-cover
```

其他支持 Agent Skills 的工具，按它的技能目录约定放。

需要 Python 3.9 以上和 Pillow：

```bash
python3 -m pip install pillow
```

脚本会自己找一款粗的中文字体（macOS 的冬青黑体、Windows 的微软雅黑、Linux 的 Noto Sans CJK）。找不到时会报错并提示怎么装，也可以在 JSON 里用 `font` 指定一个字体文件。Linux 上没有中文字体的话：

```bash
sudo apt install fonts-noto-cjk
```

在 macOS 和 Linux（Debian 加 Noto Sans CJK）上实测过。Windows 的字体路径是按系统默认位置写的，没有实测；遇到问题请用 `font` 字段指定字体。

## 用法

装好后对 Claude 说「帮我做这条视频的小红书封面」，把内容要点给它。也可以不通过 Claude，直接跑脚本：

```bash
cd examples
python3 ../scripts/cover.py spec.json --thumb
```

## 里面有什么

| 文件 | 内容 |
|---|---|
| `SKILL.md` | 做封面前要定的四样东西、出图命令、出图后必须检查的几条 |
| `scripts/cover.py` | 排版脚本，JSON 进、JPG 出 |
| `references/rules.md` | 六条规则和原因、版式、另一种「许愿式」封面、常见错误、交付前自查 |
| `references/background-prompt.md` | 给生图模型的底图提示词（只出没有字、没有人的底图） |
| `examples/` | 一个不需要任何素材就能跑的例子 |

## 它不做什么

- 不抠图。人像请自己准备透明底的 PNG（iPhone 相册长按人物「拷贝主体」，或 Mac「预览」里的「移除背景」）。
- 不生成底图。可以用任何生图模型，或者不用底图。
- 不保证点击率。规则是从一批高互动封面里归纳的经验，要用你自己前后几期的数据验证。
- 不适合 YouTube。YouTube 缩略图字越少越好，规律和这里相反。

## 许可

MIT
