from typing import Union
from .api import *
import threading
from copy import deepcopy

# 初始化角色信息
class CharacterDataLoader(threading.Thread):
    def __init__(self, alliances: dict, enemies: dict, mode: str = "default") -> None:
        super().__init__()
        self.alliances: dict = deepcopy(alliances)
        self.enemies: dict = deepcopy(enemies)
        self.totalNum: int = len(alliances) + len(enemies)
        self.currentID: int = 0
        self.mode: str = mode

    def run(self) -> None:
        data_t: dict
        for key, value in self.alliances.items():
            data_t = deepcopy(linpg.Entity.get_enity_data(value["type"]))
            data_t.update(value)
            self.alliances[key] = linpg.FriendlyCharacter(data_t, self.mode)
            self.currentID += 1
            if linpg.debug.get_developer_mode():
                print("total: {0}, current: {1}".format(self.totalNum, self.currentID))
        for key, value in self.enemies.items():
            data_t = deepcopy(linpg.Entity.get_enity_data(value["type"]))
            data_t.update(value)
            self.enemies[key] = linpg.HostileCharacter(data_t, self.mode)
            self.currentID += 1
            if linpg.debug.get_developer_mode():
                print("total: {0}, current: {1}".format(self.totalNum, self.currentID))

    def getResult(self) -> tuple[dict, dict]:
        return self.alliances, self.enemies


# 射击音效
class AttackingSoundManager(linpg.AbstractSoundManager):
    def __init__(self, volume: int, channel_id: int):
        super().__init__(channel_id)

        ATTACK_SOUNDS_PATH: str = os.path.join("Assets", "sound", "attack")

        self.__SOUNDS: dict = {
            # 突击步枪
            "AR": glob(os.path.join(ATTACK_SOUNDS_PATH, "ar_*.ogg")),
            # 手枪
            "HG": glob(os.path.join(ATTACK_SOUNDS_PATH, "hg_*.ogg")),
            # 机枪
            "MG": glob(os.path.join(ATTACK_SOUNDS_PATH, "mg_*.ogg")),
            # 步枪
            "RF": glob(os.path.join(ATTACK_SOUNDS_PATH, "rf_*.ogg")),
            # 冲锋枪
            "SMG": glob(os.path.join(ATTACK_SOUNDS_PATH, "smg_*.ogg")),
        }
        self.volume: int = volume
        for key in self.__SOUNDS:
            for i in range(len(self.__SOUNDS[key])):
                self.__SOUNDS[key][i] = linpg.sound.load(self.__SOUNDS[key][i], volume / 100.0)

    # 播放
    def play(self, kind: str) -> None:
        if kind in self.__SOUNDS:
            linpg.sound.play(self.__SOUNDS[kind][linpg.get_random_int(0, len(self.__SOUNDS[kind]) - 1)], self._channel_id)


# 需要被打印的物品
class ItemNeedBlit(linpg.GameObject2point5d):
    def __init__(self, image: Union[linpg.ImageSurface, linpg.GameObject2d], weight: int, pos: tuple, offSet: tuple):
        super().__init__(pos[0], pos[1], weight)
        self.image: Union[linpg.ImageSurface, linpg.GameObject2d] = image
        self.offSet: tuple = offSet

    def draw(self, surface: linpg.ImageSurface) -> None:
        if isinstance(self.image, linpg.ImageSurface):
            surface.blit(self.image, linpg.coordinates.add(self.pos, self.offSet))
        else:
            try:
                self.image.display(surface, self.offSet)
            except Exception:
                self.image.draw(surface)
