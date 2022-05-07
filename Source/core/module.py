from ..base import *

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
    def __init__(self, image: object, weight: int, pos: tuple, offSet: tuple):
        super().__init__(pos[0], pos[1], weight)
        self.image = image
        self.offSet: tuple = offSet

    def draw(self, surface: linpg.ImageSurface) -> None:
        if isinstance(self.image, linpg.ImageSurface):
            surface.blit(self.image, linpg.coordinates.add(self.pos, self.offSet))
        else:
            try:
                self.image.display(surface, self.offSet)
            except Exception:
                self.image.draw(surface)
