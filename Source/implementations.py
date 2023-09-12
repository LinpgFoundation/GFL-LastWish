from typing import Final
from .tbs import *


# 正在通讯中的立绘效果
class _CharacterInCommunicationFilterEffect(
    linpg.AbstractVisualNovelCharacterImageFilterEffect
):
    __KEYWORD: Final[str] = "communicating"

    def __init__(self, _x: int, _y: int, _width: int, _height: int) -> None:
        self.__N_IMAGE1: linpg.StaticImage = linpg.StaticImage(
            "<@ui>communication.png", _x, _y, _width, _height
        )
        self.__D_IMAGE1: linpg.StaticImage = self.__N_IMAGE1.copy()
        self.__D_IMAGE1.add_darkness(linpg.VisualNovelCharacterImageManager.DARKNESS)
        self.__N_IMAGE2: linpg.StaticImage = linpg.StaticImage(
            "<@ui>communication_effect.png", 0, 0
        )
        self.__D_IMAGE2: linpg.StaticImage = self.__N_IMAGE2.copy()
        self.__D_IMAGE2.add_darkness(linpg.VisualNovelCharacterImageManager.DARKNESS)
        self.__crop_rect: Optional[linpg.Rectangle] = None

    def set_crop_rect(self, rect: Optional[linpg.Rectangle]) -> None:
        self.__crop_rect = rect

    def get_rect(self) -> linpg.Rectangle:
        return self.__N_IMAGE1.get_rectangle()

    # 将滤镜应用到立绘上并渲染到屏幕上
    def render(
        self,
        characterImage: linpg.StaticImage,
        _surface: linpg.ImageSurface,
        is_silent: bool,
    ) -> None:
        # 如果自定义的crop_rect为None，则以self.__N_IMAGE1的rect为中心
        characterImage.set_crop_rect(
            self.__crop_rect if self.__crop_rect is not None else self.get_rect()
        )
        # 画出滤镜
        if not is_silent:
            self.__N_IMAGE1.set_alpha(characterImage.get_alpha())
            self.__N_IMAGE1.display(_surface, characterImage.get_pos())
        else:
            self.__D_IMAGE1.set_alpha(characterImage.get_alpha())
            self.__D_IMAGE1.display(_surface, characterImage.get_pos())
        # 画出立绘
        characterImage.draw(_surface)
        # 渲染电子信号的效果
        if self.__crop_rect is not None:
            if not is_silent:
                self.__N_IMAGE2.set_size(
                    self.__crop_rect.get_width(), self.__crop_rect.get_height()
                )
                self.__N_IMAGE2.display(
                    _surface,
                    linpg.coordinates.add(
                        characterImage.get_pos(), self.__crop_rect.get_pos()
                    ),
                )
            else:
                self.__D_IMAGE2.set_size(
                    self.__crop_rect.get_width(), self.__crop_rect.get_height()
                )
                self.__D_IMAGE2.display(
                    _surface,
                    linpg.coordinates.add(
                        characterImage.get_pos(), self.__crop_rect.get_pos()
                    ),
                )

    @classmethod
    def init(cls) -> None:
        _value = linpg.DataBase.get("Filters", cls.__KEYWORD)
        communicating_filter: _CharacterInCommunicationFilterEffect = (
            _CharacterInCommunicationFilterEffect(
                round(
                    linpg.display.get_width()
                    * linpg.numbers.convert_percentage(_value["rect"][0])
                ),
                round(
                    linpg.display.get_width()
                    * linpg.numbers.convert_percentage(_value["rect"][1])
                ),
                round(
                    linpg.display.get_width()
                    * linpg.numbers.convert_percentage(_value["rect"][2])
                ),
                round(
                    linpg.display.get_width()
                    * linpg.numbers.convert_percentage(_value["rect"][3])
                ),
            )
        )
        _crop: Optional[list] = _value.get("crop")
        if _crop is not None:
            _rect: linpg.Rectangle = communicating_filter.get_rect()
            communicating_filter.set_crop_rect(
                linpg.Rectangle(
                    _rect.x
                    + round(_rect.width * linpg.numbers.convert_percentage(_crop[0])),
                    _rect.y
                    + round(_rect.height * linpg.numbers.convert_percentage(_crop[1])),
                    round(_rect.width * linpg.numbers.convert_percentage(_crop[2])),
                    round(_rect.height * linpg.numbers.convert_percentage(_crop[3])),
                )
            )
        linpg.VisualNovelCharacterImageManager.FILTERS[
            cls.__KEYWORD
        ] = communicating_filter


# 初始化立绘滤镜
_CharacterInCommunicationFilterEffect.init()


# 重写视觉小说模组使其正确地调用和修改全局变量
class VisualNovelSystem(linpg.VisualNovelSystem):
    def stop(self) -> None:
        super().stop()
        linpg.global_variables.remove("section")
        if (
            self._content.get_section() == "dialog_before_battle"
            and self._has_reached_the_end() is True
        ):
            linpg.global_variables.set("currentMode", value="battle")
        else:
            linpg.global_variables.remove("currentMode")

    def _initialize(
        self, chapterType: str, chapterId: int, projectName: Optional[str]
    ) -> None:
        super()._initialize(chapterType, chapterId, projectName)
        linpg.global_variables.set("currentMode", value="dialog")
        linpg.global_variables.set("chapterType", value=self._chapter_type)
        linpg.global_variables.set("chapterId", value=self._chapter_id)
        linpg.global_variables.set("projectName", value=self._project_name)

    def load_progress(self, _data: dict) -> None:
        if _data.get("type") == "dialog":
            super().load_progress(_data)
        else:
            self.stop()
            # 设置参数
            linpg.global_variables.remove("section")
            linpg.global_variables.set("currentMode", value="battle")
            linpg.global_variables.remove("chapterType")
            linpg.global_variables.set("chapterId", value=0)
            linpg.global_variables.remove("projectName")
            linpg.global_variables.set("saveData", value=_data)


# 地图编辑器系统
class MapEditor(LoadingModule, linpg.AbstractMapEditor):
    def __init__(self) -> None:
        LoadingModule.__init__(self)
        linpg.AbstractMapEditor.__init__(self)
        self.set_map(AdvancedTileMap())
        # 绿色方块/方块标准
        self.__range_green: linpg.ImageSurface = linpg.Surfaces.NULL
        self.__range_red: linpg.ImageSurface = linpg.Surfaces.NULL

    def get_map(self) -> AdvancedTileMap:  # type: ignore[override]
        _map: linpg.AbstractTileMap = super().get_map()
        assert isinstance(_map, AdvancedTileMap)
        return _map

    def _init_ui(self) -> None:
        super()._init_ui()
        # 绿色方块/方块标准
        self.__range_green = linpg.Images.load(
            "<&ui>range_green.png", (self.get_map().tile_width, None)
        )
        self.__range_green.set_alpha(150)
        self.__range_red = linpg.Images.load(
            "<&ui>range_red.png", (self.get_map().tile_width, None)
        )
        self.__range_red.set_alpha(150)

    # 实现父类需要实现的方法 - 画出所有角色
    def _display_entities(self, _surface: linpg.ImageSurface) -> None:
        # 展示范围
        if self._tile_is_hovering is not None and self._no_container_is_hovered is True:
            if self._delete_mode is True:
                xTemp, yTemp = self.get_map().calculate_position(
                    self._tile_is_hovering[0], self._tile_is_hovering[1]
                )
                _surface.blit(
                    self.__range_red,
                    (
                        xTemp
                        + (self.get_map().tile_width - self.__range_red.get_width()) // 2,
                        yTemp,
                    ),
                )
            elif self.isAnyObjectSelected() is True:
                xTemp, yTemp = self.get_map().calculate_position(
                    self._tile_is_hovering[0], self._tile_is_hovering[1]
                )
                _surface.blit(
                    self.__range_green,
                    (
                        xTemp
                        + (self.get_map().tile_width - self.__range_green.get_width())
                        // 2,
                        yTemp,
                    ),
                )
        if self._show_barrier_mask is True or self._delete_mode is True:
            for y in range(self.get_map().row):
                for x in range(self.get_map().column):
                    posTupleTemp: tuple[int, int] = self.get_map().calculate_position(
                        x, y
                    )
                    if (
                        -self.get_map().tile_width
                        <= posTupleTemp[0]
                        < _surface.get_width()
                        and -self.get_map().tile_width
                        <= posTupleTemp[1]
                        < _surface.get_height()
                    ):
                        _surface.blit(
                            self.__range_green
                            if self.get_map().is_passable(x, y)
                            else self.__range_red,
                            (
                                posTupleTemp[0]
                                + (
                                    self.get_map().tile_width
                                    - self.__range_green.get_width()
                                )
                                // 2,
                                posTupleTemp[1],
                            ),
                        )
                    elif (
                        posTupleTemp[0] >= _surface.get_width()
                        or posTupleTemp[1] >= _surface.get_height()
                    ):
                        break
                if (
                    self.get_map().calculate_position(0, y + 1)[1]
                    >= _surface.get_height()
                ):
                    break
            if self._tile_is_hovering is not None:
                xTemp, yTemp = self.get_map().calculate_position(
                    self._tile_is_hovering[0], self._tile_is_hovering[1]
                )
                _surface.blit(
                    self.__range_red,
                    (
                        xTemp
                        + (self.get_map().tile_width - self.__range_red.get_width()) // 2,
                        yTemp,
                    ),
                )
        # 角色动画
        for faction in self._entities_data:
            for value in self._entities_data[faction].values():
                assert isinstance(value, BasicEntity)
                value.render(_surface, self.get_map())
                if len(self._select_pos) > 0:
                    value.set_selected(value.is_overlapped_with(self._select_rect))
        # 检测角色所占据的装饰物（即需要透明化，方便玩家看到角色）
        charactersPos: list = []
        for value1 in self._entities_data.values():
            for dataDict in value1.values():
                charactersPos.append((round(dataDict.x), round(dataDict.y)))
                charactersPos.append((round(dataDict.x) + 1, round(dataDict.y) + 1))
        # 展示场景装饰物
        self.get_map().display_decoration(_surface, tuple(charactersPos))

    # 获取角色数据 - 子类需实现
    def get_entities_data(self) -> dict[str, dict[str, linpg.Entity]]:
        return self._entities_data

    # 更新特定角色
    def update_entity(self, faction: str, key: str, data: dict) -> None:
        if faction == "GriffinKryuger":
            self._entities_data[faction][key] = FriendlyCharacter(data, "dev")
        if faction == "SangvisFerri":
            self._entities_data[faction][key] = HostileCharacter(data, "dev")

    # 加载图片 - 重写使其更新加载信息
    def _load_map(self, _data: dict) -> None:
        self._update_loading_info("now_loading_map")
        super()._load_map(_data)

    # 加载数据 - 重写使其以多线程的形式进行
    def new(
        self,
        chapterType: str,
        chapterId: int,
        projectName: Optional[str] = None,
    ) -> None:
        # 初始化加载模块
        self._initialize_loading_module()
        _task: threading.Thread = threading.Thread(
            target=super().new, args=(chapterType, chapterId, projectName)
        )
        # 开始加载
        _task.start()
        # 显示加载过程
        while _task.is_alive():
            linpg.display.get_window().fill(linpg.colors.BLACK)
            self._show_current_loading_progress(linpg.display.get_window())
            linpg.display.flip()
        # 加载完成，释放初始化模块占用的内存
        self._finish_loading()
