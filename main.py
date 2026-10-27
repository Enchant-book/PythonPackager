import tkinter as tk
from tkinter import ttk, filedialog
import subprocess
import os

class MainWindow(tk.Tk):
    __version__ = "1.0.261027"
    path_file = ""
    path_dir = ""

    def __init__(self):
        tk.Tk.__init__(self)
        self.withdraw()
        h,w = 600, 400
        self.geometry("%dx%d+%d+%d" %(h, w, (self.winfo_screenwidth() - w) // 2, (self.winfo_screenheight() - h) // 2))
        self.iconbitmap("pyp.ico")
        self.title("PythonPackager")
        self.resizable(False, False)
        self.deiconify()

        self.menubar = tk.Menu(self)
        self.config(menu=self.menubar)
        self.menu_file = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="文件", menu=self.menu_file)
        self.menu_file.add_command(label="打开文件", command=self.open_file)
        self.menu_file.add_command(label="打开文件夹", command=self.open_dir)
        self.menu_help = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="帮助", menu=self.menu_help)
        self.menu_help.add_command(label="使用指南", command=self.usage)
        self.menu_help.add_command(label="关于", command=self.about)

        l0 = tk.Label(self.menubar, text="PythonPackager")


    def open_file(self):
        path = os.path.normpath(filedialog.askopenfilename())
        if os.path.exists(path) and path != ".":
            self.path_file = path
        print(self.path_file)

    def open_dir(self):
        self.path_dir = os.path.normpath(filedialog.askdirectory())
        print(self.path_dir)

    def usage(self):
        top = tk.Toplevel()
        h, w = 300, 200
        top.geometry("%dx%d+%d+%d" %(h, w, self.winfo_x(), self.winfo_y()))
        top.iconbitmap("pyp.ico")
        top.title("使用指南")
        with open("usage", "r") as f:
            str_content = str(f.read())
        tktext_content= tk.Text(top)
        tktext_content.insert(tk.END, str_content)
        tktext_content.configure(relief="flat" , state="disabled", bg="SystemButtonFace")
        tkscrollbar = tk.Scrollbar(top, orient="vertical", command=tktext_content.yview, relief="flat")
        tkscrollbar.pack(side="right", fill="y")
        tktext_content.pack(expand=True, fill="both")
        top.mainloop()

    def about(self):
        top = tk.Toplevel()
        h, w = 300, 200
        top.geometry("%dx%d+%d+%d" % (h, w, self.winfo_x(), self.winfo_y()))
        top.iconbitmap("pyp.ico")
        top.title("关于")
        str_content = (f"版本  PythonPackager v{self.__version__}\n"
                       "作者  Enchant-Book")
        tktext_content0 = tk.Text(top)
        tktext_content0.insert(tk.END, str_content)
        tktext_content0.configure(relief="flat", state="disabled", bg="SystemButtonFace")
        tkscrollbar0 = tk.Scrollbar(top, orient="vertical", command=tktext_content0.yview, relief="flat")
        tkscrollbar0.pack(side="right", fill="y")
        tktext_content0.pack(expand=True, fill="both")

        top.mainloop()




def main():
    app = MainWindow()
    app.mainloop()

if __name__ == '__main__':
    main()