from .api import *
from .editor import MapEditor
from .tbs import TurnBasedBattleSystem, Optional


class Gamemode:

    # 储存闸门动画的图片素材
    __GateImgAbove: Optional[linpg.ImageSurface] = None
    __GateImgBelow: Optional[linpg.ImageSurface] = None
    VIDEO_BACKGROUND = None

    # 画出加载ui
    @classmethod
    def draw_loading_chapter_ui(cls, screen: linpg.ImageSurface, percent: int) -> None:
        if cls.__GateImgAbove is not None:
            cls.__GateImgAbove.set_size(screen.get_width() + 4, screen.get_height() / 1.7)
            cls.__GateImgAbove.set_bottom(cls.__GateImgAbove.get_height() / 100 * percent)
            cls.__GateImgAbove.draw(screen)
            cls.__GateImgBelow.set_size(screen.get_width() + 4, screen.get_height() / 2.05)
            cls.__GateImgBelow.set_top(screen.get_height() - cls.__GateImgBelow.get_height() / 100 * percent)
            cls.__GateImgBelow.draw(screen)
        else:
            cls.__GateImgAbove = linpg.DynamicImage(
                linpg.images.crop_bounding(linpg.load.img(r"Assets/image/UI/LoadingImgAbove.png")), -2, 0
            )
            cls.__GateImgBelow = linpg.DynamicImage(
                linpg.images.crop_bounding(linpg.load.img(r"Assets/image/UI/LoadingImgBelow.png")), -2, 0
            )
        linpg.display.flip()

    # 对话系统
    @classmethod
    def dialog(
        cls, screen: linpg.ImageSurface, chapterType: Optional[str], chapterId: int, part: str, projectName: Optional[str] = None
    ) -> None:
        # 开始加载-闸门关闭的效果
        for i in range(101):
            cls.draw_loading_chapter_ui(screen, i)
        cls.VIDEO_BACKGROUND.stop()
        # 卸载音乐
        linpg.media.unload()
        # 初始化对话系统模块
        DIALOG: object = linpg.DialogSystem()
        if chapterType is not None:
            DIALOG.new(chapterType, chapterId, part, projectName)
        else:
            DIALOG.load("Save/save.yaml")
        # 加载完成-闸门开启的效果
        for i in range(100, -1, -1):
            DIALOG.display_background_image(screen)
            cls.draw_loading_chapter_ui(screen, i)
        # DIALOG.auto_save = True
        # 主循环
        while DIALOG.is_playing():
            DIALOG.draw(screen)
            ALPHA_BUILD_WARNING.draw(screen)
            linpg.display.flip()

    # 对话编辑器
    @classmethod
    def dialogEditor(
        cls, screen: linpg.ImageSurface, chapterType: Optional[str], chapterId: int, part: str, projectName: Optional[str] = None
    ) -> None:
        cls.VIDEO_BACKGROUND.stop()
        # 卸载音乐
        linpg.media.unload()
        # 改变标题
        linpg.display.set_caption(
            "{0} ({1})".format(linpg.lang.get_text("General", "game_title"), linpg.lang.get_text("General", "dialog_editor"))
        )
        if RPC is not None:
            RPC.update(
                details=linpg.lang.get_text("DiscordStatus", "now_playing"),
                state=linpg.lang.get_text("General", "dialog_editor"),
                large_image=LARGE_IMAGE,
            )
        # 加载对话
        DIALOG: object = linpg.DialogEditor()
        DIALOG.load(chapterType, chapterId, part, projectName)
        # 主循环
        while DIALOG.is_playing():
            DIALOG.draw(screen)
            ALPHA_BUILD_WARNING.draw(screen)
            linpg.display.flip()
        # 改变标题回主菜单的样式
        linpg.display.set_caption(linpg.lang.get_text("General", "game_title"))
        if RPC is not None:
            RPC.update(state=linpg.lang.get_text("DiscordStatus", "staying_at_main_menu"), large_image=LARGE_IMAGE)

    # 战斗系统
    @classmethod
    def battle(
        cls, screen: linpg.ImageSurface, chapterType: Optional[str], chapterId: int, projectName: Optional[str] = None
    ) -> None:
        cls.VIDEO_BACKGROUND.stop()
        # 卸载音乐
        linpg.media.unload()
        BATTLE: object = TurnBasedBattleSystem()
        if chapterType is not None:
            BATTLE.new(screen, chapterType, chapterId, projectName)
        else:
            BATTLE.load(screen)
        # 战斗系统主要loop
        while BATTLE.is_playing():
            BATTLE.draw(screen)
            ALPHA_BUILD_WARNING.draw(screen)
            linpg.display.flip()
        # 暂停声效 - 尤其是环境声
        linpg.media.unload()

    # 地图编辑器
    @classmethod
    def mapEditor(
        cls, screen: linpg.ImageSurface, chapterType: Optional[str], chapterId: int, projectName: Optional[str] = None
    ) -> None:
        cls.VIDEO_BACKGROUND.stop()
        # 卸载音乐
        linpg.media.unload()
        MAP_EDITOR = MapEditor()
        MAP_EDITOR.load(screen, chapterType, chapterId, projectName)
        # 改变标题
        linpg.display.set_caption(
            "{0} ({1})".format(linpg.lang.get_text("General", "game_title"), linpg.lang.get_text("General", "map_editor"))
        )
        if RPC is not None:
            RPC.update(
                details=linpg.lang.get_text("DiscordStatus", "now_playing"),
                state=linpg.lang.get_text("General", "map_editor"),
                large_image=LARGE_IMAGE,
            )
        # 战斗系统主要loop
        while MAP_EDITOR.is_playing():
            MAP_EDITOR.draw(screen)
            ALPHA_BUILD_WARNING.draw(screen)
            linpg.display.flip()
        # 改变标题回主菜单的样式
        linpg.display.set_caption(linpg.lang.get_text("General", "game_title"))
        if RPC is not None:
            RPC.update(state=linpg.lang.get_text("DiscordStatus", "staying_at_main_menu"), large_image=LARGE_IMAGE)


# 控制台
class Console(linpg.Console):
    def _check_command(self, conditions: list) -> None:
        if conditions[0] == "load":
            if conditions[1] == "dialog":
                if len(conditions) < 5:
                    Gamemode.dialog(linpg.display.screen_window, conditions[2], conditions[3], conditions[4], conditions[5])
                else:
                    self._txt_output.append("Missing critical parameter(s).")
            elif conditions[1] == "battle":
                if len(conditions) < 4:
                    Gamemode.battle(linpg.display.screen_window, conditions[2], conditions[3], conditions[4])
                else:
                    self._txt_output.append("Missing critical parameter(s).")
            else:
                self._txt_output.append("Error, do not know what to load.")
        else:
            super()._check_command(conditions)


console: Console = Console(linpg.display.get_width() * 0.1, linpg.display.get_height() * 0.8)
