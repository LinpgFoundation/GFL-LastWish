from shutil import copyfile
from time import time as get_current_time

from .components import GameMode, console, Optional
from .api import *


# 主菜单系统
class MainMenu(linpg.AbstractSystem):
    def __init__(self, screen: linpg.ImageSurface):
        # 初始化系统模块
        super().__init__()
        """生成加载页面"""
        index: int = 0
        font_size: int = int(screen.get_width() / 64)
        self.__loading_screen: Optional[linpg.ImageSurface] = linpg.surfaces.new(
            screen.get_size()
        )
        self.__loading_screen.fill(linpg.color.BLACK)
        # 渲染健康游戏忠告
        HealthyGamingAdvice: list[linpg.ImageSurface] = (
            [
                linpg.font.render(text_t, "white", font_size, with_bounding=True)
                for text_t in linpg.lang.get_texts("HealthyGamingAdvice")
            ]
            if linpg.lang.has_key("HealthyGamingAdvice")
            else []
        )
        index = 0
        for _item in HealthyGamingAdvice:
            self.__loading_screen.blit(
                _item,
                (
                    screen.get_width() - screen.get_width() / 32 - _item.get_width(),
                    screen.get_height() * 0.9 - font_size * index * 1.5,
                ),
            )
            index += 1
        # 渲染获取光敏性癫痫警告
        PhotosensitiveSeizureWarning: list[linpg.ImageSurface] = (
            [
                linpg.font.render(text_t, "white", font_size, with_bounding=True)
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
                    screen.get_width() * 0.1,
                    screen.get_height() * 0.1 + _item.get_height() * index * 1.5,
                ),
            )
            index += 1
        # 渲染载入页面需要的数据
        self.__loading_screen.blits(
            (
                (
                    linpg.font.render(linpg.lang.get_text("title1"), "white", font_size),
                    (font_size * 2, screen.get_height() * 0.9),
                ),
                (
                    linpg.font.render(linpg.lang.get_text("title2"), "white", font_size),
                    (
                        font_size * 2,
                        screen.get_height() * 0.9 - screen.get_width() / 32,
                    ),
                ),
            )
        )
        """开始加载"""
        # 载入页面 - 渐入
        for index in range(0, 250, int(2 * linpg.display.get_delta_time())):
            screen.fill(linpg.color.BLACK)
            self.__loading_screen.set_alpha(index)
            screen.blit(self.__loading_screen, linpg.ORIGIN)
            linpg.display.flip()
        # 检测继续按钮是否可用的参数
        self.continueButtonIsOn: bool = False
        # 主菜单文字
        self.main_menu_txt: dict = {}
        # 退出确认窗口
        self.__exit_confirm_menu: linpg.ConfirmMessageWindow = linpg.ConfirmMessageWindow(
            linpg.lang.get_text("Global", "tip"), ""
        )
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
        self.click_button_sound = linpg.sound.load(
            r"Assets/sound/ui/main_menu_click_button.ogg",
            linpg.volume.get_effects() / 100.0,
        )
        self.hover_on_button_sound = linpg.sound.load(
            r"Assets/sound/ui/main_menu_hover_on_button.ogg",
            linpg.volume.get_effects() / 100.0,
        )
        self.hover_sound_play_on: int = -1
        self.last_hover_sound_play_on: int = -2
        # 初始化返回菜单判定参数
        linpg.global_value.set("BackToMainMenu", False)

    # 当前在Data/workshop文件夹中可以读取的文件夹的名字（font的形式）
    def __reload_workshop_files_list(
        self, screen_size: tuple, createMode: bool = False
    ) -> None:
        self.workshop_files.clear()
        self.workshop_files_text.clear()
        # 是否需要显示“新增”选项
        if createMode is True:
            self.workshop_files.append(self.main_menu_txt["other"]["new_project"])
        for path in glob(r"Data/workshop/*"):
            try:
                info_data = linpg.config.load(os.path.join(path, "info.yaml"))
            except Exception:
                linpg.create_new_project(path, "yaml")
            self.workshop_files_text.append(os.path.basename(path))
            self.workshop_files.append(info_data["title"][linpg.setting.get_language()])
        self.workshop_files.append(linpg.lang.get_text("Global", "back"))
        txt_location: int = int(screen_size[0] * 2 / 3)
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
                linpg.color.WHITE,
                (txt_location, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += linpg.font.get_global_font_size("medium") * 2

    # 获取章节id
    def __get_chapter_title(self, chapterType: str, chapterId: int) -> str:
        # 生成dialog文件的路径
        dialog_file_path: str = (
            os.path.join(
                "Data",
                chapterType,
                "chapter{0}_dialogs_{1}.yaml".format(
                    chapterId, linpg.setting.get_language()
                ),
            )
            if chapterType == "main_chapter"
            else os.path.join(
                "Data",
                chapterType,
                self.current_selected_workshop_project,
                "chapter{0}_dialogs_{1}.yaml".format(
                    chapterId, linpg.setting.get_language()
                ),
            )
        )
        chapter_title: str
        if os.path.exists(dialog_file_path):
            dialog_data = linpg.config.load(dialog_file_path)
            # 如果dialog文件中有title，则读取
            chapter_title = (
                dialog_data["title"]
                if "title" in dialog_data
                else linpg.lang.get_text("Global", "no_translation")
            )
        else:
            chapter_title = linpg.lang.get_text("Global", "no_translation")
        return "{0}: {1}".format(
            linpg.lang.get_text("Battle_UI", "numChapter").format(
                linpg.lang.get_num_in_local_text(chapterId)
            ),
            chapter_title,
        )

    # 重新加载章节选择菜单的选项
    def __reload_chapter_select_list(
        self,
        screen_size: tuple,
        chapterType: str = "main_chapter",
        createMode: bool = False,
    ) -> None:
        self.chapter_select.clear()
        # 是否需要显示“新增”选项
        if createMode:
            self.chapter_select.append(self.main_menu_txt["other"]["new_chapter"])
        # 历遍路径下的所有章节文件
        for path in glob(
            os.path.join("Data", chapterType, "*_map.yaml")
            if chapterType == "main_chapter"
            else os.path.join(
                "Data",
                chapterType,
                self.current_selected_workshop_project,
                "*_map.yaml",
            )
        ):
            self.chapter_select.append(
                self.__get_chapter_title(
                    chapterType, linpg.ScriptConverter.extract_info_from_path(path)[0]
                )
            )
        # 将返回按钮放到菜单列表中
        self.chapter_select.append(linpg.lang.get_text("Global", "back"))
        txt_y: int = int(
            (
                screen_size[1]
                - len(self.chapter_select) * linpg.font.get_global_font_size("medium") * 2
            )
            / 2
        )
        txt_x: int = int(screen_size[0] * 2 / 3)
        # 将菜单列表中的文字转换成文字surface
        for i in range(len(self.chapter_select)):
            self.chapter_select[i] = linpg.load.resize_when_hovered_text(
                self.chapter_select[i],
                linpg.color.WHITE,
                (txt_x, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += linpg.font.get_global_font_size("medium") * 2

    # 画出文字按钮
    def __draw_buttons(self, screen: linpg.ImageSurface) -> None:
        i: int = 0
        # 主菜单
        if self.menu_type == 0:
            for button in self.main_menu_txt["menu_main"].values():
                button.draw(screen)
                if button.is_hovered():
                    self.hover_sound_play_on = i
                i += 1
        # 选择主线的章节
        elif self.menu_type == 1:
            for button in self.chapter_select:
                button.draw(screen)
                if button.is_hovered():
                    self.hover_sound_play_on = i
                i += 1
        # 创意工坊选择菜单
        elif self.menu_type == 2:
            for button in self.main_menu_txt["menu_workshop_choice"].values():
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
            fileName = "{0} ({1})".format(fileDefaultName, avoidDuplicateId)
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
                        "*_dialogs_{}.yaml".format(linpg.setting.get_language()),
                    )
                )
            )
            + 1
        )
        # 复制视觉小说系统默认模板
        copyfile(
            "Data/chapter_dialogs_example.yaml",
            os.path.join(
                "Data",
                "workshop",
                self.current_selected_workshop_project,
                "chapter{0}_dialogs_{1}.yaml".format(
                    chapterId, linpg.setting.get_language()
                ),
            ),
        )
        # 复制战斗系统默认模板
        copyfile(
            "Data/chapter_map_example.yaml",
            os.path.join(
                "Data",
                "workshop",
                self.current_selected_workshop_project,
                "chapter{}_map.yaml".format(chapterId),
            ),
        )

    # 加载章节
    def __load_scene(
        self, chapterType: str, chapterId: int, screen: linpg.ImageSurface
    ) -> None:
        projectName = (
            None
            if chapterType == "main_chapter"
            else self.current_selected_workshop_project
        )
        GameMode.dialog(
            screen, chapterType, chapterId, "dialog_before_battle", projectName
        )
        if not linpg.global_value.get("BackToMainMenu"):
            GameMode.battle(screen, chapterType, chapterId, projectName)
            if not linpg.global_value.get("BackToMainMenu"):
                GameMode.dialog(
                    screen, chapterType, chapterId, "dialog_after_battle", projectName
                )
                linpg.global_value.if_get_set("BackToMainMenu", True, False)
            else:
                linpg.global_value.set("BackToMainMenu", False)
        else:
            linpg.global_value.set("BackToMainMenu", False)
        self.__reset_menu()

    # 继续章节
    def __continue_scene(self, screen: linpg.ImageSurface) -> None:
        SAVE: dict = dict(linpg.config.load("Save/save.yaml"))
        startPoint = SAVE["type"]
        if startPoint == "dialog_before_battle":
            GameMode.dialog(screen, None, 0, "")
            if not linpg.global_value.get("BackToMainMenu"):
                GameMode.battle(
                    screen,
                    SAVE["chapter_type"],
                    SAVE["chapter_id"],
                    SAVE["project_name"],
                )
                if not linpg.global_value.get("BackToMainMenu"):
                    GameMode.dialog(
                        screen,
                        SAVE["chapter_type"],
                        SAVE["chapter_id"],
                        "dialog_after_battle",
                        SAVE["project_name"],
                    )
                else:
                    linpg.global_value.set("BackToMainMenu", False)
            else:
                linpg.global_value.set("BackToMainMenu", False)
        elif startPoint == "battle":
            GameMode.battle(screen, None, 0)
            if not linpg.global_value.get("BackToMainMenu"):
                GameMode.dialog(
                    screen,
                    SAVE["chapter_type"],
                    SAVE["chapter_id"],
                    "dialog_after_battle",
                    SAVE["project_name"],
                )
            else:
                linpg.global_value.set("BackToMainMenu", False)
        elif startPoint == "dialog_after_battle":
            GameMode.dialog(screen, None, 0, "")
            linpg.global_value.if_get_set("BackToMainMenu", True, False)
        self.__reset_menu()

    # 重置背景
    def __restart_background(self) -> None:
        GameMode.VIDEO_BACKGROUND.restart()
        self.updated_volume()

    # 更新主菜单的部分元素
    def __reset_menu(self) -> None:
        self.__restart_background()
        # 是否可以继续游戏了（save文件是否被创建）
        if os.path.exists("Save/save.yaml") and not self.continueButtonIsOn:
            self.main_menu_txt["menu_main"][
                "0_continue"
            ] = linpg.load.resize_when_hovered_text(
                linpg.lang.get_text("MainMenu", "menu_main", "0_continue"),
                linpg.color.WHITE,
                self.main_menu_txt["menu_main"]["0_continue"].get_pos(),
                linpg.font.get_global_font_size("medium"),
            )
            self.continueButtonIsOn = True
        elif not os.path.exists("Save/save.yaml") and self.continueButtonIsOn is True:
            self.main_menu_txt["menu_main"][
                "0_continue"
            ] = linpg.load.resize_when_hovered_text(
                linpg.lang.get_text("MainMenu", "menu_main", "0_continue"),
                linpg.color.GRAY,
                self.main_menu_txt["menu_main"]["0_continue"].get_pos(),
                linpg.font.get_global_font_size("medium"),
            )
            self.continueButtonIsOn = False

    # 重新加载主菜单文字
    def __reset_menu_text(self, screen_size: tuple) -> None:
        self.main_menu_txt = linpg.lang.get_texts("MainMenu")
        # 当前不可用的菜单选项
        disabled_option = ["6_developer_team", "2_dlc", "4_collection"]
        if not os.path.exists("Save/save.yaml"):
            disabled_option.append("0_continue")
            self.continueButtonIsOn = False
        else:
            self.continueButtonIsOn = True
        # 加载主菜单页面的文字设置
        txt_location = int(screen_size[0] * 2 / 3)
        font_size = linpg.font.get_global_font_size("medium") * 2
        txt_y = (screen_size[1] - len(self.main_menu_txt["menu_main"]) * font_size) / 2
        for key, txt in self.main_menu_txt["menu_main"].items():
            color_of_text = (
                linpg.color.WHITE if key not in disabled_option else linpg.color.GRAY
            )
            self.main_menu_txt["menu_main"][key] = linpg.load.resize_when_hovered_text(
                txt,
                color_of_text,
                (txt_location, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += font_size
        # 加载创意工坊选择页面的文字
        self.main_menu_txt["menu_workshop_choice"]["map_editor"] = linpg.lang.get_text(
            "General", "map_editor"
        )
        self.main_menu_txt["menu_workshop_choice"]["dialog_editor"] = linpg.lang.get_text(
            "General", "dialog_editor"
        )
        self.main_menu_txt["menu_workshop_choice"]["back"] = linpg.lang.get_text(
            "Global", "back"
        )
        txt_y = (
            screen_size[1] - len(self.main_menu_txt["menu_workshop_choice"]) * font_size
        ) / 2
        for key, txt in self.main_menu_txt["menu_workshop_choice"].items():
            self.main_menu_txt["menu_workshop_choice"][
                key
            ] = linpg.load.resize_when_hovered_text(
                txt,
                linpg.color.WHITE,
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
                        r"Data/main_chapter/info.yaml", "cover_image"
                    )[i]
                    break
        if cover_path is not None:
            if self.__cover_img_surface is None:
                self.__cover_img_surface = linpg.load.static_image(
                    cover_path, (0, 0), screen.get_size(), cover_path
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
            self.__cover_img_surface.draw(screen)

    # 画出主菜单
    def draw(self, screen: linpg.ImageSurface) -> None:
        # 背景
        self.__draw_background(screen)
        # 菜单选项
        self.__draw_buttons(screen)
        # 展示设置UI
        linpg.option_menu.draw(screen)
        # 更新音量
        if linpg.option_menu.need_update["volume"] is True:
            self.updated_volume()
        # 更新语言
        if (
            linpg.option_menu.need_update["language"] is True
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
        console.draw(screen)
        # 判断按键
        if (
            linpg.controller.get_event("confirm") is True
            and linpg.option_menu.is_hidden()
        ):
            self.click_button_sound.play()
            # 主菜单
            if self.menu_type == 0:
                # 继续游戏
                if self.main_menu_txt["menu_main"][
                    "0_continue"
                ].is_hovered() and os.path.exists("Save/save.yaml"):
                    self.__continue_scene(screen)
                # 选择章节
                elif self.main_menu_txt["menu_main"]["1_chooseChapter"].is_hovered():
                    # 加载菜单章节选择页面的文字
                    self.__reload_chapter_select_list(screen.get_size())
                    self.menu_type = 1
                # dlc
                elif self.main_menu_txt["menu_main"]["2_dlc"].is_hovered():
                    pass
                # 创意工坊
                elif self.main_menu_txt["menu_main"]["3_workshop"].is_hovered():
                    self.menu_type = 2
                # 收集物
                elif self.main_menu_txt["menu_main"]["4_collection"].is_hovered():
                    pass
                # 设置
                elif self.main_menu_txt["menu_main"]["5_setting"].is_hovered():
                    linpg.option_menu.set_visible(True)
                # 制作组
                elif self.main_menu_txt["menu_main"]["6_developer_team"].is_hovered():
                    pass
                # 退出
                elif self.main_menu_txt["menu_main"]["7_exit"].is_hovered():
                    self.__exit_confirm_menu.update_message(
                        linpg.lang.get_text("LeavingWithoutSavingWarning", "exit_confirm")
                    )
                    if (
                        self.__exit_confirm_menu.show()
                        == linpg.ConfirmMessageWindow.YES()
                    ):
                        GameMode.VIDEO_BACKGROUND.stop()
                        self.stop()
            # 选择主线章节
            elif self.menu_type == 1:
                if self.chapter_select[-1].is_hovered():
                    self.menu_type = 0
                else:
                    for i in range(len(self.chapter_select) - 1):
                        # 章节选择
                        if self.chapter_select[i].is_hovered():
                            self.__load_scene("main_chapter", i + 1, screen)
                            break
            # 选择创意工坊选项
            elif self.menu_type == 2:
                if self.main_menu_txt["menu_workshop_choice"]["0_play"].is_hovered():
                    self.__reload_workshop_files_list(screen.get_size(), False)
                    self.menu_type = 3
                elif self.main_menu_txt["menu_workshop_choice"][
                    "map_editor"
                ].is_hovered():
                    self.__reload_workshop_files_list(screen.get_size(), True)
                    self.menu_type = 4
                elif self.main_menu_txt["menu_workshop_choice"][
                    "dialog_editor"
                ].is_hovered():
                    self.__reload_workshop_files_list(screen.get_size(), True)
                    self.menu_type = 5
                elif self.main_menu_txt["menu_workshop_choice"]["back"].is_hovered():
                    self.menu_type = 0
            # 创意工坊-选择想要游玩的合集
            elif self.menu_type == 3:
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
            elif self.menu_type == 4:
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
            elif self.menu_type == 5:
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
            elif self.menu_type == 6:
                if self.chapter_select[-1].is_hovered():
                    self.menu_type = 3
                else:
                    for i in range(len(self.chapter_select) - 1):
                        # 章节选择
                        if self.chapter_select[i].is_hovered():
                            self.__load_scene("workshop", i + 1, screen)
                            break
            # 创意工坊-选择当前合集想要编辑地图的关卡
            elif self.menu_type == 7:
                if self.chapter_select[0].is_hovered():
                    self.__create_new_chapter()
                    self.__reload_chapter_select_list(screen.get_size(), "workshop", True)
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
            elif self.menu_type == 8:
                if self.chapter_select[0].is_hovered():
                    self.__create_new_chapter()
                    self.__reload_chapter_select_list(screen.get_size(), "workshop", True)
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
        ALPHA_BUILD_WARNING.draw(screen)
        if self.__loading_screen is not None:
            alpha_t: Optional[int] = self.__loading_screen.get_alpha()
            if alpha_t is None or alpha_t <= 0:
                self.__loading_screen = None
            else:
                self.__loading_screen.set_alpha(
                    max(0, alpha_t - int(5 * linpg.display.get_delta_time()))
                )
                screen.blit(self.__loading_screen, linpg.ORIGIN)
