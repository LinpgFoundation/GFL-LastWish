# cython: language_level=3
from .survival import *

class TowerDefenseBattleSystem(BattleSystem):
    def __init__(self):
        super().__init__()