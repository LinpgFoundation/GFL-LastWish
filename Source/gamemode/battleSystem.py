# cython: language_level=3
from .editor import *

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