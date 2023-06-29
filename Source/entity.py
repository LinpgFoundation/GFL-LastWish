import os
from glob import glob
from typing import Optional

import linpg

# 初始化linpg系统模块
linpg.display.init()

# 加载版本信息
version_info: dict = linpg.config.load_file("Data/version.yaml")

# 确认linpg的版本是推荐版本
linpg.LinpgVersionChecker(
    ">=",
    version_info["recommended_linpg_revision"],
    version_info["recommended_linpg_patch"],
)


# 射击音效
class AttackingSoundManager:
    __channel_id: int = 2
    __SOUNDS: dict[str, tuple] = {}

    @classmethod
    def initialize(cls) -> None:
        path_p: tuple = ("Assets", "sound", "attack")
        cls.__SOUNDS.clear()
        cls.__SOUNDS.update(
            {
                # 突击步枪
                "AR": tuple(
                    [
                        linpg.sounds.load(_path)
                        for _path in glob(os.path.join(*path_p, "ar_*.ogg"))
                    ]
                ),
                # 手枪
                "HG": tuple(
                    [
                        linpg.sounds.load(_path)
                        for _path in glob(os.path.join(*path_p, "hg_*.ogg"))
                    ]
                ),
                # 机枪
                "MG": tuple(
                    [
                        linpg.sounds.load(_path)
                        for _path in glob(os.path.join(*path_p, "mg_*.ogg"))
                    ]
                ),
                # 步枪
                "RF": tuple(
                    [
                        linpg.sounds.load(_path)
                        for _path in glob(os.path.join(*path_p, "rf_*.ogg"))
                    ]
                ),
                # 冲锋枪
                "SMG": tuple(
                    [
                        linpg.sounds.load(_path)
                        for _path in glob(os.path.join(*path_p, "smg_*.ogg"))
                    ]
                ),
            }
        )

    # 播放
    @classmethod
    def play(cls, kind: str) -> None:
        if (sounds_c := cls.__SOUNDS.get(kind)) is not None:
            sound_to_play = sounds_c[linpg.numbers.get_random_int(0, len(sounds_c) - 1)]
            sound_to_play.set_volume(linpg.volume.get_effects() / 100.0)
            linpg.sounds.play(sound_to_play, cls.__channel_id)

    # 释放内存
    @classmethod
    def release(cls) -> None:
        cls.__SOUNDS.clear()


# 友方角色被察觉的图标管理模块
class FriendlyCharacterDynamicProgressBarSurface(linpg.DynamicProgressBarSurface):
    # 指向储存角色被察觉图标的指针
    __FULLY_EXPOSED_IMG: linpg.ImageSurface = linpg.images.quickly_load(
        "<&ui>eye_red.png"
    )
    __BEING_NOTICED_IMG: linpg.ImageSurface = linpg.images.quickly_load(
        "<&ui>eye_orange.png"
    )

    def __init__(self) -> None:
        super().__init__(self.__FULLY_EXPOSED_IMG, self.__BEING_NOTICED_IMG, 0, 0, 0, 0)


# 敌方角色警觉度的图标管理模块
class HostileCharacterDynamicProgressBarSurface(linpg.DynamicProgressBarSurface):
    # 指向储存敌方角色警觉程度图标的指针
    __ORANGE_VIGILANCE_IMG: linpg.ImageSurface = linpg.images.quickly_load(
        "<&ui>vigilance_orange.png"
    )
    __RED_VIGILANCE_IMG: linpg.ImageSurface = linpg.images.quickly_load(
        "<&ui>vigilance_red.png"
    )

    def __init__(self) -> None:
        super().__init__(
            self.__RED_VIGILANCE_IMG,
            self.__ORANGE_VIGILANCE_IMG,
            0,
            0,
            0,
            0,
            linpg.Axis.VERTICAL,
        )


# 角色血条图片管理模块
class EntityHpBar(linpg.DynamicProgressBarSurface):
    # 指向储存血条图片的指针
    __HP_GREEN_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>hp_green.png")
    __HP_RED_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>hp_red.png")
    __HP_EMPTY_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>hp_empty.png")

    def __init__(self) -> None:
        # 是否角色死亡
        self.__is_dying: bool = False
        # 初始化父类
        super().__init__(self.__HP_GREEN_IMG, self.__HP_EMPTY_IMG, 0, 0, 0, 0)

    # 获取上方图片
    def _get_img_on_top(self) -> linpg.ImageSurface:
        return super()._get_img_on_top() if not self.__is_dying else self.__HP_RED_IMG

    def set_dying(self, value: bool) -> None:
        self.__is_dying = value


# 角色受伤立绘图形模块
class EntityGetHurtImage(linpg.Square):
    # 存储角色受伤立绘的常量
    __CHARACTERS_GET_HURT_IMAGE_DICT: dict = {}

    def __init__(self, self_type: str, y: linpg.int_f, width: linpg.int_f):
        super().__init__(0, y, width)
        self.delay: int = 255
        self.alpha: int = 0
        self.add(self_type)

    def draw(self, screen: linpg.ImageSurface, characterType: str) -> None:  # type: ignore[override]
        _image: linpg.ImageSurface = linpg.images.resize(
            self.__CHARACTERS_GET_HURT_IMAGE_DICT[characterType], self.size
        )
        if self.alpha != 255:
            _image.set_alpha(self.alpha)
        screen.blit(_image, self.pos)

    def add(self, characterType: str) -> None:
        if characterType not in self.__CHARACTERS_GET_HURT_IMAGE_DICT:
            self.__CHARACTERS_GET_HURT_IMAGE_DICT[
                characterType
            ] = linpg.images.quickly_load(
                linpg.Specification.get_directory(
                    "character_image", "{}_hurt.png".format(characterType)
                )
            )


# 基础角色类
class BasicEntity(linpg.Entity):
    # 攻击所需的AP
    AP_IS_NEEDED_TO_ATTACK: int = 5
    AP_IS_NEEDED_TO_MOVE_ONE_BLOCK: int = 2
    # 濒死回合限制
    DYING_ROUND_LIMIT: int = 3

    def __init__(self, characterData: dict, mode: str) -> None:
        super().__init__(characterData, mode)
        # 最大行动值
        self.__max_action_point: int = int(characterData["max_action_point"])
        # 当前行动值
        self.__current_action_point: int = int(
            characterData.get("current_action_point", self.__max_action_point)
        )
        # 血条图片
        self.__hp_bar: EntityHpBar = EntityHpBar()
        self.__status_font: linpg.TextSurface = linpg.TextSurface(
            "", 0, 0, linpg.display.get_width() / 192
        )
        # 角色的攻击范围
        self.__effective_range_coordinates: Optional[list[list[tuple[int, int]]]] = None

    def _need_update(self) -> None:
        self.__effective_range_coordinates = None

    def set_x(self, value: linpg.number) -> None:
        if round(value) != round(self.x):
            self._need_update()
        super().set_x(value)

    def set_y(self, value: linpg.number) -> None:
        if round(value) != round(self.y):
            self._need_update()
        super().set_y(value)

    # 当前行动值
    @property
    def max_action_point(self) -> int:
        return self.__max_action_point

    # 设置当前行动值，不建议非开发者使用
    def set_max_action_point(self, point: int) -> None:
        self.__max_action_point = point

    # 当前行动值
    @property
    def current_action_point(self) -> int:
        return self.__current_action_point

    # 设置当前行动值，不建议非开发者使用
    def set_current_action_point(self, point: int) -> None:
        self.__current_action_point = point

    # 重置行动点数
    def reset_action_point(self) -> None:
        self.set_current_action_point(self.__max_action_point)

    # 是否有足够的开发点数
    def have_enough_action_point(self, value: int) -> bool:
        return self.__current_action_point >= value

    # 尝试减少行动值，如果成功，返回true,失败则返回false
    def try_reduce_action_point(self, value: int) -> bool:
        # 有足够的行动值来减去
        if self.__current_action_point >= value:
            self.__current_action_point -= value
            return True
        # 没有足够的行动值来减去
        return False

    # 根据给定的坐标和范围列表生成范围坐标列表
    @classmethod
    def _generate_range_coordinates(
        cls,
        _x: int,
        _y: int,
        _ranges: tuple[int, ...],
        MAP_P: linpg.AbstractTileMap,
        ifFlip: bool,
        ifHalfMode: bool = False,
    ) -> list[list[tuple[int, int]]]:
        # 初始化数据
        start_point: int
        end_point: int
        max_effective_range: int = sum(_ranges)
        # 确定范围
        if not ifHalfMode:
            start_point = _y - max_effective_range
            end_point = _y + max_effective_range + 1
        elif not ifFlip:
            start_point = _y - max_effective_range
            end_point = _y + 1
        else:
            start_point = _y
            end_point = _y + max_effective_range + 1
        # 所在的区域
        attack_range: list[list[tuple[int, int]]] = [[] for _ in range(len(_ranges))]
        the_range_in: int
        row_start: int = _x - max_effective_range
        row_end: int = _x + max_effective_range + 1
        # append坐标
        for y in range(start_point, end_point):
            y_offset: int = abs(y - _y)
            for x in range(row_start + y_offset, row_end - y_offset):
                if (
                    MAP_P.row > y >= 0
                    and MAP_P.column > x >= 0
                    and MAP_P.is_passable(x, y)
                    and (
                        the_range_in := cls._identify_range(
                            _ranges, abs(x - _x) + abs(y - _y)
                        )
                    )
                    >= 0
                ):
                    attack_range[the_range_in].append((x, y))
        return attack_range

    # 获取角色的攻击范围
    def get_effective_range_coordinates(
        self, MAP_P: linpg.AbstractTileMap, ifHalfMode: bool = False
    ) -> list[list[tuple[int, int]]]:
        if self.__effective_range_coordinates is None:
            self.__effective_range_coordinates = self._generate_range_coordinates(
                round(self.x),
                round(self.y),
                self.effective_range,
                MAP_P,
                self._if_flip,
                ifHalfMode,
            )
        return self.__effective_range_coordinates

    # 根据给定的坐标和半径生成覆盖范围坐标列表
    @staticmethod
    def _generate_coverage_coordinates(
        _x: int, _y: int, _radius: int, MAP_P: linpg.AbstractTileMap
    ) -> list[tuple[int, int]]:
        return list(
            filter(
                lambda pos: MAP_P.is_passable(pos[0], pos[1])
                and MAP_P.row > pos[1] >= 0
                and MAP_P.column > pos[0] >= 0,
                linpg.coordinates.get_in_diamond_shaped(_x, _y, _radius),
            )
        )

    # 获取角色的攻击覆盖范围
    def get_attack_coverage_coordinates(
        self, _x: int, _y: int, MAP_P: linpg.AbstractTileMap
    ) -> list[tuple[int, int]]:
        if (
            self._identify_range(
                self.effective_range, abs(_x - round(self.x)) + abs(_y - round(self.y))
            )
            >= 0
        ):
            return list(
                filter(
                    lambda pos: self._identify_range(
                        self.effective_range,
                        abs(pos[0] - round(self.x)) + abs(pos[1] - round(self.y)),
                    )
                    >= 0,
                    self._generate_coverage_coordinates(
                        _x, _y, self.attack_coverage, MAP_P
                    ),
                )
            )
        return []

    def to_dict(self) -> dict:
        # 获取父类信息
        _data: dict = super().to_dict()
        _data["max_action_point"] = self.__max_action_point
        if self.__current_action_point != self.__max_action_point:
            _data["current_action_point"] = self.__current_action_point
        return _data

    # 画出角色
    def render(self, _surface: linpg.ImageSurface, MAP_P: linpg.AbstractTileMap, pos: Optional[tuple[int, int]] = None, size: Optional[tuple[int, int]] = None, action: Optional[str] = None, alpha: Optional[int] = None) -> None:  # type: ignore[override]
        if size is None:
            img_width: int = linpg.TileMapImagesModule.TILE_TEMPLE_WIDTH * 2
            size = (img_width, img_width)
        # 如果没有指定pos,则默认使用当前的动作
        if pos is None:
            pos = MAP_P.calculate_position(self.x, self.y)
        pos = linpg.Coordinates.subtract(
            pos,
            (
                linpg.TileMapImagesModule.TILE_TEMPLE_WIDTH // 2,
                int(linpg.TileMapImagesModule.TILE_TEMPLE_HEIGHT * 2.1),
            ),
        )
        return super().render(_surface, pos, size, action, alpha)

    # 把角色ui画到屏幕上
    def _drawUI(
        self,
        surface: linpg.ImageSurface,
        MAP_POINTER: linpg.AbstractTileMap,
        customHpData: Optional[tuple] = None,
    ) -> tuple:
        xTemp, yTemp = MAP_POINTER.calculate_position(self.x, self.y)
        xTemp += MAP_POINTER.tile_width // 4
        yTemp -= MAP_POINTER.tile_width // 5
        self.__hp_bar.set_size(MAP_POINTER.tile_width / 2, MAP_POINTER.tile_width / 10)
        self.__hp_bar.set_pos(xTemp, yTemp)
        # 预处理血条图片
        if customHpData is None:
            self.__hp_bar.set_percentage(self.current_hp / self.max_hp)
            self.__hp_bar.set_dying(False)
            self.__status_font.set_text("{0}/{1}".format(self.current_hp, self.max_hp))
        else:
            self.__hp_bar.set_percentage(customHpData[0] / customHpData[1])
            self.__hp_bar.set_dying(customHpData[2])
            self.__status_font.set_text(
                "{0}/{1}".format(customHpData[0], customHpData[1])
            )
        # 把血条画到屏幕上
        self.__hp_bar.draw(surface)
        self.__status_font.set_pos(
            self.__hp_bar.x
            + (self.__hp_bar.get_width() - self.__status_font.get_width()) // 2,
            self.__hp_bar.y
            + (self.__hp_bar.get_height() - self.__status_font.get_height()) // 2,
        )
        self.__status_font.draw(surface)
        # 返回坐标以供子类进行处理
        return xTemp, yTemp
