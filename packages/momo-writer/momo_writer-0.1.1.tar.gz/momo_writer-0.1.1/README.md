# Momo Writer 🍑

![PyPI - Version](https://img.shields.io/pypi/v/momo-writer)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/momo-writer)
![License](https://img.shields.io/pypi/l/momo-writer)

Momo Writer 是一个沉浸式的命令行小说写作工具，专为希望在终端中专注于文字创作的作者设计。

Momo Writer is an immersive CLI novel writing tool designed for authors who want to focus on text creation in the terminal.

## ✨ 特性 Features

- **沉浸式写作**：纯净的命令行界面，支持逐行写作与自动保存。
- **项目管理**：自动管理小说章节、字数统计、目录浏览。
- **多小说支持**：自动记录并切换多本小说项目。
- **交互式操作**：通过方向键选择菜单，无需记忆复杂指令。
- **原生体验**：支持在文件管理器中一键打开目录 (`/folder`)。
- **纯文本存储**：章节内容以 Markdown 格式存储，自由掌控数据。

## 📦 安装 Installation

直接通过 pip 安装：

```bash
pip install momo-writer
```

或者从源码安装（开发模式）：

```bash
git clone https://github.com/yourusername/momo-writer.git
cd momo-writer
pip install -e .
```

## 🚀 快速开始 Quick Start

安装完成后，在终端直接输入：

```bash
momo
```

如果是首次使用，`momo` 会引导您创建一个新的小说项目：
1. **快速创建**：在默认目录（`~/momo_novels`）下自动创建。
2. **当前目录**：在当前文件夹初始化项目。
3. **自定义路径**：指定任意路径。

## 📖 命令列表 Commands

在 momo shell (`momo>`) 中，支持以下命令（支持 Tab 自动补全）：

### 常用命令
- `/new <标题>`：新建章节并直接开始写作。
- `/catlog` (或 `/catalog`)：浏览目录，使用 **↑ ↓** 选择章节，**Enter** 打开。
- `/latest`：直接打开最新一章。
- `/stats`：查看全书字数统计。
- `/folder`：在文件管理器中打开当前小说目录。
- `/help`：查看所有可用命令。
- `/exit` (或 `/q`)：退出程序。

### 章节操作
- `/open <编号>`：通过序号打开章节。
- `/rename <编号> <新标题>`：重命名章节。
- `/del <编号>`：删除章节（需确认）。
- `/find <关键词>`：全文搜索关键词。

### 写作模式
进入章节后 (`chapter: title>`)：
- `/w`：进入**专注写作模式**。此时输入的一行即为一个段落，**回车自动保存**。输入 `exit` 退出写作。
- `/show [行数]`：预览当前章节内容的最后 N 行（默认 5 行）。
- `/back`：返回主菜单。

## 📂 目录结构 Directory Structure

momo 创建的小说项目结构如下：

```text
MyNovel/
├── .momo/
│   ├── novel.json    # 小说元数据与索引
│   └── chapters/     # 存放实际章节文件
│       ├── 0001_第一章.md
│       ├── 0002_第二章.md
│       └── ...
```

章节内容以纯 Markdown 文本存储，您可以随时使用其他编辑器（如 VS Code, Typora）打开修改，`momo` 会自动同步。

## 🛠️ 开发 Development

欢迎提交 Issue 和 PR！

```bash
# 安装构建依赖
pip install build twine

# 构建发布包
python -m build

# 发布到 PyPI
twine upload dist/*
```

## License

MIT License
