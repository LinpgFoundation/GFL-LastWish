from .ui import linpg, os, glob


# 地图编辑器系统
class MapEditor(linpg.AbstractBattleSystem):
    # 返回需要保存数据
    def _get_data_need_to_save(self) -> dict:
        return self.originalData

    # 加载角色的数据
    def __load_characters_data(self, mapFileData: dict) -> None:
        # 生成进程
        self._initial_characters_loader(mapFileData["character"], mapFileData["sangvisFerri"], "dev")
        # 加载角色信息
        self._start_characters_loader()
        # 类似多线程的join，待完善
        while self._is_characters_loader_alive():
            pass

    # 初始化
    def load(
        self,
        screen: linpg.ImageSurface,
        chapterType: str,
        chapterId: int,
        projectName: str = None,
    ) -> None:
        self._initialize(chapterType, chapterId, projectName)
        self.folder_for_save_file, self.name_for_save_file = os.path.split(self.get_map_file_location())
        self.decorations_setting = linpg.config.load("Data/decorations.yaml", "decorations")
        # 载入地图数据
        mapFileData: dict = linpg.config.load(self.get_map_file_location())
        # 初始化角色信息
        self.__load_characters_data(mapFileData)
        # 初始化地图
        self.MAP = mapFileData["map"]
        if self.MAP is None or len(self.MAP) == 0:
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
        self._create_map(mapFileData)
        del mapFileData
        """加载右侧的界面"""
        # 加载容器图片
        container_width: int = int(screen.get_width() * 0.2)
        container_height: int = int(screen.get_height())
        button_width: int = int(screen.get_width() * 0.04)
        button_height: int = int(screen.get_height() * 0.2)
        panding: int = int(screen.get_height() * 0.01)
        font_size: int = int(button_width / 3)
        self.__button_select_block = linpg.load.button_with_text_in_center(
            "Assets/image/UI/menu.png",
            linpg.lang.get_text("MapEditor", "block"),
            "black",
            font_size,
            (0, screen.get_width() * 0.03),
            100,
        )
        self.__button_select_decoration = linpg.load.button_with_text_in_center(
            "Assets/image/UI/menu.png",
            linpg.lang.get_text("MapEditor", "decoration"),
            "black",
            font_size,
            (0, screen.get_width() * 0.03),
            100,
        )
        self.__button_select_block.set_left(
            int(
                (
                    container_width
                    - self.__button_select_block.get_width()
                    - self.__button_select_decoration.get_width()
                    - panding
                )
                / 2
            )
        )
        self.__button_select_decoration.set_left(self.__button_select_block.right + panding)
        self.__UIContainerRight = linpg.load.dynamic_image(
            r"Assets/image/UI/container.png",
            (0, 0),
            (container_width, container_height),
        )
        self.__UIContainerButtonRight = linpg.load.movable_image(
            r"Assets/image/UI/container_button.png",
            (
                int(screen.get_width() - button_width),
                int((screen.get_height() - button_height) / 2),
            ),
            (
                int(screen.get_width() - button_width - container_width),
                int((screen.get_height() - button_height) / 2),
            ),
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
        for imgPath in glob(r"Assets/image/environment/block/*.png"):
            self.__envImgContainer.set(
                os.path.basename(imgPath).replace(".png", ""),
                linpg.load.img(imgPath, (self.MAP.block_width / 3, None)),
            )
        self.__envImgContainer.set_item_per_line(4)
        self.__envImgContainer.set_scroll_bar_pos("right")
        self.__envImgContainer.hidden = False
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
        for imgPath in glob(r"Assets/image/environment/decoration/*.png"):
            self.__decorationsImgContainer.set(
                os.path.basename(imgPath).replace(".png", ""),
                linpg.load.img(imgPath, (self.MAP.block_width / 3, None)),
            )
        self.__decorationsImgContainer.set_item_per_line(4)
        self.__decorationsImgContainer.set_scroll_bar_pos("right")
        self.__decorationsImgContainer.hidden = True
        self.__decorationsImgContainer.distance_between_item = panding
        """加载下方的界面"""
        container_width = int(screen.get_width() * 0.8)
        container_height = int(screen.get_height() * 0.3)
        button_width = int(screen.get_width() * 0.14)
        button_height = int(screen.get_height() * 0.05)
        panding = int(screen.get_height() * 0.01)
        font_size = int(button_height / 2)
        self.__button_select_character = linpg.load.button_with_text_in_center(
            "Assets/image/UI/menu.png",
            linpg.lang.get_text("General", "griffin_Kryuger"),
            "black",
            font_size,
            (0, 0),
            100,
        )
        self.__button_select_sangvisFerri = linpg.load.button_with_text_in_center(
            "Assets/image/UI/menu.png",
            linpg.lang.get_text("General", "sangvis_ferri"),
            "black",
            font_size,
            (self.__button_select_character.get_width(), 0),
            100,
        )
        self.__UIContainerBottom = linpg.load.dynamic_image(
            r"Assets/image/UI/container.png",
            (0, 0),
            (container_width, container_height),
        )
        self.__UIContainerButtonBottom = linpg.load.movable_image(
            r"Assets/image/UI/container_button.png",
            (
                int((container_width - button_width) / 2),
                int(screen.get_height() - button_height),
            ),
            (
                int((container_width - button_width) / 2),
                int(screen.get_height() - button_height - container_height),
            ),
            (0, int(container_height / 10)),
            (button_width, button_height),
        )
        # 加载所有友方的角色的图片文件
        self.__charactersImgContainer: object = linpg.SurfaceContainerWithScrollbar(
            None,
            container_width * 0.025,
            container_height * 0.2,
            container_width * 0.95,
            container_height * 0.7,
            "horizontal",
        )
        for imgPath in glob(r"Assets/image/character/*"):
            img_name = os.path.basename(imgPath)
            self.__charactersImgContainer.set(
                img_name,
                linpg.transform.crop_bounding(
                    linpg.load.img(
                        os.path.join(imgPath, "wait", "{}_wait_0.png".format(img_name)),
                        (None, container_height * 1.5),
                    )
                ),
            )
        self.__charactersImgContainer.set_scroll_bar_pos("bottom")
        self.__charactersImgContainer.hidden = False
        self.__charactersImgContainer.distance_between_item = panding
        # 加载所有敌对角色的图片文件
        self.__sangvisFerrisImgContainer: object = linpg.SurfaceContainerWithScrollbar(
            None,
            container_width * 0.025,
            container_height * 0.2,
            container_width * 0.95,
            container_height * 0.7,
            "horizontal",
        )
        for imgPath in glob(r"Assets/image/sangvisFerri/*"):
            img_name = os.path.basename(imgPath)
            self.__sangvisFerrisImgContainer.set(
                img_name,
                linpg.transform.crop_bounding(
                    linpg.load.img(
                        os.path.join(imgPath, "wait", "{}_wait_0.png".format(img_name)),
                        (None, container_height * 1.5),
                    )
                ),
            )
        self.__sangvisFerrisImgContainer.set_scroll_bar_pos("bottom")
        self.__sangvisFerrisImgContainer.hidden = True
        self.__sangvisFerrisImgContainer.distance_between_item = panding
        # 绿色方块/方块标准
        self.greenBlock = linpg.load.img("Assets/image/UI/range/green.png", (self.MAP.block_width * 0.8, None))
        self.greenBlock.set_alpha(150)
        self.redBlock = linpg.load.img("Assets/image/UI/range/red.png", (self.MAP.block_width * 0.8, None))
        self.redBlock.set_alpha(150)
        self.deleteMode: bool = False
        self.object_to_put_down = None
        # UI按钮
        self.UIButton = {}
        UI_x = self.MAP.block_width * 0.5
        UI_y = int(screen.get_height() * 0.02)
        font_size = int(self.MAP.block_width * 0.2)
        self.UIButton["save"] = linpg.load.button_with_text_in_center(
            "Assets/image/UI/menu.png",
            linpg.lang.get_text("Global", "save"),
            "black",
            font_size,
            (UI_x, UI_y),
            100,
        )
        UI_x += self.UIButton["save"].get_width() + font_size
        self.UIButton["back"] = linpg.load.button_with_text_in_center(
            "Assets/image/UI/menu.png",
            linpg.lang.get_text("Global", "back"),
            "black",
            font_size,
            (UI_x, UI_y),
            100,
        )
        UI_x += self.UIButton["back"].get_width() + font_size
        self.UIButton["delete"] = linpg.load.button_with_text_in_center(
            "Assets/image/UI/menu.png",
            linpg.lang.get_text("Global", "delete"),
            "black",
            font_size,
            (UI_x, UI_y),
            100,
        )
        UI_x += self.UIButton["delete"].get_width() + font_size
        self.UIButton["reload"] = linpg.load.button_with_text_in_center(
            "Assets/image/UI/menu.png",
            linpg.lang.get_text("Global", "reload_file"),
            "black",
            font_size,
            (UI_x, UI_y),
            100,
        )
        # 其他函数
        self.UI_local_x = 0
        self.UI_local_y = 0
        # 未保存离开时的警告
        self.__no_save_warning = linpg.ui.generate_deault("leave_without_saving_warning")
        # 用于储存即将发下的物品的具体参数
        self.data_to_edit = None
        # 读取地图原始文件
        self.originalData = linpg.config.load(self.get_map_file_location())

    # 将地图制作器的界面画到屏幕上
    def draw(self, screen: linpg.ImageSurface) -> None:
        block_get_click = self.MAP.calBlockInMap(linpg.controller.mouse.pos)
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
                if self.__UIContainerButtonRight.is_hover():
                    self.__UIContainerButtonRight.switch()
                    self.__UIContainerButtonRight.flip()
                elif self.__UIContainerButtonBottom.is_hover():
                    self.__UIContainerButtonBottom.switch()
                    self.__UIContainerButtonBottom.flip()
                elif self.deleteMode is True and block_get_click is not None:
                    # 查看当前位置是否有装饰物
                    decoration = self.MAP.find_decoration_on((block_get_click["x"], block_get_click["y"]))
                    # 如果发现有冲突的装饰物
                    if decoration is not None:
                        self.MAP.remove_decoration(decoration)
                    else:
                        any_chara_replace = None
                        for key, value in {
                            **self.alliances_data,
                            **self.enemies_data,
                        }.items():
                            if value.x == block_get_click["x"] and value.y == block_get_click["y"]:
                                any_chara_replace = key
                                break
                        if any_chara_replace is not None:
                            if any_chara_replace in self.alliances_data:
                                self.alliances_data.pop(any_chara_replace)
                                self.originalData["character"].pop(any_chara_replace)
                            elif any_chara_replace in self.enemies_data:
                                self.enemies_data.pop(any_chara_replace)
                                self.originalData["sangvisFerri"].pop(any_chara_replace)
                elif linpg.is_hover(self.UIButton["save"]) and self.object_to_put_down is None and not self.deleteMode:
                    self.save_progress()
                elif linpg.is_hover(self.UIButton["back"]) and self.object_to_put_down is None and not self.deleteMode:
                    if linpg.config.load(self.get_map_file_location()) == self.originalData:
                        self.stop()
                        break
                    else:
                        self.__no_save_warning.hidden = False
                elif linpg.is_hover(self.UIButton["delete"]) and self.object_to_put_down is None and not self.deleteMode:
                    self.object_to_put_down = None
                    self.data_to_edit = None
                    self.deleteMode = True
                elif linpg.is_hover(self.UIButton["reload"]) and self.object_to_put_down is None and not self.deleteMode:
                    tempLocal_x, tempLocal_y = self.MAP.get_local_pos()
                    # 读取地图数据
                    mapFileData = linpg.config.load(self.get_map_file_location())
                    # 初始化角色信息
                    self.__load_characters_data(mapFileData)
                    # 加载地图
                    self._create_map(mapFileData)
                    del mapFileData
                    self.MAP.set_local_pos(tempLocal_x, tempLocal_y)
                    # 读取地图
                    self.originalData = linpg.config.load(self.get_map_file_location())
                else:
                    if (
                        linpg.controller.get_event("confirm")
                        and block_get_click is not None
                        and self.object_to_put_down is not None
                        and not linpg.is_hover(
                            self.__UIContainerRight,
                            off_set_x=self.__UIContainerButtonRight.right,
                        )
                        and not linpg.is_hover(
                            self.__UIContainerBottom,
                            off_set_y=self.__UIContainerButtonBottom.bottom,
                        )
                    ):
                        if self.object_to_put_down["type"] == "block":
                            self.originalData["map"][block_get_click["y"]][block_get_click["x"]] = self.object_to_put_down[
                                "id"
                            ]
                            self.MAP.update_block(block_get_click, self.object_to_put_down["id"])
                        elif self.object_to_put_down["type"] == "decoration":
                            # 查看当前位置是否有装饰物
                            decoration = self.MAP.find_decoration_on((block_get_click["x"], block_get_click["y"]))
                            # 如果发现有冲突的装饰物
                            if decoration is not None:
                                self.MAP.remove_decoration(decoration)
                            decorationType = self.decorations_setting[self.object_to_put_down["id"]]
                            if decorationType not in self.originalData["decoration"]:
                                self.originalData["decoration"][decorationType] = {}
                            the_id = 0
                            while (
                                self.object_to_put_down["id"] + "_" + str(the_id)
                                in self.originalData["decoration"][decorationType]
                            ):
                                the_id += 1
                            nameTemp = self.object_to_put_down["id"] + "_" + str(the_id)
                            self.originalData["decoration"][decorationType][nameTemp] = {
                                "image": self.object_to_put_down["id"],
                                "x": block_get_click["x"],
                                "y": block_get_click["y"],
                            }
                            if decorationType == "chest":
                                self.originalData["decoration"][decorationType][nameTemp]["items"] = []
                            self.MAP.load_decorations(self.originalData["decoration"])
                        elif (
                            self.object_to_put_down["type"] == "character"
                            or self.object_to_put_down["type"] == "sangvisFerri"
                        ):
                            any_chara_replace = None
                            for key, value in {
                                **self.alliances_data,
                                **self.enemies_data,
                            }.items():
                                if value.x == block_get_click["x"] and value.y == block_get_click["y"]:
                                    any_chara_replace = key
                                    break
                            if any_chara_replace is not None:
                                if any_chara_replace in self.alliances_data:
                                    self.alliances_data.pop(any_chara_replace)
                                    self.originalData["character"].pop(any_chara_replace)
                                elif any_chara_replace in self.enemies_data:
                                    self.enemies_data.pop(any_chara_replace)
                                    self.originalData["sangvisFerri"].pop(any_chara_replace)
                            the_id = 0
                            if self.object_to_put_down["type"] == "character":
                                while self.object_to_put_down["id"] + "_" + str(the_id) in self.alliances_data:
                                    the_id += 1
                                nameTemp = self.object_to_put_down["id"] + "_" + str(the_id)
                                self.originalData["character"][nameTemp] = {
                                    "bullets_carried": 100,
                                    "type": self.object_to_put_down["id"],
                                    "x": block_get_click["x"],
                                    "y": block_get_click["y"],
                                }
                                self.alliances_data[nameTemp] = linpg.FriendlyCharacter(
                                    self.originalData["character"][nameTemp],
                                    self.DATABASE[self.originalData["character"][nameTemp]["type"]],
                                    "dev",
                                )
                            elif self.object_to_put_down["type"] == "sangvisFerri":
                                while self.object_to_put_down["id"] + "_" + str(the_id) in self.enemies_data:
                                    the_id += 1
                                nameTemp = self.object_to_put_down["id"] + "_" + str(the_id)
                                self.originalData["sangvisFerri"][nameTemp] = {
                                    "type": self.object_to_put_down["id"],
                                    "x": block_get_click["x"],
                                    "y": block_get_click["y"],
                                }
                                self.enemies_data[nameTemp] = linpg.HostileCharacter(
                                    self.originalData["sangvisFerri"][nameTemp],
                                    self.DATABASE[self.originalData["sangvisFerri"][nameTemp]["type"]],
                                    "dev",
                                )
        # 其他移动的检查
        self._check_right_click_move()
        self._check_jostick_events()

        # 画出地图
        self._display_map(screen)
        if (
            block_get_click is not None
            and not linpg.is_hover(self.__UIContainerRight, off_set_x=self.__UIContainerButtonRight.right)
            and not linpg.is_hover(
                self.__UIContainerBottom,
                off_set_y=self.__UIContainerButtonBottom.bottom,
            )
        ):
            if self.deleteMode is True:
                xTemp, yTemp = self.MAP.calPosInMap(block_get_click["x"], block_get_click["y"])
                screen.blit(self.redBlock, (xTemp + self.MAP.block_width * 0.1, yTemp))
            elif self.object_to_put_down is not None:
                xTemp, yTemp = self.MAP.calPosInMap(block_get_click["x"], block_get_click["y"])
                screen.blit(self.greenBlock, (xTemp + self.MAP.block_width * 0.1, yTemp))

        # 角色动画
        for key in self.alliances_data:
            self.alliances_data[key].draw(screen, self.MAP)
            if (
                self.object_to_put_down is None
                and linpg.controller.get_event("confirm")
                and self.alliances_data[key].x == int(linpg.controller.mouse.x / self.greenBlock.get_width())
                and self.alliances_data[key].y == int(linpg.controller.mouse.y / self.greenBlock.get_height())
            ):
                self.data_to_edit = self.alliances_data[key]
        for key in self.enemies_data:
            self.enemies_data[key].draw(screen, self.MAP)
            if (
                self.object_to_put_down is None
                and linpg.controller.get_event("confirm")
                and self.enemies_data[key].x == int(linpg.controller.mouse.x / self.greenBlock.get_width())
                and self.enemies_data[key].y == int(linpg.controller.mouse.y / self.greenBlock.get_height())
            ):
                self.data_to_edit = self.enemies_data[key]

        # 展示设施
        self._display_decoration(screen)

        # 画出右侧容器的UI
        self.__UIContainerButtonRight.draw(screen)
        if self.__UIContainerButtonRight.right < screen.get_width():
            self.__UIContainerRight.display(screen, (self.__UIContainerButtonRight.right, 0))
            self.__envImgContainer.display(screen, (self.__UIContainerButtonRight.right, 0))
            self.__decorationsImgContainer.display(screen, (self.__UIContainerButtonRight.right, 0))
            if (
                linpg.is_hover(
                    self.__button_select_block,
                    off_set_x=self.__UIContainerButtonRight.right,
                )
                and linpg.controller.get_event("confirm")
            ):
                self.__envImgContainer.hidden = False
                self.__decorationsImgContainer.hidden = True
            if (
                linpg.is_hover(
                    self.__button_select_decoration,
                    off_set_x=self.__UIContainerButtonRight.right,
                )
                and linpg.controller.get_event("confirm")
            ):
                self.__envImgContainer.hidden = True
                self.__decorationsImgContainer.hidden = False
            self.__button_select_block.display(screen, (self.__UIContainerButtonRight.right, 0))
            self.__button_select_decoration.display(screen, (self.__UIContainerButtonRight.right, 0))
            if linpg.controller.get_event("confirm"):
                if not self.__envImgContainer.hidden and self.__envImgContainer.item_being_hovered is not None:
                    self.object_to_put_down = {
                        "type": "block",
                        "id": self.__envImgContainer.item_being_hovered,
                    }
                elif (
                    not self.__decorationsImgContainer.hidden
                    and self.__decorationsImgContainer.item_being_hovered is not None
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
            if (
                linpg.is_hover(
                    self.__button_select_character,
                    off_set_y=self.__UIContainerButtonBottom.bottom,
                )
                and linpg.controller.get_event("confirm")
            ):
                self.__charactersImgContainer.hidden = False
                self.__sangvisFerrisImgContainer.hidden = True
            if (
                linpg.is_hover(
                    self.__button_select_sangvisFerri,
                    off_set_y=self.__UIContainerButtonBottom.bottom,
                )
                and linpg.controller.get_event("confirm")
            ):
                self.__charactersImgContainer.hidden = True
                self.__sangvisFerrisImgContainer.hidden = False
            self.__button_select_character.display(screen, (0, self.__UIContainerButtonBottom.bottom))
            self.__button_select_sangvisFerri.display(screen, (0, self.__UIContainerButtonBottom.bottom))
            if linpg.controller.get_event("confirm"):
                if not self.__charactersImgContainer.hidden and self.__charactersImgContainer.item_being_hovered is not None:
                    self.object_to_put_down = {
                        "type": "character",
                        "id": self.__charactersImgContainer.item_being_hovered,
                    }
                elif (
                    not self.__sangvisFerrisImgContainer.hidden
                    and self.__sangvisFerrisImgContainer.item_being_hovered is not None
                ):
                    self.object_to_put_down = {
                        "type": "sangvisFerri",
                        "id": self.__sangvisFerrisImgContainer.item_being_hovered,
                    }

        # 画出上方其他按钮
        for key in self.UIButton:
            linpg.is_hover(self.UIButton[key])
            self.UIButton[key].draw(screen)

        # 跟随鼠标显示即将被放下的物品
        if self.object_to_put_down is not None:
            if self.object_to_put_down["type"] == "block":
                screen.blit(
                    self.__envImgContainer.get(self.object_to_put_down["id"]),
                    linpg.controller.mouse.pos,
                )
            elif self.object_to_put_down["type"] == "decoration":
                screen.blit(
                    self.__decorationsImgContainer.get(self.object_to_put_down["id"]),
                    linpg.controller.mouse.pos,
                )
            elif self.object_to_put_down["type"] == "character":
                screen.blit(
                    self.__charactersImgContainer.get(self.object_to_put_down["id"]),
                    linpg.controller.mouse.pos,
                )
            elif self.object_to_put_down["type"] == "sangvisFerri":
                screen.blit(
                    self.__sangvisFerrisImgContainer.get(self.object_to_put_down["id"]),
                    linpg.controller.mouse.pos,
                )

        # 显示即将被编辑的数据
        if self.data_to_edit is not None:
            screen.blits(
                (
                    (
                        linpg.font.render(
                            "action points: " + str(self.data_to_edit.max_action_point),
                            "black",
                            15,
                        ),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8),
                    ),
                    (
                        linpg.font.render(
                            "attack range: " + str(self.data_to_edit.attack_range),
                            "black",
                            15,
                        ),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20),
                    ),
                    (
                        linpg.font.render(
                            "current bullets: " + str(self.data_to_edit.current_bullets),
                            "black",
                            15,
                        ),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20 * 2),
                    ),
                    (
                        linpg.font.render(
                            "magazine capacity: " + str(self.data_to_edit.magazine_capacity),
                            "black",
                            15,
                        ),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20 * 3),
                    ),
                    (
                        linpg.font.render("max hp: " + str(self.data_to_edit.max_hp), "black", 15),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20 * 4),
                    ),
                    (
                        linpg.font.render(
                            "effective range: " + str(self.data_to_edit.effective_range),
                            "black",
                            15,
                        ),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20 * 5),
                    ),
                    (
                        linpg.font.render(
                            "max damage: " + str(self.data_to_edit.max_damage),
                            "black",
                            15,
                        ),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20 * 6),
                    ),
                    (
                        linpg.font.render(
                            "min damage: " + str(self.data_to_edit.min_damage),
                            "black",
                            15,
                        ),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20 * 7),
                    ),
                    (
                        linpg.font.render("x: " + str(self.data_to_edit.x), "black", 15),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20 * 8),
                    ),
                    (
                        linpg.font.render("y: " + str(self.data_to_edit.y), "black", 15),
                        (screen.get_width() * 0.91, screen.get_height() * 0.8 + 20 * 9),
                    ),
                )
            )
        # 未保存离开时的警告
        self.__no_save_warning.draw(screen)
        if linpg.controller.get_event("confirm") and self.__no_save_warning.item_being_hovered != "":
            # 保存并离开
            if self.__no_save_warning.item_being_hovered == "save":
                self.save_progress()
                self.stop()
            # 取消
            elif self.__no_save_warning.item_being_hovered == "cancel":
                self.__no_save_warning.hidden = True
            # 不保存并离开
            elif self.__no_save_warning.item_being_hovered == "dont_save":
                self.stop()
