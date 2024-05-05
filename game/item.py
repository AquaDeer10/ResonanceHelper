from enum import Enum

class Rarity(Enum):
    N = "N"
    R = "R"
    SR = "SR"
    SSR = "SSR"

    @classmethod
    def from_string(cls, string):
        if string == "N":
            return cls.N
        elif string == "R":
            return cls.R
        elif string == "SR":
            return cls.SR
        elif string == "SSR":
            return cls.SSR
        else:
            assert False, f"Invalid rarity string: {string}"

    def __str__(self):
        return self.value
    



class Item:
    def __init__(self, id: int, name: str, rarity: Rarity, num: int = 0):
        self.id = id
        self.name = name
        self.rarity = rarity
        self.num = num

    def set_num(self, num: int):
        self.num = num

    def __str__(self):
        return f"<item> {self.name} -- {self.rarity}"
