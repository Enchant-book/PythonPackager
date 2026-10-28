# PythonPackager

PythonPackager 是一个基于 Python 和 Tkinter 的 Windows 图形界面工具，用于将 Python 脚本打包为可执行程序。打包由 PyInstaller 完成。

## 功能

- 选择 Python 源文件、可选的 `.ico` 图标和输出目录。
- 输出目录留空时，默认输出到源文件所在目录。
- 设置输出程序名；留空时沿用源文件名。
- 选择单文件（`--onefile`）或目录模式。
- 控制生成程序是否显示控制台窗口。
- 打包前清理 PyInstaller 缓存。
- 高级选项支持：
  - 指定隐藏导入模块（`--hidden-import`）。
  - 收集整个依赖包（`--collect-all`）。
  - 排除模块（`--exclude-module`）。
  - 添加运行时需要的数据文件或文件夹（`--add-data`）。
  - 使用 UPX 压缩。
- 显示打包进度动画和 PyInstaller 实时日志；临时构建文件在任务结束后清理。

## 环境要求

- Windows
- Python 3
- Tkinter（通常随 Windows 版 Python 一起安装）
- 首次安装 PyInstaller 时需要网络连接

启用 UPX 压缩时，还需单独安装 UPX 并将其加入系统 `PATH`。

## 运行

在项目目录中运行：

```powershell
python main.py
```

也可以使用虚拟环境中的 Python：

```powershell
.\.venv\Scripts\python.exe main.py
```

如果当前 Python 环境无法导入 PyInstaller，程序会询问是否安装。PyInstaller 会安装到程序目录下的 `packages` 文件夹；安装成功后，重新点击“开始打包”即可。

## 使用步骤

1. 选择要打包的 `.py` 文件。
2. 可选：选择 `.ico` 图标文件。
3. 可选：选择输出文件夹；留空时输出到源文件目录。
4. 设置程序名和常用打包选项。
5. 需要额外设置时，展开“高级选项”并添加模块或数据文件。
6. 点击“开始打包”，在进度窗口查看 PyInstaller 日志。

多个隐藏导入模块、依赖包或排除模块使用逗号分隔。附加的单个文件放入程序的数据根目录；附加的文件夹会以原文件夹名放入数据目录。

## 打包本程序自身

1. 运行 PythonPackager，并选择项目中的 `main.py`。
2. 可将 `pyp.ico` 选作生成 exe 的图标。
3. 展开“高级选项”，添加项目中的 `usage` 和 `pyp.ico`。它们是运行时资源，仅将 `.ico` 设置为 exe 图标不会把这些文件作为程序可读取的资源附加进去。
4. 选择输出位置和选项后开始打包。

打包后的 PythonPackager 在运行打包功能时仍需要系统安装 Python（`python` 或 `py -3` 命令可用）。它会将 PyInstaller 安装到生成的 exe 同目录下的 `packages` 文件夹，因此该位置需要可写；首次安装也需要网络连接。

## 常见说明

- Windows 可执行程序应在 Windows 环境中构建。
- GUI 程序通常使用默认的“不显示控制台”设置；排查运行时错误时可启用控制台后重新打包。
- `--onefile` 程序首次启动时需要解压到临时目录，启动时间可能较长；部分安全软件可能会对自解压程序发出误报。
- 打包失败时，先查看进度窗口中的日志，并确认 Python 环境、网络连接、输入路径和资源路径正确。
- UPX 选项需要系统 `PATH` 中可以找到 `upx.exe`；启用后未找到 UPX 时程序会提示错误。
