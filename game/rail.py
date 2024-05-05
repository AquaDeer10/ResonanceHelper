from enum import Enum
from .executor import Executor
from .action import Action, action
from . import position
from io import BytesIO
from PIL import Image
from ocr import ocr
import time

import typing as t



class Site(Enum):
    SHOGGOLITH_CITY = "修格里城"
    BRCL_OUTPOST = "铁盟哨站"
    MANDER_MINE = "曼德矿场"
    WILDERNESS_STATION = "荒原站"
    ONEDERLANND = "淘金乐园"
    CLARITY_DATA_CENTER = "澄明数据中心"
    FREEPORT_VII = "7号自由港"
    ANITA_WEAPON_RESEARCH_INSTITUTE = "阿妮塔战备工厂"
    ANITA_ENERGY_RESEARCH_INSTITUTE = "阿妮塔能源研究所"
    ANITA_ROCKET_BASE = "阿妮塔发射中心"

    def from_str(name: str) -> 'Site':
        for site in Site:
            if site.value == name:
                return site
        raise ValueError("Invalid site name")

class Rail:
    def __init__(self, src: Site, dst: Site) -> None:
        self.src = src
        self.dst = dst


class RailController:
    def __init__(self, executor: Executor) -> None:
        self.executor = executor

    def execute(self, rail: Rail) -> None:
        # TODO implement rail
        self.executor.execute(action().tap(*position.map))
        while True:
            dst_position = self.detect_destination(rail)
            # 循环直到找到目标地点
            if dst_position is not None:
                break
        self.executor.execute(action().tap(*dst_position))
        self.executor.execute(action().tap(*position.rail))
        self.wait_for_arrival(5)
        self.executor.execute(action().tap(*position.arrival), 5000)


    def wait_for_arrival(self, interval_s: int) -> None:
        print("等待到达站点...")
        while True:
            image = Image.open(BytesIO(self.executor.screenshot()))
            croped_image = image.crop(position.arrival_rect)
            result, _ = ocr.recognize(croped_image)
            if result == "进入站点":
                break
            time.sleep(interval_s)

        

    def detect_destination(self, rail: Rail) -> t.Optional[t.Tuple[int, int]]:
        self.swipe_to_top_left()
        
        position = self.detect(rail)
        if position is not None:
            # 如果在第一屏就找到了，直接返回
            return position
        
        # 拖动顺序
        # 目前需要检测上下三屏，左右两屏
        swipe_order = [
            self.swipe_to_right, 
            self.swipe_to_right, 
            self.swipe_to_bottom, 
            self.swipe_to_bottom, 
            self.swipe_to_left, 
            self.swipe_to_left, 
            self.swipe_to_bottom,
            self.swipe_to_bottom,
            self.swipe_to_right,
            self.swipe_to_right
        ]
        for swipe in swipe_order:
            if position is not None:
                return position
            swipe()
            position = self.detect(rail)
        return position


    def detect(self, rail: Rail) -> t.Optional[t.Tuple[int, int]]:
        image = Image.open(BytesIO(self.executor.screenshot()))
        detect_result = ocr.detect(image)
        for x, y, name, _ in detect_result:
            if name == rail.dst.value:
                return x, y
        return None



    def swipe_to_top_left(self) -> None:
        # 将屏幕定位到左上角
        for _ in range(3):
            self.swipe_to_top()
            self.swipe_to_left()

    def swipe_to_left(self) -> None:
        # 滑动到左边，实际是向右滑动
        pos_src = int(1920 / 4), int(1080 / 2)
        pos_dst = int(1920 / 4 * 3), int(1080 / 2)
        self.executor.execute(action().swipe(*pos_src, *pos_dst), 500)

    def swipe_to_right(self) -> None:
        # 滑动到右边，实际是向左滑动
        pos_src = int(1920 / 4 * 3), int(1080 / 2)
        pos_dst = int(1920 / 4), int(1080 / 2)
        self.executor.execute(action().swipe(*pos_src, *pos_dst), 500)

    def swipe_to_top(self) -> None:
        # 滑动到上边，实际是向下滑动
        pos_src = int(1920 / 2), int(1080 / 4)
        pos_dst = int(1920 / 2), int(1080 / 4 * 3)
        self.executor.execute(action().swipe(*pos_src, *pos_dst), 500)

    def swipe_to_bottom(self) -> None:
        # 滑动到下边，实际是向上滑动
        pos_src = int(1920 / 2), int(1080 / 4 * 3)
        pos_dst = int(1920 / 2), int(1080 / 4)
        self.executor.execute(action().swipe(*pos_src, *pos_dst), 500)



