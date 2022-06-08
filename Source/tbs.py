from .character import *
from .ui import *


# 回合制游戏战斗系统
class TurnBasedBattleSystem(linpg.AbstractBattleSystem, linpg.PauseMenuModuleForGameSystem):
    def __init__(self):
        linpg.AbstractBattleSystem.__init__(self)
        linpg.PauseMenuModuleForGameSystem.__init__(self)
        # 视觉小说模块与参数
        self.__DIALOG: linpg.DialogSystem = linpg.DialogSystem(True)
        # 视觉小说缓存参数
        self.__dialog_parameters: dict = {}
        # 是否对话已经更新
        self.__is_dialog_updated: bool = False
        # 对话id查询用的字典
        self.__dialog_dictionary: dict = {}
        # 对话数据
        self.__dialog_data: dict = {}
        # 当前对话的id
        self.__dialog_key: str = ""
        # 被选中的角色
        self.characterGetClick = None
        self.enemiesGetAttack: dict = {}
        self.action_choice = None
        # 缩进
        self.__zoomIn: int = 100
        self.__zoomIntoBe: int = 100
        # 是否在战斗状态-战斗loop
        self.__is_battle_mode: bool = False
        # 是否在等待
        self.__is_waiting: bool = True
        # 是否是死亡的那个
        self.the_dead_one: dict = {}
        # 谁的回合
        self.whose_round: str = "sangvisFerrisToPlayer"
        # 技能对象
        self.skill_target = None
        # 被救助的那个角色
        self.friendGetHelp = None
        # AI系统正在操控的敌对角色ID
        self.enemies_in_control_id: int = 0
        # 所有敌对角色的名字列表
        self.sangvisFerris_name_list: list = []
        # 战斗状态数据
        self.__result_info: dict = {}
        # 储存角色受到伤害的文字surface
        self.__damage_do_to_characters = {}
        self.txt_alpha: int = None
        # 移动路径
        self.the_route: list = []
        # 上个回合因为暴露被敌人发现的角色
        # 格式：角色：[x,y]
        self.the_characters_detected_last_round: dict = {}
        # 敌人的指令
        self.enemy_instructions = None
        # 敌人当前需要执行的指令
        self.current_instruction = None
        # 积分栏的UI模块
        self.ResultBoardUI = None
        # 对话-动作是否被设置
        self.__dialog_is_route_generated: bool = False
        # 可以互动的物品列表
        self.thingsCanReact: list = []
        # 需要救助的角色列表
        self.friendsCanSave: list = []
        # 启用暂停菜单
        self._enable_pause_menu()
        # 每次需要更新的物品
        self.__items_to_blit: list = []
        # 物品比重
        self.__max_item_weight: int = 0
        # 结束回合的图片
        self.__end_round_button: linpg.StaticImage = None

    """Quick Reference"""
    # 格里芬角色数据
    @property
    def alliances(self) -> dict[str, FriendlyCharacter]:
        return self._entities_data["GriffinKryuger"]  # type: ignore

    # 正在控制的角色
    @property
    def characterInControl(self) -> FriendlyCharacter:
        return self._entities_data["GriffinKryuger"][self.characterGetClick]  # type: ignore

    # 铁血角色数据
    @property
    def enemies(self) -> dict[str, HostileCharacter]:
        return self._entities_data["SangvisFerri"]  # type: ignore

    # 正在控制的铁血角色
    @property
    def enemyInControl(self) -> HostileCharacter:
        return self._entities_data["SangvisFerri"][self.sangvisFerris_name_list[self.enemies_in_control_id]]  # type: ignore

    """加载与储存"""
    # 从存档中加载游戏进程
    def load(self, screen: linpg.ImageSurface) -> None:
        saveData: dict = linpg.config.load_file(os.path.join("Save", "save.yaml"))
        self._initialize(saveData["chapter_type"], saveData["chapter_id"], saveData["project_name"])
        DataToProcess: dict = linpg.config.load_file(self.get_map_file_location())
        DataToProcess.update(saveData)
        if DataToProcess["type"] != "battle":
            raise Exception('Error: Cannot load the data from the "save.yaml" file because the file type does not match')
        self.__process_data(screen, DataToProcess)
        try:
            # 设置对话key
            self.__dialog_key = str(DataToProcess["dialog_key"])
            # 加载视觉小说缓存参数
            self.__dialog_parameters = dict(DataToProcess["dialog_parameters"])
        except Exception:
            self.__dialog_key = ""
            self.__dialog_parameters.clear()
        # 加载战斗状态数据
        self.__result_info = dict(DataToProcess["resultInfo"])

    def new(self, screen: linpg.ImageSurface, chapterType: str, chapterId: int, projectName: Optional[str] = None):
        self._initialize(chapterType, chapterId, projectName)
        # 加载地图与角色数据
        self.__process_data(screen, linpg.config.load_file(self.get_map_file_location()))
        # 如果有战前对话，则设置对话key
        try:
            self.__dialog_key = str(self.__dialog_dictionary["initial"])
        except Exception:
            self.__dialog_key = ""
        # 初始化视觉小说缓存参数
        self.__dialog_parameters.clear()
        # 初始化战斗状态数据
        self.__result_info = {
            "total_rounds": 1,
            "total_kills": 0,
            "total_time": time.time(),
            "times_characters_down": 0,
        }

    # 加载游戏进程
    def __process_data(self, screen: linpg.ImageSurface, DataToProcess: dict) -> None:
        self.window_x, self.window_y = screen.get_size()
        # 加载视觉小说系统
        self.__DIALOG.new(self._chapter_type, self._chapter_id, "dialog_during_battle", self._project_name)
        self.__DIALOG.stop()
        # 生成标准文字渲染器
        self.FONT = linpg.font.create(self.window_x / 76)
        # 加载按钮的文字
        self.selectMenuUI = SelectMenu()
        self.battleModeUiTxt = linpg.lang.get_texts("Battle_UI")
        self.warnings_to_display = WarningSystem(int(screen.get_height() * 0.03))
        loading_info = linpg.lang.get_texts("LoadingTxt")
        # 加载剧情
        DataTmp: dict = linpg.config.load_file(self.__DIALOG.get_dialog_file_location())
        # 如果暂时没有翻译
        if "title" not in DataTmp:
            DataTmp["title"] = linpg.lang.get_text("Global", "no_translation")
        if "description" not in DataTmp:
            DataTmp["description"] = linpg.lang.get_text("Global", "no_translation")
        if "battle_info" not in DataTmp:
            DataTmp["battle_info"] = linpg.config.load(r"Data/chapter_dialogs_example.yaml", "battle_info")
        # 章节标题显示
        self.infoToDisplayDuringLoading = LoadingTitle(
            self.window_x,
            self.window_y,
            self.battleModeUiTxt["numChapter"],
            self._chapter_id,
            DataTmp["title"],
            DataTmp["description"],
        )
        self.battleMode_info = DataTmp["battle_info"]
        # 正在加载的gif动态图标
        nowLoadingIcon = linpg.load.gif(
            r"Assets/image/UI/sv98_walking.gif",
            (int(self.window_x * 0.7), int(self.window_y * 0.83)),
            (int(self.window_x * 0.003 * 15), int(self.window_x * 0.003 * 21)),
        )
        # 渐入效果
        for i in range(1, 255, 2):
            self.infoToDisplayDuringLoading.draw(screen, i)
            linpg.display.flip()
        # 开始加载地图场景
        self.infoToDisplayDuringLoading.draw(screen)
        now_loading = self.FONT.render(loading_info["now_loading_level"], linpg.color.WHITE)
        screen.blit(now_loading, (self.window_x * 0.75, self.window_y * 0.9))
        nowLoadingIcon.draw(screen)
        linpg.display.flip()
        # 背景音乐路径
        self._background_music_folder_path: str = "Assets/music"
        # 设置背景音乐
        self.set_bgm(os.path.join(self._background_music_folder_path, DataToProcess["background_music"]))
        # 加载胜利目标
        self.mission_objectives = DataToProcess["mission_objectives"]
        # 初始化天气和环境的音效 -- 频道1
        self.environment_sound = linpg.SoundManagement(1)
        if DataToProcess["weather"] is not None:
            self.environment_sound.add(os.path.join("Assets/sound/environment", "{}.ogg".format(DataToProcess["weather"])))
            self._weather_system.init(DataToProcess["weather"])
        # 加载对话信息
        self.__dialog_dictionary = dict(DataToProcess["dialogs"]["dictionary"])
        self.__dialog_data = dict(DataToProcess["dialogs"]["data"])
        # 加载对应角色所需的图片
        characterDataLoaderThread: CharacterDataLoader = CharacterDataLoader(DataToProcess["entities"])
        characterDataLoaderThread.start()
        while characterDataLoaderThread.is_alive():
            self.infoToDisplayDuringLoading.draw(screen)
            now_loading = self.FONT.render(
                loading_info["now_loading_characters"]
                + "({}/{})".format(characterDataLoaderThread.currentID, characterDataLoaderThread.totalNum),
                linpg.color.WHITE,
            )
            screen.blit(now_loading, (self.window_x * 0.75, self.window_y * 0.9))
            nowLoadingIcon.draw(screen)
            linpg.display.flip()
        self._entities_data = characterDataLoaderThread.getResult()
        # 开始加载关卡设定
        self.infoToDisplayDuringLoading.draw(screen)
        now_loading = self.FONT.render(loading_info["now_loading_map"], linpg.color.WHITE)
        screen.blit(now_loading, (self.window_x * 0.75, self.window_y * 0.9))
        nowLoadingIcon.draw(screen)
        linpg.display.flip()
        # 加载地图
        self._initialize_map(DataToProcess)
        # 计算光亮区域 并初始化地图
        self.__update_darkness()
        # 加载UI:
        # 加载结束回合的图片
        self.end_round_txt = self.FONT.render(linpg.lang.get_text("Battle_UI", "endRound"), linpg.color.WHITE)
        self.__end_round_button = linpg.load.static_image(
            r"Assets/image/UI/end_round_button.png",
            (self.window_x * 0.8, self.window_y * 0.7),
            (self.end_round_txt.get_width() * 2, self.end_round_txt.get_height() * 2.5),
        )
        # 加载子弹图片
        # bullet_img = load.img("Assets/image/UI/bullet.png", get_block_width()/6, self._MAP.block_height/12)
        # 加载显示获取到补给后的信息栏
        supply_board_width: int = int(self.window_x / 3)
        supply_board_height: int = int(self.window_y / 12)
        supply_board_x: int = int((self.window_x - supply_board_width) / 2)
        self.__supply_board = linpg.load.movable_image(
            r"Assets/image/UI/score.png",
            (supply_board_x, -supply_board_height),
            (supply_board_x, 0),
            (0, int(self.window_y * 0.005)),
            (supply_board_width, supply_board_height),
        )
        self.__supply_board_items: list = []
        self.__supply_board_stayingTime: int = 0
        RangeSystem.update_size(self._MAP.block_width * 4 // 5)
        # 角色信息UI管理
        self.characterInfoBoardUI = CharacterInfoBoard(self.window_x, self.window_y)
        # 加载用于渲染电影效果的上下黑色帘幕
        black_curtain = linpg.surfaces.new((self.window_x, self.window_y // 7))
        black_curtain.fill(linpg.color.BLACK)
        self.__up_black_curtain = linpg.MovableImage(
            black_curtain, 0, -black_curtain.get_height(), 0, 0, 0, int(black_curtain.get_height() * 0.05)
        )
        self.__down_black_curtain = linpg.MovableImage(
            black_curtain,
            0,
            self.window_y,
            0,
            int(self.window_y - black_curtain.get_height()),
            0,
            int(black_curtain.get_height() * 0.051),
        )
        """-----加载音效-----"""
        # 行走的音效 -- 频道0
        self.footstep_sounds = linpg.SoundManagement(0)
        for walkingSoundPath in glob(r"Assets/sound/snow/*.wav"):
            self.footstep_sounds.add(walkingSoundPath)
        # 更新所有音效的音量
        self._update_sound_volume()
        # 攻击的音效 -- 频道2
        AttackingSoundManager.initialize()
        # 切换回合时的UI
        self.RoundSwitchUI = RoundSwitch(self.window_x, self.window_y, self.battleModeUiTxt)
        # 关卡背景介绍信息文字
        for i in range(len(self.battleMode_info)):
            self.battleMode_info[i] = self.FONT.render(self.battleMode_info[i], linpg.color.WHITE, with_bounding=True)
        # 显示章节信息
        for a in range(0, 250, 2):
            self.infoToDisplayDuringLoading.draw(screen)
            for i in range(len(self.battleMode_info)):
                self.battleMode_info[i].set_alpha(a)
                screen.blit(
                    self.battleMode_info[i],
                    (
                        self.window_x / 20,
                        self.window_y * 0.75 + self.battleMode_info[i].get_height() * 1.2 * i,
                    ),
                )
                if i == 1:
                    temp_secode = self.FONT.render(time.strftime(":%S", time.localtime()), linpg.color.WHITE, with_bounding=True)
                    temp_secode.set_alpha(a)
                    screen.blit(
                        temp_secode,
                        (
                            self.window_x / 20 + self.battleMode_info[i].get_width(),
                            self.window_y * 0.75 + self.battleMode_info[i].get_height() * 1.2,
                        ),
                    )
            linpg.display.flip()

    def __update_darkness(self):
        self._MAP.calculate_darkness(self.alliances)  # type: ignore

    # 返回需要保存数据
    def _get_data_need_to_save(self) -> dict:
        return (
            super()._get_data_need_to_save()
            | self._MAP.get_local_pos_in_percentage()
            | {
                "type": "battle",
                "dialog_key": self.__dialog_key,
                "dialog_parameters": self.__dialog_parameters,
                "resultInfo": self.__result_info,
                "timeStamp": time.strftime(":%S", time.localtime()),
            }
        )

    """画面"""
    # 新增需要在屏幕上画出的物品
    def __add_on_screen_object(
        self,
        image: linpg.ImageSurface,
        weight: int = -1,
        pos: tuple[int, int] = linpg.ORIGIN,
        offSet: tuple[int, int] = linpg.ORIGIN,
    ) -> None:
        if weight < 0:
            self.__max_item_weight += 1
            weight = self.__max_item_weight
        elif weight > self.__max_item_weight:
            self.__max_item_weight = weight
        self.__items_to_blit.append(ItemNeedBlit(image, weight, pos, offSet))

    # 更新屏幕
    def __update_scene(self, screen: linpg.ImageSurface) -> None:
        self.__items_to_blit.sort()
        for item in self.__items_to_blit:
            item.draw(screen)
        self.__items_to_blit.clear()
        self.__max_item_weight = 0

    # 胜利失败判定
    def __check_whether_player_win_or_lost(self) -> None:
        # 常规
        """检测失败条件"""
        # 如果有回合限制
        if (
            "round_limitation" in self.mission_objectives
            and self.mission_objectives["round_limitation"] is not None
            and self.mission_objectives["round_limitation"] > 0
            and self.__result_info["total_rounds"] > self.mission_objectives["round_limitation"]
        ):
            self.whose_round = "result_fail"
        # 如果不允许失去任何一位同伴
        if "allow_any_one_die" not in self.mission_objectives or not self.mission_objectives["allow_any_one_die"]:
            for character in self.alliances:
                if self.alliances[character].is_dead():
                    self.whose_round = "result_fail"
                    break
        """检测胜利条件"""
        # 歼灭模式
        if self.mission_objectives["type"] == "annihilation":
            # 检测是否所有敌人都已经被消灭
            if "target" not in self.mission_objectives or self.mission_objectives["target"] is None:
                if len(self.enemies) == 0:
                    self.characterGetClick = None
                    RangeSystem.set_visible(False)
                    self.whose_round = "result_win"
                else:
                    pass
            # 检测是否特定敌人已经被消灭
            elif isinstance(self.mission_objectives["target"], str) and self.mission_objectives["target"] not in self.enemies:
                self.whose_round = "result_win"
            # 检测是否所有给定的目标都已经被歼灭
            elif isinstance(self.mission_objectives["target"], (list, tuple)):
                find_one = False
                for key in self.alliances:
                    if key in self.mission_objectives["target"]:
                        find_one = True
                        break
                if not find_one:
                    self.whose_round = "result_win"

    # 更新音量
    def _update_sound_volume(self) -> None:
        self.footstep_sounds.set_volume(linpg.media.volume.effects / 100)
        self.environment_sound.set_volume(linpg.media.volume.environment / 100.0)
        self.set_bgm_volume(linpg.media.volume.background_music / 100.0)

    # 更新语言
    def update_language(self) -> None:
        super().update_language()
        self._initialize_pause_menu()
        self.selectMenuUI.update()
        self.battleModeUiTxt = linpg.lang.get_texts("Battle_UI")
        self.RoundSwitchUI = RoundSwitch(self.window_x, self.window_y, self.battleModeUiTxt)
        self.end_round_txt = self.FONT.render(linpg.lang.get_text("Battle_UI", "endRound"), linpg.color.WHITE)
        self.__end_round_button = linpg.load.static_image(
            r"Assets/image/UI/end_round_button.png",
            (self.window_x * 0.8, self.window_y * 0.7),
            (self.end_round_txt.get_width() * 2, self.end_round_txt.get_height() * 2.5),
        )
        self.warnings_to_display.update_language()
        self.__DIALOG.update_language()

    # 停止
    def stop(self) -> None:
        self.__DIALOG.stop()
        AttackingSoundManager.release()
        super().stop()

    # 警告某个角色周围的敌人
    def __alert_enemy_around(self, name: str, value: int = 10) -> None:
        enemies_need_check: list = []
        for key in self.enemies:
            if self.enemies[key].range_target_in(self.alliances[name]) >= 0:
                self.enemies[key].alert(value)
                self.characterInControl.notice(value)
                enemies_need_check.append(key)
        for key in enemies_need_check:
            if self.enemies[key].is_alert:
                for character in self.alliances:
                    if self.enemies[key].range_target_in(self.alliances[character]) >= 0:
                        self.alliances[character].notice(100)

    # 切换回合
    def __switch_round(self, screen: linpg.ImageSurface) -> None:
        if self.whose_round == "playerToSangvisFerris" or self.whose_round == "sangvisFerrisToPlayer":
            if self.RoundSwitchUI.draw(screen, self.whose_round, self.__result_info["total_rounds"]):
                if self.whose_round == "playerToSangvisFerris":
                    self.enemies_in_control_id = 0
                    self.sangvisFerris_name_list.clear()
                    any_is_alert = False
                    for every_chara in self.enemies:
                        if self.enemies[every_chara].is_alive():
                            self.sangvisFerris_name_list.append(every_chara)
                            if self.enemies[every_chara].is_alert:
                                any_is_alert = True
                    # 如果有一个铁血角色已经处于完全察觉的状态，则让所有铁血角色进入警觉状态
                    if any_is_alert:
                        for every_chara in self.enemies:
                            self.enemies[every_chara].alert(100)
                    # 让倒地的角色更接近死亡
                    for every_chara in self.alliances:
                        if self.alliances[every_chara].is_dying():
                            self.alliances[every_chara].get_closer_to_death()
                    # 现在是铁血的回合！
                    self.whose_round = "sangvisFerris"
                elif self.whose_round == "sangvisFerrisToPlayer":
                    for key in self.alliances:
                        self.alliances[key].reset_action_point()
                        if not self.alliances[key].is_detected:
                            value_reduce = int(self.alliances[key].detection * 0.3)
                            if value_reduce < 15:
                                value_reduce = 15
                            self.alliances[key].notice(0 - value_reduce)
                    for key in self.enemies:
                        if not self.enemies[key].is_alert:
                            value_reduce = int(self.enemies[key].vigilance * 0.2)
                            if value_reduce < 10:
                                value_reduce = 10
                            self.enemies[key].alert(0 - value_reduce)
                    # 到你了，Good luck, you need it!
                    self.whose_round = "player"
                    self.__result_info["total_rounds"] += 1

    # 角色动画
    def _display_entities(self, screen: linpg.ImageSurface) -> None:
        if not self.__is_battle_mode:
            for every_chara in self.alliances:
                self.alliances[every_chara].draw(screen, self._MAP)
            for enemies in self.enemies:
                if self._MAP.is_coordinate_in_light_rea(self.enemies[enemies].x, self.enemies[enemies].y):
                    self.enemies[enemies].draw(screen, self._MAP)
        else:
            # 画出用彩色方块表示的范围
            RangeSystem.draw(self._MAP, screen)
            # 画出角色
            rightClickCharacterAlphaDeduct = True
            for faction in self._entities_data:
                for key, value in self._entities_data[faction].items():
                    # 如果天亮的双方都可以看见/天黑，但是是友方角色/天黑，但是是敌方角色在可观测的范围内 -- 则画出角色
                    if value.attitude > 0 or self._MAP.is_coordinate_in_light_rea(value.x, value.y):
                        if RangeSystem.get_visible() and linpg.controller.mouse.get_pressed(2):
                            self._block_is_hovering = self._MAP.calculate_coordinate()
                            if (
                                self._block_is_hovering is not None
                                and self._block_is_hovering[0] == value.x
                                and self._block_is_hovering[1] == value.y
                            ):
                                rightClickCharacterAlphaDeduct = False
                                RangeSystem.set_target_alpha(255)
                                RangeSystem.update_attack_range(value.get_effective_range_coordinates(self._MAP))
                        value.draw(screen, self._MAP)
                    else:
                        value.draw(screen, self._MAP, True)
                    # 是否有在播放死亡角色的动画（而不是倒地状态）
                    if not value.is_alive() and key not in self.the_dead_one and (value.kind == "HOC" or value.attitude < 0):
                        self.the_dead_one[key] = value.attitude
                    # 伤害/治理数值显示
                    if key in self.__damage_do_to_characters:
                        the_alpha_to_check = self.__damage_do_to_characters[key].get_alpha()
                        if the_alpha_to_check > 0:
                            xTemp, yTemp = self._MAP.calculate_position(value.x, value.y)
                            xTemp += self._MAP.block_width // 20
                            yTemp -= self._MAP.block_width // 20
                            display_in_center(self.__damage_do_to_characters[key], RangeSystem.get_image(0), xTemp, yTemp, screen)
                            self.__damage_do_to_characters[key].set_alpha(the_alpha_to_check - 5)
                        else:
                            del self.__damage_do_to_characters[key]
            # 调整范围方块的透明度
            if rightClickCharacterAlphaDeduct is True:
                RangeSystem.set_target_alpha(0)
            # 移除死亡的角色
            if len(self.the_dead_one) > 0:
                the_dead_one_remove = []
                for key in self.the_dead_one:
                    if self.the_dead_one[key] < 0:
                        if self.enemies[key].get_imgId("die") == self.enemies[key].get_imgNum("die") - 1:
                            the_alpha = self.enemies[key].get_imgAlpaha("die")
                            if the_alpha > 0:
                                self.enemies[key].set_imgAlpaha("die", the_alpha - 5)
                            else:
                                the_dead_one_remove.append(key)
                                del self.enemies[key]
                                self.__result_info["total_kills"] += 1
                    elif self.the_dead_one[key] > 0:
                        if self.alliances[key].get_imgId("die") == self.alliances[key].get_imgNum("die") - 1:
                            the_alpha = self.alliances[key].get_imgAlpaha("die")
                            if the_alpha > 0:
                                self.alliances[key].set_imgAlpaha("die", the_alpha - 5)
                            else:
                                the_dead_one_remove.append(key)
                                del self.alliances[key]
                                self.__result_info["times_characters_down"] += 1
                                self.__update_darkness()
                for key in the_dead_one_remove:
                    del self.the_dead_one[key]

    # 对话模块
    def __play_dialog(self, screen: linpg.ImageSurface) -> None:
        # 展示天气
        self._weather_system.draw(screen, self._MAP.block_width)
        # 如果战斗有对话
        if len(self.__dialog_key) > 0:
            # 营造电影视觉
            self.__up_black_curtain.move_toward()
            self.__up_black_curtain.draw(screen)
            self.__down_black_curtain.move_toward()
            self.__down_black_curtain.draw(screen)
            # 设定初始化
            if len(self.__dialog_parameters) <= 0:
                self.__dialog_parameters.update(
                    {
                        "dialogId": 0,
                        "charactersPaths": None,
                        "secondsAlreadyIdle": 0,
                        "secondsToIdle": None,
                    }
                )
            # 对话系统总循环
            if self.__dialog_parameters["dialogId"] < len(self.__dialog_data[self.__dialog_key]):
                currentDialog: dict = self.__dialog_data[self.__dialog_key][self.__dialog_parameters["dialogId"]]
                # 如果操作是移动
                if "move" in currentDialog and currentDialog["move"] is not None:
                    # 为所有角色设置路径
                    if not self.__dialog_is_route_generated:
                        routeTmp: list
                        for key, pos in currentDialog["move"].items():
                            if key in self.alliances:
                                routeTmp = self._MAP.find_path(self.alliances[key], pos, self.alliances, self.enemies)
                                if len(routeTmp) > 0:
                                    self.alliances[key].move_follow(routeTmp)
                                else:
                                    raise Exception("Error: Character {} cannot find a valid path!".format(key))
                            elif key in self.enemies:
                                routeTmp = self._MAP.find_path(self.enemies[key], pos, self.enemies, self.alliances)
                                if len(routeTmp) > 0:
                                    self.enemies[key].move_follow(routeTmp)
                                else:
                                    raise Exception("Error: Character {} cannot find a valid path!".format(key))
                            else:
                                raise Exception("Error: Cannot find character {}!".format(key))
                        self.__dialog_is_route_generated = True
                    # 播放脚步声
                    self.footstep_sounds.play()
                    # 是否所有角色都已经到达对应点
                    allGetToTargetPos = True
                    # 是否需要重新渲染地图
                    reProcessMap = False
                    for key in currentDialog["move"]:
                        if key in self.alliances:
                            if not self.alliances[key].is_idle():
                                allGetToTargetPos = False
                            if self.alliances[key].needUpdateMap():
                                reProcessMap = True
                        elif key in self.enemies and not self.enemies[key].is_idle():
                            allGetToTargetPos = False
                        else:
                            raise Exception("Error: Cannot find character {}!".format(key))
                    if reProcessMap:
                        self.__update_darkness()
                    if allGetToTargetPos:
                        # 脚步停止
                        self.footstep_sounds.stop()
                        self.__dialog_parameters["dialogId"] += 1
                        self.__dialog_is_route_generated = False
                # 改变方向
                elif "direction" in currentDialog and currentDialog["direction"] is not None:
                    for key, value in currentDialog["direction"].items():
                        if key in self.alliances:
                            self.alliances[key].set_flip(value)
                        elif key in self.enemies:
                            self.enemies[key].set_flip(value)
                        else:
                            raise Exception("Error: Cannot find character {}!".format(key))
                    self.__dialog_parameters["dialogId"] += 1
                # 改变动作（一次性）
                elif "action" in currentDialog and currentDialog["action"] is not None:
                    for key, action in currentDialog["action"].items():
                        if key in self.alliances:
                            self.alliances[key].set_action(action, False)
                        elif key in self.enemies:
                            self.enemies[key].set_action(action, False)
                    self.__dialog_parameters["dialogId"] += 1
                # 改变动作（长期）
                elif "actionLoop" in currentDialog and currentDialog["actionLoop"] is not None:
                    for key, action in currentDialog["actionLoop"].items():
                        if key in self.alliances:
                            self.alliances[key].set_action(action)
                        elif key in self.enemies:
                            self.enemies[key].set_action(action)
                    self.__dialog_parameters["dialogId"] += 1
                # 开始对话
                elif "dialog" in currentDialog:
                    # 如果当前段落的对话数据还没被更新
                    if not self.__is_dialog_updated:
                        self.__DIALOG.continue_scene(currentDialog["dialog"])
                        self.__is_dialog_updated = True
                    # 如果对话还在播放
                    if self.__DIALOG.is_playing():
                        self.__DIALOG.draw(screen)
                    else:
                        self.__dialog_parameters["dialogId"] += 1
                        self.__is_dialog_updated = False
                # 闲置一定时间（秒）
                elif "idle" in currentDialog and currentDialog["idle"] is not None:
                    if self.__dialog_parameters["secondsToIdle"] is None:
                        self.__dialog_parameters["secondsToIdle"] = currentDialog["idle"] * linpg.display.get_fps()
                    else:
                        if self.__dialog_parameters["secondsAlreadyIdle"] < self.__dialog_parameters["secondsToIdle"]:
                            self.__dialog_parameters["secondsAlreadyIdle"] += 1
                        else:
                            self.__dialog_parameters["dialogId"] += 1
                            self.__dialog_parameters["secondsAlreadyIdle"] = 0
                            self.__dialog_parameters["secondsToIdle"] = None
                # 调整窗口位置
                elif "changePos" in currentDialog and currentDialog["changePos"] is not None:
                    if self._screen_to_move_x is None or self._screen_to_move_y is None:
                        tempX, tempY = self._MAP.calculate_position(
                            currentDialog["changePos"]["x"], currentDialog["changePos"]["y"]
                        )
                        self._screen_to_move_x = int(screen.get_width() / 2 - tempX)
                        self._screen_to_move_y = int(screen.get_height() / 2 - tempY)
                    if self._screen_to_move_x == 0 and self._screen_to_move_y == 0:
                        self._screen_to_move_x = None
                        self._screen_to_move_y = None
                        self.__dialog_parameters["dialogId"] += 1
                else:
                    raise Exception(
                        "Error: Dialog Data on '{0}' with id '{1}' cannot pass through any statement!".format(
                            self.__dialog_key, self.__dialog_parameters["dialogId"]
                        )
                    )
                # 玩家输入按键判定
                if linpg.controller.get_event("back"):
                    self._show_pause_menu(screen)
            else:
                self.__dialog_parameters.clear()
                self.__dialog_key = ""
                self.__is_battle_mode = True
        # 如果战斗前无·对话
        elif len(self.__dialog_key) <= 0:
            # 角色UI
            for every_chara in self.alliances:
                self.alliances[every_chara].drawUI(screen, self._MAP)
            for enemies in self.enemies:
                if self._MAP.is_coordinate_in_light_rea(self.enemies[enemies].x, self.enemies[enemies].y):
                    self.enemies[enemies].drawUI(screen, self._MAP)
            if self.txt_alpha == 0:
                self.__is_battle_mode = True

    # 战斗模块
    def __play_battle(self, screen: linpg.ImageSurface) -> None:
        # 处理基础事件
        skill_range: Optional[dict[str, list]]
        for event in linpg.controller.events:
            if event.type == linpg.key.DOWN:
                if event.key == linpg.key.ESCAPE and self.characterGetClick is None:
                    self._show_pause_menu(screen)
                if event.key == linpg.key.ESCAPE and self.__is_waiting is True:
                    RangeSystem.set_visible(True)
                    self.characterGetClick = None
                    self.action_choice = None
                    skill_range = None
                    RangeSystem.clear()
                self._check_key_down(event)
            elif event.type == linpg.key.UP:
                self._check_key_up(event)
            # 鼠标点击
            elif event.type == linpg.MOUSE_BUTTON_DOWN:
                # 上下滚轮-放大和缩小地图
                if event.button == 4 and self.__zoomIntoBe < 150:
                    self.__zoomIntoBe += 10
                elif event.button == 5 and self.__zoomIntoBe > 50:
                    self.__zoomIntoBe -= 10

        # 玩家回合
        if self.whose_round == "player":
            if linpg.controller.get_event("confirm"):
                # 如果点击了回合结束的按钮
                if self.__end_round_button.is_hovered() and self.__is_waiting is True:
                    self.whose_round = "playerToSangvisFerris"
                    self.characterGetClick = None
                    RangeSystem.set_visible(True)
                    skill_range = None
                    RangeSystem.clear()
                # 是否在显示移动范围后点击了且点击区域在移动范围内
                elif (
                    len(self.the_route) != 0
                    and self._block_is_hovering is not None
                    and (self._block_is_hovering[0], self._block_is_hovering[1]) in self.the_route
                    and not RangeSystem.get_visible()
                ):
                    self.__is_waiting = False
                    RangeSystem.set_visible(True)
                    self.characterInControl.try_reduce_action_point(len(self.the_route) * 2)
                    self.characterInControl.move_follow(self.the_route)
                    RangeSystem.clear()
                elif self.selectMenuUI.item_being_hovered == "attack" and self.characterGetClick is not None:
                    if self.characterInControl.current_bullets > 0 and self.characterInControl.have_enough_action_point(5):
                        self.action_choice = "attack"
                        RangeSystem.set_visible(False)
                        self.selectMenuUI.set_visible(False)
                    elif self.characterInControl.current_bullets <= 0:
                        self.warnings_to_display.add("magazine_is_empty")
                    elif not self.characterInControl.have_enough_action_point(5):
                        self.warnings_to_display.add("no_enough_ap_to_attack")
                elif self.selectMenuUI.item_being_hovered == "move" and self.characterGetClick is not None:
                    if self.characterInControl.have_enough_action_point(2):
                        self.action_choice = "move"
                        RangeSystem.set_visible(False)
                        self.selectMenuUI.set_visible(False)
                    else:
                        self.warnings_to_display.add("no_enough_ap_to_move")
                elif self.selectMenuUI.item_being_hovered == "skill" and self.characterGetClick is not None:
                    if self.characterInControl.have_enough_action_point(8):
                        self.action_choice = "skill"
                        RangeSystem.set_visible(False)
                        self.selectMenuUI.set_visible(False)
                    else:
                        self.warnings_to_display.add("no_enough_ap_to_use_skill")
                elif self.selectMenuUI.item_being_hovered == "reload" and self.characterGetClick is not None:
                    if self.characterInControl.have_enough_action_point(5) and self.characterInControl.bullets_carried > 0:
                        self.action_choice = "reload"
                        RangeSystem.set_visible(False)
                        self.selectMenuUI.set_visible(False)
                    elif self.characterInControl.bullets_carried <= 0:
                        self.warnings_to_display.add("no_bullets_left")
                    elif not self.characterInControl.have_enough_action_point(5):
                        self.warnings_to_display.add("no_enough_ap_to_reload")
                elif self.selectMenuUI.item_being_hovered == "rescue" and self.characterGetClick is not None:
                    if self.characterInControl.have_enough_action_point(8):
                        self.action_choice = "rescue"
                        RangeSystem.set_visible(False)
                        self.selectMenuUI.set_visible(False)
                    else:
                        self.warnings_to_display.add("no_enough_ap_to_rescue")
                elif self.selectMenuUI.item_being_hovered == "interact" and self.characterGetClick is not None:
                    if self.characterInControl.have_enough_action_point(2):
                        self.action_choice = "interact"
                        RangeSystem.set_visible(False)
                        self.selectMenuUI.set_visible(False)
                    else:
                        self.warnings_to_display.add("no_enough_ap_to_interact")
                # 攻击判定
                elif (
                    self.action_choice == "attack"
                    and not RangeSystem.get_visible()
                    and self.characterGetClick is not None
                    and len(self.enemiesGetAttack) > 0
                ):
                    self.characterInControl.try_reduce_action_point(5)
                    self.characterInControl.notice()
                    self.characterInControl.set_action("attack", False)
                    self.__is_waiting = False
                    RangeSystem.set_visible(True)
                    RangeSystem.clear()
                # 技能
                elif (
                    self.action_choice == "skill"
                    and not RangeSystem.get_visible()
                    and self.characterGetClick is not None
                    and self.skill_target is not None
                ):
                    if self.skill_target in self.alliances:
                        self.characterInControl.set_flip_based_on_pos(self.alliances[self.skill_target])
                    elif self.skill_target in self.enemies:
                        self.characterInControl.notice()
                        self.characterInControl.set_flip_based_on_pos(self.enemies[self.skill_target])
                    self.characterInControl.try_reduce_action_point(8)
                    self.characterInControl.play_sound("skill")
                    self.characterInControl.set_action("skill", False)
                    self.__is_waiting = False
                    RangeSystem.set_visible(True)
                    skill_range = None
                    RangeSystem.clear()
                elif (
                    self.action_choice == "rescue"
                    and not RangeSystem.get_visible()
                    and self.characterGetClick is not None
                    and self.friendGetHelp is not None
                ):
                    self.characterInControl.try_reduce_action_point(8)
                    self.characterInControl.notice()
                    self.alliances[self.friendGetHelp].heal(1)
                    self.characterGetClick = None
                    self.action_choice = None
                    self.__is_waiting = True
                    RangeSystem.set_visible(True)
                    RangeSystem.clear()
                    self.__update_darkness()
                elif (
                    self.action_choice == "interact"
                    and not RangeSystem.get_visible()
                    and self.characterGetClick is not None
                    and self.decorationGetClick is not None
                ):
                    self.characterInControl.try_reduce_action_point(2)
                    self._MAP.interact_decoration_with_id(self.decorationGetClick)
                    self.__update_darkness()
                    self.characterGetClick = None
                    self.action_choice = None
                    self.__is_waiting = True
                    RangeSystem.set_visible(True)
                    RangeSystem.clear()
                # 判断是否有被点击的角色
                elif self._block_is_hovering is not None:
                    for key in self.alliances:
                        if (
                            linpg.coordinates.is_same(self.alliances[key], self._block_is_hovering)
                            and self.__is_waiting is True
                            and self.alliances[key].is_alive()
                            and RangeSystem.get_visible()
                        ):
                            self._screen_to_move_x = None
                            self._screen_to_move_y = None
                            skill_range = None
                            RangeSystem.clear()
                            if self.characterGetClick != key:
                                self.alliances[key].play_sound("get_click")
                                self.characterGetClick = key
                            self.characterInfoBoardUI.update()
                            self.friendsCanSave = [
                                key2
                                for key2 in self.alliances
                                if self.alliances[key2].is_dying() and self.alliances[key].near(self.alliances[key2])
                            ]
                            self.thingsCanReact.clear()
                            index = 0
                            for decoration in self._MAP.decorations:
                                if decoration.get_type() == "campfire" and self.alliances[key].near(decoration):
                                    self.thingsCanReact.append(index)
                                index += 1
                            self.selectMenuUI.set_visible(True)
                            break
            # 选择菜单的判定，显示功能在角色动画之后
            if self.selectMenuUI.is_visible() and self.characterGetClick is not None:
                # 移动画面以使得被点击的角色可以被更好的操作
                tempX, tempY = self._MAP.calculate_position(self.characterInControl.x, self.characterInControl.y)
                if self._screen_to_move_x is None:
                    if tempX < self.window_x * 0.2 and self._MAP.get_local_x() <= 0:
                        self._screen_to_move_x = int(self.window_x * 0.2 - tempX)
                    elif tempX > self.window_x * 0.8 and self._MAP.get_local_x() >= self._MAP.column * self._MAP.block_width * -1:
                        self._screen_to_move_x = int(self.window_x * 0.8 - tempX)
                if self._screen_to_move_y is None:
                    if tempY < self.window_y * 0.2 and self._MAP.get_local_y() <= 0:
                        self._screen_to_move_y = int(self.window_y * 0.2 - tempY)
                    elif tempY > self.window_y * 0.8 and self._MAP.get_local_y() >= self._MAP.row * self._MAP.block_height * -1:
                        self._screen_to_move_y = int(self.window_y * 0.8 - tempY)
            # 显示攻击/移动/技能范围
            if not RangeSystem.get_visible() and self.characterGetClick is not None:
                self._block_is_hovering = self._MAP.calculate_coordinate()
                # 显示移动范围
                if self.action_choice == "move":
                    if self._block_is_hovering is not None:
                        # 根据行动值计算最远可以移动的距离
                        max_blocks_can_move = int(self.characterInControl.current_action_point / 2)
                        if (
                            0
                            < abs(self._block_is_hovering[0] - self.characterInControl.x)
                            + abs(self._block_is_hovering[1] - self.characterInControl.y)
                            <= max_blocks_can_move
                        ):
                            self.the_route = self._MAP.find_path(
                                self.characterInControl,
                                self._block_is_hovering,
                                self.alliances,
                                self.enemies,
                                max_blocks_can_move,
                            )
                            if len(self.the_route) > 0:
                                # 显示路径
                                RangeSystem.set_positions(0, self.the_route)
                                xTemp, yTemp = self._MAP.calculate_position(self.the_route[-1][0], self.the_route[-1][1])
                                screen.blit(
                                    self.FONT.render(str(len(self.the_route) * 2), linpg.color.WHITE),
                                    (xTemp + self.FONT.size * 2, yTemp + self.FONT.size),
                                )
                                self.characterInControl.draw_custom("move", (xTemp, yTemp), screen, self._MAP)
                # 显示攻击范围
                elif self.action_choice == "attack":
                    attacking_range: list[list[tuple[int, int]]] = self.characterInControl.get_effective_range_coordinates(
                        self._MAP
                    )
                    RangeSystem.update_attack_range(attacking_range)
                    if self._block_is_hovering is not None:
                        the_attacking_range_area = []
                        for _coordinates in attacking_range:
                            if (self._block_is_hovering[0], self._block_is_hovering[1]) in _coordinates:
                                for y in range(
                                    self._block_is_hovering[1] - self.characterInControl.attack_coverage + 1,
                                    self._block_is_hovering[1] + self.characterInControl.attack_coverage,
                                ):
                                    if y < self._block_is_hovering[1]:
                                        for x in range(
                                            self._block_is_hovering[0]
                                            - self.characterInControl.attack_coverage
                                            - (y - self._block_is_hovering[1])
                                            + 1,
                                            self._block_is_hovering[0]
                                            + self.characterInControl.attack_coverage
                                            + (y - self._block_is_hovering[1]),
                                        ):
                                            if self._MAP.if_block_can_pass_through(x, y):
                                                the_attacking_range_area.append((x, y))
                                    else:
                                        for x in range(
                                            self._block_is_hovering[0]
                                            - self.characterInControl.attack_coverage
                                            + (y - self._block_is_hovering[1])
                                            + 1,
                                            self._block_is_hovering[0]
                                            + self.characterInControl.attack_coverage
                                            - (y - self._block_is_hovering[1]),
                                        ):
                                            if self._MAP.if_block_can_pass_through(x, y):
                                                the_attacking_range_area.append((x, y))
                                break
                        self.enemiesGetAttack.clear()
                        if len(the_attacking_range_area) > 0:
                            RangeSystem.set_positions(4, the_attacking_range_area)
                            for enemies in self.enemies:
                                if self.enemies[enemies].pos in the_attacking_range_area and self.enemies[enemies].is_alive():
                                    self.enemiesGetAttack[enemies] = self.characterInControl.range_target_in(self.enemies[enemies])

                # 显示技能范围
                elif self.action_choice == "skill":
                    self.skill_target = None
                    if self.characterInControl.max_skill_range > 0:
                        if skill_range is None:
                            skill_range = {"near": [], "middle": [], "far": []}
                            for y in range(
                                self.characterInControl.y - self.characterInControl.max_skill_range,
                                self.characterInControl.y + self.characterInControl.max_skill_range + 1,
                            ):
                                if y < self.characterInControl.y:
                                    for x in range(
                                        self.characterInControl.x
                                        - self.characterInControl.max_skill_range
                                        - (y - self.characterInControl.y),
                                        self.characterInControl.x
                                        + self.characterInControl.max_skill_range
                                        + (y - self.characterInControl.y)
                                        + 1,
                                    ):
                                        if self._MAP.row > y >= 0 and self._MAP.column > x >= 0:
                                            if (
                                                "far" in self.characterInControl.skill_effective_range
                                                and self.characterInControl.skill_effective_range["far"] is not None
                                                and self.characterInControl.skill_effective_range["far"][0]
                                                <= abs(x - self.characterInControl.x) + abs(y - self.characterInControl.y)
                                                <= self.characterInControl.skill_effective_range["far"][1]
                                            ):
                                                skill_range["far"].append([x, y])
                                            elif (
                                                "middle" in self.characterInControl.skill_effective_range
                                                and self.characterInControl.skill_effective_range["middle"] is not None
                                                and self.characterInControl.skill_effective_range["middle"][0]
                                                <= abs(x - self.characterInControl.x) + abs(y - self.characterInControl.y)
                                                <= self.characterInControl.skill_effective_range["middle"][1]
                                            ):
                                                skill_range["middle"].append([x, y])
                                            elif (
                                                "near" in self.characterInControl.skill_effective_range
                                                and self.characterInControl.skill_effective_range["near"] is not None
                                                and self.characterInControl.skill_effective_range["near"][0]
                                                <= abs(x - self.characterInControl.x) + abs(y - self.characterInControl.y)
                                                <= self.characterInControl.skill_effective_range["near"][1]
                                            ):
                                                skill_range["near"].append([x, y])
                                else:
                                    for x in range(
                                        self.characterInControl.x
                                        - self.characterInControl.max_skill_range
                                        + (y - self.characterInControl.y),
                                        self.characterInControl.x
                                        + self.characterInControl.max_skill_range
                                        - (y - self.characterInControl.y)
                                        + 1,
                                    ):
                                        if x == self.characterInControl.x and y == self.characterInControl.y:
                                            pass
                                        elif self._MAP.row > y >= 0 and self._MAP.column > x >= 0:
                                            if (
                                                "far" in self.characterInControl.skill_effective_range
                                                and self.characterInControl.skill_effective_range["far"] is not None
                                                and self.characterInControl.skill_effective_range["far"][0]
                                                <= abs(x - self.characterInControl.x) + abs(y - self.characterInControl.y)
                                                <= self.characterInControl.skill_effective_range["far"][1]
                                            ):
                                                skill_range["far"].append([x, y])
                                            elif (
                                                "middle" in self.characterInControl.skill_effective_range
                                                and self.characterInControl.skill_effective_range["middle"] is not None
                                                and self.characterInControl.skill_effective_range["middle"][0]
                                                <= abs(x - self.characterInControl.x) + abs(y - self.characterInControl.y)
                                                <= self.characterInControl.skill_effective_range["middle"][1]
                                            ):
                                                skill_range["middle"].append([x, y])
                                            elif (
                                                "near" in self.characterInControl.skill_effective_range
                                                and self.characterInControl.skill_effective_range["near"] is not None
                                                and self.characterInControl.skill_effective_range["near"][0]
                                                <= abs(x - self.characterInControl.x) + abs(y - self.characterInControl.y)
                                                <= self.characterInControl.skill_effective_range["near"][1]
                                            ):
                                                skill_range["near"].append([x, y])
                        RangeSystem.update_attack_range(skill_range)
                        self._block_is_hovering = self._MAP.calculate_coordinate()
                        if self._block_is_hovering is not None:
                            the_skill_cover_area = []
                            for area in skill_range:
                                if [
                                    self._block_is_hovering[0],
                                    self._block_is_hovering[1],
                                ] in skill_range[area]:
                                    for y in range(
                                        self._block_is_hovering[1] - self.characterInControl.skill_coverage,
                                        self._block_is_hovering[1] + self.characterInControl.skill_coverage,
                                    ):
                                        if y < self._block_is_hovering[1]:
                                            for x in range(
                                                self._block_is_hovering[0]
                                                - self.characterInControl.skill_coverage
                                                - (y - self._block_is_hovering[1])
                                                + 1,
                                                self._block_is_hovering[0]
                                                + self.characterInControl.skill_coverage
                                                + (y - self._block_is_hovering[1]),
                                            ):
                                                if (
                                                    self._MAP.row > y >= 0
                                                    and self._MAP.column > x >= 0
                                                    and self._MAP.if_block_can_pass_through(x, y)
                                                ):
                                                    the_skill_cover_area.append([x, y])
                                        else:
                                            for x in range(
                                                self._block_is_hovering[0]
                                                - self.characterInControl.skill_coverage
                                                + (y - self._block_is_hovering[1])
                                                + 1,
                                                self._block_is_hovering[0]
                                                + self.characterInControl.skill_coverage
                                                - (y - self._block_is_hovering[1]),
                                            ):
                                                if (
                                                    self._MAP.row > y >= 0
                                                    and self._MAP.column > x >= 0
                                                    and self._MAP.if_block_can_pass_through(x, y)
                                                ):
                                                    the_skill_cover_area.append([x, y])
                                    RangeSystem.set_positions(4, the_skill_cover_area)
                                    self.skill_target = self.characterInControl.get_entity_in_skill_effective_range(
                                        self.alliances, self.enemies, self._block_is_hovering
                                    )
                                    break
                    else:
                        self.skill_target = self.characterInControl.get_entity_in_skill_effective_range(
                            self.alliances, self.enemies, self._block_is_hovering
                        )
                        if len(self.skill_target) > 0:
                            self.characterInControl.try_reduce_action_point(8)
                            self.__is_waiting = False
                            RangeSystem.set_visible(True)
                # 换弹
                elif self.action_choice == "reload":
                    bullets_to_add = self.characterInControl.is_reload_needed()
                    # 需要换弹
                    if bullets_to_add > 0:
                        # 如果角色有换弹动画，则播放角色的换弹动画
                        if self.characterInControl.get_imgId("reload") != -1:
                            self.characterInControl.set_action("reload", False)
                        # 扣去对应的行动值
                        self.characterInControl.try_reduce_action_point(5)
                        # 换弹
                        self.characterInControl.reload_magazine()
                        self.__is_waiting = True
                        self.characterGetClick = None
                        self.action_choice = None
                        RangeSystem.set_visible(True)
                    # 无需换弹
                    else:
                        self.warnings_to_display.add("magazine_is_full")
                        self.selectMenuUI.set_visible(True)
                elif self.action_choice == "rescue":
                    RangeSystem.clear()
                    self.friendGetHelp = None
                    for friendNeedHelp in self.friendsCanSave:
                        if (
                            self._block_is_hovering is not None
                            and self._block_is_hovering[0] == self.alliances[friendNeedHelp].x
                            and self._block_is_hovering[1] == self.alliances[friendNeedHelp].y
                        ):
                            RangeSystem.set_positions(4, [(self._block_is_hovering[0], self._block_is_hovering[1])])
                            self.friendGetHelp = friendNeedHelp
                        else:
                            RangeSystem.append_position(0, (self.alliances[friendNeedHelp].x, self.alliances[friendNeedHelp].y))
                elif self.action_choice == "interact":
                    RangeSystem.clear()
                    self.decorationGetClick = None
                    for index in self.thingsCanReact:
                        decoration = self._MAP.find_decoration_with_id(index)
                        if self._block_is_hovering is not None and decoration.is_on_pos(self._block_is_hovering):
                            RangeSystem.set_positions(4, [(self._block_is_hovering[0], self._block_is_hovering[1])])
                            self.decorationGetClick = index
                        else:
                            RangeSystem.append_position(0, (decoration.x, decoration.y))

            # 当有角色被点击时
            if self.characterGetClick is not None and not self.__is_waiting:
                # 被点击的角色动画
                RangeSystem.set_visible(True)
                if self.action_choice == "move":
                    if not self.characterInControl.is_idle():
                        # 播放脚步声
                        self.footstep_sounds.play()
                        # 是否需要更新
                        if self.characterInControl.needUpdateMap():
                            self.__alert_enemy_around(self.characterGetClick)
                            self.__update_darkness()
                    else:
                        self.footstep_sounds.stop()
                        # 检测是不是站在补给上
                        decoration = self._MAP.find_decoration_on(self.characterInControl.get_pos())
                        if decoration is not None and decoration.get_type() == "chest":
                            if self.characterGetClick in decoration.whitelist:
                                # 清空储存列表
                                self.__supply_board_items.clear()
                                # 将物品按照类型放入列表
                                for itemType, itemData in decoration.items.items():
                                    if itemType == "bullet":
                                        self.characterInControl.add_bullets_carried(itemData)
                                        self.__supply_board_items.append(
                                            self.FONT.render(
                                                self.battleModeUiTxt["getBullets"] + ": " + str(itemData),
                                                linpg.color.WHITE,
                                            )
                                        )
                                    elif itemType == "hp":
                                        self.characterInControl.heal(itemData)
                                        self.__supply_board_items.append(
                                            self.FONT.render(
                                                self.battleModeUiTxt["getHealth"] + ": " + str(itemData),
                                                linpg.color.WHITE,
                                            )
                                        )
                                # 如果UI已经回到原位
                                if len(self.__supply_board_items) > 0:
                                    self.__supply_board.move_toward()
                                # 移除箱子
                                self._MAP.remove_decoration(decoration)
                        # 检测当前所在点是否应该触发对话
                        name_from_by_pos = str(self.characterInControl.x) + "-" + str(self.characterInControl.y)
                        if "move" in self.__dialog_dictionary and name_from_by_pos in self.__dialog_dictionary["move"]:
                            dialog_to_check = self.__dialog_dictionary["move"][name_from_by_pos]
                            if "whitelist" not in dialog_to_check or self.characterGetClick in dialog_to_check["whitelist"]:
                                self.__dialog_key = str(dialog_to_check["dialog_key"])
                                self.__is_battle_mode = False
                                # 如果对话不重复，则删除（默认不重复）
                                if "repeat" not in dialog_to_check or not dialog_to_check["repeat"]:
                                    del dialog_to_check
                        # 玩家可以继续选择需要进行的操作
                        self.__is_waiting = True
                        self.characterGetClick = None
                        self.action_choice = None
                elif self.action_choice == "attack":
                    # 根据敌我坐标判断是否需要反转角色
                    if self.characterInControl.get_imgId("attack") == 0:
                        self._block_is_hovering = self._MAP.calculate_coordinate()
                        if self._block_is_hovering is not None:
                            self.characterInControl.set_flip_based_on_pos(self._block_is_hovering)
                        self.characterInControl.play_sound("attack")
                    # 播放射击音效
                    elif self.characterInControl.get_imgId("attack") == 3:
                        AttackingSoundManager.play(self.characterInControl.kind)
                    if self.characterInControl.get_imgId("attack") == self.characterInControl.get_imgNum("attack") - 2:
                        for each_enemy in self.enemiesGetAttack:
                            if (
                                self.enemiesGetAttack[each_enemy] == "near"
                                and linpg.get_random_int(1, 100) <= 95
                                or self.enemiesGetAttack[each_enemy] == "middle"
                                and linpg.get_random_int(1, 100) <= 80
                                or self.enemiesGetAttack[each_enemy] == "far"
                                and linpg.get_random_int(1, 100) <= 65
                            ):
                                the_damage = self.characterInControl.attack(self.enemies[each_enemy])
                                self.__damage_do_to_characters[each_enemy] = self.FONT.render(
                                    "-" + str(the_damage), linpg.color.RED
                                )
                                self.enemies[each_enemy].alert(100)
                            else:
                                self.__damage_do_to_characters[each_enemy] = self.FONT.render("Miss", linpg.color.RED)
                                self.enemies[each_enemy].alert(50)
                    elif self.characterInControl.get_imgId("attack") == self.characterInControl.get_imgNum("attack") - 1:
                        self.characterInControl.subtract_current_bullets()
                        self.__is_waiting = True
                        self.characterGetClick = None
                        self.action_choice = None
                elif self.action_choice == "skill":
                    if self.characterInControl.get_imgId("skill") == self.characterInControl.get_imgNum("skill") - 2:
                        self.__damage_do_to_characters = self.__skill(
                            self.characterGetClick, None, None, "react", self.skill_target, self.__damage_do_to_characters
                        )
                    elif self.characterInControl.get_imgId("skill") == self.characterInControl.get_imgNum("skill") - 1:
                        self.__update_darkness()
                        self.__is_waiting = True
                        self.characterGetClick = None
                        self.action_choice = None

        # 敌方回合
        if self.whose_round == "sangvisFerris":
            # 如果当前角色还没做出决定
            if self.enemy_instructions is None:
                # 生成决定
                self.enemy_instructions = self.enemyInControl.make_decision(
                    self._MAP, self.alliances, self.enemies, self.the_characters_detected_last_round
                )
            if not len(self.enemy_instructions) == 0 or self.current_instruction is not None:
                # 获取需要执行的指令
                if self.current_instruction is None:
                    self.current_instruction = self.enemy_instructions.popleft()
                    if self.current_instruction.action == "move":
                        self.enemyInControl.move_follow(self.current_instruction.route)
                    elif self.current_instruction.action == "attack":
                        self.enemyInControl.set_flip_based_on_pos(self.alliances[self.current_instruction.target])
                        self.enemyInControl.set_action("attack")
                # 根据选择调整动画
                if self.current_instruction.action == "move":
                    if not self.enemyInControl.is_idle():
                        self.footstep_sounds.play()
                    else:
                        self.footstep_sounds.stop()
                        self.current_instruction = None
                elif self.current_instruction.action == "attack":
                    if self.enemyInControl.get_imgId("attack") == 3:
                        AttackingSoundManager.play(self.enemyInControl.kind)
                    elif self.enemyInControl.get_imgId("attack") == self.enemyInControl.get_imgNum("attack") - 1:
                        temp_value = linpg.get_random_int(0, 100)
                        if (
                            self.current_instruction.target_area == "near"
                            and temp_value <= 95
                            or self.current_instruction.target_area == "middle"
                            and temp_value <= 80
                            or self.current_instruction.target_area == "far"
                            and temp_value <= 65
                        ):
                            the_damage = self.enemyInControl.attack(self.alliances[self.current_instruction.target])
                            # 如果角色进入倒地或者死亡状态，则应该将times_characters_down加一
                            if not self.alliances[self.current_instruction.target].is_alive():
                                self.__result_info["times_characters_down"] += 1
                            # 重新计算迷雾区域
                            self.__update_darkness()
                            self.__damage_do_to_characters[self.current_instruction.target] = self.FONT.render(
                                "-" + str(the_damage), linpg.color.RED
                            )
                        else:
                            self.__damage_do_to_characters[self.current_instruction.target] = self.FONT.render(
                                "Miss", linpg.color.RED
                            )
                        self.current_instruction = None
            else:
                self.enemyInControl.set_action()
                self.enemies_in_control_id += 1
                self.enemy_instructions = None
                self.current_instruction = None
                if self.enemies_in_control_id >= len(self.sangvisFerris_name_list):
                    self.whose_round = "sangvisFerrisToPlayer"

        # 展示所有角色Ui
        for _alliance in self.alliances.values():
            _alliance.drawUI(screen, self._MAP)
        for _enemy in self.enemies.values():
            if self._MAP.is_coordinate_in_light_rea(int(_enemy.x), int(_enemy.y)):
                _enemy.drawUI(screen, self._MAP)
        if self.characterGetClick is not None:
            the_coord: tuple[int, int] = self._MAP.calculate_position(self.characterInControl.x, self.characterInControl.y)
            # 显示选择菜单
            self.selectMenuUI.draw(
                screen,
                round(self._MAP.block_width / 10),
                {
                    "xStart": the_coord[0],
                    "xEnd": the_coord[0] + self._MAP.block_width,
                    "yStart": the_coord[1],
                    "yEnd": the_coord[1] + self._MAP.block_width * 0.5,
                },
                self.characterInControl.kind,
                self.friendsCanSave,
                self.thingsCanReact,
            )
            # 左下角的角色信息
            if self.selectMenuUI.is_visible():
                self.characterInfoBoardUI.draw(screen, self.characterInControl)
        # 展示天气
        self._weather_system.draw(screen, self._MAP.block_width)
        # 移除电影视觉
        self.__up_black_curtain.move_back()
        self.__up_black_curtain.draw(screen)
        self.__down_black_curtain.move_back()
        self.__down_black_curtain.draw(screen)
        # 其他移动的检查
        self._check_right_click_move()
        self._check_jostick_events()
        # 检测回合是否结束
        self.__switch_round(screen)
        # 检测玩家是否胜利或失败
        self.__check_whether_player_win_or_lost()

        # 显示获取到的物资
        if self.__supply_board.has_reached_target():
            if self.__supply_board.is_moving_toward_target():
                if self.__supply_board_stayingTime >= 30:
                    self.__supply_board.move_back()
                    self.__supply_board_stayingTime = 0
                else:
                    self.__supply_board_stayingTime += 1
            elif len(self.__supply_board_items) > 0:
                self.__supply_board_items.clear()
        if len(self.__supply_board_items) > 0:
            self.__add_on_screen_object(self.__supply_board)
            lenTemp = 0
            for i in range(len(self.__supply_board_items)):
                lenTemp += self.__supply_board_items[i].get_width() * 1.5
            start_point = (self.window_x - lenTemp) / 2
            for i in range(len(self.__supply_board_items)):
                start_point += self.__supply_board_items[i].get_width() * 0.25
                self.__add_on_screen_object(
                    self.__supply_board_items[i],
                    -1,
                    (start_point, (self.__supply_board.get_height() - self.__supply_board_items[i].get_height()) / 2),
                    (0, self.__supply_board.y),
                )
                start_point += self.__supply_board_items[i].get_width() * 1.25

        if self.whose_round == "player":
            # 加载结束回合的按钮
            self.__add_on_screen_object(self.__end_round_button)
            self.__add_on_screen_object(
                self.end_round_txt,
                -1,
                self.__end_round_button.pos,
                (
                    int(self.__end_round_button.get_width() * 0.35),
                    int((self.__end_round_button.get_height() - self.FONT.size) / 2.3),
                ),
            )

        # 显示警告
        self.__add_on_screen_object(self.warnings_to_display)

        # 结束动画--胜利
        if self.whose_round == "result_win":
            if self.ResultBoardUI is None:
                self.__result_info["total_time"] = time.localtime(time.time() - self.__result_info["total_time"])
                self.ResultBoardUI = ResultBoard(self.__result_info, self.window_x // 96)
            for event in linpg.controller.events:
                if event.type == linpg.key.DOWN:
                    if event.key == linpg.key.SPACE:
                        self.__is_battle_mode = False
                        self.stop()
            self.__add_on_screen_object(self.ResultBoardUI)
        # 结束动画--失败
        elif self.whose_round == "result_fail":
            if self.ResultBoardUI is None:
                self.__result_info["total_time"] = time.localtime(time.time() - self.__result_info["total_time"])
                self.ResultBoardUI = ResultBoard(self.__result_info, self.window_x // 96, False)
            for event in linpg.controller.events:
                if event.type == linpg.key.DOWN:
                    if event.key == linpg.key.SPACE:
                        linpg.media.unload()
                        chapter_info: dict = self.get_data_of_parent_game_system()
                        self.__init__()
                        self.new(screen, chapter_info["chapter_type"], chapter_info["chapter_id"], chapter_info["project_name"])
                        break
                    elif event.key == linpg.key.BACKSPACE:
                        linpg.media.unload()
                        self.stop()
                        self.__is_battle_mode = False
                        break
            if self.ResultBoardUI is not None:
                self.__add_on_screen_object(self.ResultBoardUI)

    # 把战斗系统的画面画到screen上
    def draw(self, screen: linpg.ImageSurface) -> None:
        # 环境声音-频道1
        self.environment_sound.play()
        # 调整并更新地图大小
        if self.__zoomIntoBe != self.__zoomIn:
            if self.__zoomIntoBe < self.__zoomIn:
                self.__zoomIn -= 10
            elif self.__zoomIntoBe > self.__zoomIn:
                self.__zoomIn += 10
            self._MAP.set_tile_block_size(
                self._standard_block_width * self.__zoomIn / 100, self._standard_block_height * self.__zoomIn / 100
            )
            # 根据block尺寸重新加载对应尺寸的UI
            RangeSystem.update_size(self._MAP.block_width * 4 // 5)
            self.selectMenuUI.update()
        # 画出地图
        self._display_map(screen)
        # 游戏主循环
        if self.__is_battle_mode is True:
            self.play_bgm()
            # 营造电影视觉
            self.__up_black_curtain.move_toward()
            self.__down_black_curtain.move_toward()
            self.__play_battle(screen)
        # 在战斗状态
        else:
            self.__play_dialog(screen)
        # 渐变效果：一次性的
        if self.txt_alpha is None:
            self.txt_alpha = 250
        if self.txt_alpha > 0:
            self.infoToDisplayDuringLoading.black_bg.set_alpha(self.txt_alpha)
            self.infoToDisplayDuringLoading.draw(screen, self.txt_alpha)
            for i in range(len(self.battleMode_info)):
                self.battleMode_info[i].set_alpha(self.txt_alpha)
                screen.blit(
                    self.battleMode_info[i],
                    (self.window_x / 20, self.window_y * 0.75 + self.battleMode_info[i].get_height() * 1.2 * i),
                )
                if i == 1:
                    temp_secode = self.FONT.render(time.strftime(":%S", time.localtime()), linpg.color.WHITE, with_bounding=True)
                    temp_secode.set_alpha(self.txt_alpha)
                    screen.blit(
                        temp_secode,
                        (
                            self.window_x / 20 + self.battleMode_info[i].get_width(),
                            self.window_y * 0.75 + self.battleMode_info[i].get_height() * 1.2,
                        ),
                    )
            self.txt_alpha -= 5
        # 刷新画面
        self.__update_scene(screen)
