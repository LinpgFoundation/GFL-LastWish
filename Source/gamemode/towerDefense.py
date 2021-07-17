# cython: language_level=3
from .survival import *

__all__ = [
    "linpg", "glob", "os", "MapEditor", "time", "deque",
    "RoundSwitch", "WarningSystem", "WarningSystem", "SelectMenu", "CharacterInfoBoard", "ResultBoard", "LoadingTitle",
    "BattleSystem", "SurvivalBattleSystem", "TowerDefenseBattleSystem"
    ]

class TowerDefenseBattleSystem(BattleSystem):
    def __init__(self):
        super().__init__()