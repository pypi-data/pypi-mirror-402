class Sentinel:
    __slots__ = ("name",)
    def __init__(self, name: str): self.name = name
    def __repr__(self) -> str: return self.name

ABYSS  = Sentinel("ABYSS")
BOTTOM = Sentinel("BOTTOM")

