#!/usr/bin/env python3
"""
Android crash stack resolver using NDK llvm-addr2line.

Usage: python addr2line_tool.py
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass

# ============================================================
# Paths
# ============================================================
if getattr(sys, "frozen", False):
    # PyInstaller 打包后，exe 所在目录即项目根目录
    _PROJECT_ROOT = os.path.dirname(os.path.abspath(sys.executable))
else:
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDR2LINE_PATH = os.path.join(_PROJECT_ROOT, "tools", "llvm-addr2line.exe")
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, ".addr2line_config")
# ============================================================


@dataclass
class Frame:
    """一条 backtrace 帧。"""
    num: int
    address: str
    lib_path: str
    func_hint: str = ""
    raw_line: str = ""


# 匹配 backtrace 行: #XX pc <hex_addr> <lib_path> [(func+offset)]
_FRAME_RE = re.compile(
    r"#(\d+)\s+pc\s+([0-9a-fA-F]+)\s+(\S+)"
)


def load_config() -> str:
    """读取上次保存的 symbols 目录。"""
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except Exception:
        return ""


def save_config(symbols_dir: str):
    """保存 symbols 目录。"""
    try:
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(symbols_dir)
    except Exception:
        pass


def check_tool():
    """启动时检查 llvm-addr2line 及依赖是否可用。"""
    dll_path = os.path.join(_PROJECT_ROOT, "tools", "libwinpthread-1.dll")
    if not os.path.isfile(ADDR2LINE_PATH):
        print(f"错误: 找不到 {ADDR2LINE_PATH}")
        print("请确认 tools 目录完整，包含 llvm-addr2line.exe 和 libwinpthread-1.dll")
        input("按回车退出...")
        sys.exit(1)
    if not os.path.isfile(dll_path):
        print(f"错误: 找不到 {dll_path}")
        print("请确认 tools 目录完整，包含 libwinpthread-1.dll")
        input("按回车退出...")
        sys.exit(1)


def _parse_line(line: str) -> Frame | None:
    """从一行中提取 backtrace 帧，无匹配返回 None。"""
    m = _FRAME_RE.search(line)
    if not m:
        return None
    func_hint = ""
    rest = line[m.end():]
    func_m = re.search(r"\((.+?)\)", rest)
    if func_m:
        func_hint = func_m.group(1)
    return Frame(
        num=int(m.group(1)),
        address=m.group(2),
        lib_path=m.group(3),
        func_hint=func_hint,
        raw_line=line.rstrip(),
    )


def parse_crash_log(text: str) -> list[Frame]:
    """从剪贴板文本中提取所有 backtrace 帧。"""
    frames: list[Frame] = []
    for line in text.splitlines():
        frm = _parse_line(line)
        if frm:
            frames.append(frm)
    return frames


def parse_crash_log_file(filepath: str) -> list[Frame]:
    """流式读取大日志文件，逐行提取 backtrace 帧，不一次性加载到内存。"""
    frames: list[Frame] = []
    file_size = os.path.getsize(filepath)
    print(f"正在流式解析日志文件 ({file_size / (1024*1024):.1f} MB)...")
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            frm = _parse_line(line)
            if frm:
                frames.append(frm)
                if len(frames) % 50 == 0:
                    print(f"  已提取 {len(frames)} 条帧...", flush=True)
    print(f"完成，共提取 {len(frames)} 条帧")
    return frames


def build_symbol_index(symbols_dir: str) -> dict[str, str]:
    """一次遍历 symbols 目录，返回 {basename: full_path} 映射。仅索引 .so 文件。"""
    index: dict[str, str] = {}
    for root, _dirs, files in os.walk(symbols_dir):
        for f in files:
            if f.endswith(".so") and f not in index:
                index[f] = os.path.join(root, f)
    return index


def resolve_address(symbol_so: str, address: str) -> str:
    """逐地址解析，每个地址独立调用 addr2line，确保输出格式可预测。"""
    try:
        result = subprocess.run(
            [ADDR2LINE_PATH, "--obj", symbol_so, "--functions", "--demangle", address],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return f"<addr2line 错误 ({address}): {result.stderr.strip()}>"

        lines = result.stdout.strip().splitlines()
        func = lines[0] if len(lines) > 0 else "??"
        loc = lines[1] if len(lines) > 1 else "??:0"

        if func == "??" and loc in ("??", "??:0"):
            return "<未解析到符号>"
        return f"{func}  @ {loc}"
    except FileNotFoundError:
        return "<找不到 tools/llvm-addr2line.exe>"
    except subprocess.TimeoutExpired:
        return f"<超时: {address}>"


def read_clipboard() -> str | None:
    """从剪贴板读取文本（Windows PowerShell）。"""
    try:
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        text = result.stdout
        if text.strip():
            return text
    except Exception:
        pass
    return None


def read_clipboard_input() -> tuple[str | None, str | None]:
    """引导用户先复制日志到剪贴板，工具自动读取。
    返回 (text, filepath) — 其中一个为 None，另一个有值。
    """
    print("请先在别处 Ctrl+C 复制好 crash 日志内容")
    input("复制完成后按回车继续...")
    print("(正在读取剪贴板...)")
    clipboard = read_clipboard()
    if clipboard:
        print(clipboard)
        print("--- 以上为剪贴板内容 ---")
        confirm = input("确认使用剪贴板内容? [Y/n]: ").strip().lower()
        if confirm in ("", "y", "yes"):
            return clipboard, None
        print("已取消。请重新复制日志后运行。")
        sys.exit(0)
    # 剪贴板为空，回退到文件路径
    print("剪贴板为空。")
    _fallback_filepath = input("请输入日志文件路径: ").strip().strip('"')
    if not os.path.isfile(_fallback_filepath):
        print(f"文件不存在: {_fallback_filepath}")
        sys.exit(1)
    return None, _fallback_filepath  # 标记文件模式，调用方走流式解析


def main():
    check_tool()

    print("=" * 60)
    print("Android Crash Stack Resolver (llvm-addr2line)")
    print("=" * 60)
    print()

    # ----- 步骤1: 获取日志内容 -----
    print("输入方式:")
    print("  1. 从剪贴板读取 crash 日志（请先在别处 Ctrl+C 复制好日志内容）")
    print("  2. 提供日志文件路径")
    print()
    choice = input("请选择 [1/2]: ").strip()

    if choice == "2":
        filepath = input("日志文件路径: ").strip().strip('"')
        if not os.path.isfile(filepath):
            print(f"文件不存在: {filepath}")
            input("按回车退出...")
            sys.exit(1)
        text = None  # 标记为文件模式，后续步骤2走流式解析
    else:
        print()
        text, filepath = read_clipboard_input()
    print()

    # ----- 步骤2: 解析日志 -----
    if text is not None:
        frames = parse_crash_log(text)
        is_file_mode = False
    else:
        frames = parse_crash_log_file(filepath)
        is_file_mode = True
    if not frames:
        print("未识别到任何 backtrace 行（格式: #XX pc <addr> <lib.so>）")
        input("按回车退出...")
        sys.exit(1)
    if not is_file_mode:
        print(f"识别到 {len(frames)} 条 backtrace 帧")
    print()

    # ----- 步骤3: 获取 symbols 目录 -----
    last_dir = load_config()
    if last_dir:
        symbols_dir = input(f"symbols 库所在目录 [{last_dir}]: ").strip().strip('"')
        if not symbols_dir:
            symbols_dir = last_dir
            print(f"使用上次的目录: {last_dir}")
    else:
        symbols_dir = input("请输入 symbols 库所在目录: ").strip().strip('"')

    if not os.path.isdir(symbols_dir):
        print(f"目录不存在: {symbols_dir}")
        input("按回车退出...")
        sys.exit(1)
    save_config(symbols_dir)
    print()

    # ----- 步骤4: 建立符号索引 & 分组 -----
    print("正在建立符号索引...", end=" ", flush=True)
    symbol_index = build_symbol_index(symbols_dir)
    print(f"完成（{len(symbol_index)} 个 .so 文件）")
    if len(symbol_index) == 0:
        print("警告: 未在目录中找到任何 .so 文件，所有帧可能无法解析。")
    print()

    batch: dict[str, list[tuple[int, str]]] = {}  # so_path -> [(frame_idx, address)]
    resolved_map: dict[int, str] = {}
    not_found_libs: set[str] = set()

    for i, f in enumerate(frames):
        lib_basename = os.path.basename(f.lib_path)
        symbol_so = symbol_index.get(lib_basename)
        if symbol_so is not None:
            batch.setdefault(symbol_so, []).append((i, f.address))
        else:
            not_found_libs.add(lib_basename)
            fallback = f"<未找到 symbol 文件: {lib_basename}>"
            if f.func_hint:
                fallback += f" (日志中的函数: {f.func_hint})"
            resolved_map[i] = fallback

    # ----- 步骤5: 逐地址解析（带进度） -----
    if batch:
        print(f"正在解析 {len(frames)} 条帧，涉及 {len(batch)} 个 symbol 库...")
        print()
        for idx, (symbol_so, items) in enumerate(batch.items(), 1):
            lib_name = os.path.basename(symbol_so)
            print(f"  [{idx}/{len(batch)}] 解析 {lib_name} ({len(items)} 个地址)...")
            for j, (frame_idx, addr) in enumerate(items):
                print(f"    [{j+1}/{len(items)}] {addr}...", end=" ", flush=True)
                resolved_map[frame_idx] = resolve_address(symbol_so, addr)
                print("完成")
        print()

    # ----- 步骤6: 输出结果 -----
    print("-" * 60)
    print("解析结果:")
    print("-" * 60)
    print()

    results: list[str] = []
    for i, f in enumerate(frames):
        raw = f.raw_line
        resolved = resolved_map[i]
        output_line = f"{raw}\n  -> {resolved}"
        print(output_line)
        print()
        results.append(output_line)

    # ----- 步骤7: 总结 -----
    found_count = len(batch)
    print("-" * 60)
    print(f"完成。共 {len(results)} 条，匹配到 {found_count} 个 symbol 库。")

    if not_found_libs:
        print(f"以下库未找到: {', '.join(sorted(not_found_libs))}")
    print()

    # ----- 步骤8: 可选保存 -----
    save = input("是否保存结果到文件? [Y/n]: ").strip().lower()
    if save in ("", "y", "yes"):
        out_path = input("保存路径 (默认 crash_resolved.txt): ").strip().strip('"')
        if not out_path:
            out_path = "crash_resolved.txt"
        abs_path = os.path.abspath(out_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(results))
            f.write("\n")
        print(f"已保存到: {abs_path}")
        save_dir = os.path.dirname(abs_path)
        os.startfile(save_dir)
        print("已在资源管理器中打开保存目录。")
        sys.exit(0)

    input("按回车退出...")


if __name__ == "__main__":
    main()
