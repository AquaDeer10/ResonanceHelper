from .rail import Site
import typing as t

class Goods:
    def __init__(self, 
                 name: str, 
                 price: int=0, 
                 is_special: bool=False, 
                 is_craft: bool=False) -> None:
        self.name = name
        self.price = price
        self.is_special = is_special
        self.is_craft = is_craft

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Goods):
            return self.name == value.name
        return False

GOODS_MAPPING: t.Dict[Site, t.List[Goods]] = {
    Site.SHOGGOLITH_CITY: [
        Goods("发动机"),
        Goods("弹丸加速装置"),
        Goods("家电"),
        Goods("汽配零件"),
        Goods("红茶"),
        Goods("高档餐具"),
        Goods("沃德烤鸡"),
        Goods("罐头"),
        Goods("沃德山泉"),
        Goods("修格里严选礼包", is_craft=True),
    ],
    Site.BRCL_OUTPOST: [
        Goods("弹丸加速装置"),
        Goods("防弹背心"),
        Goods("炮弹"),
        Goods("精钢"),
        Goods("塑胶炸药"),
        Goods("子弹"),
        Goods("汽油"),
        Goods("靛红五月军用食品")
    ],
    Site.MANDER_MINE: [
        Goods("图形加速卡"),
        Goods("钛矿石"),
        Goods("铁轨用特种钢材"),
        Goods("曼德工具箱"),
        Goods("黄铜"),
        Goods("钢筋混凝土轨枕"),
        Goods("建材"),
        Goods("铁矿石"),
        Goods("石材"),
        Goods("砂石"),
    ],
    Site.WILDERNESS_STATION: [
        Goods("琥珀"),
        Goods("孔雀石"),
        Goods("绿松石"),
        Goods("棉花"),
        Goods("铅矿石"),
        Goods("石墨"),
        Goods("土豆"),
    ],
    Site.ONEDERLANND: [
        Goods("铁矿石"),
        Goods("沙金"),
        Goods("青金石"),
        Goods("玛瑙"),
        Goods("漆黑矿渣"),
        Goods("石英砂"),
        Goods("纯金线材", is_craft=True),
        Goods("	金箔", is_craft=True),
    ],
    Site.CLARITY_DATA_CENTER: [
        Goods("游戏机"),
        Goods("银矿石"),
        Goods("扬声器"),
        Goods("游戏卡带"),
        Goods("录像带"),
        Goods("荧光棒"),
        Goods("火车玩具"),
        Goods("录音带"),
    ],
    Site.FREEPORT_VII: [
        Goods("桦石发财树"),
        Goods("石墨烯"),
        Goods("人工晶花"),
        Goods("电子配件"),
        Goods("航天纪念品"),
        Goods("斑节虾"),
        Goods("坚果"),
        Goods("啤酒"),
        Goods("海盐"),
        Goods("年货大礼包", is_craft=True),
    ],
    Site.ANITA_WEAPON_RESEARCH_INSTITUTE: [
        Goods("火澄石"),
        Goods("负片炮弹"),
        Goods("阿妮塔202军用无人机"),
        Goods("抗污染防护服"),
        Goods("钛合金"),
        Goods("碳纤维"),
        Goods("形态共振瞄准器"),
        Goods("高导磁硅钢片"),
        Goods("黄铜线圈"),
    ],
    Site.ANITA_ENERGY_RESEARCH_INSTITUTE: [
        Goods("阿妮塔小型桦树发电机"),
        Goods("石墨烯电池"),
        Goods("阿妮塔101民用无人机"),
        Goods("家用太阳能电池组"),
        Goods("锂电池"),
        Goods("充电电池"),
    ],
    Site.ANITA_ROCKET_BASE: [
        Goods("航天半导体"),
        Goods("太阳电池阵"),
        Goods("蜂窝防热烧蚀材料"),
        Goods("高导热陶瓷"),
        Goods("镍基高温合金"),
        Goods("液氧甲烷燃料"),
        Goods("无刷电机"),
        Goods("火箭拼装玩具"),
    ],
}

ALL_GOODS: t.List[Goods] = []
for goods_list in GOODS_MAPPING.values():
    for goods in goods_list:
        if goods not in ALL_GOODS:
            ALL_GOODS.append(goods)

if __name__ == '__main__':
    a = Goods("发动机")
    b = [Goods("发动机"), Goods("弹丸加速装置")]
    print(a in b)