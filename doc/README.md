# Android Crash Stack Resolver

基于 NDK `llvm-addr2line` 的 Android native crash 堆栈解析工具。

## 前置要求

- Windows 操作系统（本工具仅支持 Windows）
- 无需安装 Python 或 NDK，所有依赖已内置

## 使用方法

双击 `CrashResolver.exe` 即可运行。确保 `tools/` 目录与 exe 在同一目录下。

1. 选择输入方式：
   - **方式 1（剪贴板）**：先在别处 `Ctrl+C` 复制好 crash 日志，选择此项后工具自动读取
   - **方式 2（文件）**：直接提供日志文件路径
2. 工具读取 crash 日志内容并解析 backtrace 帧
3. 输入 symbols 库所在目录
4. 输出解析结果
5. 可选保存到文件（保存后自动打开所在目录）

## 支持的日志格式

- **tombstone**：`#01 pc 0000000000001a3c  /vendor/lib64/libcam.so (func+0x1a4)`
- **logcat**：`#01 pc 0000000000001a3c  /vendor/lib64/libcam.so`

## 示例输出

```
#01 pc 0000000000001a3c  /vendor/lib64/camera/libcam.hal3a.ctrl.so (processRequest+0xb4)
  -> Camera3Device::processCaptureRequest(...)  @ device3/Camera3Device.cpp:452
```
