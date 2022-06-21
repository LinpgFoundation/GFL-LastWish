import time
from collections import deque
from typing import Union
from .dolls import *


# 中心展示模块1：接受两个item和item2的x和y，将item1展示在item2的中心位置,但不展示item2：
def display_in_center(
    item1: linpg.ImageSurface,
    item2: Union[linpg.ImageSurface, linpg.GameObject2d],
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


# 显示回合切换的UI
class RoundSwitch:
    def __init__(self, window_x: int, window_y: int):
        battleUiTxt: dict = linpg.lang.get_texts("Battle_UI")
        self.lineRedDown = linpg.load.img(r"Assets/image/UI/lineRed.png", (window_x, window_y / 50))
        self.lineRedUp = linpg.images.rotate(self.lineRedDown, 180)
        self.lineGreenDown = linpg.load.img(r"Assets/image/UI/lineGreen.png", (window_x, window_y / 50))
        self.lineGreenUp = linpg.images.rotate(self.lineGreenDown, 180)
        self.baseImg = linpg.load.img(r"Assets/image/UI/roundSwitchBase.png", (window_x, window_y / 5))
        self.baseImg.set_alpha(0)
        self.x: int = -window_x
        self.y: int = int((window_y - self.baseImg.get_height()) / 2)
        self.y2 = self.y + self.baseImg.get_height() - self.lineRedDown.get_height()
        self.baseAlphaUp = True
        self.TxtAlphaUp = True
        self.idleTime = 60
        self.now_total_rounds_text = battleUiTxt["numRound"]
        self.now_total_rounds_surface: Optional[linpg.ImageSurface] = None
        self.your_round_txt_surface = linpg.font.render(battleUiTxt["yourRound"], "white", window_x / 36)
        self.your_round_txt_surface.set_alpha(0)
        self.enemy_round_txt_surface = linpg.font.render(battleUiTxt["enemyRound"], "white", window_x / 36)
        self.enemy_round_txt_surface.set_alpha(0)

    def draw(self, screen: linpg.ImageSurface, whose_round: str, total_rounds: int) -> bool:
        # 如果“第N回合”的文字surface还没有初始化，则初始化该文字
        if self.now_total_rounds_surface is None:
            self.now_total_rounds_surface = linpg.font.render(
                self.now_total_rounds_text.format(linpg.lang.get_num_in_local_text(total_rounds)),
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
                    if whose_round == "playerToSangvisFerris":
                        alphaTemp = self.enemy_round_txt_surface.get_alpha()
                        if alphaTemp is None:
                            self.enemy_round_txt_surface.set_alpha(0)
                        elif alphaTemp < 250:
                            self.enemy_round_txt_surface.set_alpha(alphaTemp + 10)
                        else:
                            self.TxtAlphaUp = False
                    if whose_round == "sangvisFerrisToPlayer":
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
                    if whose_round == "playerToSangvisFerris":
                        self.lineRedUp.set_alpha(alphaTemp)
                        self.lineRedDown.set_alpha(alphaTemp)
                        self.enemy_round_txt_surface.set_alpha(alphaTemp)
                    elif whose_round == "sangvisFerrisToPlayer":
                        self.lineGreenUp.set_alpha(alphaTemp)
                        self.lineGreenDown.set_alpha(alphaTemp)
                        self.your_round_txt_surface.set_alpha(alphaTemp)
                else:
                    if whose_round == "playerToSangvisFerris":
                        self.lineRedUp.set_alpha(255)
                        self.lineRedDown.set_alpha(255)
                    elif whose_round == "sangvisFerrisToPlayer":
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
            self.x += screen.get_width() // 35
        # 展示UI
        screen.blits(
            (
                (self.baseImg, (0, self.y)),
                (
                    self.now_total_rounds_surface,
                    (screen.get_width() / 2 - self.now_total_rounds_surface.get_width(), self.y + screen.get_width() / 36),
                ),
            )
        )
        if whose_round == "playerToSangvisFerris":
            screen.blits(
                (
                    (self.lineRedUp, (abs(self.x), self.y)),
                    (self.lineRedDown, (self.x, self.y2)),
                    (self.enemy_round_txt_surface, (screen.get_width() / 2, self.y + screen.get_width() / 18)),
                )
            )
        elif whose_round == "sangvisFerrisToPlayer":
            screen.blits(
                (
                    (self.lineGreenUp, (abs(self.x), self.y)),
                    (self.lineGreenDown, (self.x, self.y2)),
                    (self.your_round_txt_surface, (screen.get_width() / 2, self.y + screen.get_width() / 18)),
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
    def init(cls, font_size: int = 30):
        cls.__font_size = font_size
        cls.update_language()

    # 更新语言
    @classmethod
    def update_language(cls):
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
        cls.__all_warnings.appendleft(linpg.font.render(cls.__warnings_msg[the_warning], "red", cls.__font_size, True))

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
        self, screen: linpg.ImageSurface, fontSize: int, location: dict, kind: str, friendsCanSave: list, thingsCanReact: list
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
                panding: int = int(fontSize / 10)
                for key in self.keys():
                    button_data_t = self.get(key)
                    button_data_t["button"] = selectButtonBase.copy()
                    txt_temp = linpg.font.render(selectMenuTxtDict[key], "black", big_font_size)
                    txt_temp2 = linpg.font.render(button_data_t["ap_text"], "black", small_font_size)
                    top: int = int((selectButtonBase.get_height() - txt_temp.get_height() - txt_temp2.get_height() - panding) / 2)
                    button_data_t["button"].blit(txt_temp, ((selectButtonBase.get_width() - txt_temp.get_width()) / 2, top))
                    button_data_t["button"].blit(
                        txt_temp2,
                        ((selectButtonBase.get_width() - txt_temp2.get_width()) / 2, top + panding + txt_temp.get_height()),
                    )
                self.__need_update = False
            selectButtonBaseWidth = round(fontSize * 5)
            # 攻击按钮 - 左
            txt_tempX = location["xStart"] - selectButtonBaseWidth * 0.6
            txt_tempY = location["yStart"]
            if linpg.is_hovering(self.get("attack")["button"], (txt_tempX, txt_tempY)):
                self._item_being_hovered = "attack"
            screen.blit(self.get("attack")["button"], (txt_tempX, txt_tempY))
            # 移动按钮 - 右
            txt_tempX = location["xEnd"] - selectButtonBaseWidth * 0.4
            # txt_tempY 与攻击按钮一致
            if linpg.is_hovering(self.get("move")["button"], (txt_tempX, txt_tempY)):
                self._item_being_hovered = "move"
            screen.blit(self.get("move")["button"], (txt_tempX, txt_tempY))
            # 换弹按钮 - 下
            txt_tempX = location["xStart"] + selectButtonBaseWidth * 0.5
            txt_tempY = location["yEnd"] - selectButtonBaseWidth * 0.25
            if linpg.is_hovering(self.get("reload")["button"], (txt_tempX, txt_tempY)):
                self._item_being_hovered = "reload"
            screen.blit(self.get("reload")["button"], (txt_tempX, txt_tempY))
            # 技能按钮 - 上
            if kind != "HOC":
                # txt_tempX与换弹按钮一致
                txt_tempY = location["yStart"] - selectButtonBaseWidth * 0.7
                if linpg.is_hovering(self.get("skill")["button"], (txt_tempX, txt_tempY)):
                    self._item_being_hovered = "skill"
                screen.blit(self.get("skill")["button"], (txt_tempX, txt_tempY))
            # 救助队友
            if len(friendsCanSave) > 0:
                txt_tempX = location["xStart"] - selectButtonBaseWidth * 0.6
                txt_tempY = location["yStart"] - selectButtonBaseWidth * 0.7
                if linpg.is_hovering(self.get("rescue")["button"], (txt_tempX, txt_tempY)):
                    self._item_being_hovered = "rescue"
                screen.blit(self.get("rescue")["button"], (txt_tempX, txt_tempY))
            # 互动
            if len(thingsCanReact) > 0:
                txt_tempX = location["xEnd"] - selectButtonBaseWidth * 0.4
                txt_tempY = location["yStart"] - selectButtonBaseWidth * 0.7
                if linpg.is_hovering(self.get("interact")["button"], (txt_tempX, txt_tempY)):
                    self._item_being_hovered = "interact"
                screen.blit(self.get("interact")["button"], (txt_tempX, txt_tempY))


# 角色信息板
class CharacterInfoBoard:
    def __init__(self, window_x: int, window_y: int, text_size: int = 20):
        self.boardImg: linpg.ImageSurface = linpg.load.img(r"Assets/image/UI/score.png", (window_x / 5, window_y / 6))
        self.characterIconImages: dict[str, linpg.ImageSurface] = {}
        for img_path in glob(r"Assets/image/npc_icon/*.png"):
            self.characterIconImages[os.path.basename(img_path).replace(".png", "")] = linpg.images.smoothly_resize(
                linpg.load.img(img_path), (window_y * 0.08, window_y * 0.08)
            )
        self.text_size: int = text_size
        self.informationBoard: Optional[linpg.ImageSurface] = None
        hp_empty_img = linpg.load.img(r"Assets/image/UI/hp_empty.png")
        self.hp_red = linpg.ProgressBarSurface(r"Assets/image/UI/hp_red.png", hp_empty_img, 0, 0, window_x // 15, text_size)
        self.hp_green = linpg.ProgressBarSurface(r"Assets/image/UI/hp_green.png", hp_empty_img, 0, 0, window_x // 15, text_size)
        self.action_point_blue = linpg.ProgressBarSurface(
            r"Assets/image/UI/action_point.png", hp_empty_img, 0, 0, window_x // 15, text_size
        )
        self.bullets_number_brown = linpg.ProgressBarSurface(
            r"Assets/image/UI/bullets_number.png", hp_empty_img, 0, 0, window_x // 15, text_size
        )

    # 标记需要更新
    def update(self) -> None:
        self.informationBoard = None

    # 更新信息板
    def updateInformationBoard(self, fontSize: int, theCharacterData: FriendlyCharacter) -> None:
        self.informationBoard = self.boardImg.copy()
        padding: int = (self.boardImg.get_height() - self.characterIconImages[theCharacterData.type].get_height()) // 2
        # 画出角色图标
        self.informationBoard.blit(self.characterIconImages[theCharacterData.type], (padding, padding))
        # 加载所需的文字
        tcgc_hp1 = linpg.font.render("HP: ", "white", fontSize)
        tcgc_hp2 = linpg.font.render(str(theCharacterData.current_hp) + "/" + str(theCharacterData.max_hp), "black", fontSize)
        tcgc_action_point1 = linpg.font.render("AP: ", "white", fontSize)
        tcgc_action_point2 = linpg.font.render(
            str(theCharacterData.current_action_point) + "/" + str(theCharacterData.max_action_point), "black", fontSize
        )
        tcgc_bullets_situation1 = linpg.font.render("BP: ", "white", fontSize)
        tcgc_bullets_situation2 = linpg.font.render(
            str(theCharacterData.current_bullets) + "/" + str(theCharacterData.bullets_carried), "black", fontSize
        )
        # 先画出hp,ap和bp的文字
        temp_posX: int = self.characterIconImages[theCharacterData.type].get_width() * 2
        temp_posY: int = padding - fontSize // 5
        self.informationBoard.blit(tcgc_hp1, (temp_posX, temp_posY))
        self.informationBoard.blit(tcgc_action_point1, (temp_posX, temp_posY + self.text_size * 1.5))
        self.informationBoard.blit(tcgc_bullets_situation1, (temp_posX, temp_posY + self.text_size * 3.0))
        # 设置坐标和百分比
        temp_posX = int(self.characterIconImages[theCharacterData.type].get_width() * 2.4)
        temp_posY = padding
        self.hp_red.set_pos(temp_posX, temp_posY)
        self.hp_red.set_percentage(theCharacterData.hp_precentage)
        self.hp_green.set_pos(temp_posX, temp_posY)
        self.hp_green.set_percentage(theCharacterData.hp_precentage)
        self.action_point_blue.set_pos(temp_posX, temp_posY + self.text_size * 1.5)
        self.action_point_blue.set_percentage(theCharacterData.current_action_point / theCharacterData.max_action_point)
        self.bullets_number_brown.set_pos(temp_posX, temp_posY + self.text_size * 3)
        self.bullets_number_brown.set_percentage(theCharacterData.current_bullets / theCharacterData.magazine_capacity)
        # 画出
        self.hp_green.draw(self.informationBoard)
        display_in_center(tcgc_hp2, self.hp_green, temp_posX, temp_posY, self.informationBoard)
        self.action_point_blue.draw(self.informationBoard)
        display_in_center(
            tcgc_action_point2, self.action_point_blue, temp_posX, temp_posY + int(self.text_size * 1.5), self.informationBoard
        )
        self.bullets_number_brown.draw(self.informationBoard)
        display_in_center(
            tcgc_bullets_situation2,
            self.bullets_number_brown,
            temp_posX,
            temp_posY + self.text_size * 3,
            self.informationBoard,
        )

    # 画出信息板
    def draw(self, screen: linpg.ImageSurface, theCharacterData: FriendlyCharacter) -> None:
        # 如果信息板还没更新，则应该先更新再画出
        if self.informationBoard is None:
            self.updateInformationBoard(screen.get_width() // 96, theCharacterData)
        # 画出信息板
        if self.informationBoard is not None:
            screen.blit(self.informationBoard, (0, screen.get_height() - self.boardImg.get_height()))


# 计分板
class ResultBoard:
    def __init__(self, finalResult: dict, font_size: int, is_win: bool = True):
        resultTxt: dict = linpg.lang.get_texts("ResultBoard")
        self.x = int(font_size * 10)
        self.y = int(font_size * 10)
        self.txt_x = int(font_size * 12)
        self.boardImg = linpg.load.img(r"Assets/image/UI/score.png", (font_size * 16, font_size * 32))
        self.total_kills = linpg.font.render(
            resultTxt["total_kills"] + ": " + str(finalResult["total_kills"]), "white", font_size
        )
        self.total_time = linpg.font.render(
            resultTxt["total_time"] + ": " + str(time.strftime("%M:%S", finalResult["total_time"])), "white", font_size
        )
        self.total_rounds_txt = linpg.font.render(
            resultTxt["total_rounds"] + ": " + str(finalResult["total_rounds"]), "white", font_size
        )
        self.characters_down = linpg.font.render(
            resultTxt["characters_down"] + ": " + str(finalResult["times_characters_down"]), "white", font_size
        )
        self.player_rate = linpg.font.render(resultTxt["rank"] + ": " + "A", "white", font_size)
        self.pressKeyContinue = (
            linpg.font.render(resultTxt["pressKeyContinue"], "white", font_size)
            if is_win
            else linpg.font.render(resultTxt["pressKeyRestart"], "white", font_size)
        )

    def draw(self, screen: linpg.ImageSurface) -> None:
        screen.blits(
            (
                (self.boardImg, (self.x, self.y)),
                (self.total_kills, (self.txt_x, 300)),
                (self.total_time, (self.txt_x, 350)),
                (self.total_rounds_txt, (self.txt_x, 400)),
                (self.characters_down, (self.txt_x, 450)),
                (self.player_rate, (self.txt_x, 500)),
                (self.pressKeyContinue, (self.txt_x, 700)),
            )
        )


# 章节标题(在加载时显示)
class LoadingTitle:

    black_bg: linpg.StaticImage = linpg.StaticImage(linpg.surfaces.colored(linpg.display.get_size(), linpg.color.BLACK), 0, 0)
    title_chapterNum: Optional[linpg.StaticImage] = None
    title_chapterName: Optional[linpg.StaticImage] = None
    title_description: Optional[linpg.StaticImage] = None

    @classmethod
    def update(cls, numChapter_txt: str, chapterId: int, chapterTitle_txt: str, chapterDesc_txt: str):
        # 黑色Void帘幕
        cls.black_bg.set_size(linpg.display.get_width(), linpg.display.get_height())
        title_chapterNum = linpg.font.render(numChapter_txt.format(chapterId), "white", linpg.display.get_width() / 38)
        cls.title_chapterNum = linpg.StaticImage(
            title_chapterNum, (linpg.display.get_width() - title_chapterNum.get_width()) / 2, linpg.display.get_height() * 0.37
        )
        title_chapterName = linpg.font.render(chapterTitle_txt, "white", linpg.display.get_width() / 38)
        cls.title_chapterName = linpg.StaticImage(
            title_chapterName, (linpg.display.get_width() - title_chapterName.get_width()) / 2, linpg.display.get_height() * 0.46
        )
        title_description = linpg.font.render(chapterDesc_txt, "white", linpg.display.get_width() / 76)
        cls.title_description = linpg.StaticImage(
            title_description, (linpg.display.get_width() - title_description.get_width()) / 2, linpg.display.get_height() * 0.6
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


# 需要被打印的物品
class ItemNeedBlit(linpg.GameObject2point5d):
    def __init__(
        self, image: Union[linpg.ImageSurface, linpg.GameObject2d], weight: int, pos: tuple[int, int], offSet: tuple[int, int]
    ):
        super().__init__(pos[0], pos[1], weight)
        self.image: Union[linpg.ImageSurface, linpg.GameObject2d] = image
        self.offSet: tuple[int, int] = offSet

    def draw(self, surface: linpg.ImageSurface) -> None:
        if isinstance(self.image, linpg.ImageSurface):
            surface.blit(self.image, linpg.coordinates.add(self.pos, self.offSet))
        else:
            try:
                self.image.display(surface, self.offSet)
            except Exception:
                self.image.draw(surface)


class RangeSystem:

    # 区域坐标
    __areas: tuple[list[tuple[int, int]], ...] = ([], [], [], [], [])
    # 用于表示范围的方框图片
    __images: tuple[linpg.StaticImage, ...] = (
        linpg.load.static_image(r"<&ui>range_green.png", (0, 0)),
        linpg.load.static_image(r"<&ui>range_red.png", (0, 0)),
        linpg.load.static_image(r"<&ui>range_yellow.png", (0, 0)),
        linpg.load.static_image(r"<&ui>range_blue.png", (0, 0)),
        linpg.load.static_image(r"<&ui>range_orange.png", (0, 0)),
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
    def update_attack_range(cls, rangeCanAttack: list[list]):
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
    def draw(cls, map_prt: linpg.MapObject, screen: linpg.ImageSurface) -> None:
        for prt in cls.__images:
            if prt.get_alpha() > cls.__target_alpha:
                prt.subtract_alpha(17)
            elif prt.get_alpha() < cls.__target_alpha:
                prt.add_alpha(17)
        for i in range(len(cls.__areas)):
            for _position in cls.__areas[i]:
                xTemp, yTemp = map_prt.calculate_position(_position[0], _position[1])
                cls.__images[i].set_pos(xTemp + map_prt.block_width * 0.1, yTemp)
                cls.__images[i].draw(screen)
