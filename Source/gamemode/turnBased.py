# cython: language_level=3
from .towerDefense import *

#回合制游戏战斗系统
class TurnBasedBattleSystem(BattleSystem):
    def __init__(self):
        super().__init__()
        #被选中的角色
        self.characterGetClick = None
        self.enemiesGetAttack:dict = {}
        self.action_choice = None
        #是否不要画出用于表示范围的方块
        self.__if_draw_range = True
        self.areaDrawColorBlock:dict = {"green":[],"red":[],"yellow":[],"blue":[],"orange":[]}
        #是否在战斗状态-战斗loop
        self.__is_battle_mode:bool = False
        #是否在等待
        self.__is_waiting:bool = True
        #谁的回合
        self.whose_round = "sangvisFerrisToPlayer"
        self.rightClickCharacterAlpha = None
        #技能对象
        self.skill_target = None
        #被按到的按键
        self.buttonGetHover = None
        #被救助的那个角色
        self.friendGetHelp = None
        #AI系统正在操控的敌对角色ID
        self.enemies_in_control_id:int = 0
        #所有敌对角色的名字列表
        self.sangvisFerris_name_list:list = []
        #战斗状态数据
        self.resultInfo = {
            "total_rounds" : 1,
            "total_kills" : 0,
            "total_time" : time.time(),
            "times_characters_down" : 0
        }
        #储存角色受到伤害的文字surface
        self.damage_do_to_characters = {}
        self.txt_alpha:int = None
        # 移动路径
        self.the_route = []
        #上个回合因为暴露被敌人发现的角色
        #格式：角色：[x,y]
        self.the_characters_detected_last_round:dict = {}
        #敌人的指令
        self.enemy_instructions = None
        #敌人当前需要执行的指令
        self.current_instruction = None
        #积分栏的UI模块
        self.ResultBoardUI = None
        #对话-动作是否被设置
        self.__dialog_is_route_generated:bool = False
        #可以互动的物品列表
        self.thingsCanReact:list = []
        #需要救助的角色列表
        self.friendsCanSave:list = []
        #是否从存档中加载的数据-默认否
        self.__load_from_save:bool = False
        #暂停菜单
        self.pause_menu = linpg.PauseMenu()
        #每次需要更新的物品
        self.__items_to_blit:list = []
        self.__max_item_weight:int = 0
    """Quick Reference"""
    #正在控制的角色
    @property
    def characterInControl(self) -> object: return self.alliances_data[self.characterGetClick]
    #正在控制的铁血角色
    @property
    def enemyInControl(self) -> object: return self.enemies_data[self.sangvisFerris_name_list[self.enemies_in_control_id]]
    """加载与储存"""
    #从存档中加载游戏进程
    def load(self, screen:pygame.Surface) -> None:
        DataTmp = linpg.loadConfig("Save/save.yaml")
        if DataTmp["type"] == "battle":
            self._initialize(DataTmp["chapter_type"], DataTmp["chapter_id"], DataTmp["project_name"])
            self._initial_characters_loader(DataTmp["griffin"],DataTmp["sangvisFerri"])
            self.MAP = DataTmp["MAP"]
            self.dialogKey = DataTmp["dialogKey"]
            self.dialogData = DataTmp["dialogData"]
            self.resultInfo = DataTmp["resultInfo"]
        else:
            raise Exception('Error: Cannot load the data from the "save.yaml" file because the file type does not match')
        #因为地图模块已被加载，只需加载图片即可
        self.MAP.load_env_img((round(screen.get_width()/10),round(screen.get_height()/10)))
        self.__load_from_save = True
        self.__process_data(screen)
    def new(self, screen:pygame.Surface, chapterType:str, chapterId:int, projectName:str=None):
        self._initialize(chapterType, chapterId, projectName)
        self.__process_data(screen)
    #加载游戏进程
    def __process_data(self, screen:pygame.Surface) -> None:
        self.window_x,self.window_y = screen.get_size()
        #生成标准文字渲染器
        self.FONTSIZE = int(self.window_x/76)
        self.FONT = linpg.createFont(self.FONTSIZE)
        #加载按钮的文字
        self.selectMenuUI = SelectMenu()
        self.battleModeUiTxt = linpg.get_lang("Battle_UI")
        self.warnings_to_display = WarningSystem(int(screen.get_height()*0.03))
        loading_info = linpg.get_lang("LoadingTxt")
        #加载剧情
        DataTmp = linpg.loadConfig(
            os.path.join(
                "Data", self._chapter_type,
                "chapter{0}_dialogs_{1}.yaml".format(self._chapter_id,linpg.get_setting('Language'))
                ) if self._project_name is None else os.path.join(
                    "Data", self._chapter_type, self._project_name,
                    "chapter{0}_dialogs_{1}.yaml".format(self._chapter_id,linpg.get_setting('Language'))
                    )
        )
        #如果暂时没有翻译
        if "title" not in DataTmp: DataTmp["title"] = linpg.get_lang("Global", "no_translation")
        if "description" not in DataTmp: DataTmp["description"] = linpg.get_lang("Global", "no_translation")
        if "battle_info" not in DataTmp: DataTmp["battle_info"] = linpg.loadConfig(r"Data/chapter_dialogs_example.yaml", "battle_info")
        if "dialog_during_battle" not in DataTmp: DataTmp["dialog_during_battle"] = {}
        #章节标题显示
        self.infoToDisplayDuringLoading = LoadingTitle(
            self.window_x,
            self.window_y,
            self.battleModeUiTxt["numChapter"],
            self._chapter_id,DataTmp["title"],DataTmp["description"]
        )
        self.battleMode_info = DataTmp["battle_info"]
        self.dialog_during_battle = DataTmp["dialog_during_battle"]
        #正在加载的gif动态图标
        nowLoadingIcon = linpg.loadGif(
            "Assets/image/UI/sv98_walking.gif",
            (self.window_x*0.7,self.window_y*0.83),
            (self.window_x*0.003*15,self.window_x*0.003*21)
        )
        #渐入效果
        for i in range(1,255,2):
            self.infoToDisplayDuringLoading.draw(screen,i)
            linpg.display.flip()
        #开始加载地图场景
        self.infoToDisplayDuringLoading.draw(screen)
        now_loading = self.FONT.render(loading_info["now_loading_map"],linpg.get_antialias(),(255,255,255))
        screen.blit(now_loading,(self.window_x*0.75,self.window_y*0.9))
        nowLoadingIcon.draw(screen)
        linpg.display.flip()
        #读取并初始化章节信息
        DataTmp = linpg.loadConfig(self.get_map_file_location())
        #背景音乐路径
        self._background_music_folder_path:str = "Assets/music"
        #设置背景音乐
        self.set_bgm(os.path.join(self._background_music_folder_path,DataTmp["background_music"]))
        #加载胜利目标
        self.mission_objectives = DataTmp["mission_objectives"]
        #初始化天气和环境的音效 -- 频道1
        self.environment_sound = linpg.SoundManagement(1)
        self.weatherController = None
        if DataTmp["weather"] is not None:
            self.environment_sound.add(os.path.join("Assets/sound/environment","{}.ogg".format(DataTmp["weather"])))
            self.weatherController = linpg.WeatherSystem(DataTmp["weather"],self.window_x,self.window_y)
        #加载对话信息
        self.dialogInfo = DataTmp["dialogs"]
        if not self.__load_from_save:
            self._create_map(DataTmp)
            #加载对应角色所需的图片
            self._initial_characters_loader(DataTmp["character"],DataTmp["sangvisFerri"])
            #查看是否有战斗开始前的对话
            if "initial" not in self.dialogInfo or self.dialogInfo["initial"] is None:
                self.dialogKey = None
            else:
                self.dialogKey = self.dialogInfo["initial"]
            self.dialogData = None
        #加载角色信息
        self._start_characters_loader()
        while self._is_characters_loader_alive():
            self.infoToDisplayDuringLoading.draw(screen)
            now_loading = self.FONT.render(loading_info["now_loading_characters"]+"({}/{})".format(self.characters_loaded,self.characters_total),linpg.get_antialias(),(255,255,255))
            screen.blit(now_loading,(self.window_x*0.75,self.window_y*0.9))
            nowLoadingIcon.draw(screen)
            linpg.display.flip()
        #计算光亮区域 并初始化地图
        self._calculate_darkness()
        #开始加载关卡设定
        self.infoToDisplayDuringLoading.draw(screen)
        now_loading = self.FONT.render(loading_info["now_loading_level"],linpg.get_antialias(),linpg.findColorRGBA("white"))
        screen.blit(now_loading,(self.window_x*0.75,self.window_y*0.9))
        nowLoadingIcon.draw(screen)
        linpg.display.flip()
        #加载UI:
        #加载结束回合的图片
        self.end_round_txt = self.FONT.render(linpg.get_lang("Battle_UI","endRound"),linpg.get_antialias(),linpg.findColorRGBA("white"))
        self.end_round_button = linpg.loadImage("Assets/image/UI/end_round_button.png",(self.window_x*0.8,self.window_y*0.7),self.end_round_txt.get_width()*2,self.end_round_txt.get_height()*2.5)
        #加载子弹图片
        #bullet_img = loadImg("Assets/image/UI/bullet.png", get_block_width()/6, self.MAP.block_height/12)
        #加载显示获取到补给后的信息栏
        supply_board_width:int = int(self.window_x/3)
        supply_board_height:int = int(self.window_y/12)
        supply_board_x:int = int((self.window_x-supply_board_width)/2)
        self.supply_board = linpg.loadDynamicImage(
            "Assets/image/UI/score.png",
            (supply_board_x,-supply_board_height),
            (supply_board_x,0),
            (0,int(self.window_y*0.005)),
            supply_board_width, supply_board_height
        )
        self.supply_board.items = []
        self.supply_board.stayingTime = 0
        #用于表示范围的方框图片
        self.range_ui_images = {
            "green" : linpg.StaticImageSurface("Assets/image/UI/range/green.png",0,0),
            "red" : linpg.StaticImageSurface("Assets/image/UI/range/red.png",0,0),
            "yellow": linpg.StaticImageSurface("Assets/image/UI/range/yellow.png",0,0),
            "blue": linpg.StaticImageSurface("Assets/image/UI/range/blue.png",0,0),
            "orange": linpg.StaticImageSurface("Assets/image/UI/range/orange.png",0,0),
        }
        for key in self.range_ui_images:
            self.range_ui_images[key].set_width_with_size_locked(self.MAP.block_width*0.8)
        #角色信息UI管理
        self.characterInfoBoardUI = CharacterInfoBoard(self.window_x,self.window_y)
        #加载对话框图片
        self.dialoguebox_up = linpg.DialogBox("Assets/image/UI/dialoguebox.png",self.window_x,self.window_y/2-self.window_y*0.35,self.window_x*0.3,self.window_y*0.15,self.FONTSIZE)
        self.dialoguebox_up.flip()
        self.dialoguebox_down = linpg.DialogBox("Assets/image/UI/dialoguebox.png",-self.window_x*0.3,self.window_y/2+self.window_y*0.2,self.window_x*0.3,self.window_y*0.15,self.FONTSIZE)
        #-----加载音效-----
        #行走的音效 -- 频道0
        self.footstep_sounds = linpg.SoundManagement(0)
        for walkingSoundPath in glob.glob(r'Assets/sound/snow/*.wav'):
            self.footstep_sounds.add(walkingSoundPath)
        #更新所有音效的音量
        self.__update_sound_volume()
        #攻击的音效 -- 频道2
        self.attackingSounds = linpg.AttackingSoundManager(linpg.get_setting("Sound","sound_effects"),2)
        #切换回合时的UI
        self.RoundSwitchUI = RoundSwitch(self.window_x,self.window_y,self.battleModeUiTxt)
        #关卡背景介绍信息文字
        for i in range(len(self.battleMode_info)):
            self.battleMode_info[i] = self.FONT.render(self.battleMode_info[i],linpg.get_antialias(),(255,255,255))
        #显示章节信息
        for a in range(0,250,2):
            self.infoToDisplayDuringLoading.draw(screen)
            for i in range(len(self.battleMode_info)):
                self.battleMode_info[i].set_alpha(a)
                screen.blit(self.battleMode_info[i],(self.window_x/20,self.window_y*0.75+self.battleMode_info[i].get_height()*1.2*i))
                if i == 1:
                    temp_secode = self.FONT.render(time.strftime(":%S", time.localtime()),linpg.get_antialias(),(255,255,255))
                    temp_secode.set_alpha(a)
                    screen.blit(temp_secode,(self.window_x/20+self.battleMode_info[i].get_width(),self.window_y*0.75+self.battleMode_info[i].get_height()*1.2))
            linpg.display.flip()
    #返回需要保存数据
    def _get_data_need_to_save(self) -> dict: return linpg.dicMerge(
        self.get_data_of_parent_game_system(),{
            "type": "battle",
            "griffin": self.griffinCharactersData,
            "sangvisFerri": self.sangvisFerrisData,
            "MAP": self.MAP,
            "dialogKey": self.dialogKey,
            "dialogData": self.dialogData,
            "resultInfo": self.resultInfo,
            "timeStamp": time.strftime(":%S", time.localtime())
            }
        )
    """画面"""
    #新增需要在屏幕上画出的物品
    def __add_on_screen_object(self, image:pygame.Surface, weight:int=-1, pos:Union[tuple,list]=(0,0), offSet:Union[tuple,list]=(0,0)) -> None:
        if weight < 0:
            self.__max_item_weight += 1
            weight = self.__max_item_weight
        elif weight > self.__max_item_weight:
            self.__max_item_weight = weight
        self.__items_to_blit.append(linpg.ItemNeedBlit(image,weight,pos,offSet))
    #更新屏幕
    def __update_scene(self, screen:pygame.Surface) -> None:
        self.__items_to_blit.sort()
        for item in self.__items_to_blit:
            item.draw(screen)
        self.__items_to_blit.clear()
        self.__max_item_weight = 0
    #胜利失败判定
    def __check_whether_player_win_or_lost(self) -> None:
        #常规
        """检测失败条件"""
        #如果有回合限制
        if "round_limitation" in self.mission_objectives and self.mission_objectives["round_limitation"] is not None \
            and self.mission_objectives["round_limitation"] > 0 and self.resultInfo["total_rounds"] > self.mission_objectives["round_limitation"]:
            self.whose_round = "result_fail"
        #如果不允许失去任何一位同伴
        if "allow_any_one_die" not in self.mission_objectives or not self.mission_objectives["allow_any_one_die"]:
            for character in self.alliances_data:
                if not isinstance(self.alliances_data[character].dying,bool) and self.alliances_data[character].dying == 0:
                    self.whose_round = "result_fail"
                    break
        """检测胜利条件"""
        #歼灭模式
        if self.mission_objectives["type"] == "annihilation":
            #检测是否所有敌人都已经被消灭
            if "target" not in self.mission_objectives or self.mission_objectives["target"] is None:
                if len(self.sangvisFerrisData) == 0:
                    self.characterGetClick = None
                    self.__if_draw_range = False
                    self.whose_round = "result_win"
                else:
                    pass
            #检测是否特定敌人已经被消灭
            elif isinstance(self.mission_objectives["target"],str) and self.mission_objectives["target"] not in self.enemies_data:
                self.whose_round = "result_win"
            #检测是否所有给定的目标都已经被歼灭
            elif isinstance(self.mission_objectives["target"],(list,tuple)):
                find_one = False
                for key in self.alliances_data:
                    if key in self.mission_objectives["target"]:
                        find_one = True
                        break
                if not find_one: self.whose_round = "result_win"
    #更新音量
    def __update_sound_volume(self) -> None:
        self.footstep_sounds.set_volume(linpg.get_setting("Sound","sound_effects")/100)
        self.environment_sound.set_volume(linpg.get_setting("Sound","sound_environment")/100.0)
        self.set_bgm_volume(linpg.get_setting("Sound","background_music")/100.0)
    #更新语言
    def updated_language(self, screen) -> None:
        super().updated_language()
        self.pause_menu.initialize(screen)
        self.selectMenuUI = SelectMenu()
        self.battleModeUiTxt = linpg.get_lang("Battle_UI")
        self.RoundSwitchUI = RoundSwitch(self.window_x,self.window_y,self.battleModeUiTxt)
        self.end_round_txt = self.FONT.render(linpg.get_lang("Battle_UI","endRound"),linpg.get_antialias(),linpg.findColorRGBA("white"))
        self.end_round_button = linpg.loadImage("Assets/image/UI/end_round_button.png",(self.window_x*0.8,self.window_y*0.7),self.end_round_txt.get_width()*2,self.end_round_txt.get_height()*2.5)
        self.warnings_to_display = WarningSystem(int(screen.get_height()*0.03))
        self.dialog_during_battle = linpg.loadConfig(
            os.path.join(
                "Data", self._chapter_type,
                "chapter{0}_dialogs_{1}.yaml".format(self._chapter_id,linpg.get_setting('Language'))
                ) if self._project_name is None else os.path.join(
                    "Data", self._chapter_type, self._project_name,
                    "chapter{0}_dialogs_{1}.yaml".format(self._chapter_id,linpg.get_setting('Language'))
                    ),
            "dialog_during_battle"
        )
        if not self.__is_battle_mode:
            self.dialoguebox_up.reset()
            self.dialoguebox_down.reset()
    #警告某个角色周围的敌人
    def __alert_enemy_around(self, name:str, value:int=10) -> None:
        enemies_need_check:list = []
        for key in self.sangvisFerrisData:
            if self.sangvisFerrisData[key].can_attack(self.griffinCharactersData[name]):
                self.sangvisFerrisData[key].alert(value)
                self.characterInControl.notice(value)
                enemies_need_check.append(key)
        for key in enemies_need_check:
            if self.sangvisFerrisData[key].is_alert:
                for character in self.griffinCharactersData:
                    if self.sangvisFerrisData[key].can_attack(self.griffinCharactersData[character]):
                        self.griffinCharactersData[character].notice(100)
    #重置用于储存需要画出范围方块的字典
    def reset_areaDrawColorBlock(self):
        for value in self.areaDrawColorBlock.values(): value.clear()
    #切换回合
    def __switch_round(self, screen:pygame.Surface) -> None:
        if self.whose_round == "playerToSangvisFerris" or self.whose_round == "sangvisFerrisToPlayer":
            if self.RoundSwitchUI.draw(screen,self.whose_round,self.resultInfo["total_rounds"]):
                if self.whose_round == "playerToSangvisFerris":
                    self.enemies_in_control_id = 0
                    self.sangvisFerris_name_list.clear()
                    any_is_alert = False
                    for every_chara in self.sangvisFerrisData:
                        if self.sangvisFerrisData[every_chara].is_alive():
                            self.sangvisFerris_name_list.append(every_chara)
                            if self.sangvisFerrisData[every_chara].is_alert: any_is_alert = True
                    #如果有一个铁血角色已经处于完全察觉的状态，则让所有铁血角色进入警觉状态
                    if any_is_alert:
                        for every_chara in self.sangvisFerrisData:
                            self.sangvisFerrisData[every_chara].alert(100)
                    #让倒地的角色更接近死亡
                    for every_chara in self.griffinCharactersData:
                        if self.griffinCharactersData[every_chara].dying is not False:
                            self.griffinCharactersData[every_chara].dying -= 1
                    #现在是铁血的回合！
                    self.whose_round = "sangvisFerris"
                elif self.whose_round == "sangvisFerrisToPlayer":
                    for key in self.griffinCharactersData:
                        self.griffinCharactersData[key].reset_action_point()
                        if not self.griffinCharactersData[key].is_detected:
                            value_reduce = int(self.griffinCharactersData[key].detection*0.3)
                            if value_reduce < 15: value_reduce = 15
                            self.griffinCharactersData[key].notice(0-value_reduce)
                    for key in self.sangvisFerrisData:
                        if not self.sangvisFerrisData[key].is_alert:
                            value_reduce = int(self.sangvisFerrisData[key].vigilance*0.2)
                            if value_reduce < 10: value_reduce = 10
                            self.sangvisFerrisData[key].alert(0-value_reduce)
                    #到你了，Good luck, you need it!
                    self.whose_round = "player"
                    self.resultInfo["total_rounds"] += 1
    #技能
    def __skill(self, characterName:str, pos_click:any, the_skill_cover_area:any, action:str="detect", skill_target:str=None, damage_do_to_character:dict=None) -> any:
        if action == "detect":
            skill_target = None
            if self.griffinCharactersData[characterName].type == "gsh-18":
                for character in self.griffinCharactersData:
                    if self.griffinCharactersData[character].on_pos(pos_click):
                        skill_target = character
                        break
            elif self.griffinCharactersData[characterName].type == "asval" or self.griffinCharactersData[characterName].type == "pp1901" or self.griffinCharactersData[characterName].type == "sv-98":
                for enemies in self.sangvisFerrisData:
                    if self.sangvisFerrisData[enemies].on_pos(pos_click) and self.sangvisFerrisData[enemies].current_hp>0:
                        skill_target = enemies
                        break
            return skill_target
        elif action == "react":
            if self.griffinCharactersData[characterName].type == "gsh-18":
                healed_hp = round((self.griffinCharactersData[skill_target].max_hp - self.griffinCharactersData[skill_target].current_hp)*0.3)
                self.griffinCharactersData[skill_target].heal(healed_hp)
                if not self.griffinCharactersData[skill_target].dying: self.griffinCharactersData[skill_target].dying = False
                damage_do_to_character[skill_target] = linpg.fontRender("+"+str(healed_hp),"green",25)
            elif self.griffinCharactersData[characterName].type == "asval" or self.griffinCharactersData[characterName].type == "pp1901" or self.griffinCharactersData[characterName].type == "sv-98":
                the_damage = linpg.randomInt(self.griffinCharactersData[characterName].min_damage,self.griffinCharactersData[characterName].max_damage)
                self.sangvisFerrisData[skill_target].decreaseHp(the_damage)
                damage_do_to_character[skill_target] = linpg.fontRender("-"+str(the_damage),"red",25)
            return damage_do_to_character
    #对话模块
    def __play_dialog(self, screen:pygame.Surface) -> None:
        #画出地图
        self._display_map(screen)
        #角色动画
        for every_chara in self.griffinCharactersData:
            self.griffinCharactersData[every_chara].draw(screen,self.MAP)
        for enemies in self.sangvisFerrisData:
            if self.MAP.inLightArea(self.sangvisFerrisData[enemies]):
                self.sangvisFerrisData[enemies].draw(screen,self.MAP)
        #展示设施
        self._display_decoration(screen)
        #加载雪花
        self._display_weather(screen)
        #如果战斗有对话
        if self.dialogKey is not None:
            #设定初始化
            if self.dialogData is None:
                self.dialogData = {
                    "dialogId": 0,
                    "charactersPaths": None,
                    "secondsAlreadyIdle":0,
                    "secondsToIdle":None
                }
            #对话系统总循环
            if self.dialogData["dialogId"] < len(self.dialog_during_battle[self.dialogKey]):
                currentDialog = self.dialog_during_battle[self.dialogKey][self.dialogData["dialogId"]]
                #如果操作是移动
                if "move" in currentDialog and currentDialog["move"] is not None:
                    #为所有角色设置路径
                    if not self.__dialog_is_route_generated:
                        for key,pos in currentDialog["move"].items():
                            if key in self.griffinCharactersData:
                                routeTmp = self.MAP.findPath(self.griffinCharactersData[key],pos,self.griffinCharactersData,self.sangvisFerrisData)
                                if len(routeTmp)>0:
                                    self.griffinCharactersData[key].move_follow(routeTmp)
                                else:
                                    raise Exception('Error: Character {} cannot find a valid path!'.format(key))
                            elif key in self.sangvisFerrisData:
                                routeTmp = self.MAP.findPath(self.sangvisFerrisData[key],pos,self.sangvisFerrisData,self.griffinCharactersData)
                                if len(routeTmp)>0:
                                    self.sangvisFerrisData[key].move_follow(routeTmp)
                                else:
                                    raise Exception('Error: Character {} cannot find a valid path!'.format(key))
                            else:
                                raise Exception('Error: Cannot find character {}!'.format(key))
                        self.__dialog_is_route_generated = True
                    #播放脚步声
                    self.footstep_sounds.play()
                    #是否所有角色都已经到达对应点
                    allGetToTargetPos = True
                    #是否需要重新渲染地图
                    reProcessMap = False
                    for key in currentDialog["move"]:
                        if key in self.griffinCharactersData:
                            if not self.griffinCharactersData[key].is_idle():
                                allGetToTargetPos = False
                            if self.griffinCharactersData[key].needUpdateMap():
                                reProcessMap = True
                        elif key in self.sangvisFerrisData and not self.sangvisFerrisData[key].is_idle():
                            allGetToTargetPos = False
                        else:
                            raise Exception('Error: Cannot find character {}!'.format(key))
                    if reProcessMap:
                        self._calculate_darkness()
                    if allGetToTargetPos:
                        #脚步停止
                        self.footstep_sounds.stop()
                        self.dialogData["dialogId"] += 1
                        self.__dialog_is_route_generated = False
                #改变方向
                elif "direction" in currentDialog and currentDialog["direction"] is not None:
                    for key,value in currentDialog["direction"].items():
                        if key in self.griffinCharactersData:
                            self.griffinCharactersData[key].set_flip(value)
                        elif key in self.sangvisFerrisData:
                            self.sangvisFerrisData[key].set_flip(value)
                        else:
                            raise Exception('Error: Cannot find character {}!'.format(key))
                    self.dialogData["dialogId"] += 1
                #改变动作（一次性）
                elif "action" in currentDialog and currentDialog["action"] is not None:
                    for key,action in currentDialog["action"].items():
                        if key in self.griffinCharactersData:
                            self.griffinCharactersData[key].set_action(action,False)
                        elif key in self.sangvisFerrisData:
                            self.sangvisFerrisData[key].set_action(action,False)
                    self.dialogData["dialogId"] += 1 
                #改变动作（长期）
                elif "actionLoop" in currentDialog and currentDialog["actionLoop"] is not None:
                    for key,action in currentDialog["actionLoop"].items():
                        if key in self.griffinCharactersData:
                            self.griffinCharactersData[key].set_action(action)
                        elif key in self.sangvisFerrisData:
                            self.sangvisFerrisData[key].set_action(action)
                    self.dialogData["dialogId"] += 1
                #开始对话
                elif "dialoguebox_up" in currentDialog or "dialoguebox_down" in currentDialog:
                    #上方对话框
                    if currentDialog["dialoguebox_up"] is not None:
                        #对话框的移动
                        if self.dialoguebox_up.x > self.window_x/2+self.dialoguebox_up.get_width()*0.4:
                            self.dialoguebox_up.x -= self.dialoguebox_up.get_width()*0.134
                        elif not self.dialoguebox_up.updated:
                            self.dialoguebox_up.update(
                                currentDialog["dialoguebox_up"]["content"],
                                currentDialog["dialoguebox_up"]["speaker"],
                                currentDialog["dialoguebox_up"]["speaker_icon"]
                            )
                        #对话框图片
                        self.dialoguebox_up.draw(screen,self.characterInfoBoardUI)
                    #下方对话框
                    if currentDialog["dialoguebox_down"] is not None:
                        #对话框的移动
                        if self.dialoguebox_down.x < self.window_x/2-self.dialoguebox_down.get_width()*1.4:
                            self.dialoguebox_down.x += self.dialoguebox_down.get_width()*0.134
                        elif not self.dialoguebox_down.updated:
                            self.dialoguebox_down.update(
                                currentDialog["dialoguebox_down"]["content"],
                                currentDialog["dialoguebox_down"]["speaker"],
                                currentDialog["dialoguebox_down"]["speaker_icon"]
                            )
                        #对话框图片
                        self.dialoguebox_down.draw(screen,self.characterInfoBoardUI)
                #闲置一定时间（秒）
                elif "idle" in currentDialog and currentDialog["idle"] is not None:
                    if self.dialogData["secondsToIdle"] is None:
                        self.dialogData["secondsToIdle"] = currentDialog["idle"]*linpg.display.fps
                    else:
                        if self.dialogData["secondsAlreadyIdle"] < self.dialogData["secondsToIdle"]:
                            self.dialogData["secondsAlreadyIdle"] += 1
                        else:
                            self.dialogData["dialogId"] += 1
                            self.dialogData["secondsAlreadyIdle"] = 0
                            self.dialogData["secondsToIdle"] = None
                #调整窗口位置
                elif "changePos" in currentDialog and currentDialog["changePos"] is not None:
                    if self.screen_to_move_x is None or self.screen_to_move_y is None:
                        tempX,tempY = self.MAP.calPosInMap(currentDialog["changePos"]["x"],currentDialog["changePos"]["y"])
                        self.screen_to_move_x =  screen.get_width()/2 - tempX
                        self.screen_to_move_y = screen.get_height()/2 - tempY
                    if self.screen_to_move_x == 0 and self.screen_to_move_y == 0:
                        self.screen_to_move_x = None
                        self.screen_to_move_y = None
                        self.dialogData["dialogId"] += 1
                else:
                    raise Exception("Error: Dialog Data on '{0}' with id '{1}' cannot pass through any statement!".format(self.dialogKey,self.dialogData["dialogId"]))
                #玩家输入按键判定
                for event in linpg.controller.events:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.pause_menu.hidden = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 or event.type == pygame.JOYBUTTONDOWN and linpg.controller.joystick.get_button(0) == 1:
                        goToNextSlide = False
                        if "dialoguebox_up" in currentDialog and self.dialoguebox_up.updated:
                            if not self.dialoguebox_up.is_all_played():
                                self.dialoguebox_up.play_all()
                            else:
                                goToNextSlide = True
                        if "dialoguebox_down" in currentDialog and self.dialoguebox_down.updated:
                            if not self.dialoguebox_down.is_all_played():
                                self.dialoguebox_down.play_all()
                            else:
                                goToNextSlide = True
                        if goToNextSlide:
                            self.dialogData["dialogId"] += 1
                            if self.dialogData["dialogId"] < len(self.dialog_during_battle[self.dialogKey]):
                                currentDialog = self.dialog_during_battle[self.dialogKey][self.dialogData["dialogId"]]
                                lastDialog = self.dialog_during_battle[self.dialogKey][self.dialogData["dialogId"]-1] if self.dialogData["dialogId"] > 0 else {}
                                if "dialoguebox_up" in currentDialog:
                                    #检测上方对话框
                                    if currentDialog["dialoguebox_up"] is None or "dialoguebox_up" not in lastDialog or lastDialog["dialoguebox_up"] is None or currentDialog["dialoguebox_up"]["speaker"] != lastDialog["dialoguebox_up"]["speaker"]:
                                        self.dialoguebox_up.reset()
                                    elif currentDialog["dialoguebox_up"]["content"] != lastDialog["dialoguebox_up"]["content"]:
                                        self.dialoguebox_up.updated = False
                                else:
                                    self.dialoguebox_up.reset()
                                if "dialoguebox_down" in currentDialog:
                                    #检测下方对话框    
                                    if currentDialog["dialoguebox_down"] is None or "dialoguebox_down" not in lastDialog or lastDialog["dialoguebox_down"] is None or currentDialog["dialoguebox_down"]["speaker"] != lastDialog["dialoguebox_down"]["speaker"]:
                                        self.dialoguebox_down.reset()
                                    elif currentDialog["dialoguebox_down"]["content"] != lastDialog["dialoguebox_down"]["content"]:
                                        self.dialoguebox_down.updated = False
                                else:
                                    self.dialoguebox_down.reset()
                            else:
                                self.dialoguebox_up.reset()
                                self.dialoguebox_down.reset()
            else:
                self.dialogData = None
                self.dialogKey = None
                self.__is_battle_mode = True
        #如果战斗前无·对话
        elif self.dialogKey is None:
            #角色UI
            for every_chara in self.griffinCharactersData:
                self.griffinCharactersData[every_chara].drawUI(screen,self.MAP)
            for enemies in self.sangvisFerrisData:
                if self.MAP.inLightArea(self.sangvisFerrisData[enemies]):
                    self.sangvisFerrisData[enemies].drawUI(screen,self.MAP)
            if self.txt_alpha == 0:
                self.__is_battle_mode = True
    #战斗模块
    def __play_battle(self, screen:pygame.Surface) -> None:
        self.play_bgm()
        right_click = False
        #获取鼠标坐标
        mouse_x,mouse_y = linpg.controller.get_mouse_pos()
        skill_range = None
        for event in linpg.controller.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.characterGetClick is None:
                    self.pause_menu.hidden = False
                if event.key == pygame.K_ESCAPE and self.__is_waiting is True:
                    self.__if_draw_range = True
                    self.characterGetClick = None
                    self.action_choice = None
                    skill_range = None
                    self.reset_areaDrawColorBlock()
                self._check_key_down(event)
                if event.key == pygame.K_m:
                    linpg.display.quit()
            elif event.type == pygame.KEYUP:
                self._check_key_up(event)
            #鼠标点击
            elif event.type == pygame.MOUSEBUTTONDOWN:
                #右键
                if event.button == 1 or event.type == pygame.JOYBUTTONDOWN and linpg.controller.joystick.get_button(0) == 1:
                    right_click = True
                #上下滚轮-放大和缩小地图
                elif event.button == 4 and self.zoomIntoBe < 150:
                    self.zoomIntoBe += 10
                elif event.button == 5 and self.zoomIntoBe > 50:
                    self.zoomIntoBe -= 10
        #其他移动的检查
        self._check_right_click_move(mouse_x,mouse_y)
        self._check_jostick_events()

        #根据self.zoomIntoBe调整self.zoomIn大小
        if self.zoomIntoBe != self.zoomIn:
            if self.zoomIntoBe < self.zoomIn:
                self.zoomIn -= 5
            elif self.zoomIntoBe > self.zoomIn:
                self.zoomIn += 5
            self.MAP.changePerBlockSize(self._standard_block_width*self.zoomIn/100,self._standard_block_height*self.zoomIn/100)
            #根据block尺寸重新加载对应尺寸的UI
            for key in self.range_ui_images:
                self.range_ui_images[key].set_width_with_size_locked(self.MAP.block_width*0.8)
            self.selectMenuUI.allButton = None

        #画出地图
        self._display_map(screen)

        #画出用彩色方块表示的范围
        for area in self.areaDrawColorBlock:
            for position in self.areaDrawColorBlock[area]:
                xTemp,yTemp = self.MAP.calPosInMap(position[0],position[1])
                self.range_ui_images[area].set_pos(xTemp+self.MAP.block_width*0.1,yTemp)
                self.range_ui_images[area].draw(screen)

        #玩家回合
        if self.whose_round == "player":
            if right_click is True:
                block_get_click = self.MAP.calBlockInMap(mouse_x,mouse_y)
                #如果点击了回合结束的按钮
                if linpg.isHover(self.end_round_button) and self.__is_waiting is True:
                    self.whose_round = "playerToSangvisFerris"
                    self.characterGetClick = None
                    self.__if_draw_range = True
                    skill_range = None
                    self.reset_areaDrawColorBlock()
                #是否在显示移动范围后点击了且点击区域在移动范围内
                elif len(self.the_route) != 0 and block_get_click is not None and (block_get_click["x"], block_get_click["y"]) in self.the_route and not self.__if_draw_range:
                    self.__is_waiting = False
                    self.__if_draw_range = True
                    self.characterInControl.try_reduce_action_point(len(self.the_route)*2)
                    self.characterInControl.move_follow(self.the_route)
                    self.reset_areaDrawColorBlock()
                elif self.__if_draw_range == "SelectMenu" and self.buttonGetHover == "attack":
                    if self.characterInControl.current_bullets > 0 and self.characterInControl.have_enough_action_point(5):
                        self.action_choice = "attack"
                        self.__if_draw_range = False
                    elif self.characterInControl.current_bullets <= 0:
                        self.warnings_to_display.add("magazine_is_empty")
                    elif not self.characterInControl.have_enough_action_point(5):
                        self.warnings_to_display.add("no_enough_ap_to_attack")
                elif self.__if_draw_range == "SelectMenu" and self.buttonGetHover == "move":
                    if self.characterInControl.have_enough_action_point(2):
                        self.action_choice = "move"
                        self.__if_draw_range = False
                    else:
                        self.warnings_to_display.add("no_enough_ap_to_move")
                elif self.__if_draw_range == "SelectMenu" and self.buttonGetHover == "skill":
                    if self.characterInControl.have_enough_action_point(8):
                        self.action_choice = "skill"
                        self.__if_draw_range = False
                    else:
                        self.warnings_to_display.add("no_enough_ap_to_use_skill")
                elif self.__if_draw_range == "SelectMenu" and self.buttonGetHover == "reload":
                    if self.characterInControl.have_enough_action_point(5) and self.characterInControl.bullets_carried > 0:
                        self.action_choice = "reload"
                        self.__if_draw_range = False
                    elif self.characterInControl.bullets_carried <= 0:
                        self.warnings_to_display.add("no_bullets_left")
                    elif not self.characterInControl.have_enough_action_point(5):
                        self.warnings_to_display.add("no_enough_ap_to_reload")
                elif self.__if_draw_range == "SelectMenu" and self.buttonGetHover == "rescue":
                    if self.characterInControl.have_enough_action_point(8):
                        self.action_choice = "rescue"
                        self.__if_draw_range = False
                    else:
                        self.warnings_to_display.add("no_enough_ap_to_rescue")
                elif self.__if_draw_range == "SelectMenu" and self.buttonGetHover == "interact":
                    if self.characterInControl.have_enough_action_point(2):
                        self.action_choice = "interact"
                        self.__if_draw_range = False
                    else:
                        self.warnings_to_display.add("no_enough_ap_to_interact")
                #攻击判定
                elif self.action_choice == "attack" and not self.__if_draw_range and self.characterGetClick is not None and len(self.enemiesGetAttack)>0:
                    self.characterInControl.try_reduce_action_point(5)
                    self.characterInControl.notice()
                    self.characterInControl.set_action("attack",False)
                    self.__is_waiting = False
                    self.__if_draw_range = True
                    self.reset_areaDrawColorBlock()
                #技能
                elif self.action_choice == "skill" and not self.__if_draw_range and self.characterGetClick is not None and self.skill_target is not None:
                    if self.skill_target in self.griffinCharactersData:
                        self.characterInControl.set_flip_based_on_pos(self.griffinCharactersData[self.skill_target])
                    elif self.skill_target in self.sangvisFerrisData:
                        self.characterInControl.notice()
                        self.characterInControl.set_flip_based_on_pos(self.sangvisFerrisData[self.skill_target])
                    self.characterInControl.try_reduce_action_point(8)
                    self.characterInControl.play_sound("skill")
                    self.characterInControl.set_action("skill",False)
                    self.__is_waiting = False
                    self.__if_draw_range = True
                    skill_range = None
                    self.reset_areaDrawColorBlock()
                elif self.action_choice == "rescue" and not self.__if_draw_range and self.characterGetClick is not None and self.friendGetHelp is not None:
                    self.characterInControl.try_reduce_action_point(8)
                    self.characterInControl.notice()
                    self.griffinCharactersData[self.friendGetHelp].heal(1)
                    self.characterGetClick = None
                    self.action_choice = None
                    self.__is_waiting = True
                    self.__if_draw_range = True
                    self.reset_areaDrawColorBlock()
                elif self.action_choice == "interact" and not self.__if_draw_range and self.characterGetClick is not None and self.decorationGetClick is not None:
                    self.characterInControl.try_reduce_action_point(2)
                    self.MAP.interact_decoration_with_id(self.decorationGetClick)
                    self._calculate_darkness()
                    self.characterGetClick = None
                    self.action_choice = None
                    self.__is_waiting = True
                    self.__if_draw_range = True
                    self.reset_areaDrawColorBlock()
                #判断是否有被点击的角色
                elif block_get_click is not None:
                    for key in self.griffinCharactersData:
                        if self.griffinCharactersData[key].on_pos(block_get_click) and self.__is_waiting is True and not self.griffinCharactersData[key].dying and self.__if_draw_range is not False:
                            self.screen_to_move_x = None
                            self.screen_to_move_y = None
                            skill_range = None
                            self.reset_areaDrawColorBlock()
                            if self.characterGetClick != key:
                                self.griffinCharactersData[key].play_sound("get_click")
                                self.characterGetClick = key
                            self.characterInfoBoardUI.update()
                            self.friendsCanSave = [
                                key2 for key2 in self.griffinCharactersData if self.griffinCharactersData[key2].dying is not False \
                                    and self.griffinCharactersData[key].near(self.griffinCharactersData[key2])
                                ]
                            self.thingsCanReact.clear()
                            index = 0
                            for decoration in self.MAP.decorations:
                                if decoration.type == "campfire" and self.griffinCharactersData[key].near(decoration):
                                    self.thingsCanReact.append(index)
                                index += 1
                            self.__if_draw_range = "SelectMenu"
                            break
            #选择菜单的判定，显示功能在角色动画之后
            if self.__if_draw_range == "SelectMenu":
                #移动画面以使得被点击的角色可以被更好的操作
                tempX,tempY = self.MAP.calPosInMap(self.characterInControl.x,self.characterInControl.y)
                if self.screen_to_move_x is None:
                    if tempX < self.window_x*0.2 and self.MAP.getPos_x()<=0:
                        self.screen_to_move_x = self.window_x*0.2-tempX
                    elif tempX > self.window_x*0.8 and self.MAP.getPos_x()>=self.MAP.column*self.MAP.block_width*-1:
                        self.screen_to_move_x = self.window_x*0.8-tempX
                if self.screen_to_move_y is None:
                    if tempY < self.window_y*0.2 and self.MAP.getPos_y()<=0:
                        self.screen_to_move_y = self.window_y*0.2-tempY
                    elif tempY > self.window_y*0.8 and self.MAP.getPos_y()>=self.MAP.row*self.MAP.block_height*-1:
                        self.screen_to_move_y = self.window_y*0.8-tempY
            #显示攻击/移动/技能范围
            if not self.__if_draw_range and self.characterGetClick is not None:
                block_get_click = self.MAP.calBlockInMap(mouse_x,mouse_y)
                #显示移动范围
                if self.action_choice == "move":
                    self.areaDrawColorBlock["green"].clear()
                    if block_get_click is not None:
                        #根据行动值计算最远可以移动的距离
                        max_blocks_can_move = int(self.characterInControl.current_action_point/2)
                        if 0<abs(block_get_click["x"]-self.characterInControl.x)+abs(block_get_click["y"]-self.characterInControl.y)<=max_blocks_can_move:
                            self.the_route = self.MAP.findPath(self.characterInControl,block_get_click,self.griffinCharactersData,self.sangvisFerrisData,max_blocks_can_move)
                            if len(self.the_route)>0:
                                #显示路径
                                self.areaDrawColorBlock["green"] = self.the_route
                                xTemp,yTemp = self.MAP.calPosInMap(self.the_route[-1][0],self.the_route[-1][1])
                                screen.blit(self.FONT.render(str(len(self.the_route)*2),linpg.get_antialias(),(255,255,255)),(xTemp+self.FONTSIZE*2,yTemp+self.FONTSIZE))
                                self.characterInControl.draw_custom("move",(xTemp,yTemp),screen,self.MAP)
                #显示攻击范围        
                elif self.action_choice == "attack":
                    attacking_range = self.characterInControl.getAttackRange(self.MAP)
                    self.areaDrawColorBlock["green"] = attacking_range["near"]
                    self.areaDrawColorBlock["blue"] = attacking_range["middle"]
                    self.areaDrawColorBlock["yellow"] = attacking_range["far"]
                    if block_get_click is not None:
                        the_attacking_range_area = []
                        for area in attacking_range:
                            if (block_get_click["x"],block_get_click["y"]) in attacking_range[area]:
                                for y in range(block_get_click["y"]-self.characterInControl.attack_range+1,block_get_click["y"]+self.characterInControl.attack_range):
                                    if y < block_get_click["y"]:
                                        for x in range(block_get_click["x"]-self.characterInControl.attack_range-(y-block_get_click["y"])+1,block_get_click["x"]+self.characterInControl.attack_range+(y-block_get_click["y"])):
                                            if self.MAP.ifBlockCanPassThrough({"x":x,"y":y}):
                                                the_attacking_range_area.append((x,y))
                                    else:
                                        for x in range(block_get_click["x"]-self.characterInControl.attack_range+(y-block_get_click["y"])+1,block_get_click["x"]+self.characterInControl.attack_range-(y-block_get_click["y"])):
                                            if self.MAP.ifBlockCanPassThrough({"x":x,"y":y}):
                                                the_attacking_range_area.append((x,y))
                                break
                        self.enemiesGetAttack.clear()
                        if len(the_attacking_range_area) > 0:
                            self.areaDrawColorBlock["orange"] = the_attacking_range_area
                            for enemies in self.sangvisFerrisData:
                                if self.sangvisFerrisData[enemies].pos in the_attacking_range_area and self.sangvisFerrisData[enemies].is_alive():
                                    if self.sangvisFerrisData[enemies].pos in attacking_range["far"]:
                                        self.enemiesGetAttack[enemies] = "far"
                                    elif self.sangvisFerrisData[enemies].pos in attacking_range["middle"]:
                                        self.enemiesGetAttack[enemies] = "middle"
                                    elif self.sangvisFerrisData[enemies].pos in attacking_range["near"]:
                                        self.enemiesGetAttack[enemies] = "near"
                #显示技能范围        
                elif self.action_choice == "skill":
                    self.skill_target = None
                    if self.characterInControl.max_skill_range > 0:
                        if skill_range is None:
                            skill_range = {"near":[],"middle":[],"far":[]}
                            for y in range(self.characterInControl.y-self.characterInControl.max_skill_range,self.characterInControl.y+self.characterInControl.max_skill_range+1):
                                if y < self.characterInControl.y:
                                    for x in range(self.characterInControl.x-self.characterInControl.max_skill_range-(y-self.characterInControl.y),self.characterInControl.x+self.characterInControl.max_skill_range+(y-self.characterInControl.y)+1):
                                        if self.MAP.row>y>=0 and self.MAP.column>x>=0:
                                            if "far" in self.characterInControl.skill_effective_range and self.characterInControl.skill_effective_range["far"] is not None and self.characterInControl.skill_effective_range["far"][0] <= abs(x-self.characterInControl.x)+abs(y-self.characterInControl.y) <= self.characterInControl.skill_effective_range["far"][1]:
                                                skill_range["far"].append([x,y])
                                            elif "middle" in self.characterInControl.skill_effective_range and self.characterInControl.skill_effective_range["middle"] is not None and self.characterInControl.skill_effective_range["middle"][0] <= abs(x-self.characterInControl.x)+abs(y-self.characterInControl.y) <= self.characterInControl.skill_effective_range["middle"][1]:
                                                skill_range["middle"].append([x,y])
                                            elif "near" in self.characterInControl.skill_effective_range and self.characterInControl.skill_effective_range["near"] is not None and self.characterInControl.skill_effective_range["near"][0] <= abs(x-self.characterInControl.x)+abs(y-self.characterInControl.y) <= self.characterInControl.skill_effective_range["near"][1]:
                                                skill_range["near"].append([x,y])
                                else:
                                    for x in range(self.characterInControl.x-self.characterInControl.max_skill_range+(y-self.characterInControl.y),self.characterInControl.x+self.characterInControl.max_skill_range-(y-self.characterInControl.y)+1):
                                        if x == self.characterInControl.x and y == self.characterInControl.y:
                                            pass
                                        elif self.MAP.row>y>=0 and self.MAP.column>x>=0:
                                            if "far" in self.characterInControl.skill_effective_range and self.characterInControl.skill_effective_range["far"] is not None and self.characterInControl.skill_effective_range["far"][0] <= abs(x-self.characterInControl.x)+abs(y-self.characterInControl.y) <= self.characterInControl.skill_effective_range["far"][1]:
                                                skill_range["far"].append([x,y])
                                            elif "middle" in self.characterInControl.skill_effective_range and self.characterInControl.skill_effective_range["middle"] is not None and self.characterInControl.skill_effective_range["middle"][0] <= abs(x-self.characterInControl.x)+abs(y-self.characterInControl.y) <= self.characterInControl.skill_effective_range["middle"][1]:
                                                skill_range["middle"].append([x,y])
                                            elif "near" in self.characterInControl.skill_effective_range and self.characterInControl.skill_effective_range["near"] is not None and self.characterInControl.skill_effective_range["near"][0] <= abs(x-self.characterInControl.x)+abs(y-self.characterInControl.y) <= self.characterInControl.skill_effective_range["near"][1]:
                                                skill_range["near"].append([x,y])
                        self.areaDrawColorBlock["green"] = skill_range["near"]
                        self.areaDrawColorBlock["blue"] = skill_range["middle"]
                        self.areaDrawColorBlock["yellow"] = skill_range["far"]
                        block_get_click = self.MAP.calBlockInMap(mouse_x,mouse_y)
                        if block_get_click is not None:
                            the_skill_cover_area = []
                            for area in skill_range:
                                if [block_get_click["x"],block_get_click["y"]] in skill_range[area]:
                                    for y in range(block_get_click["y"]-self.characterInControl.skill_cover_range,block_get_click["y"]+self.characterInControl.skill_cover_range):
                                        if y < block_get_click["y"]:
                                            for x in range(block_get_click["x"]-self.characterInControl.skill_cover_range-(y-block_get_click["y"])+1,block_get_click["x"]+self.characterInControl.skill_cover_range+(y-block_get_click["y"])):
                                                if self.MAP.row>y>=0 and self.MAP.column>x>=0 and self.MAP.ifBlockCanPassThrough({"x":x,"y":y}):
                                                    the_skill_cover_area.append([x,y])
                                        else:
                                            for x in range(block_get_click["x"]-self.characterInControl.skill_cover_range+(y-block_get_click["y"])+1,block_get_click["x"]+self.characterInControl.skill_cover_range-(y-block_get_click["y"])):
                                                if self.MAP.row>y>=0 and self.MAP.column>x>=0 and self.MAP.ifBlockCanPassThrough({"x":x,"y":y}):
                                                    the_skill_cover_area.append([x,y])
                                    self.areaDrawColorBlock["orange"] = the_skill_cover_area
                                    self.skill_target = self.__skill(self.characterGetClick,{"x":block_get_click["x"],"y":block_get_click["y"]},the_skill_cover_area)
                                    break
                    else:
                        self.skill_target = self.__skill(self.characterGetClick,{"x":None,"y":None},None)
                        if self.skill_target is not None:
                            self.characterInControl.try_reduce_action_point(8)
                            self.__is_waiting = False
                            self.__if_draw_range = True
                #换弹
                elif self.action_choice == "reload":
                    bullets_to_add = self.characterInControl.magazine_capacity-self.characterInControl.current_bullets
                    #需要换弹
                    if bullets_to_add > 0:
                        #如果角色有换弹动画，则播放角色的换弹动画
                        if self.characterInControl.get_imgId("reload") != -1:
                            self.characterInControl.set_action("reload",False)
                        #扣去对应的行动值
                        self.characterInControl.try_reduce_action_point(5)
                        #当所剩子弹足够换弹的时候
                        if bullets_to_add <= self.characterInControl.bullets_carried:
                            self.characterInControl.bullets_carried -= bullets_to_add
                            self.characterInControl.current_bullets += bullets_to_add
                        #当所剩子弹不足以换弹的时候
                        else:
                            self.characterInControl.current_bullets += self.characterInControl.bullets_carried
                            self.characterInControl.bullets_carried = 0
                        self.__is_waiting = True
                        self.characterGetClick = None
                        self.action_choice = None
                        self.__if_draw_range = True
                    #无需换弹
                    else:
                        self.warnings_to_display.add("magazine_is_full")
                        self.__if_draw_range = "SelectMenu"
                elif self.action_choice == "rescue":
                    self.areaDrawColorBlock["green"].clear()
                    self.areaDrawColorBlock["orange"].clear()
                    self.friendGetHelp = None
                    for friendNeedHelp in self.friendsCanSave:
                        if block_get_click is not None and block_get_click["x"] == self.griffinCharactersData[friendNeedHelp].x and block_get_click["y"] == self.griffinCharactersData[friendNeedHelp].y:
                            self.areaDrawColorBlock["orange"] = [(block_get_click["x"],block_get_click["y"])]
                            self.friendGetHelp = friendNeedHelp
                        else:
                            self.areaDrawColorBlock["green"].append((self.griffinCharactersData[friendNeedHelp].x,self.griffinCharactersData[friendNeedHelp].y))
                elif self.action_choice == "interact":
                    self.areaDrawColorBlock["green"].clear()
                    self.areaDrawColorBlock["orange"].clear()
                    self.decorationGetClick = None
                    for index in self.thingsCanReact:
                        decoration = self.MAP.find_decoration_with_id(index)
                        if block_get_click is not None and decoration.is_on_pos(block_get_click):
                            self.areaDrawColorBlock["orange"] = [(block_get_click["x"],block_get_click["y"])]
                            self.decorationGetClick = index
                        else:
                            self.areaDrawColorBlock["green"].append((decoration.x,decoration.y))

            #当有角色被点击时
            if self.characterGetClick is not None and not self.__is_waiting:
                #被点击的角色动画
                self.__if_draw_range = True
                if self.action_choice == "move":
                    if not self.characterInControl.is_idle():
                        #播放脚步声
                        self.footstep_sounds.play()
                        #是否需要更新
                        if self.characterInControl.needUpdateMap():
                            self.__alert_enemy_around(self.characterGetClick)
                            self._calculate_darkness()
                    else:
                        self.footstep_sounds.stop()
                        #检测是不是站在补给上
                        decoration = self.MAP.find_decoration_on(self.characterInControl.get_pos())
                        if decoration is not None and decoration.type == "chest":
                            if decoration.whitelist is None \
                                or self.characterGetClick == decoration.whitelist or self.characterGetClick in decoration.whitelist:
                                #清空储存列表
                                self.supply_board.items.clear()
                                #将物品按照类型放入列表
                                for itemType,itemData in decoration.items.items():
                                    if itemType == "bullet":
                                        self.characterInControl.bullets_carried += itemData
                                        self.supply_board.items.append(self.FONT.render(self.battleModeUiTxt["getBullets"]+": "+str(itemData),linpg.get_antialias(),(255,255,255)))
                                    elif itemType == "hp":
                                        self.characterInControl.heal(itemData)
                                        self.supply_board.items.append(self.FONT.render(self.battleModeUiTxt["getHealth"]+": "+str(itemData),linpg.get_antialias(),(255,255,255)))
                                #如果UI已经回到原位
                                if len(self.supply_board.items) > 0: self.supply_board.move_toward()
                                #移除箱子
                                self.MAP.remove_decoration(decoration)
                        #检测当前所在点是否应该触发对话
                        name_from_by_pos = str(self.characterInControl.x)+"-"+str(self.characterInControl.y)
                        if "move" in self.dialogInfo and name_from_by_pos in self.dialogInfo["move"]:
                            dialog_to_check = self.dialogInfo["move"][name_from_by_pos]
                            if "whitelist" not in dialog_to_check or dialog_to_check["whitelist"] is None \
                                or self.characterGetClick == dialog_to_check["whitelist"] \
                                    or self.characterGetClick in dialog_to_check["whitelist"]:
                                self.dialogKey = dialog_to_check["dialog_key"]
                                self.__is_battle_mode = False
                                #如果对话不重复，则删除（默认不重复）
                                if "repeat" not in dialog_to_check or not dialog_to_check["repeat"]: del dialog_to_check
                        #玩家可以继续选择需要进行的操作
                        self.__is_waiting = True
                        self.characterGetClick = None
                        self.action_choice = None
                elif self.action_choice == "attack":
                    #根据敌我坐标判断是否需要反转角色
                    if self.characterInControl.get_imgId("attack") == 0:
                        block_get_click = self.MAP.calBlockInMap(mouse_x,mouse_y)
                        if block_get_click is not None:
                            self.characterInControl.set_flip_based_on_pos(block_get_click)
                        self.characterInControl.play_sound("attack")
                    #播放射击音效
                    elif self.characterInControl.get_imgId("attack") == 3:
                        self.attackingSounds.play(self.characterInControl.kind)
                    if self.characterInControl.get_imgId("attack") == self.characterInControl.get_imgNum("attack")-2:
                        for each_enemy in self.enemiesGetAttack:
                            if self.enemiesGetAttack[each_enemy] == "near" and linpg.randomInt(1,100) <= 95 or self.enemiesGetAttack[each_enemy] == "middle" and linpg.randomInt(1,100) <= 80 or self.enemiesGetAttack[each_enemy] == "far" and linpg.randomInt(1,100) <= 65:
                                the_damage = self.characterInControl.attack(self.sangvisFerrisData[each_enemy])
                                self.damage_do_to_characters[each_enemy] = self.FONT.render("-"+str(the_damage),linpg.get_antialias(),linpg.findColorRGBA("red"))
                                self.sangvisFerrisData[each_enemy].alert(100)
                            else:
                                self.damage_do_to_characters[each_enemy] = self.FONT.render("Miss",linpg.get_antialias(),linpg.findColorRGBA("red"))
                                self.sangvisFerrisData[each_enemy].alert(50)
                    elif self.characterInControl.get_imgId("attack") == self.characterInControl.get_imgNum("attack")-1:
                        self.characterInControl.current_bullets -= 1
                        self.__is_waiting = True
                        self.characterGetClick = None
                        self.action_choice = None
                elif self.action_choice == "skill":
                    if self.characterInControl.get_imgId("skill") == self.characterInControl.get_imgNum("skill")-2:
                        self.damage_do_to_characters = self.__skill(self.characterGetClick,None,None,"react",self.skill_target,self.damage_do_to_characters)
                    elif self.characterInControl.get_imgId("skill") == self.characterInControl.get_imgNum("skill")-1:
                        self._calculate_darkness()
                        self.__is_waiting =True
                        self.characterGetClick = None
                        self.action_choice = None

        #敌方回合
        if self.whose_round == "sangvisFerris":
            #如果当前角色还没做出决定
            if self.enemy_instructions is None:
                #生成决定
                self.enemy_instructions = self.enemyInControl.make_decision(
                    self.MAP,self.griffinCharactersData,self.sangvisFerrisData,self.the_characters_detected_last_round)
            if not self.enemy_instructions.empty() or self.current_instruction is not None:
                #获取需要执行的指令
                if self.current_instruction is None:
                    self.current_instruction = self.enemy_instructions.get()
                    if self.current_instruction.action == "move":
                        self.enemyInControl.move_follow(self.current_instruction.route)
                    elif self.current_instruction.action == "attack":
                        self.enemyInControl.set_flip_based_on_pos(self.griffinCharactersData[self.current_instruction.target])
                        self.enemyInControl.set_action("attack")
                #根据选择调整动画
                if self.current_instruction.action == "move":
                    if not self.enemyInControl.is_idle():
                        self.footstep_sounds.play()
                    else:
                        self.footstep_sounds.stop()
                        self.current_instruction = None
                elif self.current_instruction.action == "attack":
                    if self.enemyInControl.get_imgId("attack") == 3:
                        self.attackingSounds.play(self.enemyInControl.kind)
                    elif self.enemyInControl.get_imgId("attack") == self.enemyInControl.get_imgNum("attack")-1:
                        temp_value = linpg.randomInt(0,100)
                        if self.current_instruction.target_area == "near" and temp_value <= 95 \
                        or self.current_instruction.target_area == "middle" and temp_value <= 80 \
                        or self.current_instruction.target_area == "far" and temp_value <= 65:
                            the_damage = self.enemyInControl.attack(self.griffinCharactersData[self.current_instruction.target])
                            #如果角色进入倒地或者死亡状态，则应该将times_characters_down加一
                            if not self.griffinCharactersData[self.current_instruction.target].is_alive(): self.resultInfo["times_characters_down"] += 1
                            #重新计算迷雾区域
                            self._calculate_darkness()
                            self.damage_do_to_characters[self.current_instruction.target] = self.FONT.render("-"+str(the_damage),linpg.get_antialias(),linpg.findColorRGBA("red"))
                        else:
                            self.damage_do_to_characters[self.current_instruction.target] = self.FONT.render("Miss",linpg.get_antialias(),linpg.findColorRGBA("red"))
                        self.current_instruction = None
            else:
                self.enemyInControl.set_action()
                self.enemies_in_control_id += 1
                self.enemy_instructions = None
                self.current_instruction = None
                if self.enemies_in_control_id >= len(self.sangvisFerris_name_list): self.whose_round = "sangvisFerrisToPlayer"

        """↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓角色动画展示区↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓"""
        rightClickCharacterAlphaDeduct = True
        for key,value in linpg.dicMerge(self.griffinCharactersData,self.sangvisFerrisData).items():
            #如果天亮的双方都可以看见/天黑，但是是友方角色/天黑，但是是敌方角色在可观测的范围内 -- 则画出角色
            if value.faction == "character" or value.faction == "sangvisFerri" and self.MAP.inLightArea(value):
                if self.__if_draw_range is True and pygame.mouse.get_pressed()[2]:
                    block_get_click = self.MAP.calBlockInMap(mouse_x,mouse_y)
                    if block_get_click is not None and block_get_click["x"] == value.x and block_get_click["y"]  == value.y:
                        rightClickCharacterAlphaDeduct = False
                        if self.rightClickCharacterAlpha is None:
                            self.rightClickCharacterAlpha = 0
                        if self.rightClickCharacterAlpha < 255:
                            self.rightClickCharacterAlpha += 17
                            self.range_ui_images["yellow"].set_alpha(self.rightClickCharacterAlpha)
                            self.range_ui_images["blue"].set_alpha(self.rightClickCharacterAlpha)
                            self.range_ui_images["green"].set_alpha(self.rightClickCharacterAlpha)
                        rangeCanAttack =  value.getAttackRange(self.MAP)
                        self.areaDrawColorBlock["yellow"] = rangeCanAttack["far"]
                        self.areaDrawColorBlock["blue"] =  rangeCanAttack["middle"]
                        self.areaDrawColorBlock["green"] = rangeCanAttack["near"]
                value.draw(screen,self.MAP)
            else:
                value.draw_nothing()
            #是否有在播放死亡角色的动画（而不是倒地状态）
            if not value.is_alive() and key not in self.the_dead_one:
                if value.kind == "HOC" or value.faction == "sangvisFerri":
                    self.the_dead_one[key] = value.faction
            #伤害/治理数值显示
            if key in self.damage_do_to_characters:
                the_alpha_to_check = self.damage_do_to_characters[key].get_alpha()
                if the_alpha_to_check > 0:
                    xTemp,yTemp = self.MAP.calPosInMap(value.x,value.y)
                    xTemp+=self.MAP.block_width*0.05
                    yTemp-=self.MAP.block_width*0.05
                    linpg.displayInCenter(self.damage_do_to_characters[key],self.range_ui_images["green"],xTemp,yTemp,screen)
                    self.damage_do_to_characters[key].set_alpha(the_alpha_to_check-5)
                else:
                    del self.damage_do_to_characters[key]
        #移除死亡的角色
        if len(self.the_dead_one) > 0:
            the_dead_one_remove = []
            for key,value in self.the_dead_one.items():
                if value == "sangvisFerri":
                    if self.sangvisFerrisData[key].get_imgId("die") == self.sangvisFerrisData[key].get_imgNum("die")-1:
                        the_alpha = self.sangvisFerrisData[key].get_imgAlpaha("die")
                        if the_alpha > 0:
                            self.sangvisFerrisData[key].set_imgAlpaha("die",the_alpha-5)
                        else:
                            the_dead_one_remove.append(key)
                            del self.sangvisFerrisData[key]
                            self.resultInfo["total_kills"]+=1
                elif value == "character":
                    if self.griffinCharactersData[key].get_imgId("die") == self.griffinCharactersData[key].get_imgNum("die")-1:
                        the_alpha = self.griffinCharactersData[key].get_imgAlpaha("die")
                        if the_alpha > 0:
                            self.griffinCharactersData[key].set_imgAlpaha("die",the_alpha-5)
                        else:
                            the_dead_one_remove.append(key)
                            del self.griffinCharactersData[key]
                            self.resultInfo["times_characters_down"]+=1
                            self._calculate_darkness()
            for key in the_dead_one_remove:
                del self.the_dead_one[key]
        """↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑角色动画展示区↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑"""
        #调整范围方块的透明度
        if rightClickCharacterAlphaDeduct and self.rightClickCharacterAlpha is not None:
            if self.rightClickCharacterAlpha > 0:
                self.rightClickCharacterAlpha -= 17
                self.range_ui_images["yellow"].set_alpha(self.rightClickCharacterAlpha)
                self.range_ui_images["blue"].set_alpha(self.rightClickCharacterAlpha)
                self.range_ui_images["green"].set_alpha(self.rightClickCharacterAlpha)
            elif self.rightClickCharacterAlpha == 0:
                self.areaDrawColorBlock["yellow"].clear()
                self.areaDrawColorBlock["blue"].clear()
                self.areaDrawColorBlock["green"].clear()
                self.range_ui_images["yellow"].set_alpha(255)
                self.range_ui_images["blue"].set_alpha(255)
                self.range_ui_images["green"].set_alpha(255)
                self.rightClickCharacterAlpha = None
        #展示设施
        self._display_decoration(screen)
        #展示所有角色Ui
        for every_chara in self.griffinCharactersData:
            self.griffinCharactersData[every_chara].drawUI(screen,self.MAP)
        for enemies in self.sangvisFerrisData:
            if self.MAP.isPosInLightArea(int(self.sangvisFerrisData[enemies].x),int(self.sangvisFerrisData[enemies].y)):
                self.sangvisFerrisData[enemies].drawUI(screen,self.MAP)
        #显示选择菜单
        if self.__if_draw_range == "SelectMenu":
            #左下角的角色信息
            self.characterInfoBoardUI.draw(screen,self.characterInControl)
            #----选择菜单----
            self.buttonGetHover = self.selectMenuUI.draw(screen,round(self.MAP.block_width/10),self.MAP.getBlockExactLocation(self.characterInControl.x,self.characterInControl.y),self.characterInControl.kind,self.friendsCanSave,self.thingsCanReact)
        #加载雪花
        self._display_weather(screen)
        
        #检测回合是否结束
        self.__switch_round(screen)
        #检测玩家是否胜利或失败
        self.__check_whether_player_win_or_lost()

        #显示获取到的物资
        if self.supply_board.has_reached_target():
            if self.supply_board.is_moving_toward_target() :
                if self.supply_board.stayingTime >= 30:
                    self.supply_board.move_back()
                    self.supply_board.stayingTime = 0
                else:
                    self.supply_board.stayingTime += 1
            elif len(self.supply_board.items) > 0:
                self.supply_board.items.clear()
        if len(self.supply_board.items) > 0:
            self.__add_on_screen_object(self.supply_board)
            lenTemp = 0
            for i in range(len(self.supply_board.items)):
                lenTemp += self.supply_board.items[i].get_width()*1.5
            start_point = (self.window_x - lenTemp)/2
            for i in range(len(self.supply_board.items)):
                start_point += self.supply_board.items[i].get_width()*0.25
                self.__add_on_screen_object(
                    self.supply_board.items[i],
                    -1,
                    (start_point,(self.supply_board.get_height()-self.supply_board.items[i].get_height())/2),
                    (0,self.supply_board.y)
                    )
                start_point += self.supply_board.items[i].get_width()*1.25

        if self.whose_round == "player":
            #加载结束回合的按钮
            self.__add_on_screen_object(self.end_round_button)
            self.__add_on_screen_object(self.end_round_txt,-1,self.end_round_button.pos,(self.end_round_button.get_width()*0.35,(self.end_round_button.get_height()-self.FONTSIZE)/2.3))
        
        #显示警告
        self.__add_on_screen_object(self.warnings_to_display)

        #结束动画--胜利
        if self.whose_round == "result_win":
            if self.ResultBoardUI is None:
                self.resultInfo["total_time"] = time.localtime(time.time()-self.resultInfo["total_time"])
                self.ResultBoardUI = ResultBoard(self.resultInfo,self.window_x/96)
            for event in linpg.controller.events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.__is_battle_mode = False
                        self.stop()
            self.__add_on_screen_object(self.ResultBoardUI)
        #结束动画--失败
        elif self.whose_round == "result_fail":
            if self.ResultBoardUI is None:
                self.resultInfo["total_time"] = time.localtime(time.time()-self.resultInfo["total_time"])
                self.ResultBoardUI = ResultBoard(self.resultInfo,self.window_x/96,False)
            for event in linpg.controller.events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        linpg.unloadBackgroundMusic()
                        chapter_info:dict = self.get_data_of_parent_game_system()
                        self.__init__()
                        self.new(screen,chapter_info["chapter_type"], chapter_info["chapter_id"], chapter_info["project_name"])
                        break
                    elif event.key == pygame.K_BACKSPACE:
                        linpg.unloadBackgroundMusic()
                        self.stop()
                        self.__is_battle_mode = False
                        break
            if self.ResultBoardUI is not None: self.__add_on_screen_object(self.ResultBoardUI)
    #把战斗系统的画面画到screen上
    def draw(self, screen:pygame.Surface) -> None:
        #环境声音-频道1
        self.environment_sound.play()
        # 游戏主循环
        if self.__is_battle_mode:
            self.__play_battle(screen)
        #在战斗状态
        else:
            self.__play_dialog(screen)
        #渐变效果：一次性的
        if self.txt_alpha is None:
            self.txt_alpha = 250
        if self.txt_alpha > 0:
            self.infoToDisplayDuringLoading.black_bg.set_alpha(self.txt_alpha)
            self.infoToDisplayDuringLoading.draw(screen,self.txt_alpha)
            for i in range(len(self.battleMode_info)):
                self.battleMode_info[i].set_alpha(self.txt_alpha)
                screen.blit(self.battleMode_info[i],(self.window_x/20,self.window_y*0.75+self.battleMode_info[i].get_height()*1.2*i))
                if i == 1:
                    temp_secode = self.FONT.render(time.strftime(":%S", time.localtime()),linpg.get_antialias(),(255,255,255))
                    temp_secode.set_alpha(self.txt_alpha)
                    screen.blit(temp_secode,(self.window_x/20+self.battleMode_info[i].get_width(),self.window_y*0.75+self.battleMode_info[i].get_height()*1.2))
            self.txt_alpha -= 5
        #刷新画面
        self.__update_scene(screen)
        #展示暂停菜单
        if not self.pause_menu.hidden:
            progress_saved_text = linpg.ImageSurface(self.FONT.render(linpg.get_lang("Global","progress_has_been_saved"),linpg.get_antialias(),(255,255,255)),0,0)
            progress_saved_text.set_alpha(0)
            while not self.pause_menu.hidden:
                linpg.display.flip()
                self.pause_menu.draw(screen)
                result = self.pause_menu.get_button_clicked()
                if result == "break":
                    linpg.get_option_menu().hidden = True
                    self.pause_menu.hidden = True
                elif result == "save":
                    self.save_progress()
                    progress_saved_text.set_alpha(255)
                elif result == "option_menu":
                    linpg.get_option_menu().hidden = False
                elif result == "back_to_mainMenu":
                    linpg.get_option_menu().hidden = True
                    linpg.unloadBackgroundMusic()
                    progress_saved_text.set_alpha(0)
                    self.stop()
                    self.pause_menu.hidden = True
                #展示设置UI
                linpg.get_option_menu().draw(screen)
                #更新音量
                if linpg.get_option_menu().need_update["volume"] is True: self.__update_sound_volume()
                #更新语言
                if linpg.get_option_menu().need_update["language"] is True: self.updated_language(screen)
                #显示进度已保存的文字
                progress_saved_text.drawOnTheCenterOf(screen)
                progress_saved_text.fade_out(5)
            del progress_saved_text
            self.pause_menu.screenshot = None