from emulator.adb import ADBClient
from .action import Action
from time import sleep
import typing as t
from threading import Event
import sys

class Executor:
    def __init__(self, event: Event, callback: t.Optional[t.Callable]=None) -> None:
        self._client: t.Optional[ADBClient] = None
        self.event = event
        self.callback = callback

    @property
    def client(self) -> ADBClient:
        # 如果 event 被设置，则退出
        if self.event.is_set():
            if self.callback is not None:
                self.callback()
            sys.exit(0)
        if self._client is None:
            print("ADB正在加载中...")
            self._client = ADBClient()
        return self._client

    def execute(self, action: Action, interval_ms: int = 2500) -> None:
        for command in action.action_chain:
            if "tap" in command:
                x, y = command.split(" ")[1:]
                self.client.tap(int(x), int(y))
            elif "swipe" in command:
                x1, y1, x2, y2 = command.split(" ")[1:]
                self.client.swipe(int(x1), int(y1), int(x2), int(y2))
            else:
                raise ValueError(f"Invalid command: {command}")
            sleep(interval_ms / 1000)
            
    def screenshot(self) -> bytes:
        return self.client.screenshot()
    
    
    def stop_client(self) -> None:
        if self._client is not None:
            self._client.stop_server()
            self._client = None


    def kill_client(self) -> None:
        if self._client is not None:
            self._client.stop_server()
            self._client = None
