from ui.main import Application
import tkinter as tk
import os
from monkey.patch import patch_no_window

patch_no_window()

if __name__ == '__main__':
    root = tk.Tk()
    theme_file_abs_path = os.path.join(os.path.dirname(__file__), "ui/azure.tcl")
    root.tk.call("source", theme_file_abs_path)
    root.tk.call("set_theme", "light")
    app = Application(master=root)
    root.mainloop()
