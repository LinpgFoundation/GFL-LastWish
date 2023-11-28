from shutil import copyfile

from .components import *

# 设置引擎的标准文字大小
linpg.font.set_global_font("medium", linpg.display.get_width() // 40)


# 主菜单系统
class MainMenu(linpg.AbstractSystem):
    def __init__(self, screen: linpg.ImageSurface):
        # 初始化系统模块
        super().__init__()
        """生成加载页面"""
        font_size: int = screen.get_width() // 64
        self.__loading_screen: Optional[linpg.ImageSurface] = linpg.surfaces.new(
            screen.get_size()
        )
        self.__loading_screen.fill(linpg.colors.BLACK)
        # 渲染健康游戏忠告
        HealthyGamingAdvice: list[linpg.ImageSurface] = (
            [
                linpg.font.render(text_t, "white", font_size)
                for text_t in linpg.lang.get_texts("HealthyGamingAdvice")
            ]
            if linpg.lang.has_key("HealthyGamingAdvice")
            else []
        )
        index: int = 0
        for _item in HealthyGamingAdvice:
            self.__loading_screen.blit(
                _item,
                (
                    screen.get_width() - screen.get_width() / 32 - _item.get_width(),
                    screen.get_height() * 0.9 - font_size * index * 1.5,
                ),
            )
            index += 1
        # 渲染光敏性癫痫警告
        PhotosensitiveSeizureWarning: list[linpg.ImageSurface] = (
            [
                linpg.font.render(text_t, "white", font_size)
                for text_t in linpg.lang.get_texts("PhotosensitiveSeizureWarning")
            ]
            if linpg.lang.has_key("PhotosensitiveSeizureWarning")
            else []
        )
        index = 0
        for _item in PhotosensitiveSeizureWarning:
            self.__loading_screen.blit(
                _item,
                (
                    screen.get_width() // 10,
                    screen.get_height() * 0.15 + _item.get_height() * index * 1.5,
                ),
            )
            index += 1
        # 渲染载入页面需要的数据
        self.__loading_screen.blit(
            linpg.font.render(linpg.lang.get_text("presentBy"), "white", font_size),
            (font_size * 2, screen.get_height() * 0.9),
        )
        """开始加载"""
        # 载入页面 - 渐入
        for index in range(0, 2500, linpg.display.get_delta_time() * 10):
            screen.fill(linpg.colors.BLACK)
            self.__loading_screen.set_alpha(index // 10)
            screen.blit(self.__loading_screen, linpg.ORIGIN)
            linpg.display.flip()
        # 主菜单文字
        self.__main_menu_txt: dict = {}
        # 退出确认窗口
        self.__exit_confirm_menu: linpg.ConfirmMessageWindow = linpg.ConfirmMessageWindow(
            linpg.lang.get_text("Global", "tip"), ""
        )
        # 当前禁用的按钮
        self.__disabled_options: set[str] = set()
        # 加载主菜单文字
        self.__reset_menu_text(screen.get_size())
        # 数值初始化
        self.menu_type: int = 0
        self.chapter_select: list = []
        self.workshop_files: list = []
        self.workshop_files_text: list = []
        self.current_selected_workshop_project: str = ""
        # 关卡选择的封面
        self.__cover_img_surface: Optional[linpg.StaticImage] = None
        # 音效
        self.click_button_sound = linpg.sounds.load(
            r"Assets/sound/ui/main_menu_click_button.ogg",
            linpg.volume.get_effects() / 100.0,
        )
        self.hover_on_button_sound = linpg.sounds.load(
            r"Assets/sound/ui/main_menu_hover_on_button.ogg",
            linpg.volume.get_effects() / 100.0,
        )
        self.hover_sound_play_on: int = -1
        self.last_hover_sound_play_on: int = -2
        # 存档选择
        self.__select_progress_menu: linpg.SaveOrLoadSelectedProgressMenu = (
            linpg.SaveOrLoadSelectedProgressMenu()
        )
        # 初始化返回菜单判定参数
        linpg.global_variables.set("BackToMainMenu", value=False)

    # 当前在Data/workshop文件夹中可以读取的文件夹的名字（font的形式）
    def __reload_workshop_files_list(
        self, screen_size: tuple, createMode: bool = False
    ) -> None:
        self.workshop_files.clear()
        self.workshop_files_text.clear()
        # 是否需要显示“新增”选项
        if createMode is True:
            self.workshop_files.append(self.__main_menu_txt["other"]["new_project"])
        for path in glob(r"Data/workshop/*"):
            _info_config_path: str = os.path.join(path, "info.yaml")
            if not os.path.exists(_info_config_path):
                linpg.create_new_project(path, "yaml")
            info_data: dict = linpg.config.load(_info_config_path)
            self.workshop_files_text.append(os.path.basename(path))
            self.workshop_files.append(
                info_data["title"].get(
                    linpg.setting.get_language(),
                    linpg.lang.get_text("Global", "no_translation"),
                )
            )
        self.workshop_files.append(linpg.lang.get_text("Global", "back"))
        txt_location: int = screen_size[0] * 2 // 3
        txt_y: int = int(
            (
                screen_size[1]
                - len(self.workshop_files) * linpg.font.get_global_font_size("medium") * 2
            )
            / 2
        )
        for i in range(len(self.workshop_files)):
            self.workshop_files[i] = linpg.load.resize_when_hovered_text(
                self.workshop_files[i],
                linpg.colors.WHITE,
                (txt_location, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += linpg.font.get_global_font_size("medium") * 2

    # 获取章节id
    def __get_chapter_title(self, chapterType: str, chapterId: int) -> str:
        # 生成dialog文件的路径
        level_info_file_path: str = (
            os.path.join(
                "Data",
                chapterType,
                f"chapter{chapterId}_level_info.yaml",
            )
            if chapterType == "main_chapter"
            else os.path.join(
                "Data",
                chapterType,
                self.current_selected_workshop_project,
                f"chapter{chapterId}_level_info.yaml",
            )
        )
        chapter_title: str = (
            linpg.config.try_load_file_if_exists(level_info_file_path)
            .get(linpg.setting.get_language(), {})
            .get("title", linpg.lang.get_text("Global", "no_translation"))
        )
        return "{0}: {1}".format(
            linpg.lang.get_text("Battle_UI", "numChapter").format(chapterId),
            chapter_title,
        )

    # 重新加载章节选择菜单的选项
    def __reload_chapter_select_list(
        self,
        screen_size: tuple[int, int],
        chapterType: str = "main_chapter",
        createMode: bool = False,
    ) -> None:
        self.chapter_select.clear()
        # 是否需要显示“新增”选项
        if createMode:
            self.chapter_select.append(self.__main_menu_txt["other"]["new_chapter"])
        # 历遍路径下的所有章节文件
        for path in glob(
            os.path.join("Data", chapterType, "*_level_info.yaml")
            if chapterType == "main_chapter"
            else os.path.join(
                "Data",
                chapterType,
                self.current_selected_workshop_project,
                "*_level_info.yaml",
            )
        ):
            self.chapter_select.append(
                self.__get_chapter_title(
                    chapterType, linpg.ScriptCompiler.extract_info_from_path(path)[0]
                )
            )
        # 将返回按钮放到菜单列表中
        self.chapter_select.append(linpg.lang.get_text("Global", "back"))
        txt_y: int = (
            screen_size[1]
            - len(self.chapter_select) * linpg.font.get_global_font_size("medium") * 2
        ) // 2
        txt_x: int = screen_size[0] * 2 // 3
        # 将菜单列表中的文字转换成文字surface
        for i in range(len(self.chapter_select)):
            self.chapter_select[i] = linpg.load.resize_when_hovered_text(
                self.chapter_select[i],
                linpg.colors.WHITE,
                (txt_x, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += linpg.font.get_global_font_size("medium") * 2

    # 画出文字按钮
    def __draw_buttons(self, screen: linpg.ImageSurface) -> None:
        i: int = 0
        # 主菜单
        if self.menu_type == 0:
            for button in self.__main_menu_txt["menu_main"].values():
                button.draw(screen)
                if button.is_hovered():
                    self.hover_sound_play_on = i
                i += 1
        # 选择主线的章节
        elif self.menu_type == 1:
            max_right: int = 0
            for button in self.chapter_select:
                max_right = max(button.right, max_right)
            _right_limit: int = linpg.display.get_width() * 9 // 10
            if max_right > _right_limit:
                for button in self.chapter_select:
                    button.set_right(button.right - max_right + _right_limit)
            for button in self.chapter_select:
                button.draw(screen)
                if button.is_hovered():
                    self.hover_sound_play_on = i
                i += 1
        # 创意工坊选择菜单
        elif self.menu_type == 2:
            for button in self.__main_menu_txt["menu_workshop_choice"].values():
                button.draw(screen)
                if button.is_hovered():
                    self.hover_sound_play_on = i
                i += 1
        # 展示合集 （3-游玩，4-地图编辑器，5-对话编辑器）
        elif 5 >= self.menu_type >= 3:
            for button in self.workshop_files:
                button.draw(screen)
                if button.is_hovered():
                    self.hover_sound_play_on = i
                i += 1
        # 选择章节（6-游玩，7-地图编辑器，8-对话编辑器）
        elif 8 >= self.menu_type >= 6:
            for button in self.chapter_select:
                button.draw(screen)
                if button.is_hovered():
                    self.hover_sound_play_on = i
                i += 1
        # 播放按钮的音效
        if self.last_hover_sound_play_on != self.hover_sound_play_on:
            self.hover_on_button_sound.play()
            self.last_hover_sound_play_on = self.hover_sound_play_on

    # 为新的创意工坊项目创建一个模板
    def __create_new_project(self) -> None:
        # 如果创意工坊的文件夹目录不存在，则创建一个
        if not os.path.exists("Data/workshop"):
            os.makedirs("Data/workshop")
        # 生成名称
        fileDefaultName = "example"
        avoidDuplicateId = 1
        fileName = fileDefaultName
        # 循环确保名称不重复
        while os.path.exists(os.path.join("Data", "workshop", fileName)):
            fileName = f"{fileDefaultName} ({avoidDuplicateId})"
            avoidDuplicateId += 1
        # 创建项目模板
        linpg.create_new_project(os.path.join("Data", "workshop", fileName), "yaml")

    # 创建新的对话文和地图文件
    def __create_new_chapter(self) -> None:
        chapterId: int = (
            len(
                glob(
                    os.path.join(
                        "Data",
                        "workshop",
                        self.current_selected_workshop_project,
                        f"*_dialogs_{linpg.setting.get_language()}.yaml",
                    )
                )
            )
            + 1
        )
        # 复制关卡数据默认模板
        copyfile(
            r"Data/template/chapter_level_info_example.yaml",
            os.path.join(
                "Data",
                "workshop",
                self.current_selected_workshop_project,
                f"chapter{chapterId}_level_info.yaml",
            ),
        )
        # 复制视觉小说数据默认模板
        copyfile(
            r"Data/template/chapter_dialogs_example.yaml",
            os.path.join(
                "Data",
                "workshop",
                self.current_selected_workshop_project,
                f"chapter{chapterId}_dialogs_{linpg.setting.get_language()}.yaml",
            ),
        )
        # 复制地图数据默认模板
        copyfile(
            r"Data/template/chapter_map_example.yaml",
            os.path.join(
                "Data",
                "workshop",
                self.current_selected_workshop_project,
                f"chapter{chapterId}_map.yaml",
            ),
        )

    # 循环播放
    def __loop_scenes(self, screen: linpg.ImageSurface) -> None:
        while linpg.global_variables.exists_not_none("currentMode"):
            if linpg.global_variables.get_str("currentMode") == "battle":
                GameMode.battle(
                    screen,
                    linpg.global_variables.try_get_str("chapterType"),
                    linpg.global_variables.get_int("chapterId"),
                    linpg.global_variables.try_get_str("projectName"),
                )
            else:
                _section: Optional[str] = linpg.global_variables.try_get_str("section")
                GameMode.dialog(
                    screen,
                    linpg.global_variables.try_get_str("chapterType"),
                    linpg.global_variables.get_int("chapterId"),
                    _section if _section is not None else "",
                    linpg.global_variables.try_get_str("projectName"),
                )
        self.__reset_menu()

    # 重置背景
    def __restart_background(self) -> None:
        GameMode.VIDEO_BACKGROUND.restart()
        self.updated_volume()

    # 更新主菜单的部分元素
    def __reset_menu(self) -> None:
        self.__restart_background()
        # 是否可以继续游戏了（save文件是否被创建）
        if linpg.saves.any_progress_exists() is True:
            if "0_continue" in self.__disabled_options:
                self.__main_menu_txt["menu_main"][
                    "0_continue"
                ] = linpg.load.resize_when_hovered_text(
                    linpg.lang.get_text("MainMenu", "menu_main", "0_continue"),
                    linpg.colors.WHITE,
                    self.__main_menu_txt["menu_main"]["0_continue"].get_pos(),
                    linpg.font.get_global_font_size("medium"),
                )
                self.__disabled_options.remove("0_continue")
        elif "0_continue" not in self.__disabled_options:
            self.__main_menu_txt["menu_main"][
                "0_continue"
            ] = linpg.load.resize_when_hovered_text(
                linpg.lang.get_text("MainMenu", "menu_main", "0_continue"),
                linpg.colors.GRAY,
                self.__main_menu_txt["menu_main"]["0_continue"].get_pos(),
                linpg.font.get_global_font_size("medium"),
            )
            self.__disabled_options.add("0_continue")
        # 是否创意工坊启用
        if (
            "3_workshop" in self.__disabled_options
            and linpg.PersistentVariables.try_get_bool("enable_workshop") is True
        ):
            self.__main_menu_txt["menu_main"][
                "3_workshop"
            ] = linpg.load.resize_when_hovered_text(
                linpg.lang.get_text("MainMenu", "menu_main", "3_workshop"),
                linpg.colors.GRAY,
                self.__main_menu_txt["menu_main"]["3_workshop"].get_pos(),
                linpg.font.get_global_font_size("medium"),
            )
            self.__disabled_options.remove("3_workshop")

    # 重新加载主菜单文字
    def __reset_menu_text(self, screen_size: tuple) -> None:
        self.__main_menu_txt = linpg.lang.get_texts("MainMenu")
        # 默认不可用的菜单选项
        self.__disabled_options = set(("0_continue", "2_dlc", "4_collection"))
        # 默认不禁用3_workshop
        if linpg.db.get_bool("DisableWorkshopByDefault"):
            self.__disabled_options.add("3_workshop")
        # 是否启用继续游戏按钮
        if linpg.saves.any_progress_exists() is True:
            self.__disabled_options.remove("0_continue")
        # 是否启用创意工坊按钮
        if (
            linpg.PersistentVariables.try_get_bool("enable_workshop") is True
            and "3_workshop" in self.__disabled_options
        ):
            self.__disabled_options.remove("3_workshop")
        # 加载主菜单页面的文字设置
        txt_location = screen_size[0] * 2 // 3
        font_size = linpg.font.get_global_font_size("medium") * 2
        txt_y = (screen_size[1] - len(self.__main_menu_txt["menu_main"]) * font_size) / 2
        for key, txt in self.__main_menu_txt["menu_main"].items():
            color_of_text = (
                linpg.colors.WHITE
                if key not in self.__disabled_options
                else linpg.colors.GRAY
            )
            self.__main_menu_txt["menu_main"][key] = linpg.load.resize_when_hovered_text(
                txt,
                color_of_text,
                (txt_location, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += font_size
        # 加载创意工坊选择页面的文字
        self.__main_menu_txt["menu_workshop_choice"]["map_editor"] = linpg.lang.get_text(
            "General", "map_editor"
        )
        self.__main_menu_txt["menu_workshop_choice"][
            "dialog_editor"
        ] = linpg.lang.get_text("General", "dialog_editor")
        self.__main_menu_txt["menu_workshop_choice"]["back"] = linpg.lang.get_text(
            "Global", "back"
        )
        txt_y = (
            screen_size[1] - len(self.__main_menu_txt["menu_workshop_choice"]) * font_size
        ) / 2
        for key, txt in self.__main_menu_txt["menu_workshop_choice"].items():
            self.__main_menu_txt["menu_workshop_choice"][
                key
            ] = linpg.load.resize_when_hovered_text(
                txt,
                linpg.colors.WHITE,
                (txt_location, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += font_size

    # 更新音量
    def updated_volume(self) -> None:
        self.click_button_sound.set_volume(linpg.volume.get_effects() / 100.0)
        self.hover_on_button_sound.set_volume(linpg.volume.get_effects() / 100.0)
        GameMode.VIDEO_BACKGROUND.set_volume(linpg.volume.get_background_music() / 100.0)

    # 画出背景
    def __draw_background(self, screen: linpg.ImageSurface) -> None:
        # 处理封面的更替
        cover_path: Optional[str] = None
        if self.menu_type == 1:
            for i in range(len(self.chapter_select) - 1):
                if self.chapter_select[i].is_hovered():
                    cover_path = linpg.config.load(
                        r"Data/main_chapter/info.yaml", "cover_images"
                    )[i]
                    break
        if cover_path is not None:
            if self.__cover_img_surface is None:
                self.__cover_img_surface = linpg.load.static_image(
                    cover_path, (0, 0), tag=cover_path
                )
                self.__cover_img_surface.set_alpha(10)
            elif cover_path != self.__cover_img_surface.tag:
                self.__cover_img_surface.update_image(cover_path)
                self.__cover_img_surface.tag = cover_path
            if self.__cover_img_surface is not None:
                self.__cover_img_surface.add_alpha(5)
        elif self.__cover_img_surface is not None:
            if self.__cover_img_surface.get_alpha() > 10:
                self.__cover_img_surface.subtract_alpha(5)
            else:
                self.__cover_img_surface = None
        # 背景视频
        if self.__cover_img_surface is None or self.__cover_img_surface.get_alpha() < 255:
            GameMode.VIDEO_BACKGROUND.draw(screen)
        # 封面
        if self.__cover_img_surface is not None:
            self.__cover_img_surface.set_width_with_original_image_size_locked(
                screen.get_width()
            )
            self.__cover_img_surface.set_centery(screen.get_height() // 2)
            self.__cover_img_surface.draw(screen)

    # 画出主菜单
    def draw(self, screen: linpg.ImageSurface) -> None:
        # 背景
        self.__draw_background(screen)
        # 菜单选项
        if (
            not self.__select_progress_menu.is_visible()
            and not linpg.PauseMenuModuleForGameSystem.OPTION_MENU.is_visible()
        ):
            self.__draw_buttons(screen)
        # 展示设置UI
        linpg.PauseMenuModuleForGameSystem.OPTION_MENU.draw(screen)
        # 更新音量
        if (
            linpg.PauseMenuModuleForGameSystem.OPTION_MENU.need_update.get("volume")
            is True
        ):
            self.updated_volume()
        # 更新语言
        if (
            linpg.PauseMenuModuleForGameSystem.OPTION_MENU.need_update.get("language")
            is True
            or self.language_need_update() is True
        ):
            self.update_language()
            self.__reset_menu_text(screen.get_size())
            if self.menu_type == 1:
                self.__reload_chapter_select_list(screen.get_size())
            elif self.menu_type == 6:
                self.__reload_workshop_files_list(screen.get_size(), False)
                self.__reload_chapter_select_list(screen.get_size(), "workshop")
        # 展示控制台
        global CONSOLE
        if CONSOLE is not None:
            CONSOLE.draw(screen)
        # 判断按键
        if linpg.PauseMenuModuleForGameSystem.OPTION_MENU.is_hidden():
            if linpg.controller.get_event("confirm") is True:
                self.click_button_sound.play()
                match self.menu_type:
                    # 主菜单
                    case 0:
                        # 继续游戏
                        if self.__main_menu_txt["menu_main"]["0_continue"].is_hovered():
                            self.__select_progress_menu.set_visible(True)
                            linpg.controller.set_event("confirm", False)
                        # 选择章节
                        elif self.__main_menu_txt["menu_main"][
                            "1_chooseChapter"
                        ].is_hovered():
                            # 加载菜单章节选择页面的文字
                            self.__reload_chapter_select_list(screen.get_size())
                            self.menu_type = 1
                        # dlc
                        elif self.__main_menu_txt["menu_main"]["2_dlc"].is_hovered():
                            pass
                        # 创意工坊
                        elif self.__main_menu_txt["menu_main"]["3_workshop"].is_hovered():
                            if "3_workshop" not in self.__disabled_options:
                                self.menu_type = 2
                        # 收集物
                        elif self.__main_menu_txt["menu_main"][
                            "4_collection"
                        ].is_hovered():
                            pass
                        # 设置
                        elif self.__main_menu_txt["menu_main"]["5_setting"].is_hovered():
                            linpg.PauseMenuModuleForGameSystem.OPTION_MENU.set_visible(
                                True
                            )
                        # 退出
                        elif self.__main_menu_txt["menu_main"]["7_exit"].is_hovered():
                            self.__exit_confirm_menu.update_message(
                                linpg.lang.get_text(
                                    "LeavingWithoutSavingWarning", "exit_confirm"
                                )
                            )
                            if (
                                self.__exit_confirm_menu.show()
                                == linpg.ConfirmMessageWindow.YES()
                            ):
                                GameMode.VIDEO_BACKGROUND.stop()
                                self.stop()
                    # 选择主线章节
                    case 1:
                        if self.chapter_select[-1].is_hovered():
                            self.menu_type = 0
                        else:
                            for i in range(len(self.chapter_select) - 1):
                                # 章节选择
                                if self.chapter_select[i].is_hovered():
                                    # 设置参数
                                    linpg.global_variables.set(
                                        "currentMode", value="dialog"
                                    )
                                    linpg.global_variables.set(
                                        "section", value="dialog_before_battle"
                                    )
                                    linpg.global_variables.set(
                                        "chapterType", value="main_chapter"
                                    )
                                    linpg.global_variables.set("chapterId", value=i + 1)
                                    linpg.global_variables.set("projectName", value=None)
                                    # 开始播放场景
                                    self.__loop_scenes(screen)
                                    break
                    # 选择创意工坊选项
                    case 2:
                        if self.__main_menu_txt["menu_workshop_choice"][
                            "0_play"
                        ].is_hovered():
                            self.__reload_workshop_files_list(screen.get_size(), False)
                            self.menu_type = 3
                        elif self.__main_menu_txt["menu_workshop_choice"][
                            "map_editor"
                        ].is_hovered():
                            self.__reload_workshop_files_list(screen.get_size(), True)
                            self.menu_type = 4
                        elif self.__main_menu_txt["menu_workshop_choice"][
                            "dialog_editor"
                        ].is_hovered():
                            self.__reload_workshop_files_list(screen.get_size(), True)
                            self.menu_type = 5
                        elif self.__main_menu_txt["menu_workshop_choice"][
                            "back"
                        ].is_hovered():
                            self.menu_type = 0
                    # 创意工坊-选择想要游玩的合集
                    case 3:
                        if self.workshop_files[-1].is_hovered():
                            self.menu_type = 2
                        else:
                            for i in range(len(self.workshop_files) - 1):
                                # 章节选择
                                if self.workshop_files[i].is_hovered():
                                    self.current_selected_workshop_project = (
                                        self.workshop_files_text[i]
                                    )
                                    self.__reload_chapter_select_list(
                                        screen.get_size(), "workshop"
                                    )
                                    self.menu_type = 6
                                    break
                    # 创意工坊-选择想要编辑地图的合集
                    case 4:
                        # 新建合集
                        if self.workshop_files[0].is_hovered():
                            self.__create_new_project()
                            self.__reload_workshop_files_list(screen.get_size(), True)
                        # 返回创意工坊选项菜单
                        elif self.workshop_files[-1].is_hovered():
                            self.menu_type = 2
                        else:
                            for i in range(1, len(self.workshop_files) - 1):
                                # 章节选择
                                if self.workshop_files[i].is_hovered():
                                    self.current_selected_workshop_project = (
                                        self.workshop_files_text[i - 1]
                                    )
                                    self.__reload_chapter_select_list(
                                        screen.get_size(), "workshop", True
                                    )
                                    self.menu_type = 7
                                    break
                    # 创意工坊-选择想要编辑对话的合集
                    case 5:
                        # 新建合集
                        if self.workshop_files[0].is_hovered():
                            self.__create_new_project()
                            self.__reload_workshop_files_list(screen.get_size(), True)
                        # 返回创意工坊选项菜单
                        elif self.workshop_files[-1].is_hovered():
                            self.menu_type = 2
                        else:
                            for i in range(1, len(self.workshop_files) - 1):
                                # 章节选择
                                if self.workshop_files[i].is_hovered():
                                    self.current_selected_workshop_project = (
                                        self.workshop_files_text[i - 1]
                                    )
                                    self.__reload_chapter_select_list(
                                        screen.get_size(), "workshop", True
                                    )
                                    self.menu_type = 8
                                    break
                    # 创意工坊-选择当前合集想要游玩的关卡
                    case 6:
                        if self.chapter_select[-1].is_hovered():
                            self.menu_type = 3
                        else:
                            for i in range(len(self.chapter_select) - 1):
                                # 章节选择
                                if self.chapter_select[i].is_hovered():
                                    # 设置参数
                                    linpg.global_variables.set(
                                        "currentMode", value="dialog"
                                    )
                                    linpg.global_variables.set(
                                        "section", value="dialog_before_battle"
                                    )
                                    linpg.global_variables.set(
                                        "chapterType", value="workshop"
                                    )
                                    linpg.global_variables.set("chapterId", value=i + 1)
                                    linpg.global_variables.set(
                                        "projectName",
                                        value=self.current_selected_workshop_project,
                                    )
                                    # 开始播放场景
                                    self.__loop_scenes(screen)
                                    break
                    # 创意工坊-选择当前合集想要编辑地图的关卡
                    case 7:
                        if self.chapter_select[0].is_hovered():
                            self.__create_new_chapter()
                            self.__reload_chapter_select_list(
                                screen.get_size(), "workshop", True
                            )
                        elif self.chapter_select[-1].is_hovered():
                            self.menu_type = 4
                        else:
                            for i in range(1, len(self.chapter_select) - 1):
                                # 章节选择
                                if self.chapter_select[i].is_hovered():
                                    GameMode.mapEditor(
                                        screen,
                                        "workshop",
                                        i,
                                        self.current_selected_workshop_project,
                                    )
                                    self.__restart_background()
                                    break
                    # 创意工坊-选择当前合集想要编辑对话的关卡
                    case 8:
                        if self.chapter_select[0].is_hovered():
                            self.__create_new_chapter()
                            self.__reload_chapter_select_list(
                                screen.get_size(), "workshop", True
                            )
                        elif self.chapter_select[-1].is_hovered():
                            self.menu_type = 5
                        else:
                            for i in range(1, len(self.chapter_select) - 1):
                                # 章节选择
                                if self.chapter_select[i].is_hovered():
                                    GameMode.dialogEditor(
                                        screen,
                                        "workshop",
                                        i,
                                        "dialog_before_battle",
                                        self.current_selected_workshop_project,
                                    )
                                    self.__restart_background()
                                    break
            if linpg.controller.get_event("back") is True:
                match self.menu_type:
                    # 选择主线章节 / 创意工坊选项
                    case 1 | 2:
                        self.menu_type = 0
                    # 创意工坊-选择想要游玩/编辑的合集
                    case 3 | 4 | 5:
                        self.menu_type = 2
                    # 创意工坊-选择当前合集想要游玩/编辑的关卡
                    case 6 | 7 | 8:
                        self.menu_type -= 3

        # 存档选择系统
        if self.__select_progress_menu.is_visible():
            self.__select_progress_menu.draw(screen)
            # 读取存档
            if self.__select_progress_menu.get_selected_slot() >= 0:
                _save: linpg.Saves.Progress | None = (
                    self.__select_progress_menu.get_selected_save()
                )
                if _save is not None:
                    self.__select_progress_menu.set_visible(False)
                    # 加载最近一个存档点的数据
                    SAVE: dict = _save.data
                    # 设置参数
                    linpg.global_variables.set("currentMode", value=SAVE["type"])
                    linpg.global_variables.remove("section")
                    linpg.global_variables.remove("chapterType")
                    linpg.global_variables.set("chapterId", value=0)
                    linpg.global_variables.remove("projectName")
                    linpg.global_variables.set("saveData", value=SAVE)
                    # 开始播放场景
                    self.__loop_scenes(screen)
        if self.__loading_screen is not None:
            alpha_t: Optional[int] = self.__loading_screen.get_alpha()
            if alpha_t is None or alpha_t <= 0:
                self.__loading_screen = None
            else:
                self.__loading_screen.set_alpha(max(0, alpha_t - 2))
                screen.blit(self.__loading_screen, linpg.ORIGIN)
