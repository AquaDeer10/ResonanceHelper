from .executor import Executor
from .rail import Rail, RailController, Site
from .action import Action
from . import scene
import typing as t
from collections import deque
import time
from ocr import ocr
from io import BytesIO
from PIL import Image
from . import position
from .action import action
from threading import Event
import traceback
import sys

class ResonanceHelper:
    def __init__(self, event: Event, callback: t.Optional[t.Callable]=None) -> None:
        self._scene: t.Optional[scene.Scene] = None
        self.executor = Executor(event, callback)
        self.rail_controller = RailController(self.executor)
        self.callback = callback
        self.is_first_exchange = True

    def check_scene(self):
        self._scene = scene.Scene.from_image(self.executor.screenshot())
        if self._scene is None:
            raise ValueError("Cannot detect scene")
        print(f"检测到目前界面处于：{self._scene.name}")

    def bfs(self, target_scene_name: str) -> t.List[str]:
        print(f"目标地点：{target_scene_name}，正在寻找路径...")
        start = self._scene
        queue = deque([(start, tuple())])
        visited = set()
        while queue:
            vertex, trace = queue.popleft()

            if vertex.name == target_scene_name:
                # 如果找到目标节点，跳出循环
                break
            else:
                # 如果没有匹配上，则将当前节点的邻居节点加入队列
                if vertex not in visited:
                    visited.add(vertex)
                    for scene, _ in vertex._next_scenes.items():
                        queue.append((scene, trace + (scene.name,)))
        
        # 返回路径
        print(f"路径已确定：{' -> '.join((self._scene.name, ) + trace)}")
        return list(trace)
        
    def goto(self, route: t.List[str], interval_ms: int = 2000):
        for scene_name in route:
            next_scene, action = self._scene.goto(scene_name)
            if isinstance(action, Rail):
                self.rail_controller.execute(action)
            elif isinstance(action, Action):
                self.executor.execute(action, interval_ms)
            else:
                raise ValueError("Invalid action type")
            print(f"已到达：{next_scene.name}")
            self._scene = next_scene

    def check_finished(self, 
                       determining_criterion: t.Tuple[int, int, int, int, str], 
                       interval_ms: int=3000, 
                       timeout_s: int=300
                       ) -> bool:
        start_time = time.time()
        while True:
            *box, value = determining_criterion
            image = Image.open(BytesIO(self.executor.screenshot()))
            croped_image = image.crop(box)
            text, _ = ocr.recognize(croped_image)
            if text == value:
                print("已完成")
                # 检测到后停留一个interval_ms的时间，防止界面还未刷新
                time.sleep(interval_ms / 1000)
                return True
            time.sleep(interval_ms / 1000)
            if time.time() - start_time > timeout_s:
                print("超时")
                return False
        



    def expultion_task(self, task_info: t.Tuple[str, int]):
        self.check_scene()
        site_name, num = task_info
        route = self.bfs(f"{site_name}驱逐任务")
        self.goto(route)
        while True:
            if isinstance(self._scene, scene.ExpulsionTaskScene):
                self.executor.execute(self._scene.choose(num)) 
                self.executor.execute(self._scene.start())
                self.check_finished(position.battle_win_rect + ("作战胜利", ))
                self.executor.execute(action().tap(*position.battle_end_next))
                # 等待加载时间
                time.sleep(5)
    

    def exchange_buy(self, site: Site, items: t.List[str], extra: int = 0, exchange_price_num: int = 0):
        route = self.bfs(f"{site.value}交易所购买")
        self.goto(route)
        if isinstance(self._scene, scene.ExchangeBuyScene):
            # 压价
            exchange_price_success_num = 0
            exchange_price_percent = 0.0
            while exchange_price_success_num < exchange_price_num:
                self.executor.execute(self._scene.exchange_price())

                if self.is_first_exchange:
                    sleep_time = 4
                    self.is_first_exchange = False
                else:
                    sleep_time = 2
                time.sleep(sleep_time)

                current_exchange_price_percent, can_continue =  self._scene.get_exchange_price_info(self.executor.screenshot())                
                if current_exchange_price_percent > exchange_price_percent:
                    # 如果当前压价成功，则将成功次数加一，并更新压价百分比
                    print(f"压价成功，当前压价百分比：{current_exchange_price_percent}")
                    exchange_price_success_num += 1
                    exchange_price_percent = current_exchange_price_percent
                    continue
                
                if not can_continue:
                    # 如果不能继续压价，则退出循环
                    print("压价次数已达上限，退出压价")
                    break

            # 使用道具
            for _ in range(extra):
                self.executor.execute(self._scene.use_item("进货采买书"))
            
            while len(items) > 0:
                self.executor.execute(
                    self._scene.select_item(items, self.executor.screenshot())
                )
                self.executor.execute(self._scene.next_page())
            
            action, next_scene = self._scene.buy()
            self.executor.execute(action)
            self.executor.execute(self._scene.close_form())
            self._scene = next_scene


    def exchange_sell(self, site: Site, exchange_price_num: int = 0):
        route = self.bfs(f"{site.value}交易所售出")
        self.goto(route)
        if isinstance(self._scene, scene.ExchangeSellScene):
            # 抬价
            exchange_price_success_num = 0
            exchange_price_percent = 0.0
            while exchange_price_success_num < exchange_price_num:
                self.executor.execute(self._scene.exchange_price())
                
                if self.is_first_exchange:
                    sleep_time = 4
                    self.is_first_exchange = False
                else:
                    sleep_time = 2
                time.sleep(sleep_time)
                
                current_exchange_price_percent, can_continue =  self._scene.get_exchange_price_info(self.executor.screenshot())
                if current_exchange_price_percent > exchange_price_percent:
                    # 如果当前抬价成功，则将成功次数加一，并更新抬价百分比
                    print(f"抬价成功，当前抬价百分比：{current_exchange_price_percent}")
                    exchange_price_success_num += 1
                    exchange_price_percent = current_exchange_price_percent
                    continue
                
                if not can_continue:
                    # 如果不能继续抬价，则退出循环
                    print("抬价次数已达上限，退出抬价")
                    break

            # 直接全选售出，无需一个一个点击
            '''
            while not self._scene.check_empty(self.executor.screenshot()):
                self.executor.execute(self._scene.select_item(10), 200)
            '''
            self.executor.execute(self._scene.select_all())
            action, next_scene = self._scene.sell()
            self.executor.execute(action)
            # 全选不包括本地物品，无需处理本地物品警告
            '''
            if self._scene.check_local_item_warning(self.executor.screenshot()):
                self.executor.execute(self._scene.local_item_warning_confirm())
            '''
            self.executor.execute(self._scene.close_form())
            self._scene = next_scene
            

    def exchange_task(self, task_info: t.Tuple[t.Tuple[str, t.List[str], int, int, int], t.Tuple[str, t.List[str], int, int, int]]):
        try:
            self.check_scene()
            site_1, site_2 = task_info
            if self._scene.site.value == site_1[0]:
                src = site_1
                dst = site_2
            elif self._scene.site.value == site_2[0]:
                src = site_2
                dst = site_1
            else:
                # 如果当前不在任务地点，先去任务地点
                src = site_1
                dst = site_2
            


            
            while True:
                # 购买物品后会将物品移除列表，然后根据列表是否为空来判断是否继续购买
                # 所以这里需要复制一份，以免第二次循环时物品列表为空
                src_items = src[1].copy()
                src_extra = src[2]
                src_exchange_price_buy_num = src[3]
                src_exchange_price_sell_num = src[4]
                dst_items = dst[1].copy()
                dst_extra = dst[2]
                dst_exchange_price_buy_num = dst[3]
                dst_exchange_price_sell_num = dst[4]
                self.exchange_buy(Site.from_str(src[0]), src_items, src_extra, src_exchange_price_buy_num)
                self.exchange_sell(Site.from_str(dst[0]), src_exchange_price_sell_num)
                self.exchange_buy(Site.from_str(dst[0]), dst_items, dst_extra, dst_exchange_price_buy_num)
                self.exchange_sell(Site.from_str(src[0]), dst_exchange_price_sell_num)
        except Exception:
            traceback.print_exc()
            self.callback()
            self.executor.kill_client()

    def black_tea_event_battle(self):
        try:
            while True:
                balck_tea_event_position = (1348, 273)
                self.executor.execute(action().tap(*balck_tea_event_position))
                self.executor.execute(action().tap(*position.battle_confirm))
                if self.check_finished(position.battle_win_rect + ("作战胜利", )):
                    self.executor.execute(action().tap(*position.battle_end_next))
                    time.sleep(5)
        except Exception:
            traceback.print_exc()
            self.callback()
            sys.exit(0)

            
        