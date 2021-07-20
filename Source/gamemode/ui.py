import time
from collections import deque
from ..base import *

# 显示回合切换的UI
class RoundSwitch:
    def __init__(self, window_x: int, window_y: int, battleUiTxt: dict):
        self.lineRedDown = linpg.load.img(r"Assets/image/UI/lineRed.png", (window_x, window_y / 50))
        self.lineRedUp = linpg.transform.rotate(self.lineRedDown, 180)
        self.lineGreenDown = linpg.load.img(r"Assets/image/UI/lineGreen.png", (window_x, window_y / 50))
        self.lineGreenUp = linpg.transform.rotate(self.lineGreenDown, 180)
        self.baseImg = linpg.load.img(r"Assets/image/UI/roundSwitchBase.png", (window_x, window_y / 5))
        self.baseImg.set_alpha(0)
        self.x = -window_x
        self.y = int((window_y - self.baseImg.get_height()) / 2)
        self.y2 = self.y + self.baseImg.get_height() - self.lineRedDown.get_height()
        self.baseAlphaUp = True
        self.TxtAlphaUp = True
        self.idleTime = 60
        self.now_total_rounds_text = battleUiTxt["numRound"]
        self.now_total_rounds_surface = None
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
        # 如果UI底的alpha值在渐入阶段
        if self.baseAlphaUp:
            alphaTemp = self.baseImg.get_alpha()
            # 如果值还未到255（即完全显露），则继续增加，反之如果x到0了再进入淡出阶段
            if alphaTemp > 250 and self.x >= 0:
                self.baseAlphaUp = False
            elif alphaTemp <= 250:
                self.baseImg.set_alpha(alphaTemp + 5)
        # 如果UI底的alpha值在淡出阶段
        elif not self.baseAlphaUp:
            # 如果文字不在淡出阶段
            if self.TxtAlphaUp is True:
                alphaTemp = self.now_total_rounds_surface.get_alpha()
                # “第N回合”的文字先渐入
                if alphaTemp < 250:
                    self.now_total_rounds_surface.set_alpha(alphaTemp + 10)
                else:
                    # 然后“谁的回合”的文字渐入
                    if whose_round == "playerToSangvisFerris":
                        alphaTemp = self.enemy_round_txt_surface.get_alpha()
                        if alphaTemp < 250:
                            self.enemy_round_txt_surface.set_alpha(alphaTemp + 10)
                        else:
                            self.TxtAlphaUp = False
                    if whose_round == "sangvisFerrisToPlayer":
                        alphaTemp = self.your_round_txt_surface.get_alpha()
                        if alphaTemp < 250:
                            self.your_round_txt_surface.set_alpha(alphaTemp + 10)
                        else:
                            self.TxtAlphaUp = False
            # 如果2个文字都渐入完了，会进入idle时间
            elif self.idleTime > 0:
                self.idleTime -= 1
            # 如果idle时间结束，则所有UI开始淡出
            else:
                alphaTemp = self.baseImg.get_alpha()
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
            self.x += screen.get_width() / 35
        # 展示UI
        screen.blits(
            (
                (self.baseImg, (0, self.y)),
                (
                    self.now_total_rounds_surface,
                    (
                        screen.get_width() / 2 - self.now_total_rounds_surface.get_width(),
                        self.y + screen.get_width() / 36,
                    ),
                ),
            )
        )
        if whose_round == "playerToSangvisFerris":
            screen.blits(
                (
                    (self.lineRedUp, (abs(self.x), self.y)),
                    (self.lineRedDown, (self.x, self.y2)),
                    (
                        self.enemy_round_txt_surface,
                        (screen.get_width() / 2, self.y + screen.get_width() / 18),
                    ),
                )
            )
        elif whose_round == "sangvisFerrisToPlayer":
            screen.blits(
                (
                    (self.lineGreenUp, (abs(self.x), self.y)),
                    (self.lineGreenDown, (self.x, self.y2)),
                    (
                        self.your_round_txt_surface,
                        (screen.get_width() / 2, self.y + screen.get_width() / 18),
                    ),
                )
            )
        # 如果UI展示还未完成，返回False
        return False


# 警告系统
class WarningSystem:
    def __init__(self, font_size: int = 30):
        self.__all_warnings: deque = deque()
        self.__warnings_msg: dict = linpg.lang.get_text("Warnings")
        self.font_size: int = font_size

    # 新增一个讯息
    def add(self, the_warning: str) -> None:
        if len(self.__all_warnings) >= 5:
            self.__all_warnings.pop()
        self.__all_warnings.appendleft(linpg.font.render(self.__warnings_msg[the_warning], "red", self.font_size, True))

    # 清空所有当前正在播放的警告讯息
    def clear(self) -> None:
        self.__all_warnings.clear()

    # 画出
    def draw(self, screen: linpg.ImageSurface) -> None:
        for i in range(len(self.__all_warnings)):
            try:
                img_alpha = self.__all_warnings[i].get_alpha()
            except Exception:
                break
            if img_alpha > 0:
                screen.blit(
                    self.__all_warnings[i],
                    (
                        (screen.get_width() - self.__all_warnings[i].get_width()) / 2,
                        (screen.get_height() - self.__all_warnings[i].get_height()) / 2
                        + i * self.__all_warnings[i].get_height() * 1.2,
                    ),
                )
                self.__all_warnings[i].set_alpha(img_alpha - 5)
            else:
                self.__all_warnings.pop()


# 角色行动选项菜单
class SelectMenu:
    def __init__(self):
        selectMenuTxtDic: dict = linpg.lang.get_text("SelectMenu")
        self.selectButtonImg = linpg.load.img(r"Assets/image/UI/menu.png")
        # 攻击
        self.attackAP = linpg.AP_IS_NEEDED_TO_ATTACK
        self.attackTxt = selectMenuTxtDic["attack"]
        self.attackAPTxt = str(self.attackAP) + " AP"
        # 移动
        self.moveAP = linpg.AP_IS_NEEDED_TO_MOVE_ONE_BLOCK
        self.moveTxt = selectMenuTxtDic["move"]
        self.moveAPTxt = str(self.moveAP) + "N AP"
        # 换弹
        self.reloadAP = 5
        self.reloadTxt = selectMenuTxtDic["reload"]
        self.reloadAPTxt = str(self.reloadAP) + " AP"
        # 技能
        self.skillAP = 8
        self.skillTxt = selectMenuTxtDic["skill"]
        self.skillAPTxt = str(self.skillAP) + " AP"
        # 救助
        self.rescueAP = 8
        self.rescueTxt = selectMenuTxtDic["rescue"]
        self.rescueAPTxt = str(self.rescueAP) + " AP"
        # 互动
        self.interactAP = 2
        self.interactTxt = selectMenuTxtDic["interact"]
        self.interactAPTxt = str(self.interactAP) + " AP"
        # 所有按钮
        self.allButton = None

    # 初始化按钮
    def initialButtons(self, fontSize: linpg.int_f) -> None:
        selectButtonBase = linpg.transform.resize(self.selectButtonImg, (round(fontSize * 5), round(fontSize * 2.6)))
        selectButtonBaseWidth = selectButtonBase.get_width()
        sizeBig = int(fontSize)
        sizeSmall = int(fontSize * 0.75)
        self.allButton = {
            "attack": selectButtonBase.copy(),
            "move": selectButtonBase.copy(),
            "reload": selectButtonBase.copy(),
            "skill": selectButtonBase.copy(),
            "rescue": selectButtonBase.copy(),
            "interact": selectButtonBase.copy(),
        }
        # 攻击按钮
        txt_temp = linpg.font.render(self.attackTxt, "black", sizeBig)
        txt_temp2 = linpg.font.render(self.attackAPTxt, "black", sizeSmall)
        self.allButton["attack"].blit(
            txt_temp,
            (
                (selectButtonBaseWidth - txt_temp.get_width()) / 2,
                txt_temp.get_height() * 0.15,
            ),
        )
        self.allButton["attack"].blit(
            txt_temp2,
            (
                (selectButtonBaseWidth - txt_temp2.get_width()) / 2,
                txt_temp.get_height() * 1.1,
            ),
        )
        # 移动按钮
        txt_temp = linpg.font.render(self.moveTxt, "black", sizeBig)
        txt_temp2 = linpg.font.render(self.moveAPTxt, "black", sizeSmall)
        self.allButton["move"].blit(
            txt_temp,
            (
                (selectButtonBaseWidth - txt_temp.get_width()) / 2,
                txt_temp.get_height() * 0.15,
            ),
        )
        self.allButton["move"].blit(
            txt_temp2,
            (
                (selectButtonBaseWidth - txt_temp2.get_width()) / 2,
                txt_temp.get_height() * 1.1,
            ),
        )
        # 换弹按钮
        txt_temp = linpg.font.render(self.reloadTxt, "black", sizeBig)
        txt_temp2 = linpg.font.render(self.reloadAPTxt, "black", sizeSmall)
        self.allButton["reload"].blit(
            txt_temp,
            (
                (selectButtonBaseWidth - txt_temp.get_width()) / 2,
                txt_temp.get_height() * 0.15,
            ),
        )
        self.allButton["reload"].blit(
            txt_temp2,
            (
                (selectButtonBaseWidth - txt_temp2.get_width()) / 2,
                txt_temp.get_height() * 1.1,
            ),
        )
        # 技能按钮
        txt_temp = linpg.font.render(self.skillTxt, "black", sizeBig)
        txt_temp2 = linpg.font.render(self.skillAPTxt, "black", sizeSmall)
        self.allButton["skill"].blit(
            txt_temp,
            (
                (selectButtonBaseWidth - txt_temp.get_width()) / 2,
                txt_temp.get_height() * 0.15,
            ),
        )
        self.allButton["skill"].blit(
            txt_temp2,
            (
                (selectButtonBaseWidth - txt_temp2.get_width()) / 2,
                txt_temp.get_height() * 1.1,
            ),
        )
        # 救助按钮
        txt_temp = linpg.font.render(self.rescueTxt, "black", sizeBig)
        txt_temp2 = linpg.font.render(self.rescueAPTxt, "black", sizeSmall)
        self.allButton["rescue"].blit(
            txt_temp,
            (
                (selectButtonBaseWidth - txt_temp.get_width()) / 2,
                txt_temp.get_height() * 0.15,
            ),
        )
        self.allButton["rescue"].blit(
            txt_temp2,
            (
                (selectButtonBaseWidth - txt_temp2.get_width()) / 2,
                txt_temp.get_height() * 1.1,
            ),
        )
        # 互动按钮
        txt_temp = linpg.font.render(self.interactTxt, "black", sizeBig)
        txt_temp2 = linpg.font.render(self.interactAPTxt, "black", sizeSmall)
        self.allButton["interact"].blit(
            txt_temp,
            (
                (selectButtonBaseWidth - txt_temp.get_width()) / 2,
                txt_temp.get_height() * 0.15,
            ),
        )
        self.allButton["interact"].blit(
            txt_temp2,
            (
                (selectButtonBaseWidth - txt_temp2.get_width()) / 2,
                txt_temp.get_height() * 1.1,
            ),
        )

    # 将菜单按钮画出
    def draw(
        self,
        screen: linpg.ImageSurface,
        fontSize: linpg.int_f,
        location: dict,
        kind: str,
        friendsCanSave: list,
        thingsCanReact: list,
    ) -> str:
        # 如果按钮没有初始化，则应该立刻初始化按钮
        if self.allButton is None:
            self.initialButtons(fontSize)
        buttonGetHover: str = ""
        selectButtonBaseWidth = round(fontSize * 5)
        # 攻击按钮 - 左
        txt_tempX = location["xStart"] - selectButtonBaseWidth * 0.6
        txt_tempY = location["yStart"]
        if linpg.is_hover(self.allButton["attack"], (txt_tempX, txt_tempY)):
            buttonGetHover = "attack"
        screen.blit(self.allButton["attack"], (txt_tempX, txt_tempY))
        # 移动按钮 - 右
        txt_tempX = location["xEnd"] - selectButtonBaseWidth * 0.4
        # txt_tempY 与攻击按钮一致
        if linpg.is_hover(self.allButton["move"], (txt_tempX, txt_tempY)):
            buttonGetHover = "move"
        screen.blit(self.allButton["move"], (txt_tempX, txt_tempY))
        # 换弹按钮 - 下
        txt_tempX = location["xStart"] + selectButtonBaseWidth * 0.5
        txt_tempY = location["yEnd"] - selectButtonBaseWidth * 0.25
        if linpg.is_hover(self.allButton["reload"], (txt_tempX, txt_tempY)):
            buttonGetHover = "reload"
        screen.blit(self.allButton["reload"], (txt_tempX, txt_tempY))
        # 技能按钮 - 上
        if kind != "HOC":
            # txt_tempX与换弹按钮一致
            txt_tempY = location["yStart"] - selectButtonBaseWidth * 0.7
            if linpg.is_hover(self.allButton["skill"], (txt_tempX, txt_tempY)):
                buttonGetHover = "skill"
            screen.blit(self.allButton["skill"], (txt_tempX, txt_tempY))
        # 救助队友
        if len(friendsCanSave) > 0:
            txt_tempX = location["xStart"] - selectButtonBaseWidth * 0.6
            txt_tempY = location["yStart"] - selectButtonBaseWidth * 0.7
            if linpg.is_hover(self.allButton["rescue"], (txt_tempX, txt_tempY)):
                buttonGetHover = "rescue"
            screen.blit(self.allButton["rescue"], (txt_tempX, txt_tempY))
        # 互动
        if len(thingsCanReact) > 0:
            txt_tempX = location["xEnd"] - selectButtonBaseWidth * 0.4
            txt_tempY = location["yStart"] - selectButtonBaseWidth * 0.7
            if linpg.is_hover(self.allButton["interact"], (txt_tempX, txt_tempY)):
                buttonGetHover = "interact"
            screen.blit(self.allButton["interact"], (txt_tempX, txt_tempY))
        return buttonGetHover


# 角色信息板
class CharacterInfoBoard:
    def __init__(self, window_x: int, window_y: int, text_size: int = 20):
        self.boardImg = linpg.load.img(r"Assets/image/UI/score.png", (window_x / 5, window_y / 6))
        self.characterIconImages = {}
        for img_path in glob(r"Assets/image/npc_icon/*.png"):
            self.characterIconImages[os.path.basename(img_path).replace(".png", "")] = linpg.transform.resize(
                linpg.load.img(img_path), (window_y * 0.08, window_y * 0.08)
            )
        self.text_size = text_size
        self.informationBoard = None
        hp_empty_img = linpg.load.img(r"Assets/image/UI/hp_empty.png")
        self.hp_red = linpg.ProgressBarSurface(r"Assets/image/UI/hp_red.png", hp_empty_img, 0, 0, window_x / 15, text_size)
        self.hp_green = linpg.ProgressBarSurface(
            r"Assets/image/UI/hp_green.png",
            hp_empty_img,
            0,
            0,
            window_x / 15,
            text_size,
        )
        self.action_point_blue = linpg.ProgressBarSurface(
            r"Assets/image/UI/action_point.png",
            hp_empty_img,
            0,
            0,
            window_x / 15,
            text_size,
        )
        self.bullets_number_brown = linpg.ProgressBarSurface(
            r"Assets/image/UI/bullets_number.png",
            hp_empty_img,
            0,
            0,
            window_x / 15,
            text_size,
        )

    # 标记需要更新
    def update(self) -> None:
        self.informationBoard = None

    # 更新信息板
    def updateInformationBoard(self, fontSize: int, theCharacterData: object) -> None:
        self.informationBoard = self.boardImg.copy()
        padding = (self.boardImg.get_height() - self.characterIconImages[theCharacterData.type].get_height()) / 2
        # 画出角色图标
        self.informationBoard.blit(self.characterIconImages[theCharacterData.type], (padding, padding))
        # 加载所需的文字
        tcgc_hp1 = linpg.font.render("HP: ", "white", fontSize)
        tcgc_hp2 = linpg.font.render(
            str(theCharacterData.current_hp) + "/" + str(theCharacterData.max_hp),
            "black",
            fontSize,
        )
        tcgc_action_point1 = linpg.font.render("AP: ", "white", fontSize)
        tcgc_action_point2 = linpg.font.render(
            str(theCharacterData.current_action_point) + "/" + str(theCharacterData.max_action_point),
            "black",
            fontSize,
        )
        tcgc_bullets_situation1 = linpg.font.render("BP: ", "white", fontSize)
        tcgc_bullets_situation2 = linpg.font.render(
            str(theCharacterData.current_bullets) + "/" + str(theCharacterData.bullets_carried),
            "black",
            fontSize,
        )
        # 先画出hp,ap和bp的文字
        temp_posX = self.characterIconImages[theCharacterData.type].get_width() * 2
        temp_posY = padding - fontSize * 0.2
        self.informationBoard.blit(tcgc_hp1, (temp_posX, temp_posY))
        self.informationBoard.blit(tcgc_action_point1, (temp_posX, temp_posY + self.text_size * 1.5))
        self.informationBoard.blit(tcgc_bullets_situation1, (temp_posX, temp_posY + self.text_size * 3.0))
        # 设置坐标和百分比
        temp_posX = self.characterIconImages[theCharacterData.type].get_width() * 2.4
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
        linpg.display_in_center(tcgc_hp2, self.hp_green, temp_posX, temp_posY, self.informationBoard)
        self.action_point_blue.draw(self.informationBoard)
        linpg.display_in_center(
            tcgc_action_point2,
            self.action_point_blue,
            temp_posX,
            temp_posY + self.text_size * 1.5,
            self.informationBoard,
        )
        self.bullets_number_brown.draw(self.informationBoard)
        linpg.display_in_center(
            tcgc_bullets_situation2,
            self.bullets_number_brown,
            temp_posX,
            temp_posY + self.text_size * 3,
            self.informationBoard,
        )

    # 画出信息板
    def draw(self, screen: linpg.ImageSurface, theCharacterData: object) -> None:
        # 如果信息板还没更新，则应该先更新再画出
        if self.informationBoard is None:
            self.updateInformationBoard(int(screen.get_width() / 96), theCharacterData)
        # 画出信息板
        screen.blit(self.informationBoard, (0, screen.get_height() - self.boardImg.get_height()))


# 计分板
class ResultBoard:
    def __init__(self, finalResult: dict, font_size: int, is_win: bool = True):
        resultTxt: dict = linpg.lang.get_text("ResultBoard")
        self.x = int(font_size * 10)
        self.y = int(font_size * 10)
        self.txt_x = int(font_size * 12)
        self.boardImg = linpg.load.img("Assets/image/UI/score.png", (font_size * 16, font_size * 32))
        self.total_kills = linpg.font.render(
            resultTxt["total_kills"] + ": " + str(finalResult["total_kills"]),
            "white",
            font_size,
        )
        self.total_time = linpg.font.render(
            resultTxt["total_time"] + ": " + str(time.strftime("%M:%S", finalResult["total_time"])),
            "white",
            font_size,
        )
        self.total_rounds_txt = linpg.font.render(
            resultTxt["total_rounds"] + ": " + str(finalResult["total_rounds"]),
            "white",
            font_size,
        )
        self.characters_down = linpg.font.render(
            resultTxt["characters_down"] + ": " + str(finalResult["times_characters_down"]),
            "white",
            font_size,
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
    def __init__(
        self,
        window_x: int,
        window_y: int,
        numChapter_txt: str,
        chapterId: int,
        chapterTitle_txt: str,
        chapterDesc_txt: str,
    ):
        self.black_bg = linpg.get_single_color_surface("black")
        title_chapterNum = linpg.font.render(numChapter_txt.format(chapterId), "white", window_x / 38)
        self.title_chapterNum = linpg.StaticImage(
            title_chapterNum,
            (window_x - title_chapterNum.get_width()) / 2,
            window_y * 0.37,
        )
        title_chapterName = linpg.font.render(chapterTitle_txt, "white", window_x / 38)
        self.title_chapterName = linpg.StaticImage(
            title_chapterName,
            (window_x - title_chapterName.get_width()) / 2,
            window_y * 0.46,
        )
        title_description = linpg.font.render(chapterDesc_txt, "white", window_x / 76)
        self.title_description = linpg.StaticImage(
            title_description,
            (window_x - title_description.get_width()) / 2,
            window_y * 0.6,
        )

    def draw(self, screen: linpg.ImageSurface, alpha: int = 255) -> None:
        self.title_chapterNum.set_alpha(alpha)
        self.title_chapterName.set_alpha(alpha)
        self.title_description.set_alpha(alpha)
        self.black_bg.draw(screen)
        self.title_chapterNum.draw(screen)
        self.title_chapterName.draw(screen)
        self.title_description.draw(screen)
