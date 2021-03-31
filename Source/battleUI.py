# cython: language_level=3
from .init import *

#显示回合切换的UI
class RoundSwitch:
    def __init__(self,window_x,window_y,battleUiTxt):
        self.lineRedDown = linpg.loadImg("Assets/image/UI/lineRed.png",(window_x,window_y/50))
        self.lineRedUp = pygame.transform.rotate(self.lineRedDown, 180)
        self.lineGreenDown = linpg.loadImg("Assets/image/UI/lineGreen.png",(window_x,window_y/50))
        self.lineGreenUp = pygame.transform.rotate(self.lineGreenDown, 180)
        self.baseImg = linpg.loadImg("Assets/image/UI/roundSwitchBase.png",(window_x,window_y/5))
        self.baseImg.set_alpha(0)
        self.x = -window_x
        self.y = int((window_y - self.baseImg.get_height())/2)
        self.y2 = self.y+self.baseImg.get_height()-self.lineRedDown.get_height()
        self.baseAlphaUp = True
        self.TxtAlphaUp = True
        self.idleTime = 60
        self.now_total_rounds_text = battleUiTxt["numRound"]
        self.now_total_rounds_surface = None
        self.your_round_txt_surface = linpg.fontRender(battleUiTxt["yourRound"], "white",window_x/36)
        self.your_round_txt_surface.set_alpha(0)
        self.enemy_round_txt_surface = linpg.fontRender(battleUiTxt["enemyRound"], "white",window_x/36)
        self.enemy_round_txt_surface.set_alpha(0)
    def draw(self,screen,whose_round,total_rounds):
        #如果“第N回合”的文字surface还没有初始化，则初始化该文字
        if self.now_total_rounds_surface == None:
            self.now_total_rounds_surface = linpg.fontRender(self.now_total_rounds_text.format(linpg.get_num_in_local_text(total_rounds)), "white",screen.get_width()/38)
            self.now_total_rounds_surface.set_alpha(0)
        #如果UI底的alpha值在渐入阶段
        if self.baseAlphaUp == True:
            alphaTemp = self.baseImg.get_alpha()
            #如果值还未到255（即完全显露），则继续增加，反之如果x到0了再进入淡出阶段
            if alphaTemp > 250 and self.x >= 0:
                self.baseAlphaUp = False
            elif alphaTemp <= 250 :
                self.baseImg.set_alpha(alphaTemp+5)
        #如果UI底的alpha值在淡出阶段
        elif self.baseAlphaUp == False:
            #如果文字不在淡出阶段
            if self.TxtAlphaUp == True:
                alphaTemp = self.now_total_rounds_surface.get_alpha()
                #“第N回合”的文字先渐入
                if alphaTemp < 250:
                    self.now_total_rounds_surface.set_alpha(alphaTemp+10)
                else:
                    #然后“谁的回合”的文字渐入
                    if whose_round == "playerToSangvisFerris":
                        alphaTemp = self.enemy_round_txt_surface.get_alpha()
                        if alphaTemp < 250:
                            self.enemy_round_txt_surface.set_alpha(alphaTemp+10)
                        else:
                            self.TxtAlphaUp = False
                    if whose_round == "sangvisFerrisToPlayer":
                        alphaTemp = self.your_round_txt_surface.get_alpha()
                        if alphaTemp < 250:
                            self.your_round_txt_surface.set_alpha(alphaTemp+10)
                        else:
                            self.TxtAlphaUp = False
            #如果2个文字都渐入完了，会进入idle时间
            elif self.idleTime > 0:
                self.idleTime -= 1
            #如果idle时间结束，则所有UI开始淡出
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
                    #淡出完成，重置部分参数，UI播放结束
                    self.x = -screen.get_width()
                    self.baseAlphaUp = True
                    self.TxtAlphaUp = True
                    self.idleTime = 60
                    self.now_total_rounds_surface = None
                    return True
        #横条移动
        if self.x < 0:
            self.x += screen.get_width()/35
        #展示UI
        linpg.drawImg(self.baseImg,(0,self.y),screen)
        linpg.drawImg(self.now_total_rounds_surface,(screen.get_width()/2-self.now_total_rounds_surface.get_width(),self.y+screen.get_width()/36),screen)
        if whose_round == "playerToSangvisFerris":
            linpg.drawImg(self.lineRedUp,(abs(self.x),self.y),screen)
            linpg.drawImg(self.lineRedDown,(self.x,self.y2),screen)
            linpg.drawImg(self.enemy_round_txt_surface,(screen.get_width()/2,self.y+screen.get_width()/18),screen)
        elif whose_round == "sangvisFerrisToPlayer":
            linpg.drawImg(self.lineGreenUp,(abs(self.x),self.y),screen)
            linpg.drawImg(self.lineGreenDown,(self.x,self.y2),screen)
            linpg.drawImg(self.your_round_txt_surface,(screen.get_width()/2,self.y+screen.get_width()/18),screen)
        #如果UI展示还未完成，返回False
        return False

#警告系统
class WarningSystem:
    def __init__(self):
        self.all_warnings = []
        self.warnings = linpg.get_lang("Warnings")
    def add(self,the_warning,fontSize=30):
        if len(self.all_warnings)>=5:
            self.all_warnings.pop()
        self.all_warnings.insert(0,linpg.fontRender(self.warnings[the_warning],"red",fontSize,True))
    def draw(self,screen):
        for i in range(len(self.all_warnings)):
            try:
                img_alpha = self.all_warnings[i].get_alpha()
            except BaseException:
                break
            if img_alpha > 0:
                screen.blit(self.all_warnings[i],((screen.get_width()-self.all_warnings[i].get_width())/2,(screen.get_height()-self.all_warnings[i].get_height())/2+i*self.all_warnings[i].get_height()*1.2))
                self.all_warnings[i].set_alpha(img_alpha-5)
            else:
                del self.all_warnings[i]
    def empty(self):
        self.all_warnings = []

#角色行动选项菜单
class SelectMenu:
    def __init__(self):
        selectMenuTxtDic = linpg.get_lang("SelectMenu")
        self.selectButtonImg = linpg.loadImg("Assets/image/UI/menu.png")
        #攻击
        self.attackAP = linpg.AP_IS_NEEDED_TO_ATTACK
        self.attackTxt = selectMenuTxtDic["attack"]
        self.attackAPTxt = str(self.attackAP)+" AP"
        #移动
        self.moveAP = linpg.AP_IS_NEEDED_TO_MOVE_ONE_BLOCK
        self.moveTxt = selectMenuTxtDic["move"]
        self.moveAPTxt = str(self.moveAP)+"N AP"
        #换弹
        self.reloadAP = 5
        self.reloadTxt = selectMenuTxtDic["reload"]
        self.reloadAPTxt = str(self.reloadAP)+" AP"
        #技能
        self.skillAP = 8
        self.skillTxt = selectMenuTxtDic["skill"]
        self.skillAPTxt = str(self.skillAP)+" AP"
        #救助
        self.rescueAP = 8
        self.rescueTxt = selectMenuTxtDic["rescue"]
        self.rescueAPTxt = str(self.rescueAP)+" AP"
        #互动
        self.interactAP = 2
        self.interactTxt = selectMenuTxtDic["interact"]
        self.interactAPTxt = str(self.interactAP)+" AP"
        #所有按钮
        self.allButton = None
    #初始化按钮
    def initialButtons(self,fontSize):
        selectButtonBase = linpg.resizeImg(self.selectButtonImg, (round(fontSize*5), round(fontSize*2.6)))
        selectButtonBaseWidth = selectButtonBase.get_width()
        sizeBig = int(fontSize)
        sizeSmall = int(fontSize*0.75)
        self.allButton = {
            "attack": selectButtonBase.copy(),
            "move": selectButtonBase.copy(),
            "reload": selectButtonBase.copy(),
            "skill": selectButtonBase.copy(),
            "rescue": selectButtonBase.copy(),
            "interact": selectButtonBase.copy()
        }
        #攻击按钮
        txt_temp = linpg.fontRender(self.attackTxt,"black",sizeBig)
        txt_temp2 = linpg.fontRender(self.attackAPTxt,"black",sizeSmall)
        self.allButton["attack"].blit(txt_temp,((selectButtonBaseWidth-txt_temp.get_width())/2,txt_temp.get_height()*0.15))
        self.allButton["attack"].blit(txt_temp2,((selectButtonBaseWidth-txt_temp2.get_width())/2,txt_temp.get_height()*1.1))
        #移动按钮
        txt_temp = linpg.fontRender(self.moveTxt,"black",sizeBig)
        txt_temp2 = linpg.fontRender(self.moveAPTxt,"black",sizeSmall)
        self.allButton["move"].blit(txt_temp,((selectButtonBaseWidth-txt_temp.get_width())/2,txt_temp.get_height()*0.15))
        self.allButton["move"].blit(txt_temp2,((selectButtonBaseWidth-txt_temp2.get_width())/2,txt_temp.get_height()*1.1))
        #换弹按钮
        txt_temp = linpg.fontRender(self.reloadTxt,"black",sizeBig)
        txt_temp2 = linpg.fontRender(self.reloadAPTxt,"black",sizeSmall)
        self.allButton["reload"].blit(txt_temp,((selectButtonBaseWidth-txt_temp.get_width())/2,txt_temp.get_height()*0.15))
        self.allButton["reload"].blit(txt_temp2,((selectButtonBaseWidth-txt_temp2.get_width())/2,txt_temp.get_height()*1.1))
        #技能按钮
        txt_temp = linpg.fontRender(self.skillTxt,"black",sizeBig)
        txt_temp2 = linpg.fontRender(self.skillAPTxt,"black",sizeSmall)
        self.allButton["skill"].blit(txt_temp,((selectButtonBaseWidth-txt_temp.get_width())/2,txt_temp.get_height()*0.15))
        self.allButton["skill"].blit(txt_temp2,((selectButtonBaseWidth-txt_temp2.get_width())/2,txt_temp.get_height()*1.1))
        #救助按钮
        txt_temp = linpg.fontRender(self.rescueTxt,"black",sizeBig)
        txt_temp2 = linpg.fontRender(self.rescueAPTxt,"black",sizeSmall)
        self.allButton["rescue"].blit(txt_temp,((selectButtonBaseWidth-txt_temp.get_width())/2,txt_temp.get_height()*0.15))
        self.allButton["rescue"].blit(txt_temp2,((selectButtonBaseWidth-txt_temp2.get_width())/2,txt_temp.get_height()*1.1))
        #互动按钮
        txt_temp = linpg.fontRender(self.interactTxt,"black",sizeBig)
        txt_temp2 = linpg.fontRender(self.interactAPTxt,"black",sizeSmall)
        self.allButton["interact"].blit(txt_temp,((selectButtonBaseWidth-txt_temp.get_width())/2,txt_temp.get_height()*0.15))
        self.allButton["interact"].blit(txt_temp2,((selectButtonBaseWidth-txt_temp2.get_width())/2,txt_temp.get_height()*1.1))
    def draw(self,screen,fontSize,location,kind,friendsCanSave,thingsCanReact):
        if self.allButton == None:
            self.initialButtons(fontSize)
        buttonGetHover = None
        selectButtonBaseWidth = round(fontSize*5)
        #攻击按钮 - 左
        txt_tempX = location["xStart"]-selectButtonBaseWidth*0.6
        txt_tempY = location["yStart"]
        if linpg.is_hover(self.allButton["attack"],(txt_tempX,txt_tempY)):
            buttonGetHover = "attack"
        screen.blit(self.allButton["attack"],(txt_tempX,txt_tempY))
        #移动按钮 - 右
        txt_tempX = location["xEnd"]-selectButtonBaseWidth*0.4
        #txt_tempY 与攻击按钮一致
        if linpg.is_hover(self.allButton["move"],(txt_tempX,txt_tempY)):
            buttonGetHover = "move"
        screen.blit(self.allButton["move"],(txt_tempX,txt_tempY))
        #换弹按钮 - 下
        txt_tempX = location["xStart"]+selectButtonBaseWidth*0.5
        txt_tempY = location["yEnd"]-selectButtonBaseWidth*0.25
        if linpg.is_hover(self.allButton["reload"],(txt_tempX,txt_tempY)):
            buttonGetHover = "reload"
        screen.blit(self.allButton["reload"],(txt_tempX,txt_tempY))
        #技能按钮 - 上
        if kind != "HOC":
            #txt_tempX与换弹按钮一致
            txt_tempY = location["yStart"]-selectButtonBaseWidth*0.7
            if linpg.is_hover(self.allButton["skill"],(txt_tempX,txt_tempY)):
                buttonGetHover = "skill"
            screen.blit(self.allButton["skill"],(txt_tempX,txt_tempY))
        #救助队友
        if len(friendsCanSave)>0:
            txt_tempX = location["xStart"]-selectButtonBaseWidth*0.6
            txt_tempY = location["yStart"]-selectButtonBaseWidth*0.7
            if linpg.is_hover(self.allButton["rescue"],(txt_tempX,txt_tempY)):
                buttonGetHover = "rescue"
            screen.blit(self.allButton["rescue"],(txt_tempX,txt_tempY))
        #互动
        if len(thingsCanReact)>0:
            txt_tempX = location["xEnd"]-selectButtonBaseWidth*0.4
            txt_tempY = location["yStart"]-selectButtonBaseWidth*0.7
            if linpg.is_hover(self.allButton["interact"],(txt_tempX,txt_tempY)):
                buttonGetHover = "interact"
            screen.blit(self.allButton["interact"],(txt_tempX,txt_tempY))
        return buttonGetHover

#角色信息版
class CharacterInfoBoard:
    def __init__(self,window_x,window_y,text_size=20):
        self.boardImg = linpg.loadImg("Assets/image/UI/score.png",(window_x/5,window_y/6))
        self.characterIconImages = {}
        all_icon_file_list = glob.glob(r'Assets/image/npc_icon/*.png')
        for i in range(len(all_icon_file_list)):
            img_name = all_icon_file_list[i].replace("Assets","").replace("image","").replace("npc_icon","").replace(".png","").replace("\\","").replace("/","")
            self.characterIconImages[img_name] = linpg.loadImg(all_icon_file_list[i],(window_y*0.08,window_y*0.08))
        del all_icon_file_list
        self.text_size = text_size
        self.informationBoard = None
        hp_empty_img = linpg.loadImg("Assets/image/UI/hp_empty.png")
        self.hp_red = linpg.ProgressBarSurface("Assets/image/UI/hp_red.png",hp_empty_img,0,0,window_x/15,text_size)
        self.hp_green = linpg.ProgressBarSurface("Assets/image/UI/hp_green.png",hp_empty_img,0,0,window_x/15,text_size)
        self.action_point_blue = linpg.ProgressBarSurface("Assets/image/UI/action_point.png",hp_empty_img,0,0,window_x/15,text_size)
        self.bullets_number_brown = linpg.ProgressBarSurface("Assets/image/UI/bullets_number.png",hp_empty_img,0,0,window_x/15,text_size)
    #标记需要更新
    def update(self):
        self.informationBoard = None
    #更新信息了
    def updateInformationBoard(self,fontSize,theCharacterData):
        self.informationBoard = self.boardImg.copy()
        padding = (self.boardImg.get_height()-self.characterIconImages[theCharacterData.type].get_height())/2
        #画出角色图标
        self.informationBoard.blit(self.characterIconImages[theCharacterData.type],(padding,padding))
        #加载所需的文字
        tcgc_hp1 = linpg.fontRender("HP: ","white",fontSize)
        tcgc_hp2 = linpg.fontRender(str(theCharacterData.current_hp)+"/"+str(theCharacterData.max_hp),"black",fontSize)
        tcgc_action_point1 = linpg.fontRender("AP: ","white",fontSize)
        tcgc_action_point2 = linpg.fontRender(str(theCharacterData.current_action_point)+"/"+str(theCharacterData.max_action_point),"black",fontSize)
        tcgc_bullets_situation1 = linpg.fontRender("BP: ","white",fontSize)
        tcgc_bullets_situation2 = linpg.fontRender(str(theCharacterData.current_bullets)+"/"+str(theCharacterData.bullets_carried),"black",fontSize)
        #先画出hp,ap和bp的文字
        temp_posX = self.characterIconImages[theCharacterData.type].get_width()*2
        temp_posY = padding-fontSize*0.2
        self.informationBoard.blit(tcgc_hp1,(temp_posX,temp_posY))
        self.informationBoard.blit(tcgc_action_point1,(temp_posX,temp_posY+self.text_size*1.5))
        self.informationBoard.blit(tcgc_bullets_situation1,(temp_posX,temp_posY+self.text_size*3.0))
        #设置坐标和百分比
        temp_posX = self.characterIconImages[theCharacterData.type].get_width()*2.4
        temp_posY = padding
        self.hp_red.set_pos(temp_posX,temp_posY)
        self.hp_red.set_percentage(theCharacterData.hp_precentage)
        self.hp_green.set_pos(temp_posX,temp_posY)
        self.hp_green.set_percentage(theCharacterData.hp_precentage)
        self.action_point_blue.set_pos(temp_posX,temp_posY+self.text_size*1.5)
        self.action_point_blue.set_percentage(theCharacterData.current_action_point/theCharacterData.max_action_point)
        self.bullets_number_brown.set_pos(temp_posX,temp_posY+self.text_size*3)
        self.bullets_number_brown.set_percentage(theCharacterData.current_bullets/theCharacterData.magazine_capacity)
        #画出
        self.hp_green.draw(self.informationBoard)
        linpg.displayInCenter(tcgc_hp2,self.hp_green,temp_posX ,temp_posY,self.informationBoard)
        self.action_point_blue.draw(self.informationBoard)
        linpg.displayInCenter(tcgc_action_point2,self.action_point_blue,temp_posX ,temp_posY+self.text_size*1.5,self.informationBoard)
        self.bullets_number_brown.draw(self.informationBoard)
        linpg.displayInCenter(tcgc_bullets_situation2,self.bullets_number_brown,temp_posX ,temp_posY+self.text_size*3,self.informationBoard)
    def draw(self,screen,theCharacterData):
        if self.informationBoard == None:
            self.updateInformationBoard(screen.get_width()/96,theCharacterData)
        screen.blit(self.informationBoard,(0,screen.get_height()-self.boardImg.get_height()))

#计分板
class ResultBoard:
    def __init__(self,finalResult,font_size,is_win=True):
        resultTxt = linpg.get_lang("ResultBoard")
        self.x = int(font_size*10)
        self.y = int(font_size*10)
        self.txt_x = int(font_size*12)
        self.boardImg = linpg.loadImg("Assets/image/UI/score.png",(font_size*16,font_size*32))
        self.total_kills = linpg.fontRender(resultTxt["total_kills"]+": "+str(finalResult["total_kills"]),"white",font_size)
        self.total_time = linpg.fontRender(resultTxt["total_time"]+": "+str(time.strftime('%M:%S',finalResult["total_time"])),"white",font_size)
        self.total_rounds_txt = linpg.fontRender(resultTxt["total_rounds"]+": "+str(finalResult["total_rounds"]),"white",font_size)
        self.characters_down = linpg.fontRender(resultTxt["characters_down"]+": "+str(finalResult["times_characters_down"]),"white",font_size)
        self.player_rate = linpg.fontRender(resultTxt["rank"]+": "+"A","white",font_size)
        self.pressKeyContinue = linpg.fontRender(resultTxt["pressKeyContinue"],"white",font_size) if is_win else linpg.fontRender(resultTxt["pressKeyRestart"],"white",font_size)
    def draw(self,screen):
        screen.blit(self.boardImg,(self.x,self.y))
        screen.blit(self.total_kills,(self.txt_x ,300))
        screen.blit(self.total_time,(self.txt_x ,350))
        screen.blit(self.total_rounds_txt ,(self.txt_x ,400))
        screen.blit(self.characters_down,(self.txt_x ,450))
        screen.blit(self.player_rate,(self.txt_x ,500))
        screen.blit(self.pressKeyContinue,(self.txt_x ,700))

#章节标题(在加载时显示)
class LoadingTitle:
    def __init__(self,window_x,window_y,numChapter_txt,chapterId,chapterTitle_txt,chapterDesc_txt):
        self.black_bg = linpg.get_SingleColorSurface("black")
        title_chapterNum = linpg.fontRender(numChapter_txt.format(chapterId),"white",window_x/38)
        self.title_chapterNum = linpg.ImageSurface(title_chapterNum,(window_x-title_chapterNum.get_width())/2,window_y*0.37)
        title_chapterName = linpg.fontRender(chapterTitle_txt,"white",window_x/38)
        self.title_chapterName = linpg.ImageSurface(title_chapterName,(window_x-title_chapterName.get_width())/2,window_y*0.46)
        title_description = linpg.fontRender(chapterDesc_txt,"white",window_x/76)
        self.title_description = linpg.ImageSurface(title_description,(window_x-title_description.get_width())/2,window_y*0.6)
    def draw(self,screen,alpha=255):
        self.title_chapterNum.set_alpha(alpha)
        self.title_chapterName.set_alpha(alpha)
        self.title_description.set_alpha(alpha)
        self.black_bg.draw(screen)
        self.title_chapterNum.draw(screen)
        self.title_chapterName.draw(screen)
        self.title_description.draw(screen)