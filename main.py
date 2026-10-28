import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class MainWindow(tk.Tk):
    __version__ = "1.1.261028"

    def __init__(self):
        super().__init__()
        self.path_file = ""
        self.path_icon = ""
        self.path_dir = ""
        self.withdraw()
        self.title("PythonPackager")
        self.resizable(False, False)
        self._set_window_icon()
        self._configure_styles()
        self._build_menu()
        self._build_ui()
        self._center_window()
        self.deiconify()

    def _set_window_icon(self):
        icon_path = Path(__file__).resolve().with_name("pyp.ico")
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except tk.TclError:
                pass

    def _build_menu(self):
        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.menu_help = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="帮助", menu=self.menu_help)
        self.menu_help.add_command(label="使用指南", command=self.usage)
        self.menu_help.add_command(label="关于", command=self.about)

    def _configure_styles(self):
        style = ttk.Style(self)
        for theme in ("vista", "xpnative", "winnative"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break

    def _build_ui(self):
        self.frame_main = ttk.Frame(self, padding=(24, 20))
        self.frame_main.pack(expand=True, fill="both")

        ttk.Label(self.frame_main, text="PythonPackager", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(self.frame_main, text="将 Python 脚本打包为可执行程序").pack(anchor="w", pady=(4, 16))
        ttk.Label(
            self.frame_main,
            text="提示：图标和运行时资源需要单独添加；打包环境及常见问题请查看“帮助 > 使用指南”。",
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        fields = ttk.Frame(self.frame_main, padding=(12, 8))
        fields.pack(fill="x")
        self._add_path_field(fields, 0, "Python 源文件", "entry_file", (("Python Files", "*.py"), ("All Files", "*.*")), "path_file")
        self._add_path_field(fields, 1, "程序图标（可选）", "entry_icon", (("Icon Files", "*.ico"), ("All Files", "*.*")), "path_icon")
        self._add_directory_field(fields, 2, "输出位置")
        ttk.Label(fields, text="输出程序名（留空则使用源文件名）").grid(row=6, column=0, columnspan=2, sticky="w", pady=(12, 5))
        self.entry_name = ttk.Entry(fields)
        self.entry_name.grid(row=7, column=0, columnspan=2, sticky="ew")
        fields.columnconfigure(0, weight=1)

        options_frame = ttk.LabelFrame(self.frame_main, text="打包选项", padding=(12, 8))
        options_frame.pack(fill="x", pady=(14, 0))
        self.onefile_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="打包为单个文件", variable=self.onefile_var).pack(anchor="w", pady=3)
        self.console_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="显示控制台窗口", variable=self.console_var).pack(anchor="w", pady=3)
        self.clean_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="打包前清理缓存", variable=self.clean_var).pack(anchor="w", pady=3)

        self.advanced_visible = False
        self.advanced_button = ttk.Button(
            self.frame_main,
            text="高级选项 (展开)",
            command=self._toggle_advanced_options,
        )
        self.advanced_button.pack(anchor="w", pady=(10, 0))
        self.advanced_viewport = ttk.Frame(self.frame_main)
        self.advanced_canvas = tk.Canvas(
            self.advanced_viewport,
            height=165,
            highlightthickness=0,
            borderwidth=0,
        )
        self.advanced_scrollbar = ttk.Scrollbar(
            self.advanced_viewport,
            orient="vertical",
            command=self.advanced_canvas.yview,
        )
        self.advanced_canvas.configure(yscrollcommand=self.advanced_scrollbar.set)
        self.advanced_canvas.pack(side="left", fill="both", expand=True)
        self.advanced_scrollbar.pack(side="right", fill="y")
        self.advanced_frame = ttk.LabelFrame(self.advanced_canvas, text="高级选项", padding=(12, 8))
        self.advanced_canvas_window = self.advanced_canvas.create_window(
            (0, 0),
            window=self.advanced_frame,
            anchor="nw",
        )
        self.advanced_frame.bind("<Configure>", self._update_advanced_scrollregion)
        self.advanced_canvas.bind("<Configure>", self._resize_advanced_content)
        self.bind_all("<MouseWheel>", self._on_advanced_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_advanced_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_advanced_mousewheel, add="+")
        ttk.Label(self.advanced_frame, text="隐藏导入模块（多个模块用逗号分隔）").pack(anchor="w", pady=(2, 5))
        self.entry_hidden_imports = ttk.Entry(self.advanced_frame)
        self.entry_hidden_imports.pack(fill="x", pady=(0, 10))
        ttk.Label(self.advanced_frame, text="收集整个依赖包（多个包用逗号分隔）").pack(anchor="w", pady=(0, 5))
        self.entry_collect_all = ttk.Entry(self.advanced_frame)
        self.entry_collect_all.pack(fill="x", pady=(0, 10))
        ttk.Label(self.advanced_frame, text="排除模块（多个模块用逗号分隔）").pack(anchor="w", pady=(0, 5))
        self.entry_excludes = ttk.Entry(self.advanced_frame)
        self.entry_excludes.pack(fill="x", pady=(0, 10))
        ttk.Label(self.advanced_frame, text="附加文件和文件夹").pack(anchor="w", pady=(0, 5))
        data_frame = ttk.Frame(self.advanced_frame)
        data_frame.pack(fill="x")
        self.data_listbox = tk.Listbox(data_frame, height=4, exportselection=False)
        self.data_listbox.pack(side="left", fill="both", expand=True)
        data_scrollbar = ttk.Scrollbar(data_frame, orient="vertical", command=self.data_listbox.yview)
        data_scrollbar.pack(side="left", fill="y")
        self.data_listbox.configure(yscrollcommand=data_scrollbar.set)
        data_buttons = ttk.Frame(data_frame)
        data_buttons.pack(side="left", fill="y", padx=(8, 0))
        ttk.Button(data_buttons, text="添加文件...", command=self._add_data_file).pack(fill="x", pady=(0, 5))
        ttk.Button(data_buttons, text="添加文件夹...", command=self._add_data_directory).pack(fill="x", pady=(0, 5))
        ttk.Button(data_buttons, text="移除所选", command=self._remove_data_item).pack(fill="x")
        self.data_items = []
        self.upx_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.advanced_frame,
            text="使用 UPX 压缩（需安装 UPX 并加入 PATH）",
            variable=self.upx_var,
        ).pack(anchor="w", pady=(10, 3))

        self.button_pack = ttk.Button(self.frame_main, text="开始打包", command=self.pack_project)
        self.button_pack.pack(anchor="e", pady=(16, 0), ipadx=8)

    def _add_path_field(self, parent, row, label, entry_name, filetypes, attr_name):
        ttk.Label(parent, text=label).grid(row=row * 2, column=0, columnspan=2, sticky="w", pady=(3 if row == 0 else 12, 5))
        entry = ttk.Entry(parent)
        entry.grid(row=row * 2 + 1, column=0, sticky="ew", padx=(0, 9))
        setattr(self, entry_name, entry)
        ttk.Button(
            parent,
            text="浏览...",
            command=lambda: self.open_file(entry, filetypes, attr_name),
        ).grid(row=row * 2 + 1, column=1)

    def _add_directory_field(self, parent, row, label):
        ttk.Label(parent, text=label).grid(row=row * 2, column=0, columnspan=2, sticky="w", pady=(12, 5))
        self.entry_dir = ttk.Entry(parent)
        self.entry_dir.grid(row=row * 2 + 1, column=0, sticky="ew", padx=(0, 9))
        ttk.Button(parent, text="浏览...", command=lambda: self.open_dir(self.entry_dir)).grid(row=row * 2 + 1, column=1)

    def _toggle_advanced_options(self):
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced_viewport.pack(fill="x", pady=(6, 0), after=self.advanced_button)
            self.advanced_button.configure(text="高级选项 (收起)")
        else:
            self.advanced_viewport.pack_forget()
            self.advanced_button.configure(text="高级选项 (展开)")

        self.update_idletasks()
        width = 600
        height = self.frame_main.winfo_reqheight() + 4
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _update_advanced_scrollregion(self, _event=None):
        self.advanced_canvas.configure(scrollregion=self.advanced_canvas.bbox("all"))

    def _resize_advanced_content(self, event):
        self.advanced_canvas.itemconfigure(self.advanced_canvas_window, width=event.width)

    def _on_advanced_mousewheel(self, event):
        if not self.advanced_visible:
            return

        widget = event.widget
        while widget is not None and widget is not self.advanced_canvas:
            widget = getattr(widget, "master", None)
        if widget is None:
            return

        if getattr(event, "num", None) == 4:
            units = -1
        elif getattr(event, "num", None) == 5:
            units = 1
        else:
            delta = getattr(event, "delta", 0)
            units = -int(delta / 120) if delta else 0
            if units == 0 and delta:
                units = -1 if delta > 0 else 1

        if units:
            self.advanced_canvas.yview_scroll(units, "units")
        return "break"

    def _add_data_file(self):
        path = filedialog.askopenfilename(title="选择要附加的文件")
        if path:
            self._append_data_item(Path(path), ".")

    def _add_data_directory(self):
        path = filedialog.askdirectory(title="选择要附加的文件夹")
        if path:
            directory = Path(path)
            self._append_data_item(directory, directory.name)

    def _append_data_item(self, path, destination):
        path = path.resolve()
        if not path.exists():
            messagebox.showerror("错误", f"附加路径不存在：\n{path}")
            return
        if any(existing_path == path for existing_path, _ in self.data_items):
            return
        self.data_items.append((path, destination))
        self.data_listbox.insert(tk.END, f"{path}  →  {destination}")

    def _remove_data_item(self):
        selection = self.data_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        self.data_listbox.delete(index)
        del self.data_items[index]

    def _center_window(self):
        self.update_idletasks()
        width = 600
        height = self.frame_main.winfo_reqheight() + 4
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def open_file(self, output: ttk.Entry, filetypes=(("Python Files", "*.py"), ("All Files", "*.*")), attr_name="path_file"):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if not path:
            return
        normalized = os.path.normpath(path)
        if os.path.exists(normalized) and normalized != ".":
            setattr(self, attr_name, normalized)
        output.delete(0, tk.END)
        output.insert(0, getattr(self, attr_name, normalized))

    def open_dir(self, output: ttk.Entry):
        path = filedialog.askdirectory()
        if not path:
            return
        normalized = os.path.normpath(path)
        self.path_dir = normalized
        output.delete(0, tk.END)
        output.insert(0, self.path_dir)

    def pack_project(self):
        script_path = Path(self.entry_file.get().strip())
        if not script_path or not script_path.exists() or script_path.suffix.lower() != ".py":
            messagebox.showerror("错误", "请选择有效的 Python 源文件。")
            return

        output_name = self.entry_name.get().strip() or script_path.stem
        if output_name.lower().endswith(".exe"):
            output_name = output_name[:-4]
        if (
            not output_name
            or output_name in {".", ".."}
            or output_name[-1] in {" ", "."}
            or any(ord(char) < 32 or char in '<>:"/\\|?*' for char in output_name)
            or output_name.split(".")[0].upper() in {
                "CON", "PRN", "AUX", "NUL",
                *(f"COM{number}" for number in range(1, 10)),
                *(f"LPT{number}" for number in range(1, 10)),
            }
        ):
            messagebox.showerror("错误", "程序名不能为空，也不能包含 Windows 文件名不允许的字符或保留名称。")
            return

        output_dir = Path(self.entry_dir.get().strip()) if self.entry_dir.get().strip() else script_path.resolve().parent
        output_dir.mkdir(parents=True, exist_ok=True)

        icon_path = Path(self.entry_icon.get().strip()) if self.entry_icon.get().strip() else None
        if icon_path:
            if not icon_path.is_file():
                messagebox.showerror("错误", "图标文件不存在或不是文件，请重新选择。")
                return
            if icon_path.suffix.lower() != ".ico":
                messagebox.showerror("错误", "Windows 程序图标必须是 .ico 格式。")
                return

        app_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
        packages_dir = app_dir / "packages"
        environment = os.environ.copy()
        existing_pythonpath = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = str(packages_dir) if not existing_pythonpath else str(packages_dir) + os.pathsep + existing_pythonpath
        python_command = self._get_python_command()
        if python_command is None:
            messagebox.showerror(
                "错误",
                "打包版程序不能把自身当作 Python 解释器使用。请先在系统中安装 Python，并确保 python 或 py 命令可用。",
            )
            return

        installed = subprocess.run(
            [*python_command, "-c", "import PyInstaller"],
            capture_output=True,
            text=True,
            env=environment,
        )
        if installed.returncode != 0:
            install = messagebox.askquestion(
                "缺少 PyInstaller",
                f"程序目录中尚未安装 PyInstaller。\n是否安装到：\n{packages_dir}",
                icon="warning",
            )
            if install == "yes":
                try:
                    subprocess.check_call([
                        *python_command,
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        "--target",
                        str(packages_dir),
                        "pyinstaller",
                    ])
                    messagebox.showinfo("安装成功", "PyInstaller 已安装到程序目录的 packages 文件夹，请重新尝试打包。")
                except subprocess.CalledProcessError as error:
                    messagebox.showerror("安装失败", f"安装 PyInstaller 失败（退出代码 {error.returncode}）。")
            return

        command = [*python_command, "-m", "PyInstaller"]
        if self.onefile_var.get():
            command.append("--onefile")
        if not self.console_var.get():
            command.append("--noconsole")
        if self.clean_var.get():
            command.append("--clean")
        command.extend(["--name", output_name, str(script_path)])
        if icon_path:
            command.extend(["--icon", str(icon_path)])
        for module_name in self._parse_comma_separated(self.entry_hidden_imports.get()):
            command.extend(["--hidden-import", module_name])
        for package_name in self._parse_comma_separated(self.entry_collect_all.get()):
            command.extend(["--collect-all", package_name])
        for module_name in self._parse_comma_separated(self.entry_excludes.get()):
            command.extend(["--exclude-module", module_name])
        for data_path, destination in self.data_items:
            if not data_path.exists():
                messagebox.showerror("错误", f"附加路径不存在：\n{data_path}")
                return
            command.extend(["--add-data", f"{data_path};{destination}"])
        if self.upx_var.get():
            upx_path = shutil.which("upx")
            if not upx_path:
                messagebox.showerror(
                    "缺少 UPX",
                    "已启用 UPX 压缩，但系统 PATH 中找不到 upx.exe。请安装 UPX 并将其加入 PATH 后重试。",
                )
                return
            command.extend(["--upx-dir", str(Path(upx_path).resolve().parent)])
        command.extend(["--distpath", str(output_dir)])

        exe_file = output_dir / f"{output_name}.exe"
        if not self.onefile_var.get():
            exe_file = output_dir / output_name / exe_file.name
        self._start_packaging(command, environment, exe_file)

    @staticmethod
    def _parse_comma_separated(value):
        return [item.strip() for item in value.replace("\n", ",").split(",") if item.strip()]

    def _start_packaging(self, command, environment, exe_file):
        dialog = tk.Toplevel(self)
        dialog.title("正在打包")
        dialog.resizable(False, False)
        self._prepare_dialog(dialog, 520, 330)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        container = ttk.Frame(dialog, padding=18)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="正在创建可执行程序", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Label(container, text=f"目标文件：{exe_file.name}").pack(anchor="w", pady=(5, 14))

        progress = ttk.Progressbar(
            container,
            mode="indeterminate",
            length=470,
        )
        progress.pack(fill="x")
        progress.start(10)

        status = ttk.Label(container, text="正在启动 PyInstaller...")
        status.pack(anchor="w", pady=(10, 8))
        log_output = tk.Text(
            container,
            height=7,
            width=62,
            state="disabled",
            wrap="word",
        )
        log_output.pack(fill="both", expand=True)
        ttk.Label(container, text="首次打包可能需要几分钟，请稍候。").pack(anchor="w", pady=(10, 0))
        dialog.grab_set()
        self.button_pack.configure(state="disabled")

        events = queue.Queue()
        threading.Thread(
            target=self._packaging_worker,
            args=(command, environment, events),
            daemon=True,
        ).start()
        self._poll_packaging(events, dialog, progress, status, log_output, exe_file)

    @staticmethod
    def _packaging_worker(command, environment, events):
        try:
            with tempfile.TemporaryDirectory(prefix="PythonPackager-") as build_dir:
                command.extend([
                    "--workpath",
                    str(Path(build_dir) / "build"),
                    "--specpath",
                    str(Path(build_dir) / "spec"),
                ])
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=environment,
                )
                if process.stdout is not None:
                    for line in process.stdout:
                        events.put(("log", line.rstrip()))
                return_code = process.wait()
            events.put(("finished", return_code))
        except OSError as error:
            events.put(("error", str(error)))

    def _poll_packaging(self, events, dialog, progress, status, log_output, exe_file):
        finished = None
        while True:
            try:
                event, value = events.get_nowait()
            except queue.Empty:
                break

            if event == "log" and value:
                status.configure(text=value[-90:])
                log_output.configure(state="normal")
                log_output.insert(tk.END, value + "\n")
                if int(log_output.index("end-1c").split(".")[0]) > 100:
                    log_output.delete("1.0", "2.0")
                log_output.see(tk.END)
                log_output.configure(state="disabled")
            elif event in ("finished", "error"):
                finished = (event, value)

        if finished is None:
            self.after(100, self._poll_packaging, events, dialog, progress, status, log_output, exe_file)
            return

        progress.stop()
        dialog.grab_release()
        dialog.destroy()
        self.button_pack.configure(state="normal")
        if finished[0] == "error":
            messagebox.showerror("打包失败", f"无法启动 PyInstaller：\n{finished[1]}")
        elif finished[1] != 0:
            messagebox.showerror("打包失败", f"PyInstaller 退出代码：{finished[1]}\n请查看打包日志以定位问题。")
        else:
            messagebox.showinfo("打包成功", f"可执行文件：{exe_file}")

    @staticmethod
    def _get_python_command():
        if not getattr(sys, "frozen", False):
            return [sys.executable]

        python_path = shutil.which("python")
        if python_path:
            return [python_path]

        launcher_path = shutil.which("py")
        if launcher_path:
            return [launcher_path, "-3"]
        return None

    def usage(self):
        top = tk.Toplevel(self)
        top.title("使用指南")
        self._prepare_dialog(top, 460, 340)
        with open(Path(__file__).resolve().with_name("usage"), "r", encoding="utf-8") as usage_file:
            content = usage_file.read()

        container = ttk.Frame(top, padding=14)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="使用指南", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        content_frame = ttk.Frame(container)
        content_frame.pack(fill="both", expand=True)
        text_widget = tk.Text(content_frame, wrap="word")
        text_widget.insert(tk.END, content)
        text_widget.configure(state="disabled")
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", expand=True, fill="both")
        ttk.Button(container, text="关闭", command=top.destroy).pack(anchor="e", pady=(10, 0))
        top.grab_set()

    def about(self):
        top = tk.Toplevel(self)
        top.title("关于")
        self._prepare_dialog(top, 340, 210)
        container = ttk.Frame(top, padding=18)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="PythonPackager", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        ttk.Separator(container).pack(fill="x", pady=12)
        ttk.Label(container, text=f"版本  {self.__version__}").pack(anchor="w")
        ttk.Label(container, text="作者  Enchant-Book").pack(anchor="w", pady=(8, 0))
        ttk.Button(container, text="关闭", command=top.destroy).pack(anchor="e", pady=(14, 0))
        top.grab_set()

    def _prepare_dialog(self, window, width, height):
        window.transient(self)
        window.resizable(False, False)
        self._set_window_icon_for(window)
        window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - width) // 2
        y = self.winfo_y() + (self.winfo_height() - height) // 2
        window.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def _set_window_icon_for(self, window):
        icon_path = Path(__file__).resolve().with_name("pyp.ico")
        if icon_path.exists():
            try:
                window.iconbitmap(str(icon_path))
            except tk.TclError:
                pass


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()