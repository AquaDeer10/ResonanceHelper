import typing as t
from .action import Action, action, escape, enter_urban
from . import position
from .rail import Site, Rail
from io import BytesIO
from PIL import Image
from ocr import ocr
import numpy as np



class Scene:
    scene_list: t.List['Scene'] = []

    def __init__(self, 
                 id: int, 
                 name: str, 
                 site: Site, 
                 ) -> None:
        self.id = id
        self.name = name
        self._next_scenes: t.Dict[Scene, t.Union[Action, Rail]]  = {}
        self.site: Site = site
        Scene.scene_list.append(self)
    
    def add_next_scene(self, scene: 'Scene', action: t.Union[Action, Rail]) -> None:
        self._next_scenes[scene] = action
    
    def goto(self, scene_name: str) -> t.Tuple['Scene', t.Union[Action, Rail]]:
        for scene, action in self._next_scenes.items():
            if scene.name == scene_name:
                return scene, action
        raise ValueError(f"Scene {scene_name} not found")
    
    @classmethod
    def from_image(cls, image_bytes: bytes) -> t.Optional['Scene']:
        image = Image.open(BytesIO(image_bytes))
        croped_image = image.crop(position.station_name_rect)
        text, _ = ocr.recognize(croped_image)
        text = f"{text}主界面"
        for scene in cls.scene_list:
            if text == scene.name:
                return scene
        return None
    
    @classmethod
    def from_name(cls, name: str) -> t.Optional['Scene']:
        for scene in cls.scene_list:
            if name == scene.name:
                return scene
        return None


    
class MainScene(Scene):
    def __init__(self, 
                 id: int, 
                 name: str, 
                 site: Site
                 ) -> None:
        super().__init__(id, name, site)



class UrbanScene(Scene):
    def __init__(self, 
                 id: int, 
                 name: str, 
                 site: Site,
                 ) -> None:
        super().__init__(id, name, site)


class CRBSEScene(Scene):
    def __init__(self, 
                 id: int, 
                 name: str, 
                 site: Site,
                 ) -> None:
        super().__init__(id, name, site)

class ExpulsionTaskScene(Scene):
    def __init__(self, 
                 id: int, 
                 name: str, 
                 site: Site,
                 ) -> None:
        super().__init__(id, name, site)

    def choose(self, task_number: int) -> Action:
        if task_number not in [1, 2, 3]:
            raise ValueError("task_number must be 1, 2 or 3")
        
        print(f"选择驱逐任务{task_number}")
        return action().tap(*getattr(position, f"expulsion_task_choose_{task_number}"))
    
    def get_progress(self, image_bytes: bytes) -> t.Tuple[int, int, int]:
        image = Image.open(BytesIO(image_bytes))
        croped_image_1 = image.crop(position.expulsion_task_1_progress_rect)
        croped_image_2 = image.crop(position.expulsion_task_2_progress_rect)
        croped_image_3 = image.crop(position.expulsion_task_3_progress_rect)
        progress_1, _ = ocr.recognize(croped_image_1)
        progress_2, _ = ocr.recognize(croped_image_2)
        progress_3, _ = ocr.recognize(croped_image_3)
        return int(progress_1), int(progress_2), int(progress_3)
    
    def start(self) -> Action:
        return action().tap(*position.expulsion_task_start).tap(*position.battle_confirm)
       

class ExchangeScene(Scene):
    def __init__(self, 
                 id: int, 
                 name: str, 
                 site: Site,
                 ) -> None:
        super().__init__(id, name, site)


    def exchange_price(self) -> Action:
        return action().tap(*position.exchange_price)
    
    def select_all(self) -> Action:
        return action().tap(*position.select_all)
    
    def next_page(self) -> Action:
        return action().swipe(*position.exchange_swipe)
    
    def close_form(self) -> Action:
        return action().tap(*position.blank_space)
    

class ExchangeBuyScene(ExchangeScene):
    def __init__(self, 
                 id: int, 
                 name: str, 
                 site: Site,
                 ) -> None:
        super().__init__(id, name, site)

    def select_item(self, item_list: t.List[str], image_bytes: bytes) -> Action:
        image = Image.open(BytesIO(image_bytes))
        croped_image = image.crop(position.exchange_item_rect)
        croped_image = np.array(croped_image)
        ocr_result = ocr.detect(croped_image)
        # 初始化动作链
        action_chain = action()
        for x, y, name, _ in ocr_result:
            # 转换局部坐标为全局坐标
            x += position.exchange_item_rect[0]
            y += position.exchange_item_rect[1]
            # 如果商品名称在列表中，则点击
            if name in item_list:
                action_chain = action_chain.tap(x, y)
                item_list.remove(name)
        return action_chain

    def get_exchange_price_info(self, image_bytes: bytes) -> t.Tuple[float, bool]:
        image = Image.open(BytesIO(image_bytes))
        croped_image = image.crop(position.exchange_price_percent_rect)
        result = ocr.recognize(croped_image)
        price_percent =  float(result[0].replace("%", "").strip())

        croped_image = image.crop(position.exchange_price_text_rect)
        result = ocr.recognize(croped_image)
        if result[0] == "砍价":
            return price_percent, True
        return price_percent, False
    
    def buy(self) -> t.Tuple[Action, Scene]:
        next_scene_name = self.name.replace("购买", "")
        next_scene = None

        for scene in self._next_scenes.keys():
            if scene.name == next_scene_name:
                next_scene = scene
        
        if next_scene is None:
            raise ValueError(f"Scene {next_scene_name} not found")
        
        # 交易行情变动时，需要按两次购买
        action_chain = action().tap(*position.confirm_buy_or_sell).tap(*position.confirm_buy_or_sell)
        
        return action_chain, next_scene
    
    def use_item(self, item_name: str) -> Action:
        action_chain = action()
        action_chain.tap(*position.exchange_use_item)
        if item_name == "进货采买书":
            action_chain.tap(*position.extra_buy)
        else:
            raise ValueError(f"Item {item_name} not found")
        action_chain.tap(*position.use_item_confirm)
        return action_chain

        
class ExchangeSellScene(ExchangeScene):
    def __init__(self, 
                 id: int, 
                 name: str, 
                 site: Site,
                 ) -> None:
        super().__init__(id, name, site)

    def select_item(self, num: int) -> Action:
        action_chain = action()
        for _ in range(num):
            action_chain = action_chain.tap(*position.sell_select)
        return action_chain
    
    def check_empty(self, image_bytes: bytes) -> bool:
        image = Image.open(BytesIO(image_bytes))
        croped_image = image.crop(position.exchange_item_rect)
        result = ocr.detect(croped_image)
        if len(result) == 0:
            return True
        return False
    
    def get_exchange_price_info(self, image_bytes: bytes) -> t.Tuple[float, bool]:
        image = Image.open(BytesIO(image_bytes))
        croped_image = image.crop(position.exchange_price_percent_rect)
        result = ocr.recognize(croped_image)
        price_percent =  float(result[0].replace("%", "").strip())

        croped_image = image.crop(position.exchange_price_text_rect)
        result = ocr.recognize(croped_image)
        if result[0] == "抬价":
            return price_percent, True
        return price_percent, False
        
    def sell(self) -> t.Tuple[Action, Scene]:
        next_scene_name = self.name.replace("售出", "")
        next_scene = None

        for scene in self._next_scenes.keys():
            if scene.name == next_scene_name:
                next_scene = scene
        
        if next_scene is None:
            raise ValueError(f"Scene {next_scene_name} not found")
        
        # 交易行情变动时，需要按两次卖出
        action_chain = action().tap(*position.confirm_buy_or_sell).tap(*position.confirm_buy_or_sell)
        
        return action_chain, next_scene
    
    def check_local_item_warning(self, image_bytes: bytes) -> bool:
        result = ocr.detect(Image.open(BytesIO(image_bytes)))
        for _, _, name, _ in result:
            if name == "今日不再提示":
                return True
        return False

    def local_item_warning_confirm(self) -> Action:
        return action().tap(*position.local_item_warning_confirm)


            
    
    
# -----------------主界面场景-----------------
shoggolith_city_main = MainScene(1, "修格里城主界面", Site.SHOGGOLITH_CITY)
brcl_outpost = MainScene(2, "铁盟哨站主界面", Site.BRCL_OUTPOST)
mander_mine = MainScene(3, "曼德矿场主界面", Site.MANDER_MINE)
wilderness_station = MainScene(4, "荒原站主界面", Site.WILDERNESS_STATION)
onederland = MainScene(5, "淘金乐园主界面", Site.ONEDERLANND)
clarity_data_center = MainScene(6, "澄明数据中心主界面", Site.CLARITY_DATA_CENTER)
freeport_vii = MainScene(7, "7号自由港主界面", Site.FREEPORT_VII)
anita_weapon_research_institute = MainScene(8, "阿妮塔战备工厂主界面", Site.ANITA_WEAPON_RESEARCH_INSTITUTE)
anita_energy_research_institute = MainScene(9, "阿妮塔能源研究所主界面", Site.ANITA_ENERGY_RESEARCH_INSTITUTE)
anita_rocket_base = MainScene(12, "阿妮塔发射中心主界面", Site.ANITA_ROCKET_BASE)


main_scenes = [
    shoggolith_city_main, brcl_outpost, mander_mine, wilderness_station,
    onederland, clarity_data_center, freeport_vii, anita_weapon_research_institute,
    anita_energy_research_institute, anita_rocket_base
]

# 主界面之间互相绑定
for main_scene in main_scenes:
    for other_main_scene in main_scenes:
        # 如果是同一个地点的主界面，跳过
        if main_scene.site == other_main_scene.site:
            continue
        main_scene.add_next_scene(other_main_scene, Rail(main_scene.site, other_main_scene.site))


# -----------------市区场景-----------------
shoggolith_city_urban = UrbanScene(12, "修格里城市区", Site.SHOGGOLITH_CITY)
brcl_outpost_urban = UrbanScene(13, "铁盟哨站市区", Site.BRCL_OUTPOST)
mander_mine_urban = UrbanScene(14, "曼德矿场市区", Site.MANDER_MINE)
wilderness_station_urban = UrbanScene(15, "荒原站市区", Site.WILDERNESS_STATION)
onederland_urban = UrbanScene(16, "淘金乐园市区", Site.ONEDERLANND)
clarity_data_center_urban = UrbanScene(17, "澄明数据中心市区", Site.CLARITY_DATA_CENTER)
freeport_vii_urban = UrbanScene(18, "7号自由港市区", Site.FREEPORT_VII)
anita_weapon_research_institute_urban = UrbanScene(19, "阿妮塔战备工厂市区", Site.ANITA_WEAPON_RESEARCH_INSTITUTE)
anita_energy_research_institute_urban = UrbanScene(20, "阿妮塔能源研究所市区", Site.ANITA_ENERGY_RESEARCH_INSTITUTE)
anita_rocket_base_urban = UrbanScene(23, "阿妮塔发射中心市区", Site.ANITA_ROCKET_BASE)

urban_scenes = [
    shoggolith_city_urban, brcl_outpost_urban, mander_mine_urban, wilderness_station_urban,
    onederland_urban, clarity_data_center_urban, freeport_vii_urban, anita_weapon_research_institute_urban,
    anita_energy_research_institute_urban, anita_rocket_base_urban
]

# 绑定 [主界面->市区] [市区->主界面]
for main_scene in main_scenes:
    for urban_scene in urban_scenes:
        if main_scene.site == urban_scene.site:
            main_scene.add_next_scene(urban_scene, enter_urban)
            urban_scene.add_next_scene(main_scene, escape)
            break


# -----------------铁安局场景-----------------
shoggolith_city_crbse = CRBSEScene(23, "修格里城铁安局", Site.SHOGGOLITH_CITY)
mander_mine_crbse = CRBSEScene(24, "曼德矿场铁安局", Site.MANDER_MINE)
clarity_data_center_crbse = CRBSEScene(24, "澄明数据中心铁安局", Site.CLARITY_DATA_CENTER)
freeport_vii_crbse = CRBSEScene(24, "7号自由港铁安局", Site.FREEPORT_VII)

crbse_scenes = [
    shoggolith_city_crbse, mander_mine_crbse, 
    clarity_data_center_crbse, freeport_vii_crbse
]

# 绑定 [市区->铁安局]
shoggolith_city_urban.add_next_scene(shoggolith_city_crbse, action().tap(*position.shoggolith_city_crbse))
mander_mine_urban.add_next_scene(mander_mine_crbse, action().tap(*position.mander_mine_crbse))
clarity_data_center_urban.add_next_scene(clarity_data_center_crbse, action().tap(*position.clarity_data_center_crbse))

# 绑定 [铁安局->市区]
for crbse_scene in crbse_scenes:
    for urban_scene in urban_scenes:
        if crbse_scene.site == urban_scene.site:
            crbse_scene.add_next_scene(urban_scene, escape)
            break


# -----------------驱逐任务场景-----------------
shoggolith_city_expulsion_task = ExpulsionTaskScene(24, "修格里城驱逐任务", Site.SHOGGOLITH_CITY)
mander_mine_expulsion_task = ExpulsionTaskScene(25, "曼德矿场驱逐任务", Site.MANDER_MINE)
clarity_data_center_expulsion_task = ExpulsionTaskScene(25, "澄明数据中心驱逐任务", Site.CLARITY_DATA_CENTER)
freeport_vii_expulsion_task = ExpulsionTaskScene(25, "7号自由港驱逐任务", Site.FREEPORT_VII)

expulsion_task_scenes = [
    shoggolith_city_expulsion_task, mander_mine_expulsion_task,
    clarity_data_center_expulsion_task, freeport_vii_expulsion_task
]

# 绑定铁安局和驱逐任务
for crbse_scene in crbse_scenes:
    for expulsion_task_scene in expulsion_task_scenes:
        if crbse_scene.site == expulsion_task_scene.site:
            crbse_scene.add_next_scene(expulsion_task_scene, action().tap(*position.expulsion_task))
            expulsion_task_scene.add_next_scene(crbse_scene, escape)
            break



# -------------------交易所场景-----------------
shoggolith_city_exchange = ExchangeScene(24, "修格里城交易所", Site.SHOGGOLITH_CITY)
brcl_outpost_exchange = ExchangeScene(25, "铁盟哨站交易所", Site.BRCL_OUTPOST)
mander_mine_exchange = ExchangeScene(25, "曼德矿场交易所", Site.MANDER_MINE)
wilderness_station_exchange = ExchangeScene(25, "荒原站交易所", Site.WILDERNESS_STATION)
onederland_exchange = ExchangeScene(26, "淘金乐园交易所", Site.ONEDERLANND)
clarity_data_center_exchange = ExchangeScene(27, "澄明数据中心交易所", Site.CLARITY_DATA_CENTER)
freeport_vii_exchange = ExchangeScene(27, "7号自由港交易所", Site.FREEPORT_VII)
anita_weapon_research_institute_exchange = ExchangeScene(27, "阿妮塔战备工厂交易所", Site.ANITA_WEAPON_RESEARCH_INSTITUTE)
anita_energy_research_institute_exchange = ExchangeScene(27, "阿妮塔能源研究所交易所", Site.ANITA_ENERGY_RESEARCH_INSTITUTE)
anita_rocket_base_exchange = ExchangeScene(27, "阿妮塔发射中心交易所", Site.ANITA_ROCKET_BASE)


exchange_scenes = [
    shoggolith_city_exchange, brcl_outpost_exchange, mander_mine_exchange, 
    wilderness_station_exchange, onederland_exchange, clarity_data_center_exchange, 
    freeport_vii_exchange, anita_weapon_research_institute_exchange, 
    anita_energy_research_institute_exchange, anita_rocket_base_exchange
]

# 绑定 [市区->交易所]
shoggolith_city_urban.add_next_scene(shoggolith_city_exchange, action().tap(*position.shoggolith_city_exchange))
brcl_outpost_urban.add_next_scene(brcl_outpost_exchange, action().tap(*position.brcl_outpost_exchange))
mander_mine_urban.add_next_scene(mander_mine_exchange, action().tap(*position.mander_mine_exchange))
wilderness_station_urban.add_next_scene(wilderness_station_exchange, action().tap(*position.wilderness_station_exchange))
onederland_urban.add_next_scene(onederland_exchange, action().tap(*position.onederland_exchange))
clarity_data_center_urban.add_next_scene(clarity_data_center_exchange, action().tap(*position.clarity_data_center_exchange))
freeport_vii_urban.add_next_scene(freeport_vii_exchange, action().tap(*position.freeport_vii_exchange))
anita_weapon_research_institute_urban.add_next_scene(anita_weapon_research_institute_exchange, action().tap(*position.anita_weapon_research_institute_exchange))
anita_energy_research_institute_urban.add_next_scene(anita_energy_research_institute_exchange, action().tap(*position.anita_energy_research_institute_exchange))
anita_rocket_base_urban.add_next_scene(anita_rocket_base_exchange, action().tap(*position.anita_rocket_base_exchange))


# 绑定 [交易所->市区]
for exchange_scene in exchange_scenes:
    for urban_scene in urban_scenes:
        if exchange_scene.site == urban_scene.site:
            exchange_scene.add_next_scene(urban_scene, escape)
            break


# -----------------交易所购买场景-----------------
shoggolith_city_exchange_buy = ExchangeBuyScene(28, "修格里城交易所购买", Site.SHOGGOLITH_CITY)
brcl_outpost_exchange_buy = ExchangeBuyScene(28, "铁盟哨站交易所购买", Site.BRCL_OUTPOST)
mander_mine_exchange_buy = ExchangeBuyScene(28, "曼德矿场交易所购买", Site.MANDER_MINE)
wilderness_station_exchange_buy = ExchangeBuyScene(28, "荒原站交易所购买", Site.WILDERNESS_STATION)
onederland_exchange_buy = ExchangeBuyScene(28, "淘金乐园交易所购买", Site.ONEDERLANND)
clarity_data_center_exchange_buy = ExchangeBuyScene(28, "澄明数据中心交易所购买", Site.CLARITY_DATA_CENTER)
freeport_vii_exchange_buy = ExchangeBuyScene(28, "7号自由港交易所购买", Site.FREEPORT_VII)
anita_weapon_research_institute_exchange_buy = ExchangeBuyScene(28, "阿妮塔战备工厂交易所购买", Site.ANITA_WEAPON_RESEARCH_INSTITUTE)
anita_energy_research_institute_exchange_buy = ExchangeBuyScene(28, "阿妮塔能源研究所交易所购买", Site.ANITA_ENERGY_RESEARCH_INSTITUTE)
anita_rocket_base_exchange_buy = ExchangeBuyScene(28, "阿妮塔发射中心交易所购买", Site.ANITA_ROCKET_BASE)


exchange_buy_scenes = [
    shoggolith_city_exchange_buy, brcl_outpost_exchange_buy, mander_mine_exchange_buy,
    wilderness_station_exchange_buy, onederland_exchange_buy, clarity_data_center_exchange_buy,
    freeport_vii_exchange_buy, anita_weapon_research_institute_exchange_buy,
    anita_energy_research_institute_exchange_buy, anita_rocket_base_exchange_buy
]

# 绑定 [交易所->购买] [购买->交易所]
for exchange_scene in exchange_scenes:
    for exchange_buy_scene in exchange_buy_scenes:
        if exchange_scene.site == exchange_buy_scene.site:
            exchange_scene.add_next_scene(exchange_buy_scene, action().tap(*position.buy))
            exchange_buy_scene.add_next_scene(exchange_scene, escape)
            break


# -----------------交易所售出场景-----------------
shoggolith_city_exchange_sell = ExchangeSellScene(29, "修格里城交易所售出", Site.SHOGGOLITH_CITY)
brcl_outpost_exchange_sell = ExchangeSellScene(29, "铁盟哨站交易所售出", Site.BRCL_OUTPOST)
mander_mine_exchange_sell = ExchangeSellScene(29, "曼德矿场交易所售出", Site.MANDER_MINE)
wilderness_station_exchange_sell = ExchangeSellScene(29, "荒原站交易所售出", Site.WILDERNESS_STATION)
onederland_exchange_sell = ExchangeSellScene(29, "淘金乐园交易所售出", Site.ONEDERLANND)
clarity_data_center_exchange_sell = ExchangeSellScene(29, "澄明数据中心交易所售出", Site.CLARITY_DATA_CENTER)
freeport_vii_exchange_sell = ExchangeSellScene(29, "7号自由港交易所售出", Site.FREEPORT_VII)
anita_weapon_research_institute_exchange_sell = ExchangeSellScene(29, "阿妮塔战备工厂交易所售出", Site.ANITA_WEAPON_RESEARCH_INSTITUTE)
anita_energy_research_institute_exchange_sell = ExchangeSellScene(29, "阿妮塔能源研究所交易所售出", Site.ANITA_ENERGY_RESEARCH_INSTITUTE)
anita_rocket_base_exchange_sell = ExchangeSellScene(29, "阿妮塔发射中心交易所售出", Site.ANITA_ROCKET_BASE)


exchange_sell_scenes = [
    shoggolith_city_exchange_sell, brcl_outpost_exchange_sell, mander_mine_exchange_sell,
    wilderness_station_exchange_sell, onederland_exchange_sell, clarity_data_center_exchange_sell,
    freeport_vii_exchange_sell, anita_weapon_research_institute_exchange_sell,
    anita_energy_research_institute_exchange_sell, anita_rocket_base_exchange_sell
]

# 绑定 [交易所->售出] [售出->交易所]
for exchange_scene in exchange_scenes:
    for exchange_sell_scene in exchange_sell_scenes:
        if exchange_scene.site == exchange_sell_scene.site:
            exchange_scene.add_next_scene(exchange_sell_scene, action().tap(*position.sell))
            exchange_sell_scene.add_next_scene(exchange_scene, escape)
            break


if __name__ == '__main__':
    from emulator.adb import ADBClient
    adb = ADBClient()
    scene = Scene.from_image(adb.screenshot())
    print(scene.name)
