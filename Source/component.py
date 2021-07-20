from . import gamemode
from .base import *


# blit载入页面
def get_loading_screen() -> linpg.ImageSurface:
    window_x, window_y = linpg.display.get_size()
    font_size: int = int(window_x / 64)
    surface_t = linpg.new_surface((window_x, window_y)).convert()
    surface_t.fill(linpg.color.BLACK)
    # 获取健康游戏忠告
    HealthyGamingAdvice = linpg.lang.try_to_get_text("HealthyGamingAdvice")
    if HealthyGamingAdvice == "HealthyGamingAdvice":
        HealthyGamingAdvice = []
    else:
        for i in range(len(HealthyGamingAdvice)):
            HealthyGamingAdvice[i] = linpg.font.render(HealthyGamingAdvice[i], "white", font_size)
    # 其他载入页面需要的数据
    text1 = linpg.font.render(linpg.lang.get_text("title1"), "white", font_size)
    text2 = linpg.font.render(linpg.lang.get_text("title2"), "white", font_size)
    # 画到暂时的帘幕上
    surface_t.blits(
        (
            (text1, (font_size, window_y * 0.9)),
            (text2, (font_size, window_y * 0.9 - window_x / 32)),
        )
    )
    index: int = 0
    for item_t in HealthyGamingAdvice:
        surface_t.blit(
            item_t,
            (
                window_x - window_x / 32 - item_t.get_width(),
                window_y * 0.9 - font_size * index * 1.5,
            ),
        )
        index += 1
    return surface_t


# 控制台
class Console(linpg.Console):
    def _check_command(self, conditions: list) -> None:
        if conditions[0] == "load":
            if conditions[1] == "dialog":
                gamemode.dialog(
                    linpg.display.screen_window,
                    conditions[2],
                    conditions[3],
                    conditions[4],
                    conditions[5],
                )
            elif conditions[1] == "battle":
                gamemode.battle(
                    linpg.display.screen_window,
                    conditions[2],
                    conditions[3],
                    conditions[4],
                )
            else:
                self._txt_output.append("Error, do not know what to load.")
        else:
            super()._check_command(conditions)


console = Console(linpg.display.get_width() * 0.1, linpg.display.get_height() * 0.8)
