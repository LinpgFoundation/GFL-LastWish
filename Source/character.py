import threading
from collections import deque
from copy import deepcopy
from typing import Optional, Sequence
from .api import *


# 友方角色被察觉的图标管理模块
class FriendlyCharacterDynamicProgressBarSurface(linpg.DynamicProgressBarSurface):

    # 指向储存角色被察觉图标的指针
    __FULLY_EXPOSED_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>eye_red.png")
    __BEING_NOTICED_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>eye_orange.png")

    def __init__(self) -> None:
        super().__init__(self.__FULLY_EXPOSED_IMG, self.__BEING_NOTICED_IMG, 0, 0, 0, 0)


# 敌方角色警觉度的图标管理模块
class HostileCharacterDynamicProgressBarSurface(linpg.DynamicProgressBarSurface):

    # 指向储存敌方角色警觉程度图标的指针
    __ORANGE_VIGILANCE_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>vigilance_orange.png")
    __RED_VIGILANCE_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>vigilance_red.png")

    def __init__(self) -> None:
        super().__init__(self.__RED_VIGILANCE_IMG, self.__ORANGE_VIGILANCE_IMG, 0, 0, 0, 0, "vertical")


# 角色血条图片管理模块
class EntityHpBar(linpg.DynamicProgressBarSurface):

    # 指向储存血条图片的指针
    __HP_GREEN_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>hp_green.png")
    __HP_RED_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>hp_red.png")
    __HP_EMPTY_IMG: linpg.ImageSurface = linpg.images.quickly_load("<&ui>hp_empty.png")

    def __init__(self) -> None:
        # 是否角色死亡
        self.__is_dying: bool = False
        # 初始化父类
        super().__init__(self.__HP_GREEN_IMG, self.__HP_EMPTY_IMG, 0, 0, 0, 0)

    # 获取上方图片
    def _get_img_on_top(self) -> linpg.ImageSurface:
        return super()._get_img_on_top() if not self.__is_dying else self.__HP_RED_IMG

    def set_dying(self, value: bool) -> None:
        self.__is_dying = value


# 角色受伤立绘图形模块
class EntityGetHurtImage(linpg.Square):

    # 存储角色受伤立绘的常量
    __CHARACTERS_GET_HURT_IMAGE_DICT: dict = {}

    def __init__(self, self_type: str, y: linpg.int_f, width: linpg.int_f):
        super().__init__(0, y, width)
        self.delay: int = 255
        self.alpha: int = 0
        self.add(self_type)

    def draw(self, screen: linpg.ImageSurface, characterType: str) -> None:  # type: ignore[override]
        _image = linpg.images.resize(self.__CHARACTERS_GET_HURT_IMAGE_DICT[characterType], self.size)
        if self.alpha != 255:
            _image.set_alpha(self.alpha)
        screen.blit(_image, self.pos)

    def add(self, characterType: str) -> None:
        if characterType not in self.__CHARACTERS_GET_HURT_IMAGE_DICT:
            self.__CHARACTERS_GET_HURT_IMAGE_DICT[characterType] = linpg.images.quickly_load(
                linpg.Specification.get_directory("character_image", "{}_hurt.png".format(characterType))
            )


# 基础角色类
class BasicEntity(linpg.Entity):

    # 攻击所需的AP
    AP_IS_NEEDED_TO_ATTACK: int = 5
    AP_IS_NEEDED_TO_MOVE_ONE_BLOCK: int = 2
    # 濒死回合限制
    DYING_ROUND_LIMIT: int = 3

    def __init__(self, characterData: dict, mode: str) -> None:
        super().__init__(characterData, mode)
        # 血条图片
        self.__hp_bar: EntityHpBar = EntityHpBar()
        self.__status_font: linpg.StaticTextSurface = linpg.StaticTextSurface("", 0, 0, linpg.display.get_width() / 192)

    # 把角色ui画到屏幕上
    def _drawUI(self, surface: linpg.ImageSurface, MAP_POINTER: linpg.MapObject, customHpData: Optional[tuple] = None) -> tuple:
        xTemp, yTemp = MAP_POINTER.calculate_position(self.x, self.y)
        xTemp += MAP_POINTER.block_width // 4
        yTemp -= MAP_POINTER.block_width // 5
        self.__hp_bar.set_size(MAP_POINTER.block_width / 2, MAP_POINTER.block_width / 10)
        self.__hp_bar.set_pos(xTemp, yTemp)
        # 预处理血条图片
        if customHpData is None:
            self.__hp_bar.set_percentage(self.current_hp / self.max_hp)
            self.__hp_bar.set_dying(False)
            self.__status_font.set_text("{0}/{1}".format(self.current_hp, self.max_hp))
        else:
            self.__hp_bar.set_percentage(customHpData[0] / customHpData[1])
            self.__hp_bar.set_dying(customHpData[2])
            self.__status_font.set_text("{0}/{1}".format(customHpData[0], customHpData[1]))
        # 把血条画到屏幕上
        self.__hp_bar.draw(surface)
        self.__status_font.set_pos(
            self.__hp_bar.x + (self.__hp_bar.get_width() - self.__status_font.get_width()) // 2,
            self.__hp_bar.y + (self.__hp_bar.get_height() - self.__status_font.get_height()) // 2,
        )
        self.__status_font.draw(surface)
        # 返回坐标以供子类进行处理
        return xTemp, yTemp


# 友方角色类
class FriendlyCharacter(BasicEntity):
    def __init__(self, characterData: dict, mode: str) -> None:
        super().__init__(characterData, mode)
        # 是否濒死
        self.__down_time: int = (
            int(characterData["down_time"])
            if "down_time" in characterData
            else (-1 if self.is_alive() else self.DYING_ROUND_LIMIT)
        )
        # 当前弹夹的子弹数
        self.__current_bullets: int = (
            int(characterData["current_bullets"]) if "current_bullets" in characterData else self.magazine_capacity
        )
        # 当前携带子弹数量
        _bullets_carried = characterData.get("bullets_carried")
        self.__bullets_carried: int = int(_bullets_carried) if _bullets_carried is not None else 100
        # 技能覆盖范围
        self.__skill_coverage: int = int(characterData["skill_coverage"])
        # 技能施展范围
        self.__skill_effective_range: tuple[int, ...] = (
            tuple(_data) if (_data := characterData.get("skill_effective_range")) is not None else tuple()
        )
        # 技能的类型 【0 - 伤害，1 - 治疗己方】
        self.__skill_type: int = int(characterData.get("skill_type", -1))
        # 被察觉程度
        self.__detection: int = (
            int(characterData["detection"]) if "detection" in characterData and characterData["detection"] is not None else 0
        )
        # 生成被察觉的图标
        self.__beNoticedImage: FriendlyCharacterDynamicProgressBarSurface = FriendlyCharacterDynamicProgressBarSurface()
        self.__beNoticedImage.set_percentage(self.__detection / 100)
        # 重创立绘
        self.__getHurtImage: Optional[EntityGetHurtImage] = None
        # 设置态度flag
        self.set_attitude(1)
        # 尝试加载重创立绘
        try:
            self.__getHurtImage = EntityGetHurtImage(self.type, linpg.display.get_height() // 4, linpg.display.get_height() // 2)
        except Exception:
            print("Character {} does not have damaged artwork!".format(self.type))
            self.__getHurtImage = None
            if not os.path.exists(linpg.Specification.get_directory("character_icon", "{}.png".format(self.type))):
                print("And also its icon.")

    def to_dict(self) -> dict:
        # 获取父类信息
        new_data: dict = super().to_dict()
        # 写入子类独有信息
        new_data.update(
            {
                "bullets_carried": self.__bullets_carried,
                "skill_coverage": self.__skill_coverage,
                "skill_effective_range": list(self.__skill_effective_range),
            }
        )
        # 除去重复数据
        o_data: dict = dict(self.get_enity_data(new_data["type"]))
        _keys: tuple = tuple(new_data.keys())
        for key in _keys:
            if key in o_data and o_data[key] == new_data[key]:
                del new_data[key]
        """加入友方角色可选数据"""
        if self.__current_bullets != self.magazine_capacity:
            new_data["current_bullets"] = self.__current_bullets
        if self.__detection > 0:
            new_data["detection"] = self.__detection
        if not self.is_alive():
            new_data["down_time"] = self.__down_time
        # 返回优化后的数据
        return new_data

    """
    子弹
    """

    # 当前子弹携带数量
    @property
    def bullets_carried(self) -> int:
        return self.__bullets_carried

    # 增加当前子弹携带数量
    def add_bullets_carried(self, value: int) -> None:
        self.__bullets_carried += value

    # 当前子弹数量
    @property
    def current_bullets(self) -> int:
        return self.__current_bullets

    # 减少当前子弹数量
    def subtract_current_bullets(self, value: int = 1) -> None:
        self.__current_bullets -= value

    # 是否需要换弹
    def is_reload_needed(self) -> int:
        return self.magazine_capacity - self.__current_bullets > 0

    # 换弹
    def reload_magazine(self) -> None:
        bullets_to_add: int = self.magazine_capacity - self.__current_bullets
        # 当所剩子弹足够换弹的时候
        if bullets_to_add < self.__bullets_carried:
            self.__current_bullets += bullets_to_add
            self.__bullets_carried -= bullets_to_add
        # 当所剩子弹不足以换弹的时候
        else:
            self.__current_bullets += self.__bullets_carried
            self.__bullets_carried = 0

    """
    技能
    """

    # 技能覆盖范围
    @property
    def skill_coverage(self) -> int:
        return self.__skill_coverage

    # 技能施展范围
    @property
    def skill_effective_range(self) -> tuple[int, ...]:
        return self.__skill_effective_range

    # 获取技能有效范围内的所有坐标
    def get_skill_effective_range_coordinates(
        self, MAP_P: linpg.AbstractMap, ifHalfMode: bool = False
    ) -> list[list[tuple[int, int]]]:
        return self.generate_range_coordinates(
            int(self.x), int(self.y), self.__skill_effective_range, MAP_P, self._if_flip, ifHalfMode
        )

    # 获取
    def get_entity_in_skill_effective_range(self, alliances: dict, enemies: dict, center_pos: tuple[int, int]) -> tuple[str, ...]:
        _targets: list[str] = []
        if self.__skill_type == 0:
            _targets = [
                key
                for key, value in enemies
                if abs(int(value.x - center_pos[0])) + abs(int(value.y - center_pos[1])) <= self.__skill_coverage
                and value.current_hp > 0
            ]
        elif self.__skill_type == 1:
            _targets = [
                key
                for key, value in alliances.items()
                if abs(int(value.x - center_pos[0])) + abs(int(value.y - center_pos[1])) <= self.__skill_coverage
            ]
        return tuple(_targets)

    def get_skill_coverage_coordinates(self, _x: int, _y: int, MAP_P: linpg.AbstractMap) -> list[tuple[int, int]]:
        return (
            self.generate_coverage_coordinates(_x, _y, self.__skill_coverage, MAP_P)
            if abs(round(self.x) - _x) + abs(round(self.y) - _y) <= sum(self.__skill_effective_range)
            else []
        )

    def apply_skill(self, alliances: dict, enemies: dict, _targets: tuple[str, ...]) -> dict:
        results: dict[str, tuple[int, int]] = {}
        if self.__skill_type == 0:
            the_damage: int = 0
            for key in _targets:
                the_damage = linpg.get_random_int(self.min_damage, self.max_damage)
                enemies[key].injury(the_damage)
                results[key] = (0, the_damage)
        return results

    # 是否处于濒死状态
    def is_dying(self) -> bool:
        return self.__down_time > 0

    # 更加面临死亡
    def get_closer_to_death(self) -> None:
        self.__down_time -= 1

    # 角色彻底死亡
    def is_dead(self) -> bool:
        return self.__down_time == 0

    @property
    def detection(self) -> int:
        return self.__detection

    @property
    def is_detected(self) -> bool:
        return self.__detection >= 100

    # 调整角色的隐蔽度
    def notice(self, value: int = 10) -> None:
        self.__detection += value
        if self.__detection > 100:
            self.__detection = 100
        elif self.__detection < 0:
            self.__detection = 0
        self.__beNoticedImage.set_percentage(self.__detection / 100)

    def injury(self, damage: int) -> None:
        super().injury(damage)
        # 如果角色在被攻击后处于濒死状态
        if not self.is_alive() and self.__down_time < 0 and self.kind != "HOC":
            self.__down_time = self.DYING_ROUND_LIMIT
            if self.__getHurtImage is not None:
                self.__getHurtImage.move_left(self.__getHurtImage.width)
                self.__getHurtImage.alpha = 255
                self.__getHurtImage.delay = 255
                self.play_sound("injured")

    def heal(self, hpHealed: int) -> None:
        super().heal(hpHealed)
        if self.__down_time >= 0:
            self.__down_time = -1
            self._if_play_action_in_reversing = True

    def drawUI(self, surface: linpg.ImageSurface, MAP_POINTER: linpg.MapObject) -> None:
        customHpData: Optional[tuple] = None if self.__down_time < 0 else (self.__down_time, self.DYING_ROUND_LIMIT, True)
        blit_pos = super()._drawUI(surface, MAP_POINTER, customHpData)
        # 展示被察觉的程度
        if self.__detection > 0:
            # 参数
            eyeImgWidth: int = round(MAP_POINTER.block_width / 6)
            eyeImgHeight: int = round(MAP_POINTER.block_width / 10)
            numberX: float = (eyeImgWidth - MAP_POINTER.block_width / 6) / 2
            numberY: float = (eyeImgHeight - MAP_POINTER.block_width / 10) / 2
            # 根据参数调整图片
            self.__beNoticedImage.set_size(eyeImgWidth, eyeImgHeight)
            self.__beNoticedImage.set_pos(blit_pos[0] + MAP_POINTER.block_width * 0.51 - numberX, blit_pos[1] - numberY)
            self.__beNoticedImage.draw(surface)
        # 重创立绘
        if self.__getHurtImage is not None and self.__getHurtImage.alpha > 0:
            self.__getHurtImage.draw(surface, self.type)
            if self.__getHurtImage.x < self.__getHurtImage.width / 4:
                self.__getHurtImage.move_right(self.__getHurtImage.width / 25)
            else:
                if self.__getHurtImage.delay > 0:
                    self.__getHurtImage.delay -= 5
                elif self.__getHurtImage.alpha > 0:
                    self.__getHurtImage.alpha -= 5


# 敌对角色类
class HostileCharacter(BasicEntity):

    # 用于存放角色做出的决定
    class __DecisionHolder:
        def __init__(self, action: str, data: Sequence):
            self.action: str = action
            self.data = data

        @property
        def route(self) -> list:
            if self.action != "move":
                raise Exception("The character does not decide to move!")
            return list(self.data)

        @property
        def target(self) -> str:
            if self.action != "attack":
                raise Exception("The character does not decide to attack!")
            return str(self.data[0])

        @property
        def target_area(self) -> int:
            if self.action != "attack":
                raise Exception("The character does not decide to attack!")
            return int(self.data[1])

    def __init__(self, characterData: dict, mode: str) -> None:
        super().__init__(characterData, mode)
        self.__patrol_path: deque = deque(characterData["patrol_path"]) if "patrol_path" in characterData else deque()
        self.__vigilance: int = int(characterData["vigilance"]) if "vigilance" in characterData else 0
        self.__vigilanceImage: HostileCharacterDynamicProgressBarSurface = HostileCharacterDynamicProgressBarSurface()
        self.__vigilanceImage.set_percentage(self.__vigilance / 100)
        # 设置态度flag
        self.set_attitude(-1)

    def to_dict(self) -> dict:
        # 获取父类信息
        new_data: dict = super().to_dict()
        # 写入子类独有信息
        if len(self.__patrol_path) > 0:
            new_data["patrol_path"] = list(self.__patrol_path)
        # 除去重复数据
        o_data: dict = self.get_enity_data(new_data["type"])
        _keys: tuple = tuple(new_data.keys())
        for key in _keys:
            if key in o_data and o_data[key] == new_data[key]:
                del new_data[key]
        """加入敌方角色可选数据"""
        if self.__vigilance > 0:
            new_data["vigilance"] = self.__vigilance
        # 返回优化后的数据
        return new_data

    def alert(self, value: int = 10) -> None:
        self.__vigilance += value
        # 防止警觉度数值超过阈值
        if self.__vigilance > 100:
            self.__vigilance = 100
        elif self.__vigilance < 0:
            self.__vigilance = 0
        else:
            pass
        self.__vigilanceImage.set_percentage(self.__vigilance / 100)

    @property
    def vigilance(self) -> int:
        return self.__vigilance

    @property
    def is_alert(self) -> bool:
        return self.__vigilance >= 100

    # 画UI - 列如血条
    def drawUI(self, surface: linpg.ImageSurface, MAP_POINTER: linpg.MapObject) -> None:
        blit_pos = super()._drawUI(surface, MAP_POINTER)
        # 展示警觉的程度
        if self.__vigilance > 0:
            # 参数
            eyeImgWidth: int = round(MAP_POINTER.block_width / 6)
            eyeImgHeight: int = round(MAP_POINTER.block_width / 6)
            numberX: float = (eyeImgWidth - MAP_POINTER.block_width / 6) / 2
            numberY: float = (eyeImgHeight - MAP_POINTER.block_width / 10) / 2
            # 根据参数调整图片
            self.__vigilanceImage.set_size(eyeImgWidth, eyeImgHeight)
            self.__vigilanceImage.set_pos(blit_pos[0] + MAP_POINTER.block_width * 0.51 - numberX, blit_pos[1] - numberY)
            self.__vigilanceImage.draw(surface)

    def make_decision(
        self,
        MAP_POINTER: linpg.MapObject,
        friendlyCharacters: dict,
        hostileCharacters: dict,
        characters_detected_last_round: dict,
    ) -> deque:
        # 存储友方角色价值榜
        target_value_board = []
        for name, theCharacter in friendlyCharacters.items():
            if theCharacter.is_alive() and theCharacter.is_detected:
                weight: int = 0
                # 计算距离的分数
                weight += int(abs(self.x - theCharacter.x) + abs(self.y - theCharacter.y))
                # 计算血量分数
                weight += int(self.current_hp * self.hp_precentage)
                target_value_board.append((name, weight))
        # 最大移动距离
        blocks_can_move: int = self.max_action_point // self.AP_IS_NEEDED_TO_MOVE_ONE_BLOCK
        # 角色将会在该回合采取的行动
        actions: deque = deque()
        # 如果角色有可以攻击的对象，且角色至少有足够的行动点数攻击
        if len(target_value_board) > 0 and self.max_action_point > self.AP_IS_NEEDED_TO_ATTACK:
            action_point_can_use = self.max_action_point
            # 筛选分数最低的角色作为目标
            target = target_value_board[0][0]
            min_weight = target_value_board[0][1]
            for data in target_value_board[1:]:
                if data[1] < min_weight:
                    min_weight = data[1]
                    target = data[0]
            targetCharacterData = friendlyCharacters[target]
            if self.range_target_in(targetCharacterData) >= 0:
                actions.append(self.__DecisionHolder("attack", tuple((target, self.range_target_in(targetCharacterData)))))
                action_point_can_use -= self.AP_IS_NEEDED_TO_ATTACK
                """
                if action_point_can_use > AP_IS_NEEDED_TO_ATTACK:
                    if self.hp_precentage > 0.2:
                        #如果自身血量正常，则应该考虑再次攻击角色
                        actions.append(self.__DecisionHolder("attack",target))
                        action_point_can_use -= AP_IS_NEEDED_TO_ATTACK
                    else:
                        pass
                """
            else:
                # 寻找一条能到达该角色附近的线路
                the_route = MAP_POINTER.find_path(
                    self.pos, targetCharacterData.pos, hostileCharacters, friendlyCharacters, blocks_can_move, [target]
                )
                if len(the_route) > 0:
                    potential_attacking_pos_area = -1
                    potential_attacking_pos_index = 0
                    o_pos = self.pos
                    for i in range(len(the_route) - self.AP_IS_NEEDED_TO_ATTACK // self.AP_IS_NEEDED_TO_MOVE_ONE_BLOCK + 1):
                        # 当前正在处理的坐标
                        self.set_pos(*the_route[i])
                        # 获取可能的攻击范围
                        areaT = self.range_target_in(targetCharacterData)
                        if areaT >= 0 and areaT < potential_attacking_pos_area:
                            potential_attacking_pos_area = areaT
                            potential_attacking_pos_index = i
                            if potential_attacking_pos_area == 0:
                                break
                    self.set_pos(*o_pos)
                    if potential_attacking_pos_area >= 0:
                        actions.append(self.__DecisionHolder("move", the_route[:potential_attacking_pos_index]))
                        actions.append(self.__DecisionHolder("attack", (target, potential_attacking_pos_area)))
                    else:
                        actions.append(self.__DecisionHolder("move", the_route))
                else:
                    raise Exception("A hostile character cannot find a valid path when trying to attack {}!".format(target))
        # 如果角色没有可以攻击的对象，则查看角色是否需要巡逻
        elif len(self.__patrol_path) > 0:
            # 如果巡逻坐标点只有一个（意味着角色需要在该坐标上长期镇守）
            if len(self.__patrol_path) == 1:
                if not linpg.coordinates.is_same(self.pos, self.__patrol_path[0]):
                    the_route = MAP_POINTER.find_path(
                        self.pos, self.__patrol_path[0], hostileCharacters, friendlyCharacters, blocks_can_move
                    )
                    if len(the_route) > 0:
                        actions.append(self.__DecisionHolder("move", the_route))
                    else:
                        raise Exception("A hostile character cannot find a valid path!")
                else:
                    # 如果角色在该点上，则原地待机
                    pass
            # 如果巡逻坐标点有多个
            else:
                the_route = MAP_POINTER.find_path(
                    self.pos, self.__patrol_path[0], hostileCharacters, friendlyCharacters, blocks_can_move
                )
                if len(the_route) > 0:
                    actions.append(self.__DecisionHolder("move", the_route))
                    # 如果角色在这次移动后到达了最近的巡逻点，则应该更新最近的巡逻点
                    if linpg.coordinates.is_same(the_route[-1], self.__patrol_path[0]):
                        self.__patrol_path.append(self.__patrol_path.popleft())
                else:
                    raise Exception("A hostile character cannot find a valid path!")
        else:
            pass
        # 放回一个装有指令的列表
        return actions


# 初始化角色信息
class CharacterDataLoader(threading.Thread):
    def __init__(self, entities: dict[str, dict], mode: str = "default") -> None:
        super().__init__()
        self.__entities: dict[str, dict] = deepcopy(entities)
        self.totalNum: int = 0
        for key in self.__entities:
            self.totalNum += len(self.__entities[key])
        self.currentID: int = 0
        self.mode: str = mode

    def run(self) -> None:
        data_t: dict
        for key, value in self.__entities["GriffinKryuger"].items():
            data_t = deepcopy(linpg.Entity.get_enity_data(value["type"]))
            data_t.update(value)
            self.__entities["GriffinKryuger"][key] = FriendlyCharacter(data_t, self.mode)
            self.currentID += 1
            if linpg.debug.get_developer_mode():
                print("total: {0}, current: {1}".format(self.totalNum, self.currentID))
        for key, value in self.__entities["SangvisFerri"].items():
            data_t = deepcopy(linpg.Entity.get_enity_data(value["type"]))
            data_t.update(value)
            self.__entities["SangvisFerri"][key] = HostileCharacter(data_t, self.mode)
            self.currentID += 1
            if linpg.debug.get_developer_mode():
                print("total: {0}, current: {1}".format(self.totalNum, self.currentID))

    def getResult(self) -> dict[str, dict]:
        return self.__entities


# 射击音效
class AttackingSoundManager:

    __channel_id: int = 2
    __SOUNDS: dict[str, list] = {}

    @classmethod
    def initialize(cls) -> None:
        path_p: tuple = ("Assets", "sound", "attack")
        cls.__SOUNDS.clear()
        cls.__SOUNDS.update(
            {
                # 突击步枪
                "AR": glob(os.path.join(*path_p, "ar_*.ogg")),
                # 手枪
                "HG": glob(os.path.join(*path_p, "hg_*.ogg")),
                # 机枪
                "MG": glob(os.path.join(*path_p, "mg_*.ogg")),
                # 步枪
                "RF": glob(os.path.join(*path_p, "rf_*.ogg")),
                # 冲锋枪
                "SMG": glob(os.path.join(*path_p, "smg_*.ogg")),
            }
        )
        for key in cls.__SOUNDS:
            for i in range(len(cls.__SOUNDS[key])):
                cls.__SOUNDS[key][i] = linpg.sound.load(cls.__SOUNDS[key][i])

    # 播放
    @classmethod
    def play(cls, kind: str) -> None:
        sounds_c: Optional[list] = cls.__SOUNDS.get(kind)
        if sounds_c is not None:
            sound_to_play = sounds_c[linpg.get_random_int(0, len(sounds_c) - 1)]
            sound_to_play.set_volume(linpg.media.volume.effects / 100.0)
            linpg.sound.play(sound_to_play, cls.__channel_id)

    # 释放内存
    @classmethod
    def release(cls) -> None:
        cls.__SOUNDS.clear()
