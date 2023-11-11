from copy import deepcopy
from typing import Any, Optional

import numpy

import linpg

# 初始化linpg系统模块
linpg.display.init()

# 加载版本信息
_VERSION_INFO: dict = {
    "recommended_linpg_patch": 2,
    "recommended_linpg_revision": 7,
    "revision": 2,
    "version": 1,
}

# 确认linpg的版本是推荐版本
linpg.LinpgVersionChecker(
    ">=",
    _VERSION_INFO["recommended_linpg_revision"],
    _VERSION_INFO["recommended_linpg_patch"],
)


# 篝火
class CampfireObject(linpg.DecorationObject):
    def __init__(
        self, x: int, y: int, _type: str, _variation: int, status: dict = {}
    ) -> None:
        super().__init__(x, y, _type, _variation, status)
        self.__range: int = status.get("range", 3)
        self.__img_id: int = linpg.Numbers.get_random_int(0, 90)
        if not self._has_status("lit"):
            self.set_status("lit", True)

    @staticmethod
    def from_dict(_data: dict) -> "CampfireObject":
        index_args: list[str] = str(_data["id"]).split(":")
        if not isinstance(_data.get("status"), dict):
            _data["status"] = {}
        return CampfireObject(
            _data["x"],
            _data["y"],
            index_args[0],
            0 if len(index_args) < 2 else int(index_args[1]),
            _data["status"],
        )

    def to_dict(self) -> dict:
        data_t: dict = super().to_dict()
        data_t["status"]["range"] = self.__range
        if "status" in data_t and data_t["status"]["lit"] is True:
            del data_t["status"]["lit"]
            if len(data_t["status"]) <= 0:
                del data_t["status"]
        return data_t

    def interact(self) -> None:
        self.set_status("lit", not bool(self.get_status("lit")))

    def get_range(self) -> int:
        return self.__range

    def get_lit_coordinates(self) -> list[tuple[int, int]]:
        return (
            linpg.coordinates.get_in_diamond_shaped(self.x, self.y, self.__range)
            if self.get_status("lit") is True
            else []
        )

    # 画出篝火
    def display(
        self, _surface: linpg.ImageSurface, offSet: tuple[int, int] = linpg.ORIGIN
    ) -> None:
        # 查看篝火的状态是否正在变化，并调整对应的alpha值
        if self.get_status("lit") is True:
            if self.get_alpha() < 255:
                self.set_alpha(self.get_alpha() + 15)
        elif self.get_alpha() > 0:
            self.set_alpha(self.get_alpha() - 15)
        # 底层 - 未燃烧的图片
        if self.get_alpha() < 255:
            alpha_temp: int = self.get_alpha()
            self.set_alpha(255)
            self._variation = 0
            super().display(_surface, offSet)
            self.set_alpha(alpha_temp)
        # 顶层 - 燃烧的图片
        if self.get_alpha() > 0:
            self._variation = self.__img_id // 10
            super().display(_surface, offSet)
            if (
                self._variation
                < linpg.DecorationImagesModule.count_variations(self.type) - 1
            ):
                self.__img_id += 1
            else:
                self.__img_id = 10


# 箱子
class ChestObject(linpg.DecorationObject):
    def __init__(
        self, x: int, y: int, _type: str, _variation: int = 0, status: dict = {}
    ):
        super().__init__(x, y, _type, _variation, status)
        # 箱内物品
        self.items: dict = status.get("items", {})
        # 是否箱子有白名单（只能被特定角色拾取）
        self.whitelist: list = status.get("whitelist", [])

    @staticmethod
    def from_dict(_data: dict) -> "ChestObject":
        _type = str(_data["id"]).split(":")[0]
        if not isinstance(_data.get("status"), dict):
            _data["status"] = {}
        return ChestObject(_data["x"], _data["y"], _type, status=_data["status"])

    def to_dict(self) -> dict:
        data_t: dict = super().to_dict()
        if len(self.items) > 0:
            data_t["items"] = deepcopy(self.items)
        if len(self.whitelist) > 0:
            data_t["whitelist"] = deepcopy(self.whitelist)
        return data_t


# 自定义的地图
class AdvancedTileMap(linpg.AbstractTileMap):
    def __init__(self) -> None:
        super().__init__()
        # 处于光处的区域
        self.__lit_area: tuple[tuple[int, int], ...] = tuple()

    def update(self, _data: dict, _block_size: linpg.int_f) -> None:
        super().update(_data, _block_size)
        # 处于光处的区域
        self.__lit_area = (
            tuple()
            if linpg.TileMapImagesModule.DARKNESS > 0
            else tuple(
                linpg.coordinates.convert(area_coordinate)
                for area_coordinate in _data["map"].get("lit_area", [])
            )
        )

    def to_dict(self) -> dict[str, Any]:
        _data: dict = super().to_dict()
        _data["map"]["lit_area"] = [
            list(area_coordinate) for area_coordinate in self.__lit_area
        ]
        return _data

    # 获取可视光亮区域
    def _get_lit_area(self, alliances_data: dict) -> set:
        lightArea: set[tuple[int, int]] = set()
        for _alliance in alliances_data.values():
            for _area in _alliance.get_visual_range_coordinates(self):
                for _pos in _area:
                    lightArea.add(_pos)
            lightArea.add((round(_alliance.x), round(_alliance.y)))
        for _item in self.decorations:
            if isinstance(_item, CampfireObject):
                for _pos in _item.get_lit_coordinates():
                    lightArea.add(_pos)
        return lightArea

    # 刷新可视光亮区域
    def refresh_lit_area(self, alliances_data: dict) -> None:
        self.__lit_area = tuple(self._get_lit_area(alliances_data))
        self._refresh()

    # 查看坐标是否在光亮范围内
    def is_coordinate_in_lit_area(self, x: linpg.int_f, y: linpg.int_f) -> bool:
        return (
            True
            if linpg.TileMapImagesModule.DARKNESS <= 0
            else (round(x), round(y)) in self.__lit_area
        )

    # 计算在地图中的方块
    def calculate_coordinate(
        self, on_screen_pos: Optional[tuple[int, int]] = None
    ) -> Optional[tuple[int, int]]:
        if on_screen_pos is None:
            on_screen_pos = linpg.controller.mouse.get_pos()
        guess_x: int = int(
            (on_screen_pos[0] - self.local_x) / self.tile_width
            + (on_screen_pos[1] - self.local_y) / self.tile_height
            - self.row / 2
        )
        guess_y: int = int(
            (on_screen_pos[1] - self.local_y) / self.tile_height
            - (on_screen_pos[0] - self.local_x) / self.tile_width
            + self.row / 2
        )
        return (
            (guess_x, guess_y)
            if self.column > guess_x >= 0 and self.row > guess_y >= 0
            else None
        )

    # 计算在地图中的位置
    def calculate_position(self, x: linpg.int_f, y: linpg.int_f) -> tuple[int, int]:
        return (
            round((x - y + self.row - 1) * self.tile_width / 2) + self.local_x,
            round((y + x) * self.tile_height / 2) + self.local_y,
        )

    # 新增装饰物
    def add_decoration(self, _data: dict) -> None:
        _type: str = str(_data["id"]).split(":")[0]
        if _type == "campfire":
            self._add_decoration(CampfireObject.from_dict(_data))
        elif _type == "chest":
            self._add_decoration(ChestObject.from_dict(_data))
        else:
            super().add_decoration(_data)

    # 把装饰物画到屏幕上
    def display_decoration(
        self, _surface: linpg.ImageSurface, occupied_coordinates: tuple
    ) -> None:
        # 计算需要画出的范围
        screen_min: int = -self.tile_width
        # 历遍装饰物列表里的物品
        for _item in self.decorations:
            # 在地图的坐标
            thePosInMap: tuple[int, int] = self.calculate_position(_item.x, _item.y)
            if (
                screen_min <= thePosInMap[0] < _surface.get_width()
                and screen_min <= thePosInMap[1] < _surface.get_height()
            ):
                # 透明度
                if not isinstance(_item, CampfireObject):
                    _item.set_alpha(
                        100
                        if (
                            self._DECORATION_DATABASE[_item.type].get("hidable", False)
                            is True
                            and _item.get_pos() in occupied_coordinates
                            and self.is_coordinate_in_lit_area(_item.x, _item.y)
                        )
                        else 255
                    )
                # 画出
                _item.set_dark_mode(not self.is_coordinate_in_lit_area(_item.x, _item.y))
                _item.blit(_surface, thePosInMap)

    def _get_tile_image(self, x: int, y: int) -> linpg.StaticImage:
        return linpg.TileMapImagesModule.get_image(
            self.get_tile(x, y), not self.is_coordinate_in_lit_area(x, y)
        )

    # 寻找2点之间的最短路径
    def find_path(  # type: ignore[override]
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        alliances: dict,
        enemies: dict,
        can_move_through_darkness: bool = False,
        lenMax: int | None = None,
        enemies_ignored: tuple = tuple(),
        ignore_alliances: bool = False,
    ) -> list[tuple[int, int]]:
        # 初始化寻路地图
        map2d: numpy.ndarray = numpy.ones(self.shape, dtype=numpy.byte)
        # 如果角色无法移动至黑暗处
        if not can_move_through_darkness and linpg.TileMapImagesModule.DARKNESS > 0:
            map2d.fill(0)
            for _pos in self.__lit_area:
                map2d[_pos[0], _pos[1]] = 1
        # 如果不忽略友方角色，则将所有友方角色的坐标点设置为障碍区块
        if not ignore_alliances:
            for value in alliances.values():
                map2d[round(value.x), round(value.y)] = 0
        # 如果忽略友方角色，则确保终点没有友方角色
        else:
            for value in alliances.values():
                if round(value.x) == goal[0] and round(value.y) == goal[1]:
                    return []
        # 将所有敌方角色的坐标点设置为障碍区块
        for key, value in enemies.items():
            if key not in enemies_ignored:
                map2d[round(value.x), round(value.y)] = 0
        return super().find_path(start, goal, lenMax, map2d)
