# cython: language_level=3
from .skill import *

class MapCreator(linpg.AbstractBattleSystem):
    def __init__(self,chapterType,chapterId,collection_name=None):
        linpg.AbstractBattleSystem.__init__(self,chapterType,chapterId,collection_name)
        self.fileLocation = "Data/{0}/chapter{1}_map.yaml".format(self.chapterType,self.chapterId) if self.chapterType == "main_chapter" else "Data/{0}/{1}/chapter{2}_map.yaml".format(self.chapterType,self.collection_name,self.chapterId)
    #加载角色的数据
    def __load_characters_data(self,mapFileData):
        #生成进程
        self._initial_characters_loader(mapFileData["character"],mapFileData["sangvisFerri"],"dev")
        #加载角色信息
        self._start_characters_loader()
        while self._is_characters_loader_alive():
            pass
    def initialize(self,screen):
        self.decorations_setting = linpg.loadConfig("Data/decorations.yaml","decorations")
        #载入地图数据
        mapFileData = linpg.loadConfig(self.fileLocation)
        #初始化角色信息
        self.__load_characters_data(mapFileData)
        #初始化地图
        self.MAP = mapFileData["map"]
        if self.MAP == None or len(self.MAP) == 0:
            SnowEnvImg = ["TileSnow01","TileSnow01ToStone01","TileSnow01ToStone02","TileSnow02","TileSnow02ToStone01","TileSnow02ToStone02"]
            block_y = 50
            block_x = 50
            default_map = [[SnowEnvImg[linpg.randomInt(0,5)] for a in range(block_x)] for i in range(block_y)]
            mapFileData["map"] = default_map
            linpg.saveConfig(self.fileLocation,mapFileData)
        else:
            block_y = len(mapFileData["map"])
            block_x = len(mapFileData["map"][0])
        #加载地图
        self._create_map(mapFileData)
        del mapFileData
        #加载背景图片
        self.envImgDict = {}
        for imgPath in glob.glob(r'Assets/image/environment/block/*.png'):
            self.envImgDict[os.path.basename(imgPath).replace(".png","")] = linpg.loadImg(imgPath,(self.MAP.block_width/3,None))
        #加载所有的装饰品
        self.decorationsImgDict = {}
        for imgPath in glob.glob(r'Assets/image/environment/decoration/*'):
            self.decorationsImgDict[os.path.basename(imgPath).replace(".png","")] = linpg.loadImg(imgPath,(self.MAP.block_width/5,None))
        #加载所有友方的角色的图片文件
        self.charactersImgDict = {}
        for imgPath in glob.glob(r'Assets/image/character/*'):
            img_name = os.path.basename(imgPath).replace(".png","")
            img = linpg.loadImg("{0}/wait/{1}_wait_0.png".format(imgPath,img_name),(self.MAP.block_width*1.5,None))
            pos = img.get_bounding_rect()
            self.charactersImgDict[img_name] = linpg.cropImg(img,(pos.left,pos.top),(pos.right,pos.top))
        #加载所有敌对角色的图片文件
        self.sangvisFerrisImgDict = {}
        for imgPath in glob.glob(r'Assets/image/sangvisFerri/*'):
            img_name = os.path.basename(imgPath).replace(".png","")
            img = linpg.loadImg("{0}/wait/{1}_wait_0.png".format(imgPath,img_name),(self.MAP.block_width*1.5,None))
            pos = img.get_bounding_rect()
            self.sangvisFerrisImgDict[img_name] = linpg.cropImg(img,(pos.left,pos.top),(pos.right,pos.top))
        #绿色方块/方块标准
        self.greenBlock = linpg.loadImg("Assets/image/UI/range/green.png",(self.MAP.block_width*0.8,None))
        self.greenBlock.set_alpha(150)
        self.redBlock = linpg.loadImg("Assets/image/UI/range/red.png",(self.MAP.block_width*0.8,None))
        self.redBlock.set_alpha(150)
        self.deleteMode = False
        self.object_to_put_down = None
        #加载容器图片
        self.UIContainer = linpg.loadDynamicImage(
            "Assets/image/UI/container.png",
            (0,screen.get_height()),
            (0,screen.get_height()*0.75),
            (0,screen.get_height()*0.25/10),
            int(screen.get_width()*0.8),
            int(screen.get_height()*0.25)
            )
        self.UIContainerButton = linpg.loadImage(
            "Assets/image/UI/container_button.png",
            (screen.get_width()*0.33,-screen.get_height()*0.05),
            int(screen.get_width()*0.14),
            int(screen.get_height()*0.06)
            )
        widthTmp = int(screen.get_width()*0.2)
        self.UIContainerRight = linpg.loadDynamicImage(
            "Assets/image/UI/container.png",
            (screen.get_width()*0.8+widthTmp,0),
            (screen.get_width()*0.8,0),
            (widthTmp/10,0),
            widthTmp,
            screen.get_height()
            )
        self.UIContainerRightButton = linpg.loadImage(
            "Assets/image/UI/container_button.png",
            (-screen.get_width()*0.03,screen.get_height()*0.4),
            int(screen.get_width()*0.04),
            int(screen.get_height()*0.2)
            )
        self.UIContainerRight.rotate(90)
        self.UIContainerRightButton.rotate(90)
        #UI按钮
        self.UIButton = {}
        UI_x = self.MAP.block_width*0.5
        UI_y = int(screen.get_height()*0.02)
        UI_height = int(self.MAP.block_width*0.3)
        self.UIButton["save"] = linpg.ButtonWithFadeInOut(
            "Assets/image/UI/menu.png",
            linpg.get_lang("General","save"),
            "black",100,UI_x,UI_y,UI_height
            )
        UI_x += self.UIButton["save"].get_width()+UI_height
        self.UIButton["back"] = linpg.ButtonWithFadeInOut(
            "Assets/image/UI/menu.png",
            linpg.get_lang("General","back"),
            "black",100,UI_x,UI_y,UI_height
            )
        UI_x += self.UIButton["back"].get_width()+UI_height
        self.UIButton["delete"] = linpg.ButtonWithFadeInOut(
            "Assets/image/UI/menu.png",
            linpg.get_lang("MapCreator","delete"),
            "black",100,UI_x,UI_y,UI_height
            )
        UI_x += self.UIButton["delete"].get_width()+UI_height
        self.UIButton["reload"] = linpg.ButtonWithFadeInOut(
            "Assets/image/UI/menu.png",
            linpg.get_lang("MapCreator","reload"),
            "black",100,UI_x,UI_y,UI_height
            )
        #数据控制器
        self.data_to_edit = None
        #其他函数
        self.UI_local_x = 0
        self.UI_local_y = 0
        #读取地图原始文件
        self.originalData = linpg.loadConfig(self.fileLocation)
    def draw(self,screen):
        self._update_event()
        mouse_x,mouse_y = linpg.controller.get_pos()
        block_get_click = self.MAP.calBlockInMap(mouse_x,mouse_y)
        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.object_to_put_down = None
                    self.data_to_edit = None
                    self.deleteMode = False
                self._check_key_down(event)
            elif event.type == pygame.KEYUP:
                self._check_key_up(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                #上下滚轮-放大和缩小地图
                if linpg.is_hover(self.UIContainerRight) and event.button == 4 and self.UI_local_y<0:
                    self.UI_local_y += screen.get_height()*0.1
                elif linpg.is_hover(self.UIContainerRight) and event.button == 5:
                    self.UI_local_y -= screen.get_height()*0.1
                elif linpg.is_hover(self.UIContainerRightButton,None,self.UIContainerRight.x):
                    self.UIContainerRight.switch()
                    self.UIContainerRightButton.flip(True,False)
                elif linpg.is_hover(self.UIContainerButton,None,0,self.UIContainer.y):
                    self.UIContainer.switch()
                    self.UIContainerButton.flip(False,True)
                elif linpg.is_hover(self.UIContainer):
                    #上下滚轮-放大和缩小地图
                    if event.button == 4 and self.UI_local_x<0:
                        self.UI_local_x += screen.get_width()*0.05
                    elif event.button == 5:
                        self.UI_local_x -= screen.get_width()*0.05
                elif self.deleteMode == True and block_get_click != None:
                    #查看当前位置是否有装饰物
                    decoration = self.MAP.find_decoration_on((block_get_click["x"],block_get_click["y"]))
                    #如果发现有冲突的装饰物
                    if decoration != None:
                        self.MAP.remove_decoration(decoration)
                    else:
                        any_chara_replace = None
                        for key,value in linpg.dicMerge(self.alliances_data,self.enemies_data).items():
                            if value.x == block_get_click["x"] and value.y == block_get_click["y"]:
                                any_chara_replace = key
                                break
                        if any_chara_replace != None:
                            if any_chara_replace in self.alliances_data:
                                self.alliances_data.pop(any_chara_replace)
                                self.originalData["character"].pop(any_chara_replace)
                            elif any_chara_replace in self.enemies_data:
                                self.enemies_data.pop(any_chara_replace)
                                self.originalData["sangvisFerri"].pop(any_chara_replace)
                elif linpg.is_hover(self.UIButton["save"]) and self.object_to_put_down == None and self.deleteMode == False:
                    linpg.saveConfig(self.fileLocation,self.originalData)
                elif linpg.is_hover(self.UIButton["back"]) and self.object_to_put_down == None and self.deleteMode == False:
                    self._isPlaying = False
                    break
                elif linpg.is_hover(self.UIButton["delete"]) and self.object_to_put_down == None and self.deleteMode == False:
                    self.object_to_put_down = None
                    self.data_to_edit = None
                    self.deleteMode = True
                elif linpg.is_hover(self.UIButton["reload"]) and self.object_to_put_down == None and self.deleteMode == False:
                    tempLocal_x,tempLocal_y = self.MAP.getPos()
                    #读取地图数据
                    mapFileData = linpg.loadConfig(self.fileLocation)
                    #初始化角色信息
                    self.__load_characters_data(mapFileData)
                    #加载地图
                    self._create_map(mapFileData)
                    del mapFileData
                    self.MAP.setPos(tempLocal_x,tempLocal_y)
                    #读取地图
                    self.originalData = linpg.loadConfig(self.fileLocation)
                else:
                    if pygame.mouse.get_pressed()[0] and block_get_click != None:
                        if self.object_to_put_down != None:
                            if self.object_to_put_down["type"] == "block":
                                self.originalData["map"][block_get_click["y"]][block_get_click["x"]] = self.object_to_put_down["id"]
                                self.MAP.update_block(block_get_click,self.object_to_put_down["id"])
                            elif self.object_to_put_down["type"] == "decoration":
                                #查看当前位置是否有装饰物
                                decoration = self.MAP.find_decoration_on((block_get_click["x"],block_get_click["y"]))
                                #如果发现有冲突的装饰物
                                if decoration != None:
                                    self.MAP.remove_decoration(decoration)
                                decorationType = self.decorations_setting[self.object_to_put_down["id"]]
                                if decorationType not in self.originalData["decoration"]:
                                    self.originalData["decoration"][decorationType] = {}
                                the_id = 0
                                while self.object_to_put_down["id"]+"_"+str(the_id) in self.originalData["decoration"][decorationType]:
                                    the_id+=1
                                nameTemp = self.object_to_put_down["id"]+"_"+str(the_id)
                                self.originalData["decoration"][decorationType][nameTemp] = {"image": self.object_to_put_down["id"],"x": block_get_click["x"],"y": block_get_click["y"]}
                                self.MAP.load_decorations(self.originalData["decoration"])
                            elif self.object_to_put_down["type"] == "character" or self.object_to_put_down["type"] == "sangvisFerri":
                                any_chara_replace = None
                                for key,value in linpg.dicMerge(self.alliances_data,self.enemies_data).items():
                                    if value.x == block_get_click["x"] and value.y == block_get_click["y"]:
                                        any_chara_replace = key
                                        break
                                if any_chara_replace != None:
                                    if any_chara_replace in self.alliances_data:
                                        self.alliances_data.pop(any_chara_replace)
                                        self.originalData["character"].pop(any_chara_replace)
                                    elif any_chara_replace in self.enemies_data:
                                        self.enemies_data.pop(any_chara_replace)
                                        self.originalData["sangvisFerri"].pop(any_chara_replace)
                                the_id = 0
                                if self.object_to_put_down["type"] == "character":
                                    while self.object_to_put_down["id"]+"_"+str(the_id) in self.alliances_data:
                                        the_id+=1
                                    nameTemp = self.object_to_put_down["id"]+"_"+str(the_id)
                                    self.originalData["character"][nameTemp] = {
                                        "bullets_carried": 100,
                                        "type": self.object_to_put_down["id"],
                                        "x": block_get_click["x"],
                                        "y": block_get_click["y"]
                                    }
                                    self.alliances_data[nameTemp] = linpg.FriendlyCharacter(self.originalData["character"][nameTemp],self.DATABASE[self.originalData["character"][nameTemp]["type"]],"dev")
                                elif self.object_to_put_down["type"] == "sangvisFerri":
                                    while self.object_to_put_down["id"]+"_"+str(the_id) in self.enemies_data:
                                        the_id+=1
                                    nameTemp = self.object_to_put_down["id"]+"_"+str(the_id)
                                    self.originalData["sangvisFerri"][nameTemp] = {
                                        "type": self.object_to_put_down["id"],
                                        "x": block_get_click["x"],
                                        "y": block_get_click["y"]
                                    }
                                    self.enemies_data[nameTemp] = linpg.HostileCharacter(self.originalData["sangvisFerri"][nameTemp],self.DATABASE[self.originalData["sangvisFerri"][nameTemp]["type"]],"dev")
        #其他移动的检查
        self._check_right_click_move(mouse_x,mouse_y)
        self._check_jostick_events()

        #画出地图
        self._display_map(screen)

        if block_get_click != None and not linpg.is_hover(self.UIContainerRight) and not linpg.is_hover(self.UIContainer):
            if self.deleteMode == True:
                xTemp,yTemp = self.MAP.calPosInMap(block_get_click["x"],block_get_click["y"])
                linpg.drawImg(self.redBlock,(xTemp+self.MAP.block_width*0.1,yTemp),screen)
            elif self.object_to_put_down != None:
                xTemp,yTemp = self.MAP.calPosInMap(block_get_click["x"],block_get_click["y"])
                linpg.drawImg(self.greenBlock,(xTemp+self.MAP.block_width*0.1,yTemp),screen)

        #角色动画
        for key in self.alliances_data:
            self.alliances_data[key].draw(screen,self.MAP)
            if self.object_to_put_down == None and pygame.mouse.get_pressed()[0] and self.alliances_data[key].x == int(mouse_x/self.greenBlock.get_width()) and self.alliances_data[key].y == int(mouse_y/self.greenBlock.get_height()):
                self.data_to_edit = self.alliances_data[key]
        for key in self.enemies_data:
            self.enemies_data[key].draw(screen,self.MAP)
            if self.object_to_put_down == None and pygame.mouse.get_pressed()[0] and self.enemies_data[key].x == int(mouse_x/self.greenBlock.get_width()) and self.enemies_data[key].y == int(mouse_y/self.greenBlock.get_height()):
                self.data_to_edit = self.enemies_data[key]

        #展示设施
        self._display_decoration(screen)

        #画出UI
        self.UIContainerButton.display(screen,(0,self.UIContainer.y))
        self.UIContainer.draw(screen)
        self.UIContainerRightButton.display(screen,(self.UIContainerRight.x,0))
        self.UIContainerRight.draw(screen)
        for Image in self.UIButton:
            linpg.is_hover(self.UIButton[Image])
            self.UIButton[Image].draw(screen)

        #显示所有可放置的友方角色
        i=0
        tempY = self.UIContainer.y+self.MAP.block_width*0.2
        for key in self.charactersImgDict:
            tempX = self.UIContainer.x+self.MAP.block_width*i*0.6+self.UI_local_x
            if 0 <= tempX <= self.UIContainer.get_width()*0.9:
                linpg.drawImg(self.charactersImgDict[key],(tempX,tempY),screen)
                if pygame.mouse.get_pressed()[0] and linpg.is_hover(self.charactersImgDict[key],(tempX,tempY)):
                    self.object_to_put_down = {"type":"character","id":key}
            elif tempX > self.UIContainer.get_width()*0.9:
                break
            i+=1
        i=0
        tempY += self.MAP.block_width*0.4
        #显示所有可放置的敌方角色
        for key in self.sangvisFerrisImgDict:
            tempX = self.UIContainer.x+self.MAP.block_width*i*0.6+self.UI_local_x
            if 0 <= tempX <= self.UIContainer.get_width()*0.9:
                linpg.drawImg(self.sangvisFerrisImgDict[key],(tempX,tempY),screen)
                if pygame.mouse.get_pressed()[0] and linpg.is_hover(self.sangvisFerrisImgDict[key],(tempX,tempY)):
                    self.object_to_put_down = {"type":"sangvisFerri","id":key}
            elif tempX > self.UIContainer.get_width()*0.9:
                break
            i+=1
        
        #显示所有可放置的环境方块
        i=0
        for img_name in self.envImgDict:
            posY = self.UIContainerRight.y+self.MAP.block_width*int(i/4)+self.UI_local_y
            if screen.get_height()*0.05<posY<screen.get_height()*0.9:
                posX = self.UIContainerRight.x+self.MAP.block_width/6+self.MAP.block_width/2.3*(i%4)
                linpg.drawImg(self.envImgDict[img_name],(posX,posY),screen)
                if pygame.mouse.get_pressed()[0] and linpg.is_hover(self.envImgDict[img_name],(posX,posY)):
                    self.object_to_put_down = {"type":"block","id":img_name}
            i+=1
        for img_name in self.decorationsImgDict:
            posY = self.UIContainerRight.y+self.MAP.block_width*int(i/4)+self.UI_local_y
            if screen.get_height()*0.05<posY<screen.get_height()*0.9:
                posX = self.UIContainerRight.x+self.MAP.block_width/6+self.MAP.block_width/2.3*(i%4)
                linpg.drawImg(self.decorationsImgDict[img_name],(posX,posY),screen)
                if pygame.mouse.get_pressed()[0] and linpg.is_hover(self.decorationsImgDict[img_name],(posX,posY)):
                    self.object_to_put_down = {"type":"decoration","id":img_name}
            i+=1
        
        #跟随鼠标显示即将被放下的物品
        if self.object_to_put_down != None:
            if self.object_to_put_down["type"] == "block":
                linpg.drawImg(self.envImgDict[self.object_to_put_down["id"]],(mouse_x,mouse_y),screen)
            elif self.object_to_put_down["type"] == "decoration":
                linpg.drawImg(self.decorationsImgDict[self.object_to_put_down["id"]],(mouse_x,mouse_y),screen)
            elif self.object_to_put_down["type"] == "character":
                linpg.drawImg(self.charactersImgDict[self.object_to_put_down["id"]],(mouse_x,mouse_y),screen)
            elif self.object_to_put_down["type"] == "sangvisFerri":
                linpg.drawImg(self.sangvisFerrisImgDict[self.object_to_put_down["id"]],(mouse_x,mouse_y),screen)
        
        #显示即将被编辑的数据
        if self.data_to_edit != None:
            linpg.drawImg(linpg.fontRender("action points: "+str(self.data_to_edit.max_action_point),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8),screen)
            linpg.drawImg(linpg.fontRender("attack range: "+str(self.data_to_edit.attack_range),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20),screen)
            linpg.drawImg(linpg.fontRender("current bullets: "+str(self.data_to_edit.current_bullets),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20*2),screen)
            linpg.drawImg(linpg.fontRender("magazine capacity: "+str(self.data_to_edit.magazine_capacity),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20*3),screen)
            linpg.drawImg(linpg.fontRender("max hp: "+str(self.data_to_edit.max_hp),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20*4),screen)
            linpg.drawImg(linpg.fontRender("effective range: "+str(self.data_to_edit.effective_range),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20*5),screen)
            linpg.drawImg(linpg.fontRender("max damage: "+str(self.data_to_edit.max_damage),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20*6),screen)
            linpg.drawImg(linpg.fontRender("min damage: "+str(self.data_to_edit.min_damage),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20*7),screen)
            linpg.drawImg(linpg.fontRender("x: "+str(self.data_to_edit.x),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20*8),screen)
            linpg.drawImg(linpg.fontRender("y: "+str(self.data_to_edit.y),"black",15),(screen.get_width()*0.91,screen.get_height()*0.8+20*9),screen)

        linpg.display.flip()