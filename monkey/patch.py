import subprocess

# 这也许就是动态语言的魅力吧
def patch_no_window():
    original = subprocess.Popen.__init__
    
    def init_with_no_window(*args, **kwargs):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        original(*args, **kwargs)

    subprocess.Popen.__init__ = init_with_no_window









