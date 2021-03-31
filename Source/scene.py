# cython: language_level=3
from .dialogSystem import *

#对话系统
def dialog(chapterType,chapterId,screen,part,collection_name=None):
    #加载闸门动画的图片素材
    LoadingImgAbove = linpg.loadImg("Assets/image/UI/LoadingImgAbove.png",(screen.get_width()+8,screen.get_height()/1.7))
    LoadingImgBelow = linpg.loadImg("Assets/image/UI/LoadingImgBelow.png",(screen.get_width()+8,screen.get_height()/2.05))
    #开始加载-闸门关闭的效果
    for i in range(101):
        linpg.drawImg(LoadingImgAbove,(-4,LoadingImgAbove.get_height()/100*i-LoadingImgAbove.get_height()),screen)
        linpg.drawImg(LoadingImgBelow,(-4,screen.get_height()-LoadingImgBelow.get_height()/100*i),screen)
        linpg.display.flip(True)
    #卸载音乐
    linpg.unloadBackgroundMusic()
    #初始化对话系统模块
    DIALOG = DialogSystem()
    if chapterType != None:
        DIALOG.new(chapterType,chapterId,part,collection_name)
    else:
        DIALOG.load("Save/save.yaml")
    #加载完成-闸门开启的效果
    for i in range(100,-1,-1):
        DIALOG.display_background_image(screen)
        linpg.drawImg(LoadingImgAbove,(-4,LoadingImgAbove.get_height()/100*i-LoadingImgAbove.get_height()),screen)
        linpg.drawImg(LoadingImgBelow,(-4,screen.get_height()-LoadingImgBelow.get_height()/100*i),screen)
        linpg.display.flip(True)
    #DIALOG.auto_save = True
    #主循环
    while DIALOG.is_playing():
        DIALOG.draw(screen)
        linpg.display.flip()
    #返回玩家做出的选项
    return DIALOG.dialog_options

#对话编辑器
def dialogCreator(chapterType,chapterId,screen,part,collection_name=None):
    #卸载音乐
    linpg.unloadBackgroundMusic()
    linpg.display.set_caption("{0} ({1})".format(linpg.get_lang('General','game_title'),linpg.get_lang('General','dialog_creator')))
    #加载对话
    DIALOG = linpg.DialogSystemDev(chapterType,chapterId,part,collection_name)
    #主循环
    while DIALOG.is_playing():
        DIALOG.draw(screen)
        linpg.display.flip()
    linpg.display.set_caption(linpg.get_lang('General','game_title'))

#战斗系统
def battle(chapterType,chapterId,screen,collection_name=None):
    #卸载音乐
    linpg.unloadBackgroundMusic()
    BATTLE = TurnBasedBattleSystem(chapterType,chapterId,collection_name)
    if chapterType != None:
        BATTLE.initialize(screen)
    else:
        BATTLE.load(screen)
    #战斗系统主要loop
    while BATTLE.is_playing(): BATTLE.draw(screen)
    #暂停声效 - 尤其是环境声
    linpg.unloadBackgroundMusic()
    return BATTLE.resultInfo

#地图编辑器
def mapCreator(chapterType,chapterId,screen,collection_name=None):
    #卸载音乐
    linpg.unloadBackgroundMusic()
    linpg.display.set_caption("{0} ({1})".format(linpg.get_lang('General','game_title'),linpg.get_lang('General','map_creator')))
    MAPCREATOR = MapCreator(chapterType,chapterId,collection_name)
    MAPCREATOR.initialize(screen)
    #战斗系统主要loop
    while MAPCREATOR.is_playing(): MAPCREATOR.draw(screen)
    linpg.display.set_caption(linpg.get_lang('General','game_title'))

#blit载入页面
def dispaly_loading_screen(screen,start,end,value):
    window_x,window_y = screen.get_size()
    #获取健康游戏忠告
    HealthyGamingAdvice = linpg.get_lang("HealthyGamingAdvice")
    if HealthyGamingAdvice == None:
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
        linpg.drawImg(text1,(window_x/64,window_y*0.9),screen)
        text2.set_alpha(i)
        linpg.drawImg(text2,(window_x/64,window_y*0.9-window_x/32),screen)
        for a in range(len(HealthyGamingAdvice)):
            HealthyGamingAdvice[a].set_alpha(i)
            linpg.drawImg(HealthyGamingAdvice[a],(window_x-window_x/32-HealthyGamingAdvice[a].get_width(),window_y*0.9-window_x/64*a*1.5),screen)
        linpg.display.flip(True)