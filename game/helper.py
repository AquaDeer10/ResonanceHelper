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
from abc import ABC, abstractmethod

from .data_types import *

class ResonanceHelper(ABC):
    def __init__(self, 
                 executor: Executor,
                 rail_controller: RailController,
                 callback: t.Optional[t.Callable]=None) -> None:
        self._scene: t.Optional[scene.Scene] = None
        self.executor = executor
        self.rail_controller = rail_controller
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
                       determining_criterion: t.Tuple[Rect, str], 
                       interval_ms: int=3000, 
                       timeout_s: int=300
                       ) -> bool:
        start_time = time.time()
        while True:
            box, value = determining_criterion
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
    
    @abstractmethod
    def run(self):
        pass


class ExchangeHelper(ResonanceHelper):
    def exchange_buy(self, 
                     site: Site, 
                     items: GoodsList, 
                     extra: ExtraNum = 0, 
                     exchange_price_num: ExchangePriceBuyNum = 0):
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


    def exchange_sell(self, 
                      site: Site, 
                      exchange_price_num: ExchangePriceSellNum = 0):
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

            self.executor.execute(self._scene.select_all())
            action, next_scene = self._scene.sell()
            self.executor.execute(action)
            self.executor.execute(self._scene.close_form())
            self._scene = next_scene
            

    def run(self, task_info: ExchangeTask):
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


class ExpulsionHelper(ResonanceHelper):
    def run(self, task_info: ExpulsionTask):
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


class OrderHelper(ResonanceHelper):

    def __init__(self, 
                 executor: Executor,
                 rail_controller: RailController,
                 callback: t.Optional[t.Callable]=None) -> None:

            # 所有订单地点
            self.order_scenes = scene.columba_order_scenes

            # 已经接取的订单的目的地集合
            self.order_destinations = set()

            # 是否喝酒
            self.drink_wine: bool = False

            # 是否购买每日桦石
            self.buy_daily_birch_stone: bool = False

            # 是否购买每日星云物质
            self.buy_daily_nebula_matter: bool = False

            # 每日购买物品是否完成
            self.buy_daily_items_complete: bool = False

            # 是否跑满订单
            self.run_full: bool = False

            super().__init__(executor, rail_controller, callback)
            
    def set_drink_wine(self, drink_wine: bool):
        self.drink_wine = drink_wine

    def set_run_full(self, run_full: bool):
        self.run_full = run_full

    def set_buy_daily_birch_stone(self, bug_daily_birch_stone: bool):
        self.bug_daily_birch_stone = bug_daily_birch_stone

    def set_buy_daily_nebula_matter(self, buy_daily_nebula_matter: bool):
        self.buy_daily_nebula_matter = buy_daily_nebula_matter


    def run(self):
        self.check_scene()
        
        route = self.bfs(f"{self._scene.site.value}商会订单")
        self.goto(route)

        self.accept_orders()


    def accept_orders(self):
        if not isinstance(self._scene, scene.ColumbaOrderScene):
            raise ValueError("当前不在订单界面")
        
        while True:
            orders = self._scene.get_order_info(self.executor.screenshot())
            if len(orders) == 0:
                print("没有可接取订单")
                break
            
            for order in orders:
                dst_name, button_position, order_type, occupy_size = order
                print(f"接取订单：{dst_name}，订单类型：{order_type}，占用：{occupy_size}")
                
                self.executor.execute(action().tap(*button_position))
                self.executor.execute(self._scene.accept_order())

                # TODO: 记录订单信息
                
            self.executor.execute(self._scene.next_page())

    
    def buy_daily_items(self):
        if self.buy_daily_items_complete:
            # 如果已经购买完毕，则不执行后续购买操作
            return
        
        # TODO: 判定当前城市是否存在休息区

        if self.buy_daily_birch_stone:
            self.do_buy_daily_birch_stone()

        if self.buy_daily_nebula_matter:
            self.do_buy_daily_nebula_matter()

        self.buy_daily_items_complete = True

    
    def do_buy_daily_birch_stone(self):
        route = self.bfs(f"{self._scene.site.value}休息区购买")
        self.goto(route)

        # TODO: 具体购买操作


    def do_buy_daily_nebula_matter(self):
        route = self.bfs(f"{self._scene.site.value}休息区购买")
        self.goto(route)

        # TODO: 具体购买操作