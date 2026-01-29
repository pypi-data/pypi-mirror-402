# momo writer

命令行写作工具，用于小说创作与管理。

## 安装

本地开发安装（可编辑模式，修改代码立即生效）：

```bash
python -m pip install -e .
```

安装完成后可直接使用 `momo` 命令：

```bash
momo
```

## 快速开始

```bash
momo init
momo
```

## 命令

- `/catlog` 或 `/catalog`：查看目录并用方向键选择
- `/new <标题>`：新建章节
- `/open <编号>`：直接打开指定章节
- `/latest`：打开最新一章
- `/del <编号>`：删除章节
- `/rename <编号> <标题>`：重命名章节
- `/stats`：字数统计
- `/find <关键词>`：搜索
- `/exit`：退出

章节内命令：

- `/w`：逐行写作（每行回车自动保存成段落，输入 `exit` 结束）
- `/show [行数]`：预览章节内容（默认 5 行）
- `/back`：返回上级
- `/exit` 或 `/q`：退出 momo

## 全局配置

全局配置文件：`~/.momo/config.json`

```bash
# 查看配置
momo config

# 设置默认小说目录
momo config root D:\novels

# 在默认目录下创建新小说
momo init "我的小说"
```

当你在非项目目录运行 `momo` 时，会列出已登记小说并选择进入。

## 交互式初始化

直接运行 `momo init` 会进入选择流程：
1) 在默认目录创建（输入书名）
2) 在当前目录创建（输入书名）
3) 指定路径创建（输入路径 + 书名）
4) 退出

## Notes

- On first run, the tool uses the current folder name as the novel title.
- Chapters live under `.momo/chapters` and are plain markdown files.
- The chapter picker uses `prompt_toolkit` if available; otherwise it falls back to numeric input.
