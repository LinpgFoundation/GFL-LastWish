from ..base import linpg


# 生存类游戏战斗系统
class SurvivalBattleSystem(linpg.AbstractBattleSystem):
    def __init__(self):
        """data"""
        super().__init__()
        # 用于检测是否有方向键被按到的字典
        self.__pressKeyToMoveMe = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
        }
        self.window_x, self.window_y = linpg.display.get_size()
        self.DATABASE = linpg.loadCharacterData()
        self.original_UI_img = {
            "green": linpg.load.img("Assets/image/UI/range/green.png"),
            "red": linpg.load.img("Assets/image/UI/range/red.png"),
            "yellow": linpg.load.img("Assets/image/UI/range/yellow.png"),
            "blue": linpg.load.img("Assets/image/UI/range/blue.png"),
            "orange": linpg.load.img("Assets/image/UI/range/orange.png"),
            "eyeImg": linpg.ProgressBarSurface(
                "Assets/image/UI/eye_red.png",
                "Assets/image/UI/eye_orange.png",
                0,
                0,
                0,
                0,
            ),
            "vigilanceImg": linpg.ProgressBarSurface(
                "Assets/image/UI/vigilance_red.png",
                "Assets/image/UI/vigilance_orange.png",
                0,
                0,
                0,
                0,
                "height",
            ),
            "supplyBoard": linpg.load.dynamic_image(
                r"Assets/image/UI/score.png",
                ((self.window_x - self.window_x / 3) / 2, -self.window_y / 12),
                (self.window_x / 3, self.window_y / 12),
            ),
        }
        """init"""
        # shutil.copyfile("Data/chapter_map_example.yaml","Save/map1.yaml")
        mapFileData = linpg.config.load("Save/map1.yaml")
        SnowEnvImg = [
            "TileSnow01",
            "TileSnow01ToStone01",
            "TileSnow01ToStone02",
            "TileSnow02",
            "TileSnow02ToStone01",
            "TileSnow02ToStone02",
        ]
        block_y = 50
        block_x = 50
        default_map = [
            [SnowEnvImg[linpg.get_random_int(0, len(SnowEnvImg) - 1)] for a in range(block_x)] for i in range(block_y)
        ]
        mapFileData["map"] = default_map
        self.MAP = linpg.MapObject(
            mapFileData,
            round(linpg.display.get_width() / 10),
            round(linpg.display.get_height() / 10),
            True,
        )
        self.alliances = {"me": linpg.FriendlyCharacter(mapFileData["character"]["sv-98"], self.DATABASE["sv-98"])}
        self.MAP.calculate_darkness(self.alliances)
        self.pos_last = self.alliances["me"].get_pos()

    def _check_key_down(self, event: object) -> None:
        super()._check_key_down(event)
        if event.unicode == "w":
            self.__pressKeyToMoveMe["up"] = True
        if event.unicode == "s":
            self.__pressKeyToMoveMe["down"] = True
        if event.unicode == "a":
            self.__pressKeyToMoveMe["left"] = True
        if event.unicode == "d":
            self.__pressKeyToMoveMe["right"] = True

    def _check_key_up(self, event: object) -> None:
        super()._check_key_up(event)
        if event.unicode == "w":
            self.__pressKeyToMoveMe["up"] = False
        if event.unicode == "s":
            self.__pressKeyToMoveMe["down"] = False
        if event.unicode == "a":
            self.__pressKeyToMoveMe["left"] = False
        if event.unicode == "d":
            self.__pressKeyToMoveMe["right"] = False

    def _check_if_move_screen(self) -> None:
        super()._check_if_move_screen()
        ifDisplayMove = False
        if self.__pressKeyToMoveMe["up"]:
            self.alliances["me"].y -= 0.03
            self.alliances["me"].x -= 0.03
            ifDisplayMove = True
        if self.__pressKeyToMoveMe["down"]:
            self.alliances["me"].y += 0.03
            self.alliances["me"].x += 0.03
            ifDisplayMove = True
        if self.__pressKeyToMoveMe["left"]:
            self.alliances["me"].x -= 0.03
            self.alliances["me"].y += 0.03
            ifDisplayMove = True
            self.alliances["me"].set_flip(True)
        if self.__pressKeyToMoveMe["right"]:
            self.alliances["me"].x += 0.03
            self.alliances["me"].y -= 0.03
            ifDisplayMove = True
            self.alliances["me"].set_flip(False)
        if ifDisplayMove:
            if self.alliances["me"].get_action() != "move":
                self.alliances["me"].set_action("move")
            if self.pos_last != (
                int(self.alliances["me"].x),
                int(self.alliances["me"].y),
            ):
                self.MAP.calculate_darkness(self.alliances)
                self.pos_last = (
                    int(self.alliances["me"].x),
                    int(self.alliances["me"].y),
                )
        else:
            if self.alliances["me"].get_action() != "wait":
                self.alliances["me"].set_action("wait")

    # 根据本地坐标移动屏幕
    def _move_screen(self) -> None:
        tempX, tempY = self.MAP.calPosInMap(self.alliances["me"].x, self.alliances["me"].y)
        if tempX < self.window_x * 0.3 and self.MAP.get_local_x() <= 0:
            self.screen_to_move_x = self.window_x * 0.3 - tempX
        elif tempX > self.window_x * 0.7 and self.MAP.get_local_x() >= self.MAP.column * self.MAP.block_width * -1:
            self.screen_to_move_x = self.window_x * 0.7 - tempX
        if tempY < self.window_y * 0.3 and self.MAP.get_local_y() <= 0:
            self.screen_to_move_y = self.window_y * 0.3 - tempY
        elif tempY > self.window_y * 0.7 and self.MAP.get_local_y() >= self.MAP.row * self.MAP.block_height * -1:
            self.screen_to_move_y = self.window_y * 0.7 - tempY
        super()._move_screen()

    # 展示场景装饰物
    def _display_decoration(self, screen: linpg.ImageSurface) -> None:
        self.MAP.display_decoration(screen, self.alliances, {})

    # 把所有内容画到屏幕上
    def draw(self, screen: linpg.ImageSurface) -> None:
        for event in linpg.controller.events:
            if event.type == linpg.key.DOWN:
                if event.key == linpg.key.ESCAPE:
                    self.stop()
                self._check_key_down(event)
            elif event.type == linpg.key.UP:
                self._check_key_up(event)
        # 其他移动的检查
        self._check_right_click_move()
        # 画出地图
        self._display_map(screen)
        self.alliances["me"].draw(screen, self.MAP)
        self.alliances["me"].drawUI(screen, self.original_UI_img, self.MAP)
        # 展示设施
        self._display_decoration(screen)
        pos_x, pos_y = self.MAP.calPosInMap(self.alliances["me"].x, self.alliances["me"].y)
        pos_x += linpg.display.get_width() / 20
        # pygame.draw.line(screen,linpg.color.RED,(pos_x,pos_y),(mouse_x,mouse_y),5)
        linpg.display.flip()
