import shutil
from time import time as get_current_time
from .component import console, gamemode, get_loading_screen
from .base import *

__all__ = ["MainMenu", "linpg"]

# 主菜单系统
class MainMenu(linpg.AbstractSystem):
    def __init__(self, screen: linpg.ImageSurface):
        # 初始化系统模块
        super().__init__()
        self.loading_screen: linpg.ImageSurface = get_loading_screen()
        # 载入页面 - 渐入
        for i in range(0, 250, int(2 * linpg.display.sfpsp)):
            screen.fill(linpg.color.BLACK)
            self.loading_screen.set_alpha(i)
            screen.blit(self.loading_screen, linpg.pos.ORIGIN)
            linpg.display.flip()
        # 检测继续按钮是否可用的参数
        self.continueButtonIsOn: bool = False
        # 主菜单文字
        self.main_menu_txt: dict = None
        # 退出确认窗口
        self.exit_confirm_menu: linpg.Message = None
        # 加载主菜单文字
        self.__reset_menu_text(screen.get_size())
        # 数值初始化
        self.menu_type: int = 0
        self.chapter_select: list = []
        self.workshop_files: list = []
        self.workshop_files_text: list = []
        self.current_selected_workshop_project = None
        # 关卡选择的封面
        self.__cover_img_surface = None
        # 音效
        self.click_button_sound = linpg.sound.load(
            r"Assets/sound/ui/main_menu_click_button.ogg",
            linpg.media.volume.effects / 100.0,
        )
        self.hover_on_button_sound = linpg.sound.load(
            r"Assets/sound/ui/main_menu_hover_on_button.ogg",
            linpg.media.volume.effects / 100.0,
        )
        self.hover_sound_play_on = None
        self.last_hover_sound_play_on = None
        # 加载主菜单背景
        self.__background = linpg.VedioSurface(r"Assets/movie/SquadAR.mp4", True, True, (935, 3105))
        self.__background.set_volume(linpg.media.volume.background_music / 100.0)
        # 初始化返回菜单判定参数
        linpg.global_value.set("BackToMainMenu", False)
        # 设置Discord状态
        if RPC is not None:
            RPC.update(
                state=linpg.lang.get_text("DiscordStatus", "staying_at_main_menu"),
                large_image=LARGE_IMAGE,
            )

    # 当前在Data/workshop文件夹中可以读取的文件夹的名字（font的形式）
    def __reload_workshop_files_list(self, screen_size: tuple, createMode: bool = False) -> None:
        self.workshop_files.clear()
        self.workshop_files_text.clear()
        # 是否需要显示“新增”选项
        if createMode:
            self.workshop_files.append(self.main_menu_txt["other"]["new_project"])
        for path in glob(r"Data/workshop/*"):
            try:
                info_data = linpg.config.load(os.path.join(path, "info.yaml"))
            except Exception:
                info_data = linpg.config.load(r"Data/info_example.yaml")
                info_data["default_lang"] = linpg.setting.language
                linpg.config.save(os.path.join(path, "info.yaml"), info_data)
            self.workshop_files_text.append(os.path.basename(path))
            self.workshop_files.append(info_data["title"][linpg.setting.language])
        self.workshop_files.append(linpg.lang.get_text("Global", "back"))
        txt_location: int = int(screen_size[0] * 2 / 3)
        txt_y: int = int((screen_size[1] - len(self.workshop_files) * linpg.font.get_global_font_size("medium") * 2) / 2)
        for i in range(len(self.workshop_files)):
            self.workshop_files[i] = linpg.load_dynamic_text(
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
                "chapter{0}_dialogs_{1}.yaml".format(chapterId, linpg.setting.language),
            )
            if chapterType == "main_chapter"
            else os.path.join(
                "Data",
                chapterType,
                self.current_selected_workshop_project,
                "chapter{0}_dialogs_{1}.yaml".format(chapterId, linpg.setting.language),
            )
        )
        chapter_title: str
        if os.path.exists(dialog_file_path):
            dialog_data = linpg.config.load(dialog_file_path)
            # 如果dialog文件中有title，则读取
            chapter_title = (
                dialog_data["title"] if "title" in dialog_data else linpg.lang.get_text("Global", "no_translation")
            )
        else:
            chapter_title = linpg.lang.get_text("Global", "no_translation")
        return "{0}: {1}".format(
            linpg.lang.get_text("Battle_UI", "numChapter").format(linpg.lang.get_num_in_local_text(chapterId)),
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
            self.chapter_select.append(self.__get_chapter_title(chapterType, self.__find_chapter_id(path)))
        # 将返回按钮放到菜单列表中
        self.chapter_select.append(linpg.lang.get_text("Global", "back"))
        txt_y: int = int((screen_size[1] - len(self.chapter_select) * linpg.font.get_global_font_size("medium") * 2) / 2)
        txt_x: int = int(screen_size[0] * 2 / 3)
        # 将菜单列表中的文字转换成文字surface
        for i in range(len(self.chapter_select)):
            self.chapter_select[i] = linpg.load_dynamic_text(
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
                if linpg.is_hover(button):
                    self.hover_sound_play_on = i
                i += 1
        # 选择主线的章节
        elif self.menu_type == 1:
            for button in self.chapter_select:
                button.draw(screen)
                if linpg.is_hover(button):
                    self.hover_sound_play_on = i
                i += 1
        # 创意工坊选择菜单
        elif self.menu_type == 2:
            for button in self.main_menu_txt["menu_workshop_choice"].values():
                button.draw(screen)
                if linpg.is_hover(button):
                    self.hover_sound_play_on = i
                i += 1
        # 展示合集 （3-游玩，4-地图编辑器，5-对话编辑器）
        elif 5 >= self.menu_type >= 3:
            for button in self.workshop_files:
                button.draw(screen)
                if linpg.is_hover(button):
                    self.hover_sound_play_on = i
                i += 1
        # 选择章节（6-游玩，7-地图编辑器，8-对话编辑器）
        elif 8 >= self.menu_type >= 6:
            for button in self.chapter_select:
                button.draw(screen)
                if linpg.is_hover(button):
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
        # 创建文件夹
        os.makedirs(os.path.join("Data", "workshop", fileName))
        # 储存数据
        info_data: dict = linpg.config.load(r"Data/info_example.yaml")
        info_data["default_lang"] = linpg.setting.language
        linpg.config.save(os.path.join("Data", "workshop", fileName, "info.yaml"), info_data)

    # 创建新的对话文和地图文件
    def __create_new_chapter(self) -> None:
        chapterId: int = (
            len(
                glob(
                    os.path.join(
                        "Data",
                        "workshop",
                        self.current_selected_workshop_project,
                        "*_dialogs_{}.yaml".format(linpg.setting.language),
                    )
                )
            )
            + 1
        )
        # 复制视觉小说系统默认模板
        shutil.copyfile(
            "Data/chapter_dialogs_example.yaml",
            os.path.join(
                "Data",
                "workshop",
                self.current_selected_workshop_project,
                "chapter{0}_dialogs_{1}.yaml".format(chapterId, linpg.setting.language),
            ),
        )
        # 复制战斗系统默认模板
        shutil.copyfile(
            "Data/chapter_map_example.yaml",
            os.path.join(
                "Data",
                "workshop",
                self.current_selected_workshop_project,
                "chapter{}_map.yaml".format(chapterId),
            ),
        )

    # 根据路径判定章节的Id
    def __find_chapter_id(self, path: str) -> int:
        fileName = os.path.basename(path)
        if fileName[0:7] == "chapter":
            return int(fileName[7 : fileName.index("_")])
        else:
            raise Exception("Error: Cannot find the id of chapter because the file is not properly named!")

    # 加载章节
    def __load_scene(self, chapterType: str, chapterId: int, screen: linpg.ImageSurface) -> None:
        if RPC is not None:
            RPC.update(
                details=linpg.lang.get_text("General", "main_chapter")
                if chapterType == "main_chapter"
                else linpg.lang.get_text("General", "workshop"),
                state=self.__get_chapter_title(chapterType, chapterId),
                large_image=LARGE_IMAGE,
                start=get_current_time(),
            )
        self.__background.stop()
        projectName = None if chapterType == "main_chapter" else self.current_selected_workshop_project
        gamemode.dialog(screen, chapterType, chapterId, "dialog_before_battle", projectName)
        if not linpg.global_value.get("BackToMainMenu"):
            gamemode.battle(screen, chapterType, chapterId, projectName)
            if not linpg.global_value.get("BackToMainMenu"):
                gamemode.dialog(screen, chapterType, chapterId, "dialog_after_battle", projectName)
                linpg.global_value.if_get_set("BackToMainMenu", True, False)
            else:
                linpg.global_value.set("BackToMainMenu", False)
        else:
            linpg.global_value.set("BackToMainMenu", False)
        self.__reset_menu()
        if RPC is not None:
            RPC.update(
                state=linpg.lang.get_text("DiscordStatus", "staying_at_main_menu"),
                large_image=LARGE_IMAGE,
            )

    # 继续章节
    def __continue_scene(self, screen: linpg.ImageSurface) -> None:
        self.__background.stop()
        SAVE: dict = linpg.config.load(r"Save/save.yaml")
        if RPC is not None:
            RPC.update(
                details=linpg.lang.get_text("General", "main_chapter")
                if SAVE["chapter_type"] == "main_chapter"
                else linpg.lang.get_text("General", "workshop"),
                state=self.__get_chapter_title(SAVE["chapter_type"], SAVE["chapter_id"]),
                large_image=LARGE_IMAGE,
                start=get_current_time(),
            )
        startPoint = SAVE["type"]
        if startPoint == "dialog_before_battle":
            gamemode.dialog(screen, None, None, None)
            if not linpg.global_value.get("BackToMainMenu"):
                gamemode.battle(
                    screen,
                    SAVE["chapter_type"],
                    SAVE["chapter_id"],
                    SAVE["project_name"],
                )
                if not linpg.global_value.get("BackToMainMenu"):
                    gamemode.dialog(
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
            gamemode.battle(screen, None, None)
            if not linpg.global_value.get("BackToMainMenu"):
                gamemode.dialog(
                    screen,
                    SAVE["chapter_type"],
                    SAVE["chapter_id"],
                    "dialog_after_battle",
                    SAVE["project_name"],
                )
            else:
                linpg.global_value.set("BackToMainMenu", False)
        elif startPoint == "dialog_after_battle":
            gamemode.dialog(screen, None, None, None)
            linpg.global_value.if_get_set("BackToMainMenu", True, False)
        self.__reset_menu()
        if RPC is not None:
            RPC.update(
                state=linpg.lang.get_text("DiscordStatus", "staying_at_main_menu"),
                large_image=LARGE_IMAGE,
            )

    # 重置背景
    def __restart_background(self) -> None:
        self.__background.restart()
        self.updated_volume()

    # 更新主菜单的部分元素
    def __reset_menu(self) -> None:
        self.__restart_background()
        # 是否可以继续游戏了（save文件是否被创建）
        if os.path.exists("Save/save.yaml") and not self.continueButtonIsOn:
            self.main_menu_txt["menu_main"]["0_continue"] = linpg.load_dynamic_text(
                linpg.lang.get_text("MainMenu", "menu_main")["0_continue"],
                linpg.color.WHITE,
                self.main_menu_txt["menu_main"]["0_continue"].get_pos(),
                linpg.font.get_global_font_size("medium"),
            )
            self.continueButtonIsOn = True
        elif not os.path.exists("Save/save.yaml") and self.continueButtonIsOn is True:
            self.main_menu_txt["menu_main"]["0_continue"] = linpg.load_dynamic_text(
                linpg.lang.get_text("MainMenu", "menu_main")["0_continue"],
                linpg.color.GRAY,
                self.main_menu_txt["menu_main"]["0_continue"].get_pos(),
                linpg.font.get_global_font_size("medium"),
            )
            self.continueButtonIsOn = False

    # 重新加载主菜单文字
    def __reset_menu_text(self, screen_size: tuple) -> None:
        self.main_menu_txt = linpg.lang.get_text("MainMenu")
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
            color_of_text = linpg.color.WHITE if key not in disabled_option else linpg.color.GRAY
            self.main_menu_txt["menu_main"][key] = linpg.load_dynamic_text(
                txt,
                color_of_text,
                (txt_location, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += font_size
        # 加载创意工坊选择页面的文字
        self.main_menu_txt["menu_workshop_choice"]["map_editor"] = linpg.lang.get_text("General", "map_editor")
        self.main_menu_txt["menu_workshop_choice"]["dialog_editor"] = linpg.lang.get_text("General", "dialog_editor")
        self.main_menu_txt["menu_workshop_choice"]["back"] = linpg.lang.get_text("Global", "back")
        txt_y = (screen_size[1] - len(self.main_menu_txt["menu_workshop_choice"]) * font_size) / 2
        for key, txt in self.main_menu_txt["menu_workshop_choice"].items():
            self.main_menu_txt["menu_workshop_choice"][key] = linpg.load_dynamic_text(
                txt,
                linpg.color.WHITE,
                (txt_location, txt_y),
                linpg.font.get_global_font_size("medium"),
            )
            txt_y += font_size
        # 加载退出确认消息框
        self.exit_confirm_menu = linpg.Message(
            self.main_menu_txt["other"]["tip"],
            self.main_menu_txt["other"]["exit_confirm"],
            (
                self.main_menu_txt["other"]["confirm"],
                self.main_menu_txt["other"]["deny"],
            ),
            True,
            return_button=1,
            escape_button=1,
        )

    # 更新语言
    def updated_language(self, screen: linpg.ImageSurface) -> None:
        super().updated_language()
        self.__reset_menu_text(screen.get_size())
        if self.menu_type == 1:
            self.__reload_chapter_select_list(screen.get_size())
        elif self.menu_type == 6:
            self.__reload_workshop_files_list(screen.get_size(), False)
            self.__reload_chapter_select_list(screen.get_size(), "workshop")

    # 更新音量
    def updated_volume(self) -> None:
        self.click_button_sound.set_volume(linpg.media.volume.effects / 100.0)
        self.hover_on_button_sound.set_volume(linpg.media.volume.effects / 100.0)
        self.__background.set_volume(linpg.media.volume.background_music / 100.0)

    # 画出背景
    def __draw_background(self, screen: linpg.ImageSurface) -> None:
        # 处理封面的更替
        cover_path: str = None
        if self.menu_type == 1:
            for i in range(len(self.chapter_select) - 1):
                if linpg.is_hover(self.chapter_select[i]):
                    cover_path = linpg.config.load(r"Data/main_chapter/info.yaml", "cover_image")[i]
                    break
        if cover_path is not None:
            if self.__cover_img_surface is None:
                self.__cover_img_surface = linpg.load.static_image(cover_path, (0, 0), screen.get_size(), cover_path)
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
            self.__background.draw(screen)
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
        if linpg.option_menu.need_update["language"] is True or self.language_need_update() is True:
            self.updated_language(screen)
        # 展示控制台
        console.draw(screen)
        # 判断按键
        if linpg.controller.get_event("confirm") is True and linpg.option_menu.hidden is True:
            self.click_button_sound.play()
            # 主菜单
            if self.menu_type == 0:
                # 继续游戏
                if linpg.is_hover(self.main_menu_txt["menu_main"]["0_continue"]) and os.path.exists("Save/save.yaml"):
                    self.__continue_scene(screen)
                # 选择章节
                elif linpg.is_hover(self.main_menu_txt["menu_main"]["1_chooseChapter"]):
                    # 加载菜单章节选择页面的文字
                    self.__reload_chapter_select_list(screen.get_size())
                    self.menu_type = 1
                # dlc
                elif linpg.is_hover(self.main_menu_txt["menu_main"]["2_dlc"]):
                    pass
                # 创意工坊
                elif linpg.is_hover(self.main_menu_txt["menu_main"]["3_workshop"]):
                    self.menu_type = 2
                # 收集物
                elif linpg.is_hover(self.main_menu_txt["menu_main"]["4_collection"]):
                    pass
                # 设置
                elif linpg.is_hover(self.main_menu_txt["menu_main"]["5_setting"]):
                    linpg.option_menu.hidden = False
                # 制作组
                elif linpg.is_hover(self.main_menu_txt["menu_main"]["6_developer_team"]):
                    pass
                # 退出
                elif linpg.is_hover(self.main_menu_txt["menu_main"]["7_exit"]) and self.exit_confirm_menu.show() == 0:
                    self.__background.stop()
                    self.stop()
                    if RPC is not None:
                        RPC.close()
            # 选择主线章节
            elif self.menu_type == 1:
                if linpg.is_hover(self.chapter_select[-1]):
                    self.menu_type = 0
                else:
                    for i in range(len(self.chapter_select) - 1):
                        # 章节选择
                        if linpg.is_hover(self.chapter_select[i]):
                            self.__load_scene("main_chapter", i + 1, screen)
                            break
            # 选择创意工坊选项
            elif self.menu_type == 2:
                if linpg.is_hover(self.main_menu_txt["menu_workshop_choice"]["0_play"]):
                    self.__reload_workshop_files_list(screen.get_size(), False)
                    self.menu_type = 3
                elif linpg.is_hover(self.main_menu_txt["menu_workshop_choice"]["map_editor"]):
                    self.__reload_workshop_files_list(screen.get_size(), True)
                    self.menu_type = 4
                elif linpg.is_hover(self.main_menu_txt["menu_workshop_choice"]["dialog_editor"]):
                    self.__reload_workshop_files_list(screen.get_size(), True)
                    self.menu_type = 5
                elif linpg.is_hover(self.main_menu_txt["menu_workshop_choice"]["back"]):
                    self.menu_type = 0
            # 创意工坊-选择想要游玩的合集
            elif self.menu_type == 3:
                if linpg.is_hover(self.workshop_files[-1]):
                    self.menu_type = 2
                else:
                    for i in range(len(self.workshop_files) - 1):
                        # 章节选择
                        if linpg.is_hover(self.workshop_files[i]):
                            self.current_selected_workshop_project = self.workshop_files_text[i]
                            self.__reload_chapter_select_list(screen.get_size(), "workshop")
                            self.menu_type = 6
                            break
            # 创意工坊-选择想要编辑地图的合集
            elif self.menu_type == 4:
                # 新建合集
                if linpg.is_hover(self.workshop_files[0]):
                    self.__create_new_project()
                    self.__reload_workshop_files_list(screen.get_size(), True)
                # 返回创意工坊选项菜单
                elif linpg.is_hover(self.workshop_files[-1]):
                    self.menu_type = 2
                else:
                    for i in range(1, len(self.workshop_files) - 1):
                        # 章节选择
                        if linpg.is_hover(self.workshop_files[i]):
                            self.current_selected_workshop_project = self.workshop_files_text[i - 1]
                            self.__reload_chapter_select_list(screen.get_size(), "workshop", True)
                            self.menu_type = 7
                            break
            # 创意工坊-选择想要编辑对话的合集
            elif self.menu_type == 5:
                # 新建合集
                if linpg.is_hover(self.workshop_files[0]):
                    self.__create_new_project()
                    self.__reload_workshop_files_list(screen.get_size(), True)
                # 返回创意工坊选项菜单
                elif linpg.is_hover(self.workshop_files[-1]):
                    self.menu_type = 2
                else:
                    for i in range(1, len(self.workshop_files) - 1):
                        # 章节选择
                        if linpg.is_hover(self.workshop_files[i]):
                            self.current_selected_workshop_project = self.workshop_files_text[i - 1]
                            self.__reload_chapter_select_list(screen.get_size(), "workshop", True)
                            self.menu_type = 8
                            break
            # 创意工坊-选择当前合集想要游玩的关卡
            elif self.menu_type == 6:
                if linpg.is_hover(self.chapter_select[-1]):
                    self.menu_type = 3
                else:
                    for i in range(len(self.chapter_select) - 1):
                        # 章节选择
                        if linpg.is_hover(self.chapter_select[i]):
                            self.__load_scene("workshop", i + 1, screen)
                            break
            # 创意工坊-选择当前合集想要编辑地图的关卡
            elif self.menu_type == 7:
                if linpg.is_hover(self.chapter_select[0]):
                    self.__create_new_chapter()
                    self.__reload_chapter_select_list(screen.get_size(), "workshop", True)
                elif linpg.is_hover(self.chapter_select[-1]):
                    self.menu_type = 4
                else:
                    for i in range(1, len(self.chapter_select) - 1):
                        # 章节选择
                        if linpg.is_hover(self.chapter_select[i]):
                            self.__background.stop()
                            gamemode.mapEditor(
                                screen,
                                "workshop",
                                i,
                                self.current_selected_workshop_project,
                            )
                            self.__restart_background()
                            break
            # 创意工坊-选择当前合集想要编辑对话的关卡
            elif self.menu_type == 8:
                if linpg.is_hover(self.chapter_select[0]):
                    self.__create_new_chapter()
                    self.__reload_chapter_select_list(screen.get_size(), "workshop", True)
                elif linpg.is_hover(self.chapter_select[-1]):
                    self.menu_type = 5
                else:
                    for i in range(1, len(self.chapter_select) - 1):
                        # 章节选择
                        if linpg.is_hover(self.chapter_select[i]):
                            self.__background.stop()
                            gamemode.dialogEditor(
                                screen,
                                "workshop",
                                i,
                                "dialog_before_battle",
                                self.current_selected_workshop_project,
                            )
                            self.__restart_background()
                            break
        ALPHA_BUILD_WARNING.draw(screen)
        if self.loading_screen is not None:
            alpha_t: int = self.loading_screen.get_alpha()
            if alpha_t <= 0:
                self.loading_screen = None
            else:
                self.loading_screen.set_alpha(max(0, alpha_t - int(5 * linpg.display.sfpsp)))
                screen.blit(self.loading_screen, linpg.pos.ORIGIN)
