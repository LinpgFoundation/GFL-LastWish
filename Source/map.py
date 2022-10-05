from copy import deepcopy
from .ui import *

# 篝火
class CampfireObject(linpg.DecorationObject):
    def __init__(
        self, x: int, y: int, _type: str, _variation: int = 0, status: dict = {}
    ):
        super().__init__(x, y, _type, _variation, status)
        self.__range: int = status.get("range", 3)
        self.__alpha: int = 255
        self.__img_id: int = linpg.Numbers.get_random_int(0, 90)
        if not self._has_status("lit"):
            self.set_status("lit", True)

    @staticmethod
    def from_dict(_data: dict) -> "CampfireObject":
        _type, sub_id = str(_data["id"]).split(":")
        if not isinstance(_data.get("status"), dict):
            _data["status"] = {}
        return CampfireObject(_data["x"], _data["y"], _type, id(sub_id), _data["status"])

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

    # 画出篝火（注意，alpha不会被使用，它只因为兼容性和一致性而存在）
    def blit(self, _surface: linpg.ImageSurface, pos: tuple[int, int], is_dark: bool, alpha: int) -> None:  # type: ignore[override]
        # 查看篝火的状态是否正在变化，并调整对应的alpha值
        if self.get_status("lit") is True:
            if self.__alpha < 255:
                self.__alpha += 15
        elif self.__alpha > 0:
            self.__alpha -= 15
        # 底层 - 未燃烧的图片
        if self.__alpha < 255:
            self._variation = 0
            super().blit(_surface, pos, is_dark, 255)
        # 顶层 - 燃烧的图片
        if self.__alpha > 0:
            self._variation = self.__img_id // 10
            super().blit(_surface, pos, is_dark, self.__alpha)
            if (
                self._variation
                < linpg.DecorationImagesModule.get_image_num(self.type) - 1
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
        del data_t["image"]
        if len(self.items) > 0:
            data_t["items"] = deepcopy(self.items)
        if len(self.whitelist) > 0:
            data_t["whitelist"] = deepcopy(self.whitelist)
        return data_t


class AdvancedTileMap(linpg.TileMap):
    def __init__(self) -> None:
        super().__init__()

    def add_decoration(self, _data: dict, _sort: bool = False) -> None:
        _type: str = str(_data["id"]).split(":")[0]
        if _type == "campfire":
            self.decorations.append(CampfireObject.from_dict(_data))
        elif _type == "chest":
            self.decorations.append(ChestObject.from_dict(_data))
        else:
            super().add_decoration(_data)
        if _sort is True:
            self.decorations.sort()

    def _get_lit_area(self, alliances_data: dict) -> set:
        lightArea: set[tuple[int, int]] = super()._get_lit_area(alliances_data)
        for _item in self.decorations:
            if isinstance(_item, CampfireObject):
                for _pos in _item.get_lit_coordinates():
                    lightArea.add(_pos)
        return lightArea
