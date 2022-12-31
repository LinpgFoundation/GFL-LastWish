import time
from collections import deque
from typing import Any
from enum import IntEnum, auto

from .dolls import *


# 中心展示模块1：接受两个item和item2的x和y，将item1展示在item2的中心位置,但不展示item2：
def display_in_center(
    item1: linpg.ImageSurface,
    item2: linpg.ImageSurface | linpg.GameObject2d,
    x: int,
    y: int,
    screen: linpg.ImageSurface,
    off_set_x: int = 0,
    off_set_y: int = 0,
) -> None:
    screen.blit(
        item1,
        (
            x + (item2.get_width() - item1.get_width()) / 2 + off_set_x,
            y + (item2.get_height() - item1.get_height()) / 2 + off_set_y,
        ),
    )


# 谁的回合？
class WhoseRound(IntEnum):
    player = auto()
    sangvisFerrisToPlayer = auto()
    sangvisFerris = auto()
    playerToSangvisFerris = auto()
    result_win = auto()
    result_fail = auto()


# 显示回合切换的UI
class RoundSwitch:
    def __init__(self, window_x: int, window_y: int):
        battleUiTxt: dict = linpg.lang.get_texts("Battle_UI")
        self.lineRedDown = linpg.load.img(
            r"Assets/image/UI/lineRed.png", (window_x, window_y / 50)
        )
        self.lineRedUp = linpg.images.rotate(self.lineRedDown, 180)
        self.lineGreenDown = linpg.load.img(
            r"Assets/image/UI/lineGreen.png", (window_x, window_y / 50)
        )
        self.lineGreenUp = linpg.images.rotate(self.lineGreenDown, 180)
        self.baseImg = linpg.load.img(
            r"Assets/image/UI/roundSwitchBase.png", (window_x, window_y / 5)
        )
        self.baseImg.set_alpha(0)
        self.x: int = -window_x
        self.y: int = int((window_y - self.baseImg.get_height()) / 2)
        self.y2 = self.y + self.baseImg.get_height() - self.lineRedDown.get_height()
        self.baseAlphaUp = True
        self.TxtAlphaUp = True
        self.idleTime = 60
        self.now_total_rounds_text = battleUiTxt["numRound"]
        self.now_total_rounds_surface: Optional[linpg.ImageSurface] = None
        self.your_round_txt_surface = linpg.font.render(
            battleUiTxt["yourRound"], "white", window_x / 36
        )
        self.your_round_txt_surface.set_alpha(0)
        self.enemy_round_txt_surface = linpg.font.render(
            battleUiTxt["enemyRound"], "white", window_x / 36
        )
        self.enemy_round_txt_surface.set_alpha(0)

    def draw(
        self, screen: linpg.ImageSurface, whose_round: WhoseRound, total_rounds: int
    ) -> bool:
        # 如果“第N回合”的文字surface还没有初始化，则初始化该文字
        if self.now_total_rounds_surface is None:
            self.now_total_rounds_surface = linpg.font.render(
                self.now_total_rounds_text.format(
                    linpg.lang.get_num_in_local_text(total_rounds)
                ),
                "white",
                screen.get_width() / 38,
            )
            self.now_total_rounds_surface.set_alpha(0)
        alphaTemp: Optional[int] = None
        # 如果UI底的alpha值在渐入阶段
        if self.baseAlphaUp:
            alphaTemp = self.baseImg.get_alpha()
            # 如果值还未到255（即完全显露），则继续增加，反之如果x到0了再进入淡出阶段
            if alphaTemp is None:
                self.baseImg.set_alpha(0)
            elif alphaTemp > 250 and self.x >= 0:
                self.baseAlphaUp = False
            elif alphaTemp <= 250:
                self.baseImg.set_alpha(alphaTemp + 5)
        # 如果UI底的alpha值在淡出阶段
        elif not self.baseAlphaUp:
            # 如果文字不在淡出阶段
            if self.TxtAlphaUp is True:
                alphaTemp = self.now_total_rounds_surface.get_alpha()
                # “第N回合”的文字先渐入
                if alphaTemp is None:
                    self.now_total_rounds_surface.set_alpha(0)
                elif alphaTemp < 250:
                    self.now_total_rounds_surface.set_alpha(alphaTemp + 10)
                else:
                    # 然后“谁的回合”的文字渐入
                    if whose_round is WhoseRound.playerToSangvisFerris:
                        alphaTemp = self.enemy_round_txt_surface.get_alpha()
                        if alphaTemp is None:
                            self.enemy_round_txt_surface.set_alpha(0)
                        elif alphaTemp < 250:
                            self.enemy_round_txt_surface.set_alpha(alphaTemp + 10)
                        else:
                            self.TxtAlphaUp = False
                    if whose_round is WhoseRound.sangvisFerrisToPlayer:
                        alphaTemp = self.your_round_txt_surface.get_alpha()
                        if alphaTemp is None:
                            self.your_round_txt_surface.set_alpha(0)
                        elif alphaTemp < 250:
                            self.your_round_txt_surface.set_alpha(alphaTemp + 10)
                        else:
                            self.TxtAlphaUp = False
            # 如果2个文字都渐入完了，会进入idle时间
            elif self.idleTime > 0:
                self.idleTime -= 1
            # 如果idle时间结束，则所有UI开始淡出
            else:
                alphaTemp = self.baseImg.get_alpha()
                if alphaTemp is None:
                    alphaTemp = 255
                if alphaTemp > 0:
                    alphaTemp -= 10
                    self.baseImg.set_alpha(alphaTemp)
                    self.now_total_rounds_surface.set_alpha(alphaTemp)
                    if whose_round is WhoseRound.playerToSangvisFerris:
                        self.lineRedUp.set_alpha(alphaTemp)
                        self.lineRedDown.set_alpha(alphaTemp)
                        self.enemy_round_txt_surface.set_alpha(alphaTemp)
                    elif whose_round is WhoseRound.sangvisFerrisToPlayer:
                        self.lineGreenUp.set_alpha(alphaTemp)
                        self.lineGreenDown.set_alpha(alphaTemp)
                        self.your_round_txt_surface.set_alpha(alphaTemp)
                else:
                    if whose_round is WhoseRound.playerToSangvisFerris:
                        self.lineRedUp.set_alpha(255)
                        self.lineRedDown.set_alpha(255)
                    elif whose_round is WhoseRound.sangvisFerrisToPlayer:
                        self.lineGreenUp.set_alpha(255)
                        self.lineGreenDown.set_alpha(255)
                    # 淡出完成，重置部分参数，UI播放结束
                    self.x = -screen.get_width()
                    self.baseAlphaUp = True
                    self.TxtAlphaUp = True
                    self.idleTime = 60
                    self.now_total_rounds_surface = None
                    return True
        # 横条移动
        if self.x < 0:
            self.x = min(self.x + screen.get_width() // 35, 0)
        # 展示UI
        screen.blits(
            (
                (self.baseImg, (0, self.y)),
                (
                    self.now_total_rounds_surface,
                    (
                        screen.get_width() // 2
                        - self.now_total_rounds_surface.get_width(),
                        self.y + screen.get_width() // 36,
                    ),
                ),
            )
        )
        if whose_round is WhoseRound.playerToSangvisFerris:
            screen.blits(
                (
                    (self.lineRedUp, (abs(self.x), self.y)),
                    (self.lineRedDown, (self.x, self.y2)),
                    (
                        self.enemy_round_txt_surface,
                        (screen.get_width() // 2, self.y + screen.get_width() // 18),
                    ),
                )
            )
        elif whose_round is WhoseRound.sangvisFerrisToPlayer:
            screen.blits(
                (
                    (self.lineGreenUp, (abs(self.x), self.y)),
                    (self.lineGreenDown, (self.x, self.y2)),
                    (
                        self.your_round_txt_surface,
                        (screen.get_width() // 2, self.y + screen.get_width() // 18),
                    ),
                )
            )
        # 如果UI展示还未完成，返回False
        return False


# 警告系统
class WarningMessageSystem:

    __all_warnings: deque = deque()
    __warnings_msg: dict = {}
    __font_size: int = 0

    @classmethod
    def init(cls, font_size: int = 30) -> None:
        cls.__font_size = font_size
        cls.update_language()

    # 更新语言
    @classmethod
    def update_language(cls) -> None:
        # 清空所有当前正在播放的警告讯息
        cls.__all_warnings.clear()
        # 更新语言
        cls.__warnings_msg.clear()
        cls.__warnings_msg.update(linpg.lang.get_texts("Warnings"))

    # 新增一个讯息
    @classmethod
    def add(cls, the_warning: str) -> None:
        if len(cls.__all_warnings) >= 5:
            cls.__all_warnings.pop()
        cls.__all_warnings.appendleft(
            linpg.font.render(
                cls.__warnings_msg[the_warning], "red", cls.__font_size, True
            )
        )

    # 画出
    @classmethod
    def draw(cls, screen: linpg.ImageSurface) -> None:
        for i in range(len(cls.__all_warnings)):
            try:
                img_alpha = cls.__all_warnings[i].get_alpha()
            except Exception:
                break
            if img_alpha > 0:
                screen.blit(
                    cls.__all_warnings[i],
                    (
                        (screen.get_width() - cls.__all_warnings[i].get_width()) / 2,
                        (screen.get_height() - cls.__all_warnings[i].get_height()) / 2
                        + i * cls.__all_warnings[i].get_height() * 1.2,
                    ),
                )
                cls.__all_warnings[i].set_alpha(img_alpha - 5)
            else:
                cls.__all_warnings.pop()


# 角色行动选项菜单
class SelectMenu(linpg.GameObjectsDictContainer):
    def __init__(self) -> None:
        super().__init__(None, 0, 0, 0, 0)
        self.selectButtonImg = linpg.load.img("<&ui>button.png")
        self._update(
            {
                # 攻击
                "attack": {
                    "button": None,
                    "ap": BasicEntity.AP_IS_NEEDED_TO_ATTACK,
                    "ap_text": str(BasicEntity.AP_IS_NEEDED_TO_ATTACK) + " AP",
                },
                # 移动
                "move": {
                    "button": None,
                    "ap": BasicEntity.AP_IS_NEEDED_TO_MOVE_ONE_BLOCK,
                    "ap_text": str(BasicEntity.AP_IS_NEEDED_TO_MOVE_ONE_BLOCK) + "N AP",
                },
                # 换弹
                "reload": {"button": None, "ap": 5, "ap_text": "5 AP"},
                # 技能
                "skill": {"button": None, "ap": 8, "ap_text": "8 AP"},
                # 救援
                "rescue": {"button": None, "ap": 8, "ap_text": "8 AP"},
                # 互动
                "interact": {"button": None, "ap": 2, "ap_text": "2 AP"},
            }
        )
        self.__need_update: bool = True
        self.set_visible(False)

    def update(self) -> None:
        self.__need_update = True

    # 将菜单按钮画出
    def draw(  # type: ignore[override]
        self,
        screen: linpg.ImageSurface,
        fontSize: int,
        location: dict,
        kind: str,
        friendsCanSave: list,
        thingsCanReact: list,
    ) -> None:
        self._item_being_hovered = None
        if self.is_visible():
            # 如果按钮没有初始化，则应该立刻初始化按钮
            if self.__need_update is True:
                selectButtonBase = linpg.images.smoothly_resize(
                    self.selectButtonImg, (round(fontSize * 5), round(fontSize * 2.6))
                )
                big_font_size: int = int(fontSize)
                small_font_size: int = int(fontSize * 0.75)
                selectMenuTxtDict: dict = linpg.lang.get_texts("SelectMenu")
                padding: int = int(fontSize / 10)
                for key in self.keys():
                    button_data_t = self.get(key)
                    button_data_t["button"] = selectButtonBase.copy()
                    txt_temp = linpg.font.render(
                        selectMenuTxtDict[key], "black", big_font_size
                    )
                    txt_temp2 = linpg.font.render(
                        button_data_t["ap_text"], "black", small_font_size
                    )
                    top: int = int(
                        (
                            selectButtonBase.get_height()
                            - txt_temp.get_height()
                            - txt_temp2.get_height()
                            - padding
                        )
                        / 2
                    )
                    button_data_t["button"].blit(
                        txt_temp,
                        (
                            (selectButtonBase.get_width() - txt_temp.get_width()) / 2,
                            top,
                        ),
                    )
                    button_data_t["button"].blit(
                        txt_temp2,
                        (
                            (selectButtonBase.get_width() - txt_temp2.get_width()) / 2,
                            top + padding + txt_temp.get_height(),
                        ),
                    )
                self.__need_update = False
            selectButtonBaseWidth = round(fontSize * 5)
            # 攻击按钮 - 左
            txt_tempX: int = int(location["xStart"] - selectButtonBaseWidth * 0.6)
            txt_tempY: int = int(location["yStart"])
            if linpg.is_hovering(self.get("attack")["button"], (txt_tempX, txt_tempY)):
                self._item_being_hovered = "attack"
            screen.blit(self.get("attack")["button"], (txt_tempX, txt_tempY))
            # 移动按钮 - 右
            txt_tempX = int(location["xEnd"] - selectButtonBaseWidth * 0.4)
            # txt_tempY 与攻击按钮一致
            if linpg.is_hovering(self.get("move")["button"], (txt_tempX, txt_tempY)):
                self._item_being_hovered = "move"
            screen.blit(self.get("move")["button"], (txt_tempX, txt_tempY))
            # 换弹按钮 - 下
            txt_tempX = int(location["xStart"] + selectButtonBaseWidth * 0.5)
            txt_tempY = int(location["yEnd"] - selectButtonBaseWidth * 0.25)
            if linpg.is_hovering(self.get("reload")["button"], (txt_tempX, txt_tempY)):
                self._item_being_hovered = "reload"
            screen.blit(self.get("reload")["button"], (txt_tempX, txt_tempY))
            # 技能按钮 - 上
            if kind != "HOC":
                # txt_tempX与换弹按钮一致
                txt_tempY = int(location["yStart"] - selectButtonBaseWidth * 0.7)
                if linpg.is_hovering(self.get("skill")["button"], (txt_tempX, txt_tempY)):
                    self._item_being_hovered = "skill"
                screen.blit(self.get("skill")["button"], (txt_tempX, txt_tempY))
            # 救助队友
            if len(friendsCanSave) > 0:
                txt_tempX = int(location["xStart"] - selectButtonBaseWidth * 0.6)
                txt_tempY = int(location["yStart"] - selectButtonBaseWidth * 0.7)
                if linpg.is_hovering(
                    self.get("rescue")["button"], (txt_tempX, txt_tempY)
                ):
                    self._item_being_hovered = "rescue"
                screen.blit(self.get("rescue")["button"], (txt_tempX, txt_tempY))
            # 互动
            if len(thingsCanReact) > 0:
                txt_tempX = int(location["xEnd"] - selectButtonBaseWidth * 0.4)
                txt_tempY = int(location["yStart"] - selectButtonBaseWidth * 0.7)
                if linpg.is_hovering(
                    self.get("interact")["button"], (txt_tempX, txt_tempY)
                ):
                    self._item_being_hovered = "interact"
                screen.blit(self.get("interact")["button"], (txt_tempX, txt_tempY))


# 角色信息板
class CharacterInfoBoard:
    def __init__(self) -> None:
        self.__board: Optional[linpg.ImageSurface] = None

    # 标记需要更新
    def update(self) -> None:
        self.__board = None

    # 画出信息板
    def draw(self, _surface: linpg.ImageSurface, _character: FriendlyCharacter) -> None:
        # 外间隙
        _margin: int = int(_surface.get_width() * 0.03)
        # 如果信息板还没更新，则应该先更新再画出
        if self.__board is None:
            _width: int = int(_surface.get_width() * 0.15)
            _height: int = int(_width * 0.75)
            _back_rect_margin: int = _margin // 10
            # 新建一个透明图层用于渲染
            self.__board = linpg.Surfaces.transparent(
                (
                    _width + (_back_rect_margin + 1) * 2 + 2,
                    _height + (_back_rect_margin + 1) * 2,
                )
            )
            # 新增一个矩形用于渲染主体
            _info_rect: linpg.Rectangle = linpg.Rectangle(
                _back_rect_margin, _back_rect_margin, _width, _height
            )
            # 后面棕色阴影经过的点
            _points: tuple[tuple[int, int], ...] = (
                (0, _info_rect.top + _back_rect_margin),
                (_info_rect.right - _back_rect_margin, 0),
                (
                    _info_rect.right + _back_rect_margin,
                    _info_rect.bottom - _back_rect_margin,
                ),
                (
                    _info_rect.left + _back_rect_margin,
                    _info_rect.bottom + _back_rect_margin,
                ),
            )
            linpg.Draw.polygon(self.__board, (125, 95, 0, 255), _points)
            linpg.Draw.polygon(self.__board, linpg.Colors.BLACK, _points, 2)
            # 画出背景
            _info_rect.draw_outline(self.__board, (255, 235, 200, 255), 0)
            # 画出黑色条
            _line_num: int = 10
            _line_size: int = _width // _line_num
            for i in range(_line_num - 1):
                _x: int = (i + 1) * _line_size + _info_rect.x
                linpg.Draw.line(
                    self.__board,
                    (100, 100, 100, 155),
                    (_x, _info_rect.top),
                    (_x, _info_rect.bottom - 1),
                )
            _line_num = 8
            _line_size = _height // _line_num
            for i in range(_line_num - 1):
                _y: int = (i + 1) * _line_size + _info_rect.y
                linpg.Draw.line(
                    self.__board,
                    (100, 100, 100, 155),
                    (_info_rect.left, _y),
                    (_info_rect.right - 1, _y),
                )
            # 画出黑色外壳
            _info_rect.draw_outline(self.__board, linpg.Colors.BLACK)
            # 渲染文字
            _padding: int = _width // 15
            _padding_x: int = _info_rect.x + _padding
            self.__board.blits(
                (
                    (
                        linpg.Font.render("HP: ", linpg.colors.BLACK, _height // 10),
                        (_padding_x, _info_rect.y + _width // 10),
                    ),
                    (
                        linpg.Font.render("AP: ", linpg.colors.BLACK, _height // 10),
                        (_padding_x, _info_rect.y + _width * 0.225),
                    ),
                )
            )
            # 渲染数据进度条
            _bar: linpg.SimpleRectPointsBar = linpg.SimpleRectPointsBar(
                _info_rect.x + _width // 4,
                _info_rect.y + _width // 10,
                int(_width * 0.7),
                int(_height * 0.13),
                (135, 190, 100, 255),
                linpg.Colors.GRAY,
                linpg.Colors.WHITE,
                linpg.Colors.BLACK,
            )
            _bar.set_max_point(_character.max_hp)
            _bar.set_current_point(_character.current_hp)
            _bar.draw(self.__board)
            _bar.set_top(_info_rect.y + _width * 0.225)
            _bar.set_color((235, 125, 50, 255))
            _bar.set_max_point(_character.max_action_point)
            _bar.set_current_point(_character.current_action_point)
            _bar.draw(self.__board)
            # 角色立绘
            character_image: linpg.ImageSurface = linpg.Images.smoothly_resize(
                linpg.load.img(
                    linpg.Specification.get_directory(
                        "character_icon", "{}.png".format(_character.type)
                    )
                ),
                (_width // 3, _width // 3),
            )
            character_image_dest: tuple[int, int] = (
                _info_rect.y + int(_padding * 1.5),
                _info_rect.bottom - _padding - character_image.get_height(),
            )
            linpg.Draw.rect(
                self.__board,
                (255, 235, 200, 255),
                (character_image_dest, character_image.get_size()),
            )
            self.__board.blit(character_image, character_image_dest)
            linpg.Draw.rect(
                self.__board,
                linpg.Colors.BLACK,
                (character_image_dest, character_image.get_size()),
                2,
            )
            # 子弹信息
            _current_bullets_text: linpg.ImageSurface = linpg.Font.render(
                _character.current_bullets, linpg.Colors.BLACK, _height // 5, True
            )
            self.__board.blit(
                _current_bullets_text,
                (
                    _info_rect.x
                    + _info_rect.width * 0.7
                    - _current_bullets_text.get_width(),
                    _info_rect.y + _info_rect.height * 0.5,
                ),
            )
            self.__board.blit(
                linpg.Font.render(
                    "/ " + str(_character.bullets_carried),
                    linpg.Colors.BLACK,
                    _height // 10,
                ),
                (
                    _info_rect.x + _info_rect.width * 0.7,
                    _info_rect.y + _info_rect.height * 0.7,
                ),
            )
        # 画出信息板
        _surface.blit(
            self.__board,
            (_margin, _surface.get_height() - self.__board.get_height() - _margin),
        )


# 章节标题(在加载时显示)
class LoadingTitle:

    black_bg: linpg.StaticImage = linpg.StaticImage(
        linpg.surfaces.colored(linpg.display.get_size(), linpg.colors.BLACK), 0, 0
    )
    title_chapterNum: Optional[linpg.StaticImage] = None
    title_chapterName: Optional[linpg.StaticImage] = None
    title_description: Optional[linpg.StaticImage] = None

    @classmethod
    def update(
        cls,
        numChapter_txt: str,
        chapterId: int,
        chapterTitle_txt: str,
        chapterDesc_txt: str,
    ) -> None:
        # 黑色Void帘幕
        cls.black_bg.set_size(linpg.display.get_width(), linpg.display.get_height())
        title_chapterNum = linpg.font.render(
            numChapter_txt.format(chapterId), "white", linpg.display.get_width() / 38
        )
        cls.title_chapterNum = linpg.StaticImage(
            title_chapterNum,
            (linpg.display.get_width() - title_chapterNum.get_width()) / 2,
            linpg.display.get_height() * 0.37,
        )
        title_chapterName = linpg.font.render(
            chapterTitle_txt, "white", linpg.display.get_width() / 38
        )
        cls.title_chapterName = linpg.StaticImage(
            title_chapterName,
            (linpg.display.get_width() - title_chapterName.get_width()) / 2,
            linpg.display.get_height() * 0.46,
        )
        title_description = linpg.font.render(
            chapterDesc_txt, "white", linpg.display.get_width() / 76
        )
        cls.title_description = linpg.StaticImage(
            title_description,
            (linpg.display.get_width() - title_description.get_width()) / 2,
            linpg.display.get_height() * 0.6,
        )

    @classmethod
    def draw(cls, screen: linpg.ImageSurface, alpha: int = 255) -> None:
        cls.black_bg.draw(screen)
        if cls.title_chapterNum is not None:
            cls.title_chapterNum.set_alpha(alpha)
            cls.title_chapterNum.draw(screen)
        if cls.title_chapterName is not None:
            cls.title_chapterName.set_alpha(alpha)
            cls.title_chapterName.draw(screen)
        if cls.title_description is not None:
            cls.title_description.set_alpha(alpha)
            cls.title_description.draw(screen)


class RangeSystem:

    # 区域坐标
    __areas: tuple[list[tuple[int, int]], ...] = ([], [], [], [], [])
    # 用于表示范围的方框图片
    __images: tuple[linpg.StaticImage, ...] = (
        linpg.load.static_image(r"<&ui>range_green.png"),
        linpg.load.static_image(r"<&ui>range_red.png"),
        linpg.load.static_image(r"<&ui>range_yellow.png"),
        linpg.load.static_image(r"<&ui>range_blue.png"),
        linpg.load.static_image(r"<&ui>range_orange.png"),
    )
    # 是否不要画出用于表示范围的方块
    __is_visible: bool = True
    # 目标透明度
    __target_alpha: int = 255

    # 更新尺寸
    @classmethod
    def update_size(cls, _width: int) -> None:
        for _prt in cls.__images:
            _prt.set_width_with_original_image_size_locked(_width)

    # 重置用于储存需要画出范围方块的字典
    @classmethod
    def clear(cls) -> None:
        for _prt in cls.__areas:
            _prt.clear()

    # 设置透明度
    @classmethod
    def set_alpha(cls, _value: int) -> None:
        cls.__target_alpha = _value
        for _prt in cls.__images:
            _prt.set_alpha(_value)

    # 设置目标透明度（渐变效果）
    @classmethod
    def set_target_alpha(cls, _value: int) -> None:
        cls.__target_alpha = _value

    # 通过index获取图片
    @classmethod
    def get_image(cls, index: int) -> linpg.StaticImage:
        return cls.__images[index]

    # 设置需要画出范围的坐标
    @classmethod
    def set_positions(cls, index: int, _positions: list) -> None:
        cls.__areas[index].clear()
        cls.__areas[index].extend(_positions)

    # 更新范围的坐标
    @classmethod
    def update_attack_range(cls, rangeCanAttack: list[list]) -> None:
        if len(rangeCanAttack) > 0:
            cls.set_positions(0, rangeCanAttack[0])
        else:
            cls.__areas[0].clear()
        if len(rangeCanAttack) > 1:
            cls.set_positions(3, rangeCanAttack[1])
        else:
            cls.__areas[3].clear()
        if len(rangeCanAttack) > 2:
            cls.set_positions(2, rangeCanAttack[2])
        else:
            cls.__areas[2].clear()

    # 为指定的范围新增坐标
    @classmethod
    def append_position(cls, index: int, _position: tuple[int, int]) -> None:
        cls.__areas[index].append(_position)

    # 设置是否可见
    @classmethod
    def set_visible(cls, visible: bool) -> None:
        cls.__is_visible = visible

    # 获取可见度
    @classmethod
    def get_visible(cls) -> bool:
        return cls.__is_visible

    # 渲染到屏幕上
    @classmethod
    def draw(cls, map_prt: linpg.TileMap, screen: linpg.ImageSurface) -> None:
        for prt in cls.__images:
            if prt.get_alpha() > cls.__target_alpha:
                prt.subtract_alpha(17)
            elif prt.get_alpha() < cls.__target_alpha:
                prt.add_alpha(17)
        for i in range(len(cls.__areas)):
            for _position in cls.__areas[i]:
                xTemp, yTemp = map_prt.calculate_position(_position[0], _position[1])
                cls.__images[i].set_pos(xTemp + map_prt.tile_width // 10, yTemp)
                cls.__images[i].draw(screen)


# 战斗系统数据统计struct
class BattleStatistics:
    def __init__(self) -> None:
        self.total_rounds: int = 1
        self.total_kills: int = 0
        self.starting_time: float = time.time()
        self.total_time: int = 0
        self.times_characters_down: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rounds": self.total_rounds,
            "total_kills": self.total_kills,
            "starting_time": self.starting_time,
            "total_time": self.total_time,
            "times_characters_down": self.times_characters_down,
        }

    def update(self, _data: dict[str, Any]) -> None:
        self.total_rounds = int(_data["total_rounds"])
        self.total_kills = int(_data["total_kills"])
        self.starting_time = float(_data["starting_time"])
        self.total_time = int(_data["total_time"])
        self.times_characters_down = int(_data["times_characters_down"])


# 战斗系统数据计分板
class ScoreBoard:
    # 主题颜色
    __COLOR: tuple[int, int, int, int] = (255, 192, 0, 150)
    # 黑色帘幕
    __DARK_CURTAIN: linpg.ImageSurface = linpg.surfaces.colored(
        linpg.display.get_size(), linpg.colors.BLACK
    )
    # 黑色帘幕的透明度
    __DARK_CURTAIN_ALPHA: int = 0
    # 右边黄色帘幕
    __YELLOW_RIGHT_CURTAIN: linpg.MovableStaticImage = linpg.MovableStaticImage(
        linpg.surfaces.colored(
            (linpg.display.get_width() * 3 // 7, linpg.display.get_height()), __COLOR
        ),
        linpg.display.get_width(),
        0,
        linpg.display.get_width() * 4 // 7,
        0,
        linpg.display.get_width() // 20,
        0,
    )
    __YELLOW_RIGHT_CURTAIN.set_alpha(150)
    __YELLOW_RIGHT_CURTAIN.move_toward()
    # 左边数据栏的Rectangle数据
    __INFO_BOX_RECT: linpg.Rectangle = linpg.Rectangle(
        linpg.display.get_width() * 1 // 7,
        linpg.display.get_height() // 4,
        linpg.display.get_width() * 2 // 7,
        linpg.display.get_height() // 2,
    )
    # 间距
    __PADDING: int = __INFO_BOX_RECT.height // 10
    # 大字字体大小
    __CONTENT_FONT_BIG: int = __INFO_BOX_RECT.height // 10
    # 小字字体大小
    __CONTENT_FONT_SMALL: int = __INFO_BOX_RECT.height // 15
    # 参数
    __NPC_NAME: str = "kalina_1"
    __CHAPTER_NUM: int = 0
    __TITLE: str = "Unknown Area"
    __RESULT_WIN: bool = False
    __STATISTICS: BattleStatistics = BattleStatistics()
    __RATING: str = "S"
    # 图层
    __NPC_IMAGE: Optional[linpg.StaticImage] = None
    __CHAPTER_NUM_TXT: Optional[linpg.ImageSurface] = None
    __NEXT_STEP_INSTRUCTION: Optional[linpg.ImageSurface] = None
    __TITLE_TXT: Optional[linpg.ImageSurface] = None
    __TIME_TXT: Optional[linpg.ImageSurface] = None
    __TOTAL_ROUNDS_TXT: Optional[linpg.ImageSurface] = None
    __TOTAL_KILLS_TXT: Optional[linpg.ImageSurface] = None
    __RATING_TXT: Optional[linpg.ImageSurface] = None
    __RATING_ICON: Optional[linpg.ImageSurface] = None
    # 是否已经更新
    __is_updated: bool = False

    # 更新数据
    @classmethod
    def update(
        cls,
        _npc_name: str,
        _chapter_num: int,
        _title: str,
        _result_win: bool,
        _statistics: BattleStatistics,
        _rating: str,
    ) -> None:
        # 重置部分数据
        cls.__DARK_CURTAIN_ALPHA = 0
        cls.__YELLOW_RIGHT_CURTAIN.reset_position()
        cls.__YELLOW_RIGHT_CURTAIN.move_toward()
        # 更新参数
        cls.__NPC_NAME = _npc_name
        cls.__CHAPTER_NUM = _chapter_num
        cls.__TITLE = _title
        cls.__RESULT_WIN = _result_win
        cls.__STATISTICS = _statistics
        cls.__RATING = _rating
        # 清空无用的图层，在需要时重新加载
        cls.__NPC_IMAGE = None
        cls.__CHAPTER_NUM_TXT = None
        cls.__NEXT_STEP_INSTRUCTION = None
        cls.__TITLE_TXT = None
        cls.__TIME_TXT = None
        cls.__TOTAL_ROUNDS_TXT = None
        cls.__TOTAL_KILLS_TXT = None
        cls.__RATING_TXT = None
        cls.__RATING_ICON = None
        # 切换更新的flag
        cls.__is_updated = True

    # 是否已经更新
    @classmethod
    def is_updated(cls) -> bool:
        return cls.__is_updated

    # 切换flag以提醒更新
    @classmethod
    def need_updated(cls) -> None:
        cls.__is_updated = False

    # 渲染
    @classmethod
    def draw(cls, _surface: linpg.ImageSurface) -> None:
        cls.__DARK_CURTAIN.set_alpha(cls.__DARK_CURTAIN_ALPHA)
        _surface.blit(cls.__DARK_CURTAIN, (0, 0))
        if cls.__DARK_CURTAIN_ALPHA < 150:
            cls.__DARK_CURTAIN_ALPHA += 5
        else:
            cls.__YELLOW_RIGHT_CURTAIN.draw(_surface)
            if cls.__NPC_IMAGE is None:
                cls.__NPC_IMAGE = linpg.StaticImage(
                    "Assets/image/npc/{}.png".format(cls.__NPC_NAME),
                    linpg.display.get_width() // 2,
                    0,
                    -1,
                    linpg.display.get_height(),
                )
            cls.__NPC_IMAGE.draw(_surface)
            cls.__INFO_BOX_RECT.draw_outline(_surface, (0, 0, 0, 100), 0)
            cls.__INFO_BOX_RECT.draw_outline(_surface, linpg.colors.WHITE, 5)
            if cls.__NEXT_STEP_INSTRUCTION is None:
                cls.__NEXT_STEP_INSTRUCTION = linpg.font.render(
                    linpg.lang.get_text(
                        "ScoreBoard",
                        "pressKeyContinue"
                        if cls.__RESULT_WIN is True
                        else "pressKeyRestart",
                    ),
                    linpg.colors.WHITE,
                    linpg.display.get_width() // 80,
                )
            _surface.blit(
                cls.__NEXT_STEP_INSTRUCTION,
                (
                    (
                        linpg.display.get_width() * 4 // 7
                        - cls.__NEXT_STEP_INSTRUCTION.get_width()
                    )
                    // 2,
                    cls.__INFO_BOX_RECT.bottom + cls.__PADDING,
                ),
            )
            if cls.__CHAPTER_NUM_TXT is None:
                cls.__CHAPTER_NUM_TXT = linpg.font.render(
                    linpg.lang.get_text("Battle_UI", "numChapter").format(
                        cls.__CHAPTER_NUM
                    )
                    + ":",
                    linpg.colors.WHITE,
                    cls.__CONTENT_FONT_BIG,
                )
            _surface.blit(
                cls.__CHAPTER_NUM_TXT,
                (
                    cls.__INFO_BOX_RECT.x + cls.__PADDING // 2,
                    cls.__INFO_BOX_RECT.y + cls.__PADDING // 2,
                ),
            )
            if cls.__TITLE_TXT is None:
                cls.__TITLE_TXT = linpg.font.render(
                    cls.__TITLE, linpg.colors.WHITE, cls.__CONTENT_FONT_BIG
                )
            title_text_y: int = cls.__INFO_BOX_RECT.y + int(cls.__PADDING * 2)
            title_text_shadow: tuple[int, int, int, int] = (
                cls.__INFO_BOX_RECT.x + cls.__PADDING - 2,
                title_text_y + cls.__PADDING // 2,
                cls.__TITLE_TXT.get_width() * 5 // 6,
                cls.__TITLE_TXT.get_height() * 3 // 5,
            )
            linpg.Draw.rect(_surface, cls.__COLOR, title_text_shadow)
            _surface.blit(
                cls.__TITLE_TXT, (cls.__INFO_BOX_RECT.x + cls.__PADDING, title_text_y)
            )
            if cls.__TIME_TXT is None:
                cls.__TIME_TXT = linpg.font.render(
                    linpg.lang.get_text("ScoreBoard", "total_time").format(
                        time.strftime(
                            "%H:%M", time.localtime(cls.__STATISTICS.total_time)
                        )
                    ),
                    linpg.colors.WHITE,
                    cls.__CONTENT_FONT_SMALL,
                )
            if cls.__TOTAL_ROUNDS_TXT is None:
                cls.__TOTAL_ROUNDS_TXT = linpg.font.render(
                    linpg.lang.get_text("ScoreBoard", "total_rounds").format(
                        cls.__STATISTICS.total_rounds
                    ),
                    linpg.colors.WHITE,
                    cls.__CONTENT_FONT_SMALL,
                )
            if cls.__TOTAL_KILLS_TXT is None:
                cls.__TOTAL_KILLS_TXT = linpg.font.render(
                    linpg.lang.get_text("ScoreBoard", "total_kills").format(
                        cls.__STATISTICS.total_kills
                    ),
                    linpg.colors.WHITE,
                    cls.__CONTENT_FONT_SMALL,
                )
            if cls.__RATING_TXT is None:
                cls.__RATING_TXT = linpg.font.render(
                    linpg.lang.get_text("ScoreBoard", "rank"),
                    linpg.colors.WHITE,
                    cls.__CONTENT_FONT_SMALL,
                )
            _surface.blit(
                cls.__TIME_TXT,
                (
                    cls.__INFO_BOX_RECT.x + cls.__PADDING + cls.__CONTENT_FONT_SMALL,
                    title_text_y + cls.__PADDING + cls.__CONTENT_FONT_SMALL,
                ),
            )
            _surface.blit(
                cls.__TOTAL_ROUNDS_TXT,
                (
                    cls.__INFO_BOX_RECT.x + cls.__PADDING + cls.__CONTENT_FONT_SMALL,
                    title_text_y + cls.__PADDING * 2 + cls.__CONTENT_FONT_SMALL,
                ),
            )
            _surface.blit(
                cls.__TOTAL_KILLS_TXT,
                (
                    cls.__INFO_BOX_RECT.x + cls.__PADDING + cls.__CONTENT_FONT_SMALL,
                    title_text_y + cls.__PADDING * 3 + cls.__CONTENT_FONT_SMALL,
                ),
            )
            rating_text_y: int = (
                title_text_y + cls.__PADDING * 4 + cls.__CONTENT_FONT_SMALL
            )
            icon_size: int = cls.__INFO_BOX_RECT.bottom - rating_text_y
            if cls.__RATING_ICON is None:
                cls.__RATING_ICON = linpg.images.load(
                    "Assets/image/UI/ratings/{}.png".format(cls.__RATING),
                    (None, icon_size),
                )
            _surface.blit(
                cls.__RATING_TXT,
                (
                    cls.__INFO_BOX_RECT.x + cls.__PADDING + cls.__CONTENT_FONT_SMALL,
                    rating_text_y,
                ),
            )
            _surface.blit(
                cls.__RATING_ICON,
                (
                    cls.__INFO_BOX_RECT.x
                    + cls.__PADDING * 2
                    + cls.__RATING_TXT.get_width(),
                    rating_text_y,
                ),
            )
