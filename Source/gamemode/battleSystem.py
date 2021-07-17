# cython: language_level=3
from .battleUI import *

__all__ = [
    "linpg", "glob", "os", "MapEditor", "time", "deque",
    "RoundSwitch", "WarningSystem", "WarningSystem", "SelectMenu", "CharacterInfoBoard", "ResultBoard", "LoadingTitle",
    "BattleSystem"
    ]

#战斗系统
class BattleSystem(linpg.AbstractBattleSystem):
    def __init__(self) -> None:
        super().__init__()
    #格里芬角色
    @property
    def griffinCharactersData(self) -> dict: return self.alliances_data
    #铁血角色
    @property
    def sangvisFerrisData(self) -> dict: return self.enemies_data