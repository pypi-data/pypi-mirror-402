#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import json
import os
import sys
from datetime import datetime

PROJECT_DIR = ".momo"
STATE_FILE = "novel.json"
CHAPTERS_DIR = "chapters"
GLOBAL_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".momo_config")
OLD_GLOBAL_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".momo")
GLOBAL_CONFIG_FILE = "config.json"


def project_root(cwd):
    candidate = os.path.join(cwd, PROJECT_DIR)
    if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, STATE_FILE)):
        return cwd
    return None


def state_path(root):
    return os.path.join(root, PROJECT_DIR, STATE_FILE)


def chapters_dir(root):
    return os.path.join(root, PROJECT_DIR, CHAPTERS_DIR)


def load_state(root):
    with open(state_path(root), "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(root, state):
    with open(state_path(root), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def next_chapter_id(state):
    if not state["chapters"]:
        return "0001"
    last = state["chapters"][-1]["id"]
    return f"{int(last) + 1:04d}"


def safe_filename(title):
    keep = []
    for ch in title.strip():
        if ch.isalnum() or ch in (" ", "-", "_"):
            keep.append(ch)
    name = "".join(keep).strip().replace(" ", "_")
    return name or "chapter"


def global_config_path():
    return os.path.join(GLOBAL_CONFIG_DIR, GLOBAL_CONFIG_FILE)


def load_global_config():
    path = global_config_path()
    default_novels_dir = os.path.join(os.path.expanduser("~"), "momo_novels")
    
    # Check for legacy config directory and migrate if needed
    if not os.path.exists(GLOBAL_CONFIG_DIR) and os.path.exists(OLD_GLOBAL_CONFIG_DIR):
        old_config = os.path.join(OLD_GLOBAL_CONFIG_DIR, GLOBAL_CONFIG_FILE)
        old_state = os.path.join(OLD_GLOBAL_CONFIG_DIR, STATE_FILE)
        # Migrate only if it looks like a config dir (has config, no novel state)
        if os.path.exists(old_config) and not os.path.exists(old_state):
            try:
                os.rename(OLD_GLOBAL_CONFIG_DIR, GLOBAL_CONFIG_DIR)
                print(f"系统消息: 已将旧配置目录迁移至 {GLOBAL_CONFIG_DIR}")
            except Exception as e:
                print(f"系统消息: 配置目录迁移失败 ({e})，将使用新目录。")

    if not os.path.exists(path):
        return {"default_root": default_novels_dir, "novels": [], "welcome_shown": False}
    with open(path, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
        except Exception:
            config = {}
        
        if not config.get("default_root"):
            config["default_root"] = default_novels_dir
            
        # Clean up invalid novels (those that exist but are not valid momo projects)
        if "novels" in config:
            valid_novels = []
            cleaned = False
            for n in config["novels"]:
                p = n.get("path")
                if p and os.path.exists(p):
                    # It exists, so it MUST be a valid project.
                    if os.path.exists(os.path.join(p, PROJECT_DIR, STATE_FILE)):
                         valid_novels.append(n)
                    else:
                         cleaned = True # Exists but invalid -> remove
                else:
                    # Doesn't exist (maybe USB removed) -> Keep it
                    valid_novels.append(n)
            
            if cleaned:
                config["novels"] = valid_novels
                save_global_config(config)

        if "welcome_shown" not in config:
            config["welcome_shown"] = False
        return config


def save_global_config(config):
    os.makedirs(GLOBAL_CONFIG_DIR, exist_ok=True)
    with open(global_config_path(), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def register_novel(root):
    config = load_global_config()
    root = os.path.abspath(root)
    try:
        state = load_state(root)
        title = state.get("title", os.path.basename(root))
    except Exception:
        title = os.path.basename(root)
    novels = config.get("novels", [])
    for item in novels:
        if os.path.abspath(item.get("path", "")) == root:
            item["title"] = title
            save_global_config(config)
            return
    novels.append({"path": root, "title": title})
    config["novels"] = novels
    if not config.get("default_root"):
        config["default_root"] = os.path.dirname(root)
    save_global_config(config)


def select_novel_prompt_toolkit(novels):
    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.styles import Style

    selected = 0

    def render():
        lines = []
        for i, novel in enumerate(novels):
            prefix = "> " if i == selected else "  "
            title = novel.get("title") or os.path.basename(novel.get("path", ""))
            path = novel.get("path", "")
            lines.append(prefix + f"{i + 1:02d}. {title}  [{path}]")
        lines.append("")
        lines.append("Up/Down to move, Enter to open, Esc to cancel.")
        return "\n".join(lines)

    control = FormattedTextControl(text=render)
    kb = KeyBindings()

    @kb.add("up")
    def _up(event):
        nonlocal selected
        selected = (selected - 1) % len(novels)
        event.app.invalidate()

    @kb.add("down")
    def _down(event):
        nonlocal selected
        selected = (selected + 1) % len(novels)
        event.app.invalidate()

    @kb.add("enter")
    def _enter(event):
        event.app.exit(result=selected)

    @kb.add("escape")
    def _esc(event):
        event.app.exit(result=None)

    style = Style.from_dict({"": "bg:#1c1c1c #d0d0d0"})
    app = Application(
        layout=Layout(Window(control)),
        key_bindings=kb,
        full_screen=True,
        style=style,
    )
    return app.run()


def select_novel(config):
    novels = [n for n in config.get("novels", []) if n.get("path")]
    if not novels:
        print("No novels found. Run: momo init")
        return None
    try:
        idx = select_novel_prompt_toolkit(novels)
        if idx is None:
            return None
        return novels[idx]
    except Exception:
        for idx, novel in enumerate(novels, 1):
            title = novel.get("title") or os.path.basename(novel.get("path", ""))
            print(f"{idx:02d}. {title}  [{novel.get('path','')}]")
        choice = input("Select novel number (or blank to cancel): ").strip()
        if not choice:
            return None
        if not choice.isdigit():
            print("Invalid selection.")
            return None
        sel = int(choice) - 1
        if sel < 0 or sel >= len(novels):
            print("Out of range.")
            return None
        return novels[sel]


def init_project(root, title_override=None):
    os.makedirs(os.path.join(root, PROJECT_DIR), exist_ok=True)
    os.makedirs(chapters_dir(root), exist_ok=True)
    if os.path.exists(state_path(root)):
        print("Project already initialized.")
        return
    title = title_override or os.path.basename(os.path.abspath(root)) or "Novel"
    state = {"title": title, "created_at": datetime.now().isoformat(), "chapters": []}
    save_state(root, state)
    print(f"Initialized momo project in {os.path.join(root, PROJECT_DIR)}")


def create_chapter(root, state, title):
    chapter_id = next_chapter_id(state)
    filename = f"{chapter_id}_{safe_filename(title)}.md"
    rel_path = os.path.join(PROJECT_DIR, CHAPTERS_DIR, filename)
    abs_path = os.path.join(root, rel_path)
    with open(abs_path, "a", encoding="utf-8"):
        pass
    chapter = {"id": chapter_id, "title": title, "file": rel_path}
    state["chapters"].append(chapter)
    save_state(root, state)
    return chapter


def show_chapter_list(state):
    for idx, chapter in enumerate(state["chapters"], 1):
        print(f"{idx:02d}. {chapter['title']}")


def select_chapter_prompt_toolkit(chapters):
    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.styles import Style

    selected = 0

    def render():
        lines = []
        for i, ch in enumerate(chapters):
            prefix = "> " if i == selected else "  "
            lines.append(prefix + f"{i + 1:02d}. {ch['title']}")
        lines.append("")
        lines.append("Up/Down to move, Enter to open, Esc to cancel.")
        return "\n".join(lines)

    control = FormattedTextControl(text=render)
    kb = KeyBindings()

    @kb.add("up")
    def _up(event):
        nonlocal selected
        selected = (selected - 1) % len(chapters)
        event.app.invalidate()

    @kb.add("down")
    def _down(event):
        nonlocal selected
        selected = (selected + 1) % len(chapters)
        event.app.invalidate()

    @kb.add("enter")
    def _enter(event):
        event.app.exit(result=selected)

    @kb.add("escape")
    def _esc(event):
        event.app.exit(result=None)

    style = Style.from_dict({"": "bg:#1c1c1c #d0d0d0"})
    app = Application(
        layout=Layout(Window(control)),
        key_bindings=kb,
        full_screen=True,
        style=style,
    )
    return app.run()


def select_chapter(state):
    chapters = state["chapters"]
    if not chapters:
        print("No chapters yet. Use /new <title> to create one.")
        return None
    try:
        return select_chapter_prompt_toolkit(chapters)
    except Exception:
        show_chapter_list(state)
        choice = input("Select chapter number (or blank to cancel): ").strip()
        if not choice:
            return None
        if not choice.isdigit():
            print("Invalid selection.")
            return None
        idx = int(choice) - 1
        if idx < 0 or idx >= len(chapters):
            print("Out of range.")
            return None
        return idx


def chapter_path(root, chapter):
    return os.path.join(root, chapter["file"])


def edit_chapter(root, chapter):
    path = chapter_path(root, chapter)
    print("Enter lines. Each line is saved as a paragraph.")
    print("Type 'exit' on its own line to stop.")
    def clear_terminal():
        sys.stdout.write("\x1b[2J\x1b[H\x1b[3J")
        sys.stdout.flush()

    def read_line():
        try:
            from prompt_toolkit.shortcuts import prompt
            return prompt("> ", erase_when_done=True)
        except Exception:
            return input("> ")

    with open(path, "a", encoding="utf-8") as f:
        while True:
            line = read_line()
            if line.strip() == "exit":
                break
            f.write(line.rstrip() + "\n\n")
            f.flush()
            clear_terminal()
            print("(saved, hidden)")


def show_chapter(root, chapter, height=5):
    path = chapter_path(root, chapter)
    if not os.path.exists(path):
        print("Chapter file missing.")
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import Window
        from prompt_toolkit.layout.controls import FormattedTextControl
        from prompt_toolkit.styles import Style

        height = max(1, int(height))
        offset = 0

        def render():
            window = lines[offset:offset + height]
            if not window:
                window = [""]
            return "\n".join(window) + "\n\nUp/Down to scroll, Esc to close."

        control = FormattedTextControl(text=render)
        kb = KeyBindings()

        @kb.add("up")
        def _up(event):
            nonlocal offset
            if offset > 0:
                offset -= 1
                event.app.invalidate()

        @kb.add("down")
        def _down(event):
            nonlocal offset
            if offset + height < len(lines):
                offset += 1
                event.app.invalidate()

        @kb.add("escape")
        def _esc(event):
            event.app.exit()

        style = Style.from_dict({"": "bg:#1c1c1c #d0d0d0"})
        app = Application(
            layout=Layout(Window(control, height=height + 2)),
            key_bindings=kb,
            full_screen=False,
            style=style,
        )
        app.run()
    except Exception:
        for line in lines:
            print(line)


def count_words(text):
    count = 0
    for ch in text:
        if not ch.isspace():
            count += 1
    return count


def stats_all(root, state):
    total_chars = 0
    for chapter in state["chapters"]:
        path = chapter_path(root, chapter)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            total_chars += count_words(f.read())
    print(f"Total characters (non-space): {total_chars}")
    for idx, chapter in enumerate(state["chapters"], 1):
        path = chapter_path(root, chapter)
        if not os.path.exists(path):
            print(f"{idx:02d}. {chapter['title']} - missing")
            continue
        with open(path, "r", encoding="utf-8") as f:
            chars = count_words(f.read())
        print(f"{idx:02d}. {chapter['title']} - {chars}")


def find_in_chapters(root, state, keyword):
    if not keyword:
        print("Keyword required.")
        return
    for idx, chapter in enumerate(state["chapters"], 1):
        path = chapter_path(root, chapter)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        hits = []
        for line_no, line in enumerate(lines, 1):
            if keyword in line:
                hits.append((line_no, line))
        if hits:
            print(f"{idx:02d}. {chapter['title']}")
            for line_no, line in hits:
                print(f"  L{line_no}: {line}")


def chapter_shell(root, state, chapter_index):
    chapter = state["chapters"][chapter_index]
    def read_cmd():
        try:
            from prompt_toolkit.completion import Completer, Completion
            from prompt_toolkit.shortcuts import prompt
            class SlashCompleter(Completer):
                def __init__(self, words):
                    self.words = words

                def get_completions(self, document, complete_event):
                    text = document.text_before_cursor
                    if text == "/":
                        for word in self.words:
                            yield Completion(word.lstrip("/"), start_position=0)
                        return
                    for word in self.words:
                        if word.startswith(text):
                            yield Completion(word, start_position=-len(text))

            completer = SlashCompleter(["/w", "/show", "/show 10", "/back", "/help", "/exit"])
            return prompt(
                f"chapter:{chapter['title']}> ",
                completer=completer,
                complete_while_typing=True,
            )
        except Exception:
            return input(f"chapter:{chapter['title']}> ")

    while True:
        cmd = read_cmd().strip()
        if cmd in ("/back", "back"):
            return False
        if cmd in ("/exit", "exit", "/quit", "quit", "/q", "q"):
            return True
        if cmd in ("/help", "help"):
            print("章节命令：")
            print("  /w                 开始写作（逐行保存）")
            print("  /show [行数]        查看章节内容（默认5行）")
            print("  /back               返回上一级")
            print("  /exit 或 /q          退出 momo")
            continue
        if cmd in ("/w", "w"):
            edit_chapter(root, chapter)
            continue
        if cmd.startswith("/show") or cmd.startswith("show"):
            parts = cmd.split()
            if len(parts) > 1 and parts[1].isdigit():
                show_chapter(root, chapter, height=int(parts[1]))
            else:
                show_chapter(root, chapter)
            continue
        print("Commands: /w, /show, /back")


def momo_shell(root):
    register_novel(root)
    state = load_state(root)
    print("欢迎使用 momo 写作工具！")
    print("使用提示：")
    print("  1) /catlog 浏览目录，方向键选择章节，回车进入")
    print("  2) /new <标题> 新建章节并进入")
    print("  3) 进入章节后用 /w 开始写作，逐行回车自动保存")
    print("  4) /show [行数] 预览章节内容，默认 5 行")
    print("  5) /find <关键词> 搜索，/stats 查看字数")
    print("  6) /q 退出，/help 查看完整命令")
    def read_cmd():
        try:
            from prompt_toolkit.completion import Completer, Completion
            from prompt_toolkit.shortcuts import prompt
            
            # Command dictionary with usage hints
            COMMANDS = {
                "/catlog": "浏览目录",
                "/catalog": "浏览目录",
                "/new": "<标题> 新建章节并进入",
                "/open": "<编号> 打开指定章节",
                "/latest": "打开最新一章",
                "/del": "<编号> 删除指定章节",
                "/rename": "<编号> <新标题> 重命名",
                "/stats": "统计字数",
                "/find": "<关键词> 搜索内容",
                "/folder": "在文件管理器中打开小说目录",
                "/help": "查看帮助",
                "/exit": "退出程序",
                "/q": "退出程序",
            }

            class SlashCompleter(Completer):
                def get_completions(self, document, complete_event):
                    text = document.text_before_cursor.lstrip()
                    # Only complete if we are at the start of the line or just typed a slash
                    for cmd, meta in COMMANDS.items():
                        if cmd.startswith(text):
                            yield Completion(
                                cmd,
                                start_position=-len(text),
                                display_meta=meta
                            )

            completer = SlashCompleter()
            return prompt(
                "momo> ",
                completer=completer,
                complete_while_typing=True,
            )
        except Exception:
            return input("momo> ")

    while True:
        cmd = read_cmd().strip()
        if cmd in ("/exit", "/quit", "/q", "exit", "quit", "q"):
            return
        if cmd in ("/help", "help"):
            print("命令列表：")
            print("  /catlog 或 /catalog  查看目录并选择章节")
            print("  /new <标题>          新建章节并进入")
            print("  /open <编号>         打开指定章节")
            print("  /latest              打开最新一章")
            print("  /folder              在文件管理器中打开")
            print("  /rename <编号> <标题> 重命名章节")
            print("  /del <编号>          删除指定章节")
            print("  /stats               统计字数")
            print("  /find <关键词>       搜索关键词")
            print("  /exit 或 /q          退出")
            continue
        if cmd in ("/folder", "folder"):
            try:
                if sys.platform == "win32":
                    os.startfile(root)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.call(["open", root])
                else:
                    import subprocess
                    subprocess.call(["xdg-open", root])
                print(f"已打开目录: {root}")
            except Exception as e:
                print(f"无法打开目录: {e}")
            continue
        if cmd in ("/catlog", "/catalog"):
            idx = select_chapter(state)
            if idx is not None:
                should_exit = chapter_shell(root, state, idx)
                if should_exit:
                    return
            state = load_state(root)
            continue
        if cmd.startswith("/new "):
            title = cmd[5:].strip()
            if not title:
                print("Title required.")
                continue
            chapter = create_chapter(root, state, title)
            print(f"Created: {chapter['title']}")
            should_exit = chapter_shell(root, state, len(state["chapters"]) - 1)
            if should_exit:
                return
            state = load_state(root)
            continue
        if cmd.startswith("/open "):
            raw = cmd[6:].strip()
            if not raw.isdigit():
                print("Use /open <number>.")
                continue
            idx = int(raw) - 1
            if idx < 0 or idx >= len(state["chapters"]):
                print("Out of range.")
                continue
            should_exit = chapter_shell(root, state, idx)
            if should_exit:
                return
            state = load_state(root)
            continue
        if cmd.startswith("/rename "):
            raw = cmd[8:].strip()
            parts = raw.split(maxsplit=1)
            if len(parts) < 2 or not parts[0].isdigit():
                print("Use /rename <number> <title>.")
                continue
            idx = int(parts[0]) - 1
            if idx < 0 or idx >= len(state["chapters"]):
                print("Out of range.")
                continue
            new_title = parts[1].strip()
            if not new_title:
                print("Title required.")
                continue
            chapter = state["chapters"][idx]
            old_path = chapter_path(root, chapter)
            chapter["title"] = new_title
            new_filename = f"{chapter['id']}_{safe_filename(new_title)}.md"
            new_rel_path = os.path.join(PROJECT_DIR, CHAPTERS_DIR, new_filename)
            new_abs_path = os.path.join(root, new_rel_path)
            if old_path != new_abs_path:
                try:
                    os.replace(old_path, new_abs_path)
                except FileNotFoundError:
                    pass
                chapter["file"] = new_rel_path
            save_state(root, state)
            print("Renamed.")
            continue
        if cmd in ("/stats", "stats"):
            stats_all(root, state)
            continue
        if cmd.startswith("/find "):
            keyword = cmd[6:].strip()
            find_in_chapters(root, state, keyword)
            continue
        if cmd in ("/latest", "latest"):
            if not state["chapters"]:
                print("No chapters yet.")
                continue
            should_exit = chapter_shell(root, state, len(state["chapters"]) - 1)
            if should_exit:
                return
            state = load_state(root)
            continue
        if cmd.startswith("/del "):
            raw = cmd[5:].strip()
            if not raw.isdigit():
                print("Use /del <number>.")
                continue
            idx = int(raw) - 1
            if idx < 0 or idx >= len(state["chapters"]):
                print("Out of range.")
                continue
            chapter = state["chapters"][idx]
            confirm = input(f"Delete chapter '{chapter['title']}'? (y/N): ").strip().lower()
            if confirm != "y":
                print("Canceled.")
                continue
            try:
                os.remove(os.path.join(root, chapter["file"]))
            except FileNotFoundError:
                pass
            del state["chapters"][idx]
            save_state(root, state)
            print("Deleted.")
            continue
        if cmd:
            print("Unknown command. Use /help.")


def run_init_interactive(cwd):
    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.styles import Style

    # Load config to get default root for display
    config = load_global_config()
    default_root = config.get("default_root", "未设置")

    options = [
        f"1. 快速创建新书 (默认保存至 {default_root})",
        "2. 在当前文件夹下创建 (适合已创建好空文件夹的情况)",
        "3. 自定义路径创建 (手动指定完整路径)",
        "4. 暂不创建，退出"
    ]
    selected = 0

    def get_formatted_text():
        lines = []
        lines.append(("", "👋 欢迎！您还没有创建过小说，请选择一种方式创建一个新小说：\n"))
        lines.append(("", "\n"))
        for i, opt in enumerate(options):
            prefix = "> " if i == selected else "  "
            # Use 'class:selected' to reference the style defined in Style.from_dict
            style = "class:selected" if i == selected else ""
            lines.append((style, prefix + opt + "\n"))
        return lines

    kb = KeyBindings()

    @kb.add("up")
    def _(event):
        nonlocal selected
        selected = (selected - 1) % len(options)

    @kb.add("down")
    def _(event):
        nonlocal selected
        selected = (selected + 1) % len(options)

    @kb.add("enter")
    def _(event):
        event.app.exit(result=selected)

    @kb.add("c-c")
    @kb.add("escape")
    def _(event):
        event.app.exit(result=None)

    style = Style.from_dict({
        "selected": "bg:#1c1c1c #d0d0d0"
    })

    app = Application(
        layout=Layout(Window(FormattedTextControl(get_formatted_text))),
        key_bindings=kb,
        full_screen=True,
        style=style,
    )

    choice_idx = app.run()

    if choice_idx is None or choice_idx == 3:
        print("已取消/退出。")
        return None

    # Option 1: Default Path
    if choice_idx == 0:
        config = load_global_config()
        default_root = config.get("default_root")
        if not default_root:
            print("默认目录未设置。")
            path_input = input("请输入默认小说存储路径: ").strip()
            if not path_input:
                print("路径不能为空。")
                return None
            default_root = os.path.abspath(os.path.expanduser(path_input))
            try:
                os.makedirs(default_root, exist_ok=True)
            except Exception as e:
                print(f"无法创建目录: {e}")
                return None
            config["default_root"] = default_root
            save_global_config(config)
            print(f"已设置默认路径: {default_root}")
        
        print(f"默认小说根目录: {default_root}")
        title = input("请输入书名: ").strip()
        if not title:
            print("书名不能为空。")
            return None
        target = os.path.join(default_root, safe_filename(title))
        if os.path.exists(target) and os.listdir(target):
            print("目标目录已存在且非空。")
            return None
        os.makedirs(target, exist_ok=True)
        init_project(target, title_override=title)
        register_novel(target)
        return target

    # Option 2: Current Dir
    if choice_idx == 1:
        print(f"当前目录: {cwd}")
        print("提示: 建议在新建的空目录中进行初始化。")
        title = input("请输入书名: ").strip()
        if not title:
            print("书名不能为空。")
            return None
        init_project(cwd, title_override=title)
        register_novel(cwd)
        return cwd

    # Option 3: Specify Path
    if choice_idx == 2:
        target = input("请输入小说路径: ").strip()
        if not target:
            print("路径不能为空。")
            return None
        title = input("请输入书名: ").strip()
        if not title:
            print("书名不能为空。")
            return None
        if os.path.exists(target) and os.listdir(target):
            print("目标目录已存在且非空。")
            return None
        os.makedirs(target, exist_ok=True)
        init_project(target, title_override=title)
        register_novel(target)
        return target
    
    return None


def main():
    parser = argparse.ArgumentParser(description="momo: CLI writing tool")
    sub = parser.add_subparsers(dest="command")
    init_parser = sub.add_parser("init", help="initialize novel project")
    init_parser.add_argument("name", nargs="?", help="novel name to create under default root")
    config_parser = sub.add_parser("config", help="show or set global config")
    config_parser.add_argument("action", nargs="?", default="show", help="show or root")
    config_parser.add_argument("value", nargs="?", help="value for action")
    args = parser.parse_args()

    cwd = os.getcwd()
    if args.command == "init":
        path = run_init_interactive(cwd)
        if path:
            momo_shell(path)
        return

    if args.command == "config":
        config = load_global_config()
        if args.action in ("show", None):
            print(f"default_root: {config.get('default_root','')}")
            novels = config.get("novels", [])
            if not novels:
                print("novels: (empty)")
                return
            print("novels:")
            for idx, novel in enumerate(novels, 1):
                title = novel.get("title") or os.path.basename(novel.get("path", ""))
                print(f"  {idx:02d}. {title}  [{novel.get('path','')}]")
            return
        if args.action == "root":
            if not args.value:
                print(f"default_root: {config.get('default_root','')}")
                print("Usage: momo config root <path>")
                return
            config["default_root"] = os.path.abspath(args.value)
            save_global_config(config)
            print(f"default_root set to: {config['default_root']}")
            return
        print("Unknown config action. Use: momo config show | momo config root <path>")
        return

    root = project_root(cwd)
    if root:
        momo_shell(root)
        return
    
    config = load_global_config()
    novels = [n for n in config.get("novels", []) if n.get("path")]
    if not novels:
        print("欢迎使用 momo 写作工具！")
        print("当前没有已登记的小说，正在进入创建向导...")
        path = run_init_interactive(cwd)
        if path:
            momo_shell(path)
        return

    novel = select_novel(config)
    if not novel:
        return
    root = novel.get("path", "")
    if not root or not os.path.isdir(root):
        print("Selected novel path missing.")
        return
    os.chdir(root)
    momo_shell(root)


if __name__ == "__main__":
    main()
