# Android Crash Stack Resolver / Android 崩溃堆栈解析器

[中文](#中文) | [English](#english)

---

## 中文

基于 NDK `llvm-addr2line` 的 Android native crash 堆栈解析工具。

### 前置要求

- Windows 操作系统（本工具仅支持 Windows）
- 无需安装 Python 或 NDK，所有依赖已内置

### 使用方法

双击 `CrashResolver.exe` 即可运行。确保 `tools/` 目录与 exe 在同一目录下。

1. 选择输入方式：
   - **方式 1（剪贴板）**：先在别处 `Ctrl+C` 复制好 crash 日志，选择此项后工具自动读取
   - **方式 2（文件）**：直接提供日志文件路径
2. 工具读取 crash 日志内容并解析 backtrace 帧
3. 输入 symbols 库所在目录
4. 输出解析结果
5. 可选保存到文件（保存后自动打开所在目录）

### 支持的日志格式

- **tombstone**：`#01 pc 0000000000001a3c  /vendor/lib64/libcam.so (func+0x1a4)`
- **logcat**：`#01 pc 0000000000001a3c  /vendor/lib64/libcam.so`

### 示例输出

```
#01 pc 0000000000001a3c  /vendor/lib64/camera/libcam.hal3a.ctrl.so (processRequest+0xb4)
  -> Camera3Device::processCaptureRequest(...)  @ device3/Camera3Device.cpp:452
```

### 项目结构

```
autoAddr2line/
├── CrashResolver.exe                   # 主程序（内置 Python 运行时）
├── src/
│   └── addr2line_tool.py               # 核心逻辑源码
├── tools/
│   ├── llvm-addr2line.exe              # NDK addr2line 工具
│   └── libwinpthread-1.dll             # 运行时依赖
└── doc/
    └── README.md
```

---

## English

An Android native crash stack resolver based on NDK `llvm-addr2line`.

### Prerequisites

- Windows OS (this tool is Windows-only)
- No Python or NDK installation required — all dependencies are bundled

### Usage

Double-click `CrashResolver.exe` to run. Make sure the `tools/` directory is in the same folder as the exe.

1. Choose input method:
   - **Method 1 (Clipboard)**: Copy the crash log with `Ctrl+C` first, then the tool reads it automatically
   - **Method 2 (File)**: Provide the log file path directly
2. The tool reads and parses backtrace frames from the crash log
3. Enter the directory containing symbol libraries
4. View the resolved output
5. Optionally save to file (auto-opens the folder after saving)

### Supported Log Formats

- **tombstone**: `#01 pc 0000000000001a3c  /vendor/lib64/libcam.so (func+0x1a4)`
- **logcat**: `#01 pc 0000000000001a3c  /vendor/lib64/libcam.so`

### Sample Output

```
#01 pc 0000000000001a3c  /vendor/lib64/camera/libcam.hal3a.ctrl.so (processRequest+0xb4)
  -> Camera3Device::processCaptureRequest(...)  @ device3/Camera3Device.cpp:452
```

### Project Structure

```
autoAddr2line/
├── CrashResolver.exe                   # Main executable (bundled Python runtime)
├── src/
│   └── addr2line_tool.py               # Core logic source
├── tools/
│   ├── llvm-addr2line.exe              # NDK addr2line binary
│   └── libwinpthread-1.dll             # Runtime dependency
└── doc/
    └── README.md
```
