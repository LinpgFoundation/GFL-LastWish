from .implementations import *


# 控制台
class _Console(linpg.Console):
    def _check_command(self, conditions: list) -> None:
        if conditions[0] == "load":
            if conditions[1] == "dialog":
                if len(conditions) < 5:
                    GameMode.dialog(
                        linpg.display.get_window(),
                        conditions[2],
                        conditions[3],
                        conditions[4],
                        conditions[5],
                    )
                else:
                    self._txt_output.append("Missing critical parameter(s).")
            elif conditions[1] == "battle":
                if len(conditions) < 4:
                    GameMode.battle(
                        linpg.display.get_window(),
                        conditions[2],
                        conditions[3],
                        conditions[4],
                    )
                else:
                    self._txt_output.append("Missing critical parameter(s).")
            else:
                self._txt_output.append("Error, do not know what to load.")
        else:
            super()._check_command(conditions)


# 根据设定决定是否启用控制台
CONSOLE: Optional[_Console] = None
if linpg.setting.try_get_bool("EnableConsole") is True:
    CONSOLE = _Console(
        linpg.display.get_width() // 10, linpg.display.get_height() * 4 // 5
    )
    # if linpg.debug.get_developer_mode() is True:
    #    CONSOLE.start()
linpg.global_variables.set("CONSOLE", value=CONSOLE)


class GameMode:
    # 储存闸门动画的图片素材
    __GateImgAbove: Optional[linpg.StaticImage] = None
    __GateImgBelow: Optional[linpg.StaticImage] = None
    # 加载主菜单背景
    VIDEO_BACKGROUND: linpg.VideoSurface = linpg.VideoSurface(
        r"Assets/movie/SquadAR.mp4",
        True,
        not linpg.debug.get_developer_mode(),
        (935, 3105),
        cache_key="into",
    )
    VIDEO_BACKGROUND.set_volume(linpg.volume.get_background_music() / 100.0)

    # 画出加载ui
    @classmethod
    def draw_loading_chapter_ui(cls, screen: linpg.ImageSurface, percent: int) -> None:
        if cls.__GateImgAbove is not None and cls.__GateImgBelow is not None:
            cls.__GateImgAbove.set_size(screen.get_width() + 4, screen.get_height() / 1.7)
            cls.__GateImgAbove.set_bottom(
                cls.__GateImgAbove.get_height() * percent // 100
            )
            cls.__GateImgAbove.draw(screen)
            cls.__GateImgBelow.set_size(
                screen.get_width() + 4, screen.get_height() / 2.05
            )
            cls.__GateImgBelow.set_top(
                screen.get_height() - cls.__GateImgBelow.get_height() * percent // 100
            )
            cls.__GateImgBelow.draw(screen)
        else:
            cls.__GateImgAbove = linpg.StaticImage(
                linpg.images.crop_bounding(
                    linpg.load.img(r"Assets/image/UI/LoadingImgAbove.png")
                ),
                -2,
                0,
            )
            cls.__GateImgBelow = linpg.StaticImage(
                linpg.images.crop_bounding(
                    linpg.load.img(r"Assets/image/UI/LoadingImgBelow.png")
                ),
                -2,
                0,
            )
        linpg.display.flip()

    # 对话系统
    @classmethod
    def dialog(
        cls,
        screen: linpg.ImageSurface,
        chapterType: Optional[str],
        chapterId: int,
        part: str,
        projectName: Optional[str] = None,
    ) -> None:
        # 开始加载-闸门关闭的效果
        for i in range(101):
            cls.draw_loading_chapter_ui(screen, i)
        cls.VIDEO_BACKGROUND.stop()
        # 卸载音乐
        linpg.media.unload()
        # 初始化对话系统模块
        _DIALOG: VisualNovelPlayer = VisualNovelPlayer()
        if chapterType is not None:
            _DIALOG.new(chapterType, chapterId, part, projectName)
        else:
            _data: Optional[dict] = linpg.global_variables.try_get_dict("saveData")
            if _data is not None:
                _DIALOG.load_progress(_data)
                linpg.global_variables.remove("saveData")
            else:
                _DIALOG.load()
        # 加载完成-闸门开启的效果
        for i in range(100, -1, -1):
            _DIALOG.display_background_image(screen)
            cls.draw_loading_chapter_ui(screen, i)
        # _DIALOG.auto_save = True
        # 主循环
        while _DIALOG.is_playing():
            _DIALOG.draw(screen)
            linpg.display.flip()

    # 对话编辑器
    @classmethod
    def dialogEditor(
        cls,
        screen: linpg.ImageSurface,
        chapterType: str,
        chapterId: int,
        part: str,
        projectName: Optional[str] = None,
    ) -> None:
        cls.VIDEO_BACKGROUND.stop()
        # 卸载音乐
        linpg.media.unload()
        # 改变标题
        linpg.display.set_caption(
            "{0} ({1})".format(
                linpg.lang.get_text("General", "game_title"),
                linpg.lang.get_text("General", "dialog_editor"),
            )
        )
        # 加载对话
        _DIALOG: VisualNovelEditor = VisualNovelEditor()
        _DIALOG.new(chapterType, chapterId, part, projectName)
        # 主循环
        while _DIALOG.is_playing():
            _DIALOG.draw(screen)
            linpg.display.flip()
        # 改变标题回主菜单的样式
        linpg.display.set_caption(linpg.lang.get_text("General", "game_title"))

    # 战斗系统
    @classmethod
    def battle(
        cls,
        screen: linpg.ImageSurface,
        chapterType: Optional[str],
        chapterId: int,
        projectName: Optional[str] = None,
    ) -> None:
        cls.VIDEO_BACKGROUND.stop()
        # 卸载音乐
        linpg.media.unload()
        _BATTLE: TurnBasedBattleSystem = TurnBasedBattleSystem()
        if chapterType is not None:
            _BATTLE.new(chapterType, chapterId, projectName)
        else:
            _data: Optional[dict] = linpg.global_variables.try_get_dict("saveData")
            if _data is not None:
                _BATTLE.load_progress(_data)
                linpg.global_variables.remove("saveData")
            else:
                _BATTLE.load()
        # 战斗系统主要loop
        while _BATTLE.is_playing():
            _BATTLE.draw(screen)
            linpg.display.flip()
        # 暂停声效 - 尤其是环境声
        linpg.media.unload()

    # 地图编辑器
    @classmethod
    def mapEditor(
        cls,
        screen: linpg.ImageSurface,
        chapterType: str,
        chapterId: int,
        projectName: Optional[str] = None,
    ) -> None:
        cls.VIDEO_BACKGROUND.stop()
        # 卸载音乐
        linpg.media.unload()
        MAP_EDITOR: MapEditor = MapEditor()
        MAP_EDITOR.new(chapterType, chapterId, projectName)
        # 改变标题
        linpg.display.set_caption(
            "{0} ({1})".format(
                linpg.lang.get_text("General", "game_title"),
                linpg.lang.get_text("General", "map_editor"),
            )
        )
        # 战斗系统主要loop
        while MAP_EDITOR.is_playing():
            MAP_EDITOR.draw(screen)
            linpg.display.flip()
        # 改变标题回主菜单的样式
        linpg.display.set_caption(linpg.lang.get_text("General", "game_title"))
