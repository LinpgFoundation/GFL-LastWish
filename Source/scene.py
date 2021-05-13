# cython: language_level=3
from .basic import *

#视觉小说系统
class DialogSystem(linpg.DialogSystem):
    #保存数据
    def save_progress(self) -> None:
        super().save_progress()
        #检查global.yaml配置文件
        if not os.path.exists(os.path.join(self.folder_for_save_file,"global.yaml")):
            DataTmp = {"chapter_unlocked":1}
            linpg.saveConfig(os.path.join(self.folder_for_save_file,"global.yaml"),DataTmp)

#对话系统
def dialog(screen:pygame.Surface, chapterType:str, chapterId:int, part:str, projectName:str=None) -> dict:
    #加载闸门动画的图片素材
    LoadingImgAbove:pygame.Surface = linpg.loadImg("Assets/image/UI/LoadingImgAbove.png",(screen.get_width()+8,screen.get_height()/1.7))
    LoadingImgBelow:pygame.Surface = linpg.loadImg("Assets/image/UI/LoadingImgBelow.png",(screen.get_width()+8,screen.get_height()/2.05))
    #开始加载-闸门关闭的效果
    for i in range(101):
        screen.blit(LoadingImgAbove,(-4,LoadingImgAbove.get_height()/100*i-LoadingImgAbove.get_height()))
        screen.blit(LoadingImgBelow,(-4,screen.get_height()-LoadingImgBelow.get_height()/100*i))
        linpg.display.flip()
    #卸载音乐
    linpg.unloadBackgroundMusic()
    #初始化对话系统模块
    DIALOG:object = DialogSystem()
    if chapterType is not None:
        DIALOG.new(chapterType,chapterId,part,projectName)
    else:
        DIALOG.load("Save/save.yaml")
    #加载完成-闸门开启的效果
    for i in range(100,-1,-1):
        DIALOG.display_background_image(screen)
        screen.blit(LoadingImgAbove,(-4,LoadingImgAbove.get_height()/100*i-LoadingImgAbove.get_height()))
        screen.blit(LoadingImgBelow,(-4,screen.get_height()-LoadingImgBelow.get_height()/100*i))
        linpg.display.flip()
    #DIALOG.auto_save = True
    #主循环
    while DIALOG.is_playing():
        DIALOG.draw(screen)
        ALPHA_BUILD_WARNING.draw(screen)
        linpg.display.flip()
    #返回玩家做出的选项
    return DIALOG.dialog_options

#对话编辑器
def dialogEditor(screen:pygame.Surface, chapterType:str, chapterId:int, part:str, projectName:str=None) -> None:
    #卸载音乐
    linpg.unloadBackgroundMusic()
    #改变标题
    linpg.display.set_caption("{0} ({1})".format(linpg.get_lang('General','game_title'),linpg.get_lang('General','dialog_editor')))
    if RPC is not None:
        RPC.update(details=linpg.get_lang("DiscordStatus","now_playing"),state=linpg.get_lang('General','dialog_editor'),large_image=LARGE_IMAGE)
    #加载对话
    DIALOG:object = linpg.DialogEditor()
    DIALOG.load(chapterType,chapterId,part,projectName)
    #主循环
    while DIALOG.is_playing():
        DIALOG.draw(screen)
        ALPHA_BUILD_WARNING.draw(screen)
        linpg.display.flip()
    #改变标题回主菜单的样式
    linpg.display.set_caption(linpg.get_lang('General','game_title'))
    if RPC is not None: RPC.update(state=linpg.get_lang("DiscordStatus","staying_at_main_menu"),large_image=LARGE_IMAGE)

#战斗系统
def battle(screen:pygame.Surface, chapterType:str, chapterId:int, projectName:str=None) -> dict:
    #卸载音乐
    linpg.unloadBackgroundMusic()
    BATTLE:object = TurnBasedBattleSystem()
    if chapterType is not None:
        BATTLE.new(screen, chapterType, chapterId, projectName)
    else:
        BATTLE.load(screen)
    #战斗系统主要loop
    while BATTLE.is_playing():
        BATTLE.draw(screen)
        ALPHA_BUILD_WARNING.draw(screen)
        linpg.display.flip()
    #暂停声效 - 尤其是环境声
    linpg.unloadBackgroundMusic()
    return BATTLE.resultInfo

#地图编辑器
def mapEditor(screen:pygame.Surface, chapterType:str, chapterId:int, projectName:str=None) -> None:
    #卸载音乐
    linpg.unloadBackgroundMusic()
    MAP_EDITOR = MapEditor()
    MAP_EDITOR.load(screen, chapterType, chapterId, projectName)
    #改变标题
    linpg.display.set_caption("{0} ({1})".format(linpg.get_lang('General','game_title'),linpg.get_lang('General','map_editor')))
    if RPC is not None:
        RPC.update(details=linpg.get_lang("DiscordStatus","now_playing"),state=linpg.get_lang('General','map_editor'),large_image=LARGE_IMAGE)
    #战斗系统主要loop
    while MAP_EDITOR.is_playing():
        MAP_EDITOR.draw(screen)
        ALPHA_BUILD_WARNING.draw(screen)
        linpg.display.flip()
    #改变标题回主菜单的样式
    linpg.display.set_caption(linpg.get_lang('General','game_title'))
    if RPC is not None: RPC.update(state=linpg.get_lang("DiscordStatus","staying_at_main_menu"),large_image=LARGE_IMAGE)

#blit载入页面
def dispaly_loading_screen(screen:pygame.Surface, start:int, end:int, value:int) -> None:
    window_x,window_y = screen.get_size()
    #获取健康游戏忠告
    HealthyGamingAdvice = linpg.try_get_lang("HealthyGamingAdvice")
    if HealthyGamingAdvice == "HealthyGamingAdvice":
        HealthyGamingAdvice = []
    else:
        for i in range(len(HealthyGamingAdvice)):
            HealthyGamingAdvice[i] = linpg.fontRender(HealthyGamingAdvice[i],"white",window_x/64)
    #其他载入页面需要的数据
    text1 = linpg.fontRender(linpg.get_lang("title1"),"white",window_x/64)
    text2 = linpg.fontRender(linpg.get_lang("title2"),"white",window_x/64)
    #主循环
    for i in range(start,end,value):
        screen.fill(linpg.findColorRGBA("black"))
        text1.set_alpha(i)
        text2.set_alpha(i)
        screen.blits(((text1,(window_x/64,window_y*0.9)),(text2,(window_x/64,window_y*0.9-window_x/32))))
        for a in range(len(HealthyGamingAdvice)):
            HealthyGamingAdvice[a].set_alpha(i)
            screen.blit(HealthyGamingAdvice[a],(window_x-window_x/32-HealthyGamingAdvice[a].get_width(),window_y*0.9-window_x/64*a*1.5))
        linpg.display.flip()