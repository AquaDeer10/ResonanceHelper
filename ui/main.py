from game.helper import ResonanceHelper
from web.browser import Browser
import tkinter as tk
from tkinter import ttk
import threading
import sys
import typing as t
from game.rail import Site
from game.goods import GOODS_MAPPING, ALL_GOODS
from . import statics
import os
from PIL import Image
import pystray

class Application:
    def __init__(self, master: tk.Tk):
        self.master = master

        # 游戏相关数据初始化
        self.src = tk.StringVar()
        self.dst = tk.StringVar()

        # 进货列表
        self.src_goods: t.List[str] = []
        self.dst_goods: t.List[str] = []

        # 使用进货书次数
        self.src_extra_goods_num = tk.IntVar()
        self.dst_extra_goods_num = tk.IntVar()

        # 讲价次数
        self.src_exchange_price_buy_num = tk.IntVar()
        self.src_exchange_price_sell_num = tk.IntVar()

        self.dst_exchange_price_buy_num = tk.IntVar()
        self.dst_exchange_price_sell_num = tk.IntVar()

        # UI 界面
        self.master.title("共振助手")
        # 设置icon
        icon_path = os.path.join(os.path.dirname(__file__), "../icon/resonance.ico")
        self.master.iconbitmap(icon_path)

        self.src_radio_buttons: t.List[ttk.Radiobutton] = []
        self.dst_radio_buttons: t.List[ttk.Radiobutton] = []

        self.src_goods_checkbox: t.Dict[str, ttk.Checkbutton] = {}
        self.dst_goods_checkbox: t.Dict[str, ttk.Checkbutton] = {}

        # 主框架
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.up_frame = ttk.Frame(self.main_frame)
        self.up_frame.pack()
        self.down_frame = ttk.Frame(self.main_frame)
        self.down_frame.pack()
        self.create_src_and_dst(self.up_frame)
        
        self.start_end_frame = ttk.Frame(self.down_frame)
        self.start_end_frame.pack(pady=10)
        # 创建开始、停止按钮、从商会获取信息按钮
        self.start_button = ttk.Button(self.start_end_frame, text="开始", style="Accent.TButton", command=self.start, state=tk.NORMAL, width=statics.START_STOP_BUTTON_WIDTH)
        self.stop_button = ttk.Button(self.start_end_frame, text="停止", command=self.stop, state=tk.DISABLED, width=statics.START_STOP_BUTTON_WIDTH)
        self.start_browser_button = ttk.Button(self.start_end_frame, text="从商会获取信息", command=self.start_browser, width=statics.GET_INFO_BUTTON_WIDTH)

        self.start_button.pack(side=tk.LEFT, padx=10)
        self.stop_button.pack(side=tk.RIGHT, padx=10)
        self.start_browser_button.pack(side=tk.RIGHT, padx=10)

        # 创建圆角边框的日志框架
        self.log_frame = ttk.Labelframe(self.down_frame, text="日志")

        self.log_frame.pack(pady=10)
        
        # 创建日志框
        self.log = tk.Text(self.log_frame, height=statics.LOG_FRAME_HEIGHT, borderwidth=0, highlightthickness=0)

        # 设置只读
        self.log.config(state=tk.DISABLED)

        # 设置滚动条
        scroll = ttk.Scrollbar(self.log_frame, command=self.log.yview)
        self.log.config(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log.pack()

        # console 重定向
        sys.stdout = self
        sys.stderr = self

        # 子线程相关
        self.helper_event = threading.Event()
        self.browser_event = threading.Event()

        self.helper_thread: t.Optional[threading.Thread] = None
        self.browser_thread: t.Optional[threading.Thread] = None
        self.tray_thread: t.Optional[threading.Thread] = None

        # 助手初始化
        self.helper = ResonanceHelper(self.helper_event, self.stop_callback)

        # 浏览器初始化
        self.browser = Browser(self.browser_event, self.browser_callback)

        # 托盘图标
        image = Image.open(os.path.join(os.path.dirname(__file__), "../icon/resonance.ico"))
        image = image.resize((16, 16))
        self.tray_icon = pystray.Icon("resonance", image, "共振助手")
        self.tray_icon.menu = pystray.Menu(
            pystray.MenuItem("显示", self.show, default=True),
            pystray.MenuItem("隐藏", self.hide),
            pystray.MenuItem("退出", self.quit),
        )

        # 启动托盘线程
        self.tray_thread = threading.Thread(target=self.tray_icon.run)
        self.tray_thread.start()

        # 窗口关闭事件设置为隐藏
        self.master.protocol("WM_DELETE_WINDOW", self.hide)
        self._close = False
        self._notified = False

    def create_src_and_dst(self, frame):
        # 左侧框架
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 创建单选项
        for site in Site:
            button = ttk.Radiobutton(
                left_frame, 
                text=site.value, 
                variable=self.src, 
                value=site.value,
                command=self.src_select
            ).pack(anchor=tk.CENTER)
            self.src_radio_buttons.append(button)



        # 右侧框架
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        # 创建单选项
        for site in Site:
            button = ttk.Radiobutton(
                right_frame, 
                text=site.value, 
                variable=self.dst, 
                value=site.value,
                command=self.dst_select
            ).pack(anchor=tk.CENTER)
            self.dst_radio_buttons.append(button)
 
        # 默认哪个选项都不选
        self.src.set(None)
        self.dst.set(None)

        self.create_src_goods_list(left_frame)
        self.create_dst_goods_list(right_frame)

        # -----------------左侧框架-----------------
        # 创建进货书次数和讲价次数数字栏
        ttk.Label(left_frame, text="进货书次数").pack()

        src_extra_goods_frame = tk.Frame(left_frame)
        src_extra_goods_frame.pack()
        
        ttk.Button(src_extra_goods_frame, text="-", command=lambda: self.src_extra_goods_num.set(
            self.src_extra_goods_num.get() - 1 if self.src_extra_goods_num.get() > 0 else 0
        ), width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)
        ttk.Entry(src_extra_goods_frame, textvariable=self.src_extra_goods_num, state=tk.DISABLED, width=5, justify=tk.CENTER).pack(side=tk.LEFT)
        ttk.Button(src_extra_goods_frame, text="+", command=lambda: self.src_extra_goods_num.set(
            self.src_extra_goods_num.get() + 1
        ), width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)
        
        src_exchange_price_frame = tk.Frame(left_frame)
        src_exchange_price_frame.pack()
        
        src_exchange_price_buy_frame = tk.Frame(src_exchange_price_frame)
        src_exchange_price_buy_frame.pack(side=tk.LEFT, padx=statics.PRICE_UP_DOWN_PADX)

        ttk.Label(src_exchange_price_buy_frame, text="购买压价").pack()
        
        src_exchange_price_buy_input_frame = tk.Frame(src_exchange_price_buy_frame)
        src_exchange_price_buy_input_frame.pack()

        ttk.Button(
            src_exchange_price_buy_input_frame, 
            text="-", 
            command=lambda: self.src_exchange_price_buy_num.set(
                self.src_exchange_price_buy_num.get() - 1 if self.src_exchange_price_buy_num.get() > 0 else 0
            ), 
            width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)
        ttk.Entry(
            src_exchange_price_buy_input_frame, 
            textvariable=self.src_exchange_price_buy_num, 
            state=tk.DISABLED, 
            width=statics.PRICE_UP_DOWN_ENTRY_WIDTH, 
            justify=tk.CENTER
        ).pack(side=tk.LEFT)
        ttk.Button(
            src_exchange_price_buy_input_frame, 
            text="+", 
            command=lambda: self.src_exchange_price_buy_num.set(
                self.src_exchange_price_buy_num.get() + 1
            ), 
            width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)


        src_exchange_price_sell_frame = tk.Frame(src_exchange_price_frame)
        src_exchange_price_sell_frame.pack(side=tk.LEFT, padx=statics.PRICE_UP_DOWN_PADX)

        ttk.Label(src_exchange_price_sell_frame, text="出售抬价").pack()
        
        src_exchange_price_sell_input_frame = tk.Frame(src_exchange_price_sell_frame)
        src_exchange_price_sell_input_frame.pack()

        ttk.Button(src_exchange_price_sell_input_frame, text="-", command=lambda: self.src_exchange_price_sell_num.set(
            self.src_exchange_price_sell_num.get() - 1 if self.src_exchange_price_sell_num.get() > 0 else 0
        ), width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)
        ttk.Entry(src_exchange_price_sell_input_frame, textvariable=self.src_exchange_price_sell_num, state=tk.DISABLED, width=5, justify=tk.CENTER).pack(side=tk.LEFT)
        ttk.Button(src_exchange_price_sell_input_frame, text="+", command=lambda: self.src_exchange_price_sell_num.set(
            self.src_exchange_price_sell_num.get() + 1
        ), width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)


        # 默认次数为0
        self.src_extra_goods_num.set(0)
        self.src_exchange_price_buy_num.set(0)
        self.src_exchange_price_sell_num.set(0)


        # -----------------右侧框架-----------------
        # 创建进货书次数和讲价次数数字栏
        ttk.Label(right_frame, text="进货书次数").pack()

        dst_extra_goods_frame = tk.Frame(right_frame)
        dst_extra_goods_frame.pack()
        
        ttk.Button(dst_extra_goods_frame, text="-", command=lambda: self.dst_extra_goods_num.set(
            self.dst_extra_goods_num.get() - 1 if self.dst_extra_goods_num.get() > 0 else 0
        ), width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)
        ttk.Entry(dst_extra_goods_frame, textvariable=self.dst_extra_goods_num, state=tk.DISABLED, width=5, justify=tk.CENTER).pack(side=tk.LEFT)
        ttk.Button(dst_extra_goods_frame, text="+", command=lambda: self.dst_extra_goods_num.set(
            self.dst_extra_goods_num.get() + 1
        ), width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)
        
        dst_exchange_price_frame = tk.Frame(right_frame)
        dst_exchange_price_frame.pack()
        
        dst_exchange_price_buy_frame = tk.Frame(dst_exchange_price_frame)
        dst_exchange_price_buy_frame.pack(side=tk.LEFT, padx=statics.PRICE_UP_DOWN_PADX)

        ttk.Label(dst_exchange_price_buy_frame, text="购买压价").pack()
        
        dst_exchange_price_buy_input_frame = tk.Frame(dst_exchange_price_buy_frame)
        dst_exchange_price_buy_input_frame.pack()

        ttk.Button(
            dst_exchange_price_buy_input_frame, 
            text="-", 
            command=lambda: self.dst_exchange_price_buy_num.set(
                self.dst_exchange_price_buy_num.get() - 1 if self.dst_exchange_price_buy_num.get() > 0 else 0
            ), 
            width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)
        ttk.Entry(
            dst_exchange_price_buy_input_frame, 
            textvariable=self.dst_exchange_price_buy_num, 
            state=tk.DISABLED, 
            width=statics.PRICE_UP_DOWN_ENTRY_WIDTH, 
            justify=tk.CENTER
        ).pack(side=tk.LEFT)
        ttk.Button(
            dst_exchange_price_buy_input_frame, 
            text="+", 
            command=lambda: self.dst_exchange_price_buy_num.set(
                self.dst_exchange_price_buy_num.get() + 1
            ), 
            width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)


        dst_exchange_price_sell_frame = tk.Frame(dst_exchange_price_frame)
        dst_exchange_price_sell_frame.pack(side=tk.LEFT, padx=statics.PRICE_UP_DOWN_PADX)

        ttk.Label(dst_exchange_price_sell_frame, text="出售抬价").pack()
        
        dst_exchange_price_sell_input_frame = tk.Frame(dst_exchange_price_sell_frame)
        dst_exchange_price_sell_input_frame.pack()

        ttk.Button(dst_exchange_price_sell_input_frame, text="-", command=lambda: self.dst_exchange_price_sell_num.set(
            self.dst_exchange_price_sell_num.get() - 1 if self.dst_exchange_price_sell_num.get() > 0 else 0
        ), width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)
        ttk.Entry(dst_exchange_price_sell_input_frame, textvariable=self.dst_exchange_price_sell_num, state=tk.DISABLED, width=5, justify=tk.CENTER).pack(side=tk.LEFT)
        ttk.Button(dst_exchange_price_sell_input_frame, text="+", command=lambda: self.dst_exchange_price_sell_num.set(
            self.dst_exchange_price_sell_num.get() + 1
        ), width= statics.PLUS_MINUS_BUTTON_WIDTH
        ).pack(side=tk.LEFT)


        # 默认次数为0
        self.dst_extra_goods_num.set(0)
        self.dst_exchange_price_buy_num.set(0)
        self.dst_exchange_price_sell_num.set(0)
    
    
    def create_src_goods_list(self, frame):
        show_goods_frame = ttk.Labelframe(
            frame, 
            width=statics.GOODS_FRAME_WIDTH, 
            height=statics.GOODS_FRAME_HEIGHT
        )
        show_goods_frame.grid_propagate(False)
        show_goods_frame.pack()
        for goods in ALL_GOODS:
            var = tk.BooleanVar()
            checkbutton = ttk.Checkbutton(
                show_goods_frame, 
                text=goods.name,
                variable=var,
                command=lambda goods=goods, var=var: self.src_goods.append(goods.name) if var.get() else self.src_goods.remove(goods.name)
            )
            self.src_goods_checkbox[goods.name] = checkbutton


    def create_dst_goods_list(self, frame):
        show_goods_frame = ttk.Labelframe(
            frame,
            width=statics.GOODS_FRAME_WIDTH, 
            height=statics.GOODS_FRAME_HEIGHT
        )
        show_goods_frame.grid_propagate(False)
        show_goods_frame.pack()
        for goods in ALL_GOODS:
            var = tk.BooleanVar()
            checkbutton = ttk.Checkbutton(
                show_goods_frame, 
                text=goods.name,
                variable=var,
                command=lambda goods=goods, var=var: self.dst_goods.append(goods.name) if var.get() else self.dst_goods.remove(goods.name)
            )
            self.dst_goods_checkbox[goods.name] = checkbutton
            


    # 自定义src选中事件
    def src_select(self):
        # 隐藏所有可选货物并清除所有勾选
        for goods in self.src_goods_checkbox.values():
            if goods.instate(['selected']):
                goods.invoke()
            goods.grid_forget()

        # 显示可选货物
        site = Site.from_str(self.src.get())
        goods_list = GOODS_MAPPING.get(site, [])
        for index, goods in enumerate(goods_list):
            if goods.is_craft:
                continue
            self.src_goods_checkbox[goods.name].grid(row=index // 3, column= index % 3, sticky=tk.W)
    
    # 自定义dst选中事件
    def dst_select(self):
        # 隐藏所有可选货物并清除所有勾选
        for goods in self.dst_goods_checkbox.values():
            if goods.instate(['selected']):
                goods.invoke()
            goods.grid_forget()
        # 显示可选货物
        site = Site.from_str(self.dst.get())
        goods_list = GOODS_MAPPING.get(site, [])
        for index, goods in enumerate(goods_list):
            if goods.is_craft:
                continue
            self.dst_goods_checkbox[goods.name].grid(row=index // 3, column= index % 3, sticky=tk.W)
    


    
    def write(self, text):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, text)
        # 滚动到底部
        self.log.see(tk.END)
        
        self.log.update_idletasks()
        self.log.config(state=tk.DISABLED)


    def flush(self):
        pass

    def check_info(self):
        if self.src.get() == "None" or self.dst.get() == "None":
            print("请选择起点和终点")
            return False
        if self.src.get() == self.dst.get():
            print("起点和终点不能相同")
            return False
        if not self.src_goods or not self.dst_goods:
            print("请选择起点和终点的货物")
            return False
        return True


    def start(self):
        if self._close:
            print("正在退出...请勿操作")
            return
        if not self.check_info():
            return
        self.start_button.config(state=tk.DISABLED)
        self.helper_event.clear()
        src_info = (
            self.src.get(), 
            self.src_goods, 
            self.src_extra_goods_num.get(), 
            self.src_exchange_price_buy_num.get(),
            self.src_exchange_price_sell_num.get()
        )
        dst_info = (
            self.dst.get(), 
            self.dst_goods, 
            self.dst_extra_goods_num.get(), 
            self.dst_exchange_price_buy_num.get(),
            self.dst_exchange_price_sell_num.get()
        )
        self.helper_thread = threading.Thread(
            target=self.helper.exchange_task, 
            args=(((src_info, dst_info,), ))
        )
        self.helper_thread.start()
        self.stop_button.config(state=tk.NORMAL)
        

    def stop(self):
        self.stop_button.config(state=tk.DISABLED)
        self.helper_event.set()
        # 此处不能直接调用join，否则会阻塞主线程
        print("正在停止...")
        
    
    def stop_callback(self):
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        print("已停止")
        self.helper_thread = None


    def start_browser(self):
        if self._close:
            print("正在退出...请勿操作")
            return
        self.browser_thread = threading.Thread(target=self.browser.wait_for_info)
        self.browser_thread.start()
        

    def browser_callback(self, info):
        src_info , dst_info = info
        src, src_goods, src_extra_goods_num = src_info
        dst, dst_goods, dst_extra_goods_num = dst_info

        # 将数据反显到UI
        self.src.set(src)
        self.dst.set(dst)

        # 刷新进货列表显示框
        self.src_select()
        self.dst_select()

        # 勾选货物
        for goods in src_goods:
            self.src_goods_checkbox[goods].invoke()
        for goods in dst_goods:
            self.dst_goods_checkbox[goods].invoke()

        self.src_extra_goods_num.set(src_extra_goods_num)
        self.dst_extra_goods_num.set(dst_extra_goods_num)

        print(f"{' '.join(self.src_goods)}\n{' '.join(self.dst_goods)}")

    def check_thread(self, thread: threading.Thread, then: t.Callable):
        if thread.is_alive():
            self.master.after(100, self.check_thread, thread, then)
        else:
            then()

    def clean_up(self):
        # 关闭helper线程
        if self.helper_thread is not None:
            print("helper线程正在关闭...")
            self.stop()
            self.helper_thread.join()    

            print("helper线程已关闭")
        

        # 关闭browser线程
        if self.browser_thread is not None:
            print("browser线程正在关闭...")
            self.browser_event.set()
            # 等待线程结束
            self.browser_thread.join()
            
            print("browser线程已关闭")
        
        # 关闭adb-server
        print("正在关闭adb-server...")
        self.helper.executor.stop_client()
        print("adb-server已关闭")

    def quit(self):
        if self._close:
            print("正在退出...请勿重复点击退出按钮")
            return
        self._close = True
        # 退出托盘
        self.tray_icon.stop()

        thread = threading.Thread(target=self.clean_up)
        thread.start()
        # 每隔100ms检查线程是否结束，结束后退出
        self.master.after(100, self.check_thread, thread, self.master.quit)

    def hide(self):
        if self.master.state() == "withdrawn":
            return
        self.master.withdraw()
        
        # 每次启动程序期间只通知一次
        if not self._notified:
            # 系统通知
            self.tray_icon.notify("共振助手正在后台运行", "已隐藏")
            self._notified = True

    def show(self):
        self.master.deiconify()


