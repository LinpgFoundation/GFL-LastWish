# cython: language_level=3
from .scene import *

#blit载入页面
def dispaly_loading_screen(screen:linpg.ImageSurface, start:int, end:int, value:int) -> None:
    window_x,window_y = screen.get_size()
    #获取健康游戏忠告
    HealthyGamingAdvice = linpg.try_get_lang("HealthyGamingAdvice")
    if HealthyGamingAdvice == "HealthyGamingAdvice":
        HealthyGamingAdvice = []
    else:
        for i in range(len(HealthyGamingAdvice)):
            HealthyGamingAdvice[i] = linpg.render_font(HealthyGamingAdvice[i],"white",window_x/64)
    #其他载入页面需要的数据
    text1 = linpg.render_font(linpg.get_lang("title1"), "white", window_x/64)
    text2 = linpg.render_font(linpg.get_lang("title2"), "white", window_x/64)
    #主循环
    for i in range(start,end,value):
        screen.fill(linpg.Color.BLACK)
        text1.set_alpha(i)
        text2.set_alpha(i)
        screen.blits(((text1,(window_x/64,window_y*0.9)),(text2,(window_x/64,window_y*0.9-window_x/32))))
        for a in range(len(HealthyGamingAdvice)):
            HealthyGamingAdvice[a].set_alpha(i)
            screen.blit(HealthyGamingAdvice[a],(window_x-window_x/32-HealthyGamingAdvice[a].get_width(),window_y*0.9-window_x/64*a*1.5))
        linpg.display.flip()

#控制台
class Console(linpg.Console):
    def _check_command(self, conditions:list) -> None:
        if conditions[0] == "load":
            if conditions[1] == "dialog":
                dialog(linpg.display.screen_window, conditions[2], conditions[3], conditions[4], conditions[5])
            elif conditions[1] == "battle":
                battle(linpg.display.screen_window, conditions[2], conditions[3], conditions[4])
            else:
                self.txtOutput.append("Error, do not know what to load.")
        else:
            super()._check_command(conditions)

console = Console(linpg.display.get_width()*0.1, linpg.display.get_height()*0.8)