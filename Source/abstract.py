import threading
from .map import *


# 加载模块
class LoadingModule:
    def __init__(self) -> None:
        # 当前正在加载的数据的信息 - 已经预处理
        self.__now_loading: Optional[linpg.ImageSurface] = None
        # 多线程锁
        self.__THREADING_LOCK: threading.Lock = threading.Lock()
        # 加载信息
        self.__loading_info_msg: dict[str, str] = {}
        # 文字模块
        self.__FONT: linpg.FontGenerator = linpg.font.create(
            linpg.display.get_width() / 76
        )
        # 正在加载的gif动态图标
        self.__loading_icon: Optional[linpg.AnimatedImage] = None
        # 是否初始化
        self.__initialized = False

    # 初始化加载模块
    def _initialize_loading_module(self) -> None:
        self.__initialize_loading_info_msg()
        self.__loading_icon = linpg.load.gif(
            r"Assets/image/UI/sv98_walking.gif",
            (
                int(linpg.display.get_width() * 0.7),
                int(linpg.display.get_height() * 0.83),
            ),
            (
                int(linpg.display.get_width() * 0.003 * 15),
                int(linpg.display.get_width() * 0.003 * 21),
            ),
        )
        self.__initialized = True
        # 开始加载
        self._update_loading_info("now_loading_level")

    # 初始化加载信息
    def __initialize_loading_info_msg(self) -> None:
        self.__loading_info_msg.clear()
        self.__loading_info_msg.update(linpg.lang.get_texts("LoadingTxt"))

    # 完成加载 - 释放内存
    def _finish_loading(self) -> None:
        self.__now_loading = None
        self.__loading_info_msg.clear()
        self.__loading_icon = None
        self.__initialized = False

    # 更新当前正在加载的数据的信息
    def __update_loading_info(self, text: str) -> None:
        self.__THREADING_LOCK.acquire()
        self.__now_loading = self.__FONT.render(text, linpg.colors.WHITE)
        self.__THREADING_LOCK.release()

    # 根据key更新当前正在加载的数据的信息
    def _update_loading_info(self, _key: str) -> None:
        self.__update_loading_info(self.__loading_info_msg[_key])

    # 获取文字模块
    @property
    def _FONT(self) -> linpg.FontGenerator:
        return self.__FONT

    # 获取角色数据 - 子类需实现
    def get_entities_data(self) -> dict[str, dict[str, linpg.Entity]]:
        raise NotImplementedError()

    # 加载角色所需的图片
    def _load_entities(self, _entities: dict, _mode: str) -> None:
        totalNum: int = 0
        for key in _entities:
            totalNum += len(_entities[key])
            self.get_entities_data()[key] = {}
        if not self.__initialized:
            self._initialize_loading_module()
        currentID: int = 0
        data_t: dict
        for key, value in _entities["GriffinKryuger"].items():
            data_t = deepcopy(linpg.Entity.get_entity_data(value["type"]))
            data_t.update(value)
            self.get_entities_data()["GriffinKryuger"][key] = Dolls.new(
                data_t, _mode, value["type"]
            )
            currentID += 1
            self.__update_loading_info(
                self.__loading_info_msg["now_loading_characters"]
                + "({}/{})".format(currentID, totalNum)
            )
        for key, value in _entities["SangvisFerri"].items():
            data_t = deepcopy(linpg.Entity.get_entity_data(value["type"]))
            data_t.update(value)
            self.get_entities_data()["SangvisFerri"][key] = HostileCharacter(
                data_t, _mode
            )
            currentID += 1
            self.__update_loading_info(
                self.__loading_info_msg["now_loading_characters"]
                + "({}/{})".format(currentID, totalNum)
            )

    # 显示正在加载的数据信息
    def _show_current_loading_progress(self, screen: linpg.ImageSurface) -> None:
        self.__THREADING_LOCK.acquire()
        if self.__now_loading is not None:
            screen.blit(
                self.__now_loading,
                (screen.get_width() * 0.75, screen.get_height() * 0.9),
            )
        if self.__loading_icon is not None:
            self.__loading_icon.draw(screen)
        self.__THREADING_LOCK.release()


# 基础战斗系统框架
class AbstractBattleSystemWithInGameDialog(
    LoadingModule, linpg.AbstractBattleSystem, linpg.PauseMenuModuleForGameSystem
):
    def __init__(self) -> None:
        LoadingModule.__init__(self)
        linpg.AbstractBattleSystem.__init__(self)
        linpg.PauseMenuModuleForGameSystem.__init__(self)
        self.set_map(AdvancedTileMap())
        # 视觉小说模块与参数
        self.__DIALOG: linpg.VisualNovelSystem = linpg.VisualNovelSystem()
        self.__DIALOG.disable_basic_features()
        # 视觉小说缓存参数
        self.__dialog_parameters: dict = {}
        # 是否对话已经更新
        self.__is_dialog_updated: bool = False
        # 对话数据
        self.__dialog_data: dict = {}
        # 当前对话的id
        self.__dialog_key: str = ""
        # 对话-动作是否被设置
        self.__dialog_is_route_generated: bool = False
        # 行走的音效 -- 频道0
        self._footstep_sounds: linpg.SoundsManager = linpg.SoundsManager(0)
        # 启用暂停菜单
        self._enable_pause_menu()

    """Quick Reference"""

    # 格里芬角色数据
    @property
    def alliances(self) -> dict[str, FriendlyCharacter]:
        return self._entities_data["GriffinKryuger"]  # type: ignore

    # 正在控制的格里芬角色
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

    """关键重写或实现"""

    # 加载图片 - 重写使其更新加载信息
    def _load_map(self, _data: dict) -> None:
        self._update_loading_info("now_loading_map")
        super()._load_map(_data)

    # 获取角色数据的字典 - 加载模块父类要求实现
    def get_entities_data(self) -> dict[str, dict[str, linpg.Entity]]:
        return self._entities_data

    # 更新语言
    def update_language(self) -> None:
        super().update_language()
        self._initialize_pause_menu()
        self.__DIALOG.update_language()

    def stop(self) -> None:
        self.__DIALOG.stop()
        self._footstep_sounds.clear()
        super().stop()

    def _get_data_need_to_save(self) -> dict:
        return (
            super()._get_data_need_to_save()
            | self.get_map().get_local_pos_in_percentage()
            | {
                "dialog_key": self.__dialog_key,
                "dialog_parameters": self.__dialog_parameters,
            }
        )

    # 角色动画
    def _display_entities(self, screen: linpg.ImageSurface) -> None:
        for _alliance in self.alliances.values():
            _alliance.render(screen, self.get_map())
        for _enemy in self.enemies.values():
            if self.get_map().is_coordinate_in_lit_area(_enemy.x, _enemy.y):
                _enemy.render(screen, self.get_map())

    # 更新音量
    def _update_sound_volume(self) -> None:
        self._footstep_sounds.set_volume(linpg.volume.get_effects() / 100)
        self.set_bgm_volume(linpg.volume.get_background_music() / 100.0)

    """其他"""

    def _get_level_info(self) -> dict:
        return linpg.config.try_load_file_if_exists(
            self.get_data_file_path().replace(
                "_map", "_level_info_" + linpg.setting.get_language()
            )
        )

    # 初始化视觉小说系统
    def _init_dialog(self, _data: dict) -> None:
        self.__dialog_data.clear()
        self.__DIALOG.new(
            self._chapter_type,
            self._chapter_id,
            "dialog_during_battle",
            self._project_name,
        )
        self.__DIALOG.stop()
        if len(_data) > 0:
            self.__dialog_data.update(_data)

    # 更新视觉小说系统使其开始播放特定的对话
    def _update_dialog(self, _key: str, _parameters: dict = {}) -> None:
        # 设置对话key
        self.__dialog_key = _key
        if len(_parameters) > 0 and len(self.__dialog_key) > 0:
            # 加载视觉小说缓存参数
            self.__dialog_parameters = _parameters
        else:
            # 初始化视觉小说缓存参数
            self.__dialog_parameters.clear()

    # 是否当前有任何对话在播放
    def _is_any_dialog_playing(self) -> bool:
        return len(self.__dialog_key) > 0

    # 更新正在被照亮的区域
    def _update_darkness(self) -> None:
        self.get_map().refresh_lit_area(self.alliances)

    # 渲染到屏幕上
    def draw(self, screen: linpg.ImageSurface) -> None:
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
        if self.__dialog_parameters["dialogId"] < len(
            self.__dialog_data[self.__dialog_key]
        ):
            currentDialog: dict = self.__dialog_data[self.__dialog_key][
                self.__dialog_parameters["dialogId"]
            ]
            # 如果操作是移动
            if "move" in currentDialog and currentDialog["move"] is not None:
                # 为所有角色设置路径
                if not self.__dialog_is_route_generated:
                    routeTmp: list
                    for key, pos in currentDialog["move"].items():
                        if key in self.alliances:
                            routeTmp = self.get_map().find_path(
                                self.alliances[key].get_coordinate(),
                                linpg.Coordinates.convert(pos),
                                self.alliances,
                                self.enemies,
                                True,
                            )
                            if len(routeTmp) > 0:
                                self.alliances[key].move_follow(routeTmp)
                            else:
                                raise Exception(
                                    "Error: Character {} cannot find a valid path!".format(
                                        key
                                    )
                                )
                        elif key in self.enemies:
                            routeTmp = self.get_map().find_path(
                                self.enemies[key].get_coordinate(),
                                linpg.Coordinates.convert(pos),
                                self.enemies,
                                self.alliances,
                                True,
                            )
                            if len(routeTmp) > 0:
                                self.enemies[key].move_follow(routeTmp)
                            else:
                                raise Exception(
                                    "Error: Character {} cannot find a valid path!".format(
                                        key
                                    )
                                )
                        else:
                            raise Exception(
                                "Error: Cannot find character {}!".format(key)
                            )
                    self.__dialog_is_route_generated = True
                # 播放脚步声
                self._footstep_sounds.play()
                # 是否所有角色都已经到达对应点
                allGetToTargetPos = True
                # 是否需要重新渲染地图
                reProcessMap: bool = False
                for key in currentDialog["move"]:
                    if key in self.alliances:
                        if not self.alliances[key].is_idle():
                            allGetToTargetPos = False
                        if self.alliances[key].just_entered_a_new_tile():
                            reProcessMap = True
                    elif key in self.enemies and not self.enemies[key].is_idle():
                        allGetToTargetPos = False
                    else:
                        raise Exception("Error: Cannot find character {}!".format(key))
                if reProcessMap is True:
                    self._update_darkness()
                if allGetToTargetPos:
                    # 脚步停止
                    self._footstep_sounds.stop()
                    self.__dialog_parameters["dialogId"] += 1
                    self.__dialog_is_route_generated = False
            # 改变方向
            elif currentDialog.get("direction") is not None:
                for key, value in currentDialog["direction"].items():
                    if key in self.alliances:
                        self.alliances[key].set_flip(value)
                    elif key in self.enemies:
                        self.enemies[key].set_flip(value)
                    else:
                        raise Exception("Error: Cannot find character {}!".format(key))
                self.__dialog_parameters["dialogId"] += 1
            # 改变动作（一次性）
            elif currentDialog.get("action") is not None:
                for key, action in currentDialog["action"].items():
                    if key in self.alliances:
                        self.alliances[key].set_action(action, False)
                    elif key in self.enemies:
                        self.enemies[key].set_action(action, False)
                self.__dialog_parameters["dialogId"] += 1
            # 改变动作（长期）
            elif currentDialog.get("actionLoop") is not None:
                for key, action in currentDialog["actionLoop"].items():
                    if key in self.alliances:
                        self.alliances[key].set_action(action)
                    elif key in self.enemies:
                        self.enemies[key].set_action(action)
                self.__dialog_parameters["dialogId"] += 1
            # 开始对话
            elif currentDialog.get("dialog") is not None:
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
            elif currentDialog.get("idle") is not None:
                if self.__dialog_parameters["secondsToIdle"] is None:
                    self.__dialog_parameters["secondsToIdle"] = (
                        currentDialog["idle"] * linpg.display.get_current_fps()
                    )
                else:
                    if (
                        self.__dialog_parameters["secondsAlreadyIdle"]
                        < self.__dialog_parameters["secondsToIdle"]
                    ):
                        self.__dialog_parameters["secondsAlreadyIdle"] += 1
                    else:
                        self.__dialog_parameters["dialogId"] += 1
                        self.__dialog_parameters["secondsAlreadyIdle"] = 0
                        self.__dialog_parameters["secondsToIdle"] = None
            # 调整窗口位置
            elif currentDialog.get("changePos") is not None:
                tempX, tempY = self.get_map().calculate_position(
                    currentDialog["changePos"]["x"], currentDialog["changePos"]["y"]
                )
                tempX -= self.get_map().local_x
                tempY -= self.get_map().local_y
                self.get_map().set_local_pos(
                    linpg.numbers.keep_int_in_range(
                        screen.get_width() // 2 - tempX,
                        screen.get_width() - self.get_map().get_width(),
                        0,
                    ),
                    linpg.numbers.keep_int_in_range(
                        screen.get_height() // 2 - tempY,
                        screen.get_height() - self.get_map().get_height(),
                        0,
                    ),
                )
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
            self._update_dialog("")
