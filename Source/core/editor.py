from .ui import linpg, os, glob
from copy import deepcopy

# 地图编辑器系统
class MapEditor(linpg.AbstractBattleSystem):
    def __init__(self) -> None:
        self.__originalData: dict = {}
        self.__buttons_container: linpg.GameObjectsDictContainer = linpg.ui.generate_container("map_editor_buttons")
        self.__right_container_buttons: linpg.GameObjectsDictContainer = linpg.ui.generate_container(
            "map_editor_right_container_buttons"
        )
        self.__bottom_container_buttons: linpg.GameObjectsDictContainer = linpg.ui.generate_container(
            "map_editor_bottom_container_buttons"
        )
        super().__init__()

    # 返回需要保存数据
    def _get_data_need_to_save(self) -> dict:
        return self.__originalData | super()._get_data_need_to_save()

    # 加载角色的数据
    def __load_characters_data(self, mapFileData: dict) -> None:
        # 生成进程并开始加载角色信息
        self._start_loading_characters(mapFileData["character"], mapFileData["sangvisFerri"], "dev")
        # 类似多线程的join，待完善
        while self._is_characters_loader_alive():
            pass

    # 初始化
    def load(self, screen: linpg.ImageSurface, chapterType: str, chapterId: int, projectName: str = None) -> None:
        self._initialize(chapterType, chapterId, projectName)
        self.folder_for_save_file, self.name_for_save_file = os.path.split(self.get_map_file_location())
        # 载入地图数据
        mapFileData: dict = linpg.config.load(self.get_map_file_location())
        # 初始化角色信息
        self.__load_characters_data(mapFileData)
        # 初始化地图
        if "map" not in mapFileData or mapFileData["map"] is None or len(mapFileData["map"]) == 0:
            SnowEnvImg = [
                "TileSnow01",
                "TileSnow01ToStone01",
                "TileSnow01ToStone02",
                "TileSnow02",
                "TileSnow02ToStone01",
                "TileSnow02ToStone02",
            ]
            block_y = 50
            block_x = 50
            default_map = [[SnowEnvImg[linpg.get_random_int(0, 5)] for a in range(block_x)] for i in range(block_y)]
            mapFileData["map"] = default_map
            linpg.config.save(self.get_map_file_location(), mapFileData)
        # 加载地图
        self._initialize_map(mapFileData)
        del mapFileData
        """加载右侧的界面"""
        # 加载容器图片
        container_width: int = int(screen.get_width() * 0.2)
        container_height: int = int(screen.get_height())
        button_width: int = int(screen.get_width() * 0.04)
        button_height: int = int(screen.get_height() * 0.2)
        panding: int = int(screen.get_height() * 0.01)
        self.__right_container_buttons.get("select_block").set_left(
            int(
                (
                    container_width
                    - self.__right_container_buttons.get("select_block").get_width()
                    - self.__right_container_buttons.get("select_decoration").get_width()
                    - panding
                )
                / 2
            )
        )
        self.__right_container_buttons.get("select_decoration").set_left(
            self.__right_container_buttons.get("select_block").right + panding
        )
        self.__UIContainerRight = linpg.load.dynamic_image("<!ui>container.png", (0, 0), (container_width, container_height))
        self.__UIContainerButtonRight = linpg.load.movable_image(
            "<!ui>container_button.png",
            (int(screen.get_width() - button_width), int((screen.get_height() - button_height) / 2)),
            (int(screen.get_width() - button_width - container_width), int((screen.get_height() - button_height) / 2)),
            (int(container_width / 10), 0),
            (button_width, button_height),
        )
        self.__UIContainerRight.rotate(90)
        self.__UIContainerButtonRight.rotate(90)
        # 加载背景图片
        self.__envImgContainer: object = linpg.SurfaceContainerWithScrollbar(
            None,
            int(container_width * 0.075),
            int(screen.get_height() * 0.1),
            int(container_width * 0.85),
            int(screen.get_height() * 0.85),
            "vertical",
        )
        for imgPath in glob(os.path.join(linpg.ASSET.get_internal_environment_image_path("block"), "*.png")):
            self.__envImgContainer.set(
                os.path.basename(imgPath).replace(".png", ""), linpg.load.img(imgPath, (self._MAP.block_width / 3, None))
            )
        self.__envImgContainer.set_item_per_line(4)
        self.__envImgContainer.set_scroll_bar_pos("right")
        self.__envImgContainer.set_visible(True)
        self.__envImgContainer.distance_between_item = panding
        # 加载所有的装饰品
        self.__decorationsImgContainer: object = linpg.SurfaceContainerWithScrollbar(
            None,
            int(container_width * 0.075),
            int(screen.get_height() * 0.1),
            int(container_width * 0.85),
            int(screen.get_height() * 0.85),
            "vertical",
        )
        for imgPath in glob(os.path.join(linpg.ASSET.get_internal_environment_image_path("decoration"), "*.png")):
            self.__decorationsImgContainer.set(
                os.path.basename(imgPath).replace(".png", ""), linpg.load.img(imgPath, (self._MAP.block_width / 3, None))
            )
        self.__decorationsImgContainer.set_item_per_line(4)
        self.__decorationsImgContainer.set_scroll_bar_pos("right")
        self.__decorationsImgContainer.set_visible(False)
        self.__decorationsImgContainer.distance_between_item = panding
        """加载下方的界面"""
        container_width = int(screen.get_width() * 0.8)
        container_height = int(screen.get_height() * 0.3)
        button_width = int(screen.get_width() * 0.14)
        button_height = int(screen.get_height() * 0.05)
        self.__bottom_container_buttons.get("select_sangvis_ferri").set_left(
            self.__bottom_container_buttons.get("select_griffin").right + panding
        )
        self.__UIContainerBottom = linpg.load.dynamic_image("<!ui>container.png", (0, 0), (container_width, container_height))
        self.__UIContainerButtonBottom = linpg.load.movable_image(
            "<!ui>container_button.png",
            (int((container_width - button_width) / 2), int(screen.get_height() - button_height)),
            (int((container_width - button_width) / 2), int(screen.get_height() - button_height - container_height)),
            (0, int(container_height / 10)),
            (button_width, button_height),
        )
        # 加载所有友方的角色的图片文件
        self.__charactersImgContainer: object = linpg.SurfaceContainerWithScrollbar(
            None, container_width * 0.025, container_height * 0.2, container_width * 0.95, container_height * 0.7, "horizontal"
        )
        for imgPath in glob(r"Assets/image/character/*"):
            img_name = os.path.basename(imgPath)
            self.__charactersImgContainer.set(
                img_name,
                linpg.transform.crop_bounding(
                    linpg.load.img(
                        os.path.join(imgPath, "wait", "{}_wait_0.png".format(img_name)), (None, container_height * 1.5)
                    )
                ),
            )
        self.__charactersImgContainer.set_scroll_bar_pos("bottom")
        self.__charactersImgContainer.set_visible(True)
        self.__charactersImgContainer.distance_between_item = panding
        # 加载所有敌对角色的图片文件
        self.__sangvisFerrisImgContainer: object = linpg.SurfaceContainerWithScrollbar(
            None, container_width * 0.025, container_height * 0.2, container_width * 0.95, container_height * 0.7, "horizontal"
        )
        for imgPath in glob(r"Assets/image/sangvisFerri/*"):
            img_name = os.path.basename(imgPath)
            self.__sangvisFerrisImgContainer.set(
                img_name,
                linpg.transform.crop_bounding(
                    linpg.load.img(
                        os.path.join(imgPath, "wait", "{}_wait_0.png".format(img_name)), (None, container_height * 1.5)
                    )
                ),
            )
        self.__sangvisFerrisImgContainer.set_scroll_bar_pos("bottom")
        self.__sangvisFerrisImgContainer.set_visible(False)
        self.__sangvisFerrisImgContainer.distance_between_item = panding
        # 绿色方块/方块标准
        self.greenBlock = linpg.load.img("Assets/image/UI/range/green.png", (self._MAP.block_width * 0.8, None))
        self.greenBlock.set_alpha(150)
        self.redBlock = linpg.load.img("Assets/image/UI/range/red.png", (self._MAP.block_width * 0.8, None))
        self.redBlock.set_alpha(150)
        self.deleteMode: bool = False
        self.object_to_put_down = None
        # 设置按钮位置
        self.__buttons_container.get("back").set_left(self.__buttons_container.get("save").get_right() + panding)
        self.__buttons_container.get("delete").set_left(self.__buttons_container.get("back").get_right() + panding)
        self.__buttons_container.get("reload").set_left(self.__buttons_container.get("delete").get_right() + panding)
        # 未保存离开时的警告
        self.__no_save_warning = linpg.ui.generate("leave_without_saving_warning")
        # 用于储存即将发下的物品的具体参数
        self.data_to_edit = None
        # 读取地图原始文件
        self.__originalData = linpg.config.load(self.get_map_file_location())
        del self.__originalData["map"], self.__originalData["decoration"]
        del self.__originalData["character"], self.__originalData["sangvisFerri"]

    # 将地图制作器的界面画到屏幕上
    def draw(self, screen: linpg.ImageSurface) -> None:
        block_get_click = self._MAP.calBlockInMap()
        for event in linpg.controller.events:
            if event.type == linpg.key.DOWN:
                if event.key == linpg.key.ESCAPE:
                    self.object_to_put_down = None
                    self.data_to_edit = None
                    self.deleteMode = False
                self._check_key_down(event)
            elif event.type == linpg.key.UP:
                self._check_key_up(event)
            elif event.type == linpg.MOUSE_BUTTON_DOWN:
                # 上下滚轮-放大和缩小地图
                if self.__UIContainerButtonRight.is_hovered():
                    self.__UIContainerButtonRight.switch()
                    self.__UIContainerButtonRight.flip(True)
                elif self.__UIContainerButtonBottom.is_hovered():
                    self.__UIContainerButtonBottom.switch()
                    self.__UIContainerButtonBottom.flip(False, True)
                elif self.deleteMode is True and block_get_click is not None:
                    # 查看当前位置是否有装饰物
                    decoration = self._MAP.find_decoration_on((block_get_click["x"], block_get_click["y"]))
                    # 如果发现有冲突的装饰物
                    if decoration is not None:
                        self._MAP.remove_decoration(decoration)
                    else:
                        any_chara_replace = None
                        for key, value in {
                            **self._alliances_data,
                            **self._enemies_data,
                        }.items():
                            if value.x == block_get_click["x"] and value.y == block_get_click["y"]:
                                any_chara_replace = key
                                break
                        if any_chara_replace is not None:
                            if any_chara_replace in self._alliances_data:
                                self._alliances_data.pop(any_chara_replace)
                            elif any_chara_replace in self._enemies_data:
                                self._enemies_data.pop(any_chara_replace)
                else:
                    if (
                        linpg.controller.get_event("confirm")
                        and block_get_click is not None
                        and self.object_to_put_down is not None
                        and not self.__UIContainerRight.is_hovered((self.__UIContainerButtonRight.right, 0))
                        and not self.__UIContainerBottom.is_hovered((self.__UIContainerButtonBottom.bottom, 0))
                    ):
                        if self.object_to_put_down["type"] == "block":
                            self._MAP.update_block(block_get_click, self.object_to_put_down["id"])
                        elif self.object_to_put_down["type"] == "decoration":
                            # 查看当前位置是否有装饰物
                            decoration = self._MAP.find_decoration_on((block_get_click["x"], block_get_click["y"]))
                            # 如果发现有冲突的装饰物
                            if decoration is not None:
                                self._MAP.remove_decoration(decoration)
                            self._MAP.add_decoration(
                                {
                                    "image": self.object_to_put_down["id"],
                                    "x": block_get_click["x"],
                                    "y": block_get_click["y"],
                                },
                                linpg.DataBase.get("Decorations")[self.object_to_put_down["id"]],
                                "{0}_{1}".format(self.object_to_put_down["id"], self._MAP.count_decorations()),
                            )
                        elif self.object_to_put_down["type"] == "character" or self.object_to_put_down["type"] == "sangvisFerri":
                            any_chara_replace = None
                            for key, value in {**self._alliances_data, **self._enemies_data}.items():
                                if value.x == block_get_click["x"] and value.y == block_get_click["y"]:
                                    any_chara_replace = key
                                    break
                            if any_chara_replace is not None:
                                if any_chara_replace in self._alliances_data:
                                    self._alliances_data.pop(any_chara_replace)
                                elif any_chara_replace in self._enemies_data:
                                    self._enemies_data.pop(any_chara_replace)
                            the_id = 0
                            if self.object_to_put_down["type"] == "character":
                                while self.object_to_put_down["id"] + "_" + str(the_id) in self._alliances_data:
                                    the_id += 1
                                nameTemp = self.object_to_put_down["id"] + "_" + str(the_id)
                                self._alliances_data[nameTemp] = linpg.FriendlyCharacter(
                                    deepcopy(linpg.CHARACTER_DATABASE[self.object_to_put_down["id"]])
                                    | {
                                        "x": block_get_click["x"],
                                        "y": block_get_click["y"],
                                        "type": self.object_to_put_down["id"],
                                        "bullets_carried": 100,
                                    },
                                    "dev",
                                )
                            elif self.object_to_put_down["type"] == "sangvisFerri":
                                while self.object_to_put_down["id"] + "_" + str(the_id) in self._enemies_data:
                                    the_id += 1
                                nameTemp = self.object_to_put_down["id"] + "_" + str(the_id)
                                self._enemies_data[nameTemp] = linpg.HostileCharacter(
                                    deepcopy(linpg.CHARACTER_DATABASE[self.object_to_put_down["id"]])
                                    | {
                                        "x": block_get_click["x"],
                                        "y": block_get_click["y"],
                                        "type": self.object_to_put_down["id"],
                                        "bullets_carried": 100,
                                    },
                                    "dev",
                                )
        # 其他移动的检查
        self._check_right_click_move()
        self._check_jostick_events()

        # 画出地图
        self._display_map(screen)
        if (
            block_get_click is not None
            and not self.__UIContainerRight.is_hovered((self.__UIContainerButtonRight.right, 0))
            and not self.__UIContainerBottom.is_hovered((self.__UIContainerButtonBottom.bottom, 0))
        ):
            if self.deleteMode is True:
                xTemp, yTemp = self._MAP.calPosInMap(block_get_click["x"], block_get_click["y"])
                screen.blit(self.redBlock, (xTemp + self._MAP.block_width * 0.1, yTemp))
            elif self.object_to_put_down is not None:
                xTemp, yTemp = self._MAP.calPosInMap(block_get_click["x"], block_get_click["y"])
                screen.blit(self.greenBlock, (xTemp + self._MAP.block_width * 0.1, yTemp))

        # 角色动画
        for key in self._alliances_data:
            self._alliances_data[key].draw(screen, self._MAP)
            if (
                self.object_to_put_down is None
                and linpg.controller.get_event("confirm")
                and self._alliances_data[key].x == int(linpg.controller.mouse.x / self.greenBlock.get_width())
                and self._alliances_data[key].y == int(linpg.controller.mouse.y / self.greenBlock.get_height())
            ):
                self.data_to_edit = self._alliances_data[key]
        for key in self._enemies_data:
            self._enemies_data[key].draw(screen, self._MAP)
            if (
                self.object_to_put_down is None
                and linpg.controller.get_event("confirm")
                and self._enemies_data[key].x == int(linpg.controller.mouse.x / self.greenBlock.get_width())
                and self._enemies_data[key].y == int(linpg.controller.mouse.y / self.greenBlock.get_height())
            ):
                self.data_to_edit = self._enemies_data[key]

        # 展示设施
        self._display_decoration(screen)

        # 画出右侧容器的UI
        self.__UIContainerButtonRight.draw(screen)
        if self.__UIContainerButtonRight.right < screen.get_width():
            self.__UIContainerRight.display(screen, (self.__UIContainerButtonRight.right, 0))
            self.__envImgContainer.display(screen, (self.__UIContainerButtonRight.right, 0))
            self.__decorationsImgContainer.display(screen, (self.__UIContainerButtonRight.right, 0))
            self.__right_container_buttons.display(screen, (self.__UIContainerButtonRight.right, 0))
            if linpg.controller.get_event("confirm") is True:
                if self.__right_container_buttons.item_being_hovered == "select_block":
                    self.__envImgContainer.set_visible(True)
                    self.__decorationsImgContainer.set_visible(False)
                elif self.__right_container_buttons.item_being_hovered == "select_decoration":
                    self.__envImgContainer.set_visible(False)
                    self.__decorationsImgContainer.set_visible(True)
            if linpg.controller.get_event("confirm"):
                if self.__envImgContainer.is_visible() and self.__envImgContainer.item_being_hovered is not None:
                    self.object_to_put_down = {
                        "type": "block",
                        "id": self.__envImgContainer.item_being_hovered,
                    }
                elif (
                    self.__decorationsImgContainer.is_visible() and self.__decorationsImgContainer.item_being_hovered is not None
                ):
                    self.object_to_put_down = {
                        "type": "decoration",
                        "id": self.__decorationsImgContainer.item_being_hovered,
                    }
        # 画出下方容器的UI
        self.__UIContainerButtonBottom.draw(screen)
        if self.__UIContainerButtonBottom.bottom < screen.get_height():
            self.__UIContainerBottom.display(screen, (0, self.__UIContainerButtonBottom.bottom))
            self.__charactersImgContainer.display(screen, (0, self.__UIContainerButtonBottom.bottom))
            self.__sangvisFerrisImgContainer.display(screen, (0, self.__UIContainerButtonBottom.bottom))
            self.__bottom_container_buttons.display(screen, (0, self.__UIContainerButtonBottom.bottom))
            if linpg.controller.get_event("confirm"):
                if self.__bottom_container_buttons.item_being_hovered == "select_griffin":
                    self.__charactersImgContainer.set_visible(True)
                    self.__sangvisFerrisImgContainer.set_visible(False)
                elif self.__bottom_container_buttons.item_being_hovered == "select_sangvis_ferri":
                    self.__charactersImgContainer.set_visible(False)
                    self.__sangvisFerrisImgContainer.set_visible(True)
                if self.__charactersImgContainer.is_visible() and self.__charactersImgContainer.item_being_hovered is not None:
                    self.object_to_put_down = {"type": "character", "id": self.__charactersImgContainer.item_being_hovered}
                elif (
                    self.__sangvisFerrisImgContainer.is_visible()
                    and self.__sangvisFerrisImgContainer.item_being_hovered is not None
                ):
                    self.object_to_put_down = {"type": "sangvisFerri", "id": self.__sangvisFerrisImgContainer.item_being_hovered}

        self.__buttons_container.draw(screen)
        if linpg.controller.get_event("confirm") and self.object_to_put_down is None and not self.deleteMode:
            if self.__buttons_container.item_being_hovered == "save":
                self.save_progress()
            elif self.__buttons_container.item_being_hovered == "back":
                if linpg.config.load(self.get_map_file_location()) == self.__originalData:
                    self.stop()
                else:
                    self.__no_save_warning.set_visible(True)
            elif self.__buttons_container.item_being_hovered == "delete":
                self.object_to_put_down = None
                self.data_to_edit = None
                self.deleteMode = True
            elif self.__buttons_container.item_being_hovered == "reload":
                tempLocal_x, tempLocal_y = self._MAP.get_local_pos()
                # 读取地图数据
                mapFileData = linpg.config.load(self.get_map_file_location())
                # 初始化角色信息
                self.__load_characters_data(mapFileData)
                # 加载地图
                self._initialize_map(mapFileData)
                del mapFileData
                self._MAP.set_local_pos(tempLocal_x, tempLocal_y)
                # 读取地图
                self.__originalData = linpg.config.load(self.get_map_file_location())
                del self.__originalData["map"], self.__originalData["decoration"]
                del self.__originalData["character"], self.__originalData["sangvisFerri"]

        # 跟随鼠标显示即将被放下的物品
        if self.object_to_put_down is not None:
            if self.object_to_put_down["type"] == "block":
                screen.blit(self.__envImgContainer.get(self.object_to_put_down["id"]), linpg.controller.mouse.pos)
            elif self.object_to_put_down["type"] == "decoration":
                screen.blit(self.__decorationsImgContainer.get(self.object_to_put_down["id"]), linpg.controller.mouse.pos)
            elif self.object_to_put_down["type"] == "character":
                screen.blit(self.__charactersImgContainer.get(self.object_to_put_down["id"]), linpg.controller.mouse.pos)
            elif self.object_to_put_down["type"] == "sangvisFerri":
                screen.blit(self.__sangvisFerrisImgContainer.get(self.object_to_put_down["id"]), linpg.controller.mouse.pos)

        # 显示即将被编辑的数据
        if self.data_to_edit is not None:
            pass
        # 未保存离开时的警告
        self.__no_save_warning.draw(screen)
        if linpg.controller.get_event("confirm") and self.__no_save_warning.item_being_hovered != "":
            # 保存并离开
            if self.__no_save_warning.item_being_hovered == "save":
                self.save_progress()
                self.stop()
            # 取消
            elif self.__no_save_warning.item_being_hovered == "cancel":
                self.__no_save_warning.set_visible(False)
            # 不保存并离开
            elif self.__no_save_warning.item_being_hovered == "dont_save":
                self.stop()
