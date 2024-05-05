import os
import socket
import typing as t
import random
import tkinter as tk
import threading
import configparser
import subprocess

class ADBClient:
    def __init__(self):
        self.adb_executable_file = os.path.join(os.path.dirname(__file__), "platform-tools/adb.exe")
        # 解析配置文件
        config = configparser.ConfigParser()
        config_file_abs_path = os.path.join(os.getcwd(), "adb.ini")
        config.read(config_file_abs_path)

        self.device_host = config.get("ADB", "device_host")
        self.device_port = config.getint("ADB", "device_port")

        self._device = f"{self.device_host}:{self.device_port}"
        self._socket = None
        self.current_positon_x = 0
        self.current_positon_y = 0
        self.width: t.Optional[int] = None
        self.height: t.Optional[int] = None
        
        self.start_server()



    def start_server(self) -> None:
        sub_proc = subprocess.Popen([
            self.adb_executable_file, 
            "connect", 
            f"{self.device_host}:{self.device_port}"
        ])
        sub_proc.wait()


    @property
    def adb_socket(self) -> socket.socket:
        if self._socket is None or getattr(self._socket, "_closed", True):
            self._socket = self._create_connection()
        return self._socket

    def _create_connection(self) -> socket.socket:
        # 创建 Socket 对象
        adb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接本地 ADB 服务器
        adb_socket.connect(('127.0.0.1', 5037))
        return adb_socket
    
    def _send(self, command: str) -> bytes:
        # 发送命令
        self.adb_socket.send(f"{len(command):04x}{command}".encode())
        # 接受前 4 个字节的数据
        status = self.adb_socket.recv(4).decode()

        if status != "OKAY":
            # 发送命令失败, 关闭连接
            err_msg = self._get_err_msg()
            self._socket.close()
            raise Exception(f"Failed to send command {command}, error message: {err_msg}")
        
        # 尝试获取数据长度
        res = self.adb_socket.recv(4)
        try:
            lengh = int(res, 16)
        except ValueError:
            msg =  res + self._receive_all()
            self.adb_socket.close()
            return msg

        msg = self.adb_socket.recv(lengh)
        self.adb_socket.close()
        return msg
    
    def _set_device(self) -> None:
        set_device_command = f"host:transport:{self._device}"
        self.adb_socket.send(f"{len(set_device_command):04x}{set_device_command}".encode())
        status = self.adb_socket.recv(4).decode()
        if status != "OKAY":
            # 设置设备失败, 关闭连接
            err_msg = self._get_err_msg()
            self._socket.close()
            raise Exception(f"Failed to set device {self._device}, error message: {err_msg}")

    def _send_shell(self, command: str) -> bytes:
        self._set_device()
        msg = self._send(f"shell:{command}")
        return msg
    
    def _receive_all(self, buffer_size=4096) -> bytes:
        """Receive data from socket until no more data is available."""
        data = b''
        while True:
            chunk = self.adb_socket.recv(buffer_size)
            if not chunk:
                break
            data += chunk
        return data
    
    def screenshot(self, filename: t.Optional[str]=None) -> t.Optional[bytes]:
        msg = self._send_shell("screencap -p")
        if filename:
            with open(filename, "wb") as f:
                f.write(msg)
        else:
            return msg
        
    def stop_server(self) -> None:
        if self._socket is not None:
            self._socket.close()
        sub_proc = subprocess.Popen([self.adb_executable_file, "kill-server"])
        sub_proc.wait()
        
    def tap(self, x: int, y: int) -> None:
        # 用拖拽的方式实现点击以控制点击时长
        duration = random.randint(100, 120)
        self._send_shell(f"input swipe {x} {y} {x+1} {y+1} {duration}")

    def swipe(self, x1: int, y1: int, x2: int, y2: int) -> None:
        duration = random.randint(1500, 2000)
        self._send_shell(f"input swipe {x1} {y1} {x2} {y2} {duration}")

    def listen_event(self) -> None:
        if self.width is None or self.height is None:
            self.width, self.height = self._get_screen_size()
        
        self._set_device()
        command = "shell:getevent -lt"
        # 发送命令
        self.adb_socket.send(f"{len(command):04x}{command}".encode())
        # 接受前 4 个字节的数据
        status = self.adb_socket.recv(4).decode()
        print(status)
        # 新开一个线程显示坐标
        threading.Thread(target=self.show_position).start()
        while True:
            event = self.adb_socket.recv(4096)
            if not event:
                break
            try:
                self._process_event(event.decode())
            except ValueError:
                # 坐标解析错误
                # 原因是坐标时间恰好在事件名和坐标之间截断了，这种情况直接跳过，不处理
                continue

    def _process_event(self, event_str: str) -> None:
        events = [event.strip() for event in event_str.split("\n")]
        for event in events:
            if "ABS_MT_POSITION_X" in event:
                # 由于是横屏，所以x y坐标需要调换
                y = int(event.split(" ")[-1], 16)
                # 且y坐标需要取反
                y = self.height - y

                self.current_positon_y = y
            if "ABS_MT_POSITION_Y" in event:
                # 由于是横屏，所以x y坐标需要调换
                x = int(event.split(" ")[-1], 16)
                self.current_positon_x = x

            
    

    def _get_err_msg(self) -> str:
        lengh = int(self.adb_socket.recv(4), 16)
        return self.adb_socket.recv(lengh).decode()


    def _get_screen_size(self) -> t.Tuple[int, int]:
        msg = self._send_shell("wm size")
        screen_size = msg.decode().split(" ")[-1].strip()
        # 由于是横屏，所以宽高需要调换
        height, width = screen_size.split("x")
        return int(width), int(height)

    def show_position(self) -> None:
        # 设置窗口大小为300*100
        root = tk.Tk()
        root.geometry("300x50")
        # 设置窗口始终在最上层
        root.wm_attributes('-topmost', 1)
        # 设置窗口位置到屏幕左上角
        root.geometry("+0+0")
        root.title("Position")
        label = tk.Label(root, text=f"X: {self.current_positon_x}, Y: {self.current_positon_y}", font=("Arial", 20))
        label.pack()
        # 定时刷新x y坐标
        def refresh_position():
            label.config(text=f"X: {self.current_positon_x}, Y: {self.current_positon_y}")
            root.after(10, refresh_position)
        refresh_position()
        root.mainloop()

    
if __name__ == "__main__":
    import time
    client = ADBClient()
    client.listen_event()
