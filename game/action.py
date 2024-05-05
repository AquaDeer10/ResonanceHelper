import typing as t
from . import position

class Action:
    def __init__(self) -> None:
        self.action_chain: t.List[str] = []

    def tap(self, x: int, y: int) -> 'Action':
        self.action_chain.append(f"tap {x} {y}")
        return self
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int) -> 'Action':
        self.action_chain.append(f"swipe {x1} {y1} {x2} {y2}")
        return self

def action():
    return Action()

escape = action().tap(*position.escape)
enter_urban = action().tap(*position.enter_urban)
