import typing as t

Position = t.Tuple[int, int]

Rect = t.Tuple[int, int, int, int]

SiteName = str

GoodsName = str

GoodsList = t.List[GoodsName]

ExtraNum = int

ExchangePriceBuyNum = int

ExchangePriceSellNum = int

ExchangeInfo = t.Tuple[SiteName, GoodsList, ExtraNum, ExchangePriceBuyNum, ExchangePriceSellNum]

ExchangeTask = t.Tuple[ExchangeInfo, ExchangeInfo]

ExpulsionIndex = int

ExpulsionTask = t.Tuple[SiteName, ExpulsionIndex]

ExpulsionProgress = int

ExpulsionProgresses = t.Tuple[ExpulsionProgress, ExpulsionProgress, ExpulsionProgress]

OccupySize = int

OrderType = str

OrderInfo = t.Tuple[SiteName, Position, OrderType, OccupySize]
