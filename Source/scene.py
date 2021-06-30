# cython: language_level=3
from .base import *

#视觉小说系统
class DialogSystem(linpg.DialogSystem):
    #保存数据
    def save_progress(self) -> None:
        super().save_progress()
        #检查global.yaml配置文件
        if not os.path.exists(os.path.join(self.folder_for_save_file,"global.yaml")):
            DataTmp = {"chapter_unlocked":1}
            linpg.config.save(os.path.join(self.folder_for_save_file,"global.yaml"),DataTmp)

#对话系统
def dialog(screen:linpg.ImageSurface, chapterType:str, chapterId:int, part:str, projectName:str=None) -> None:
    #加载闸门动画的图片素材
    LoadingImgAbove:linpg.ImageSurface = linpg.smoothly_resize_img(
        linpg.cope_bounding(linpg.load.img(r"Assets/image/UI/LoadingImgAbove.png")), (screen.get_width()+4, screen.get_height()/1.7)
        )
    LoadingImgBelow:linpg.ImageSurface = linpg.smoothly_resize_img(
        linpg.cope_bounding(linpg.load.img(r"Assets/image/UI/LoadingImgBelow.png")), (screen.get_width()+4, screen.get_height()/2.05)
    )
    #开始加载-闸门关闭的效果
    for i in range(101):
        screen.blit(LoadingImgAbove,(-2,LoadingImgAbove.get_height()/100*i-LoadingImgAbove.get_height()))
        screen.blit(LoadingImgBelow,(-2,screen.get_height()-LoadingImgBelow.get_height()/100*i))
        linpg.display.flip()
    #卸载音乐
    linpg.unload_all_music()
    #初始化对话系统模块
    DIALOG:object = DialogSystem()
    if chapterType is not None:
        DIALOG.new(chapterType,chapterId,part,projectName)
    else:
        DIALOG.load("Save/save.yaml")
    #加载完成-闸门开启的效果
    for i in range(100,-1,-1):
        DIALOG.display_background_image(screen)
        screen.blit(LoadingImgAbove,(-2,LoadingImgAbove.get_height()/100*i-LoadingImgAbove.get_height()))
        screen.blit(LoadingImgBelow,(-2,screen.get_height()-LoadingImgBelow.get_height()/100*i))
        linpg.display.flip()
    #DIALOG.auto_save = True
    #主循环
    while DIALOG.is_playing():
        DIALOG.draw(screen)
        ALPHA_BUILD_WARNING.draw(screen)
        linpg.display.flip()

#对话编辑器
def dialogEditor(screen:linpg.ImageSurface, chapterType:str, chapterId:int, part:str, projectName:str=None) -> None:
    #卸载音乐
    linpg.unload_all_music()
    #改变标题
    linpg.display.set_caption("{0} ({1})".format(linpg.lang.get_text('General','game_title'),linpg.lang.get_text('General','dialog_editor')))
    if RPC is not None:
        RPC.update(details=linpg.lang.get_text("DiscordStatus","now_playing"),state=linpg.lang.get_text('General','dialog_editor'),large_image=LARGE_IMAGE)
    #加载对话
    DIALOG:object = linpg.DialogEditor()
    DIALOG.load(chapterType,chapterId,part,projectName)
    #主循环
    while DIALOG.is_playing():
        DIALOG.draw(screen)
        ALPHA_BUILD_WARNING.draw(screen)
        linpg.display.flip()
    #改变标题回主菜单的样式
    linpg.display.set_caption(linpg.lang.get_text('General','game_title'))
    if RPC is not None: RPC.update(state=linpg.lang.get_text("DiscordStatus","staying_at_main_menu"),large_image=LARGE_IMAGE)

#战斗系统
def battle(screen:linpg.ImageSurface, chapterType:str, chapterId:int, projectName:str=None) -> dict:
    #卸载音乐
    linpg.unload_all_music()
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
    linpg.unload_all_music()
    return BATTLE.resultInfo

#地图编辑器
def mapEditor(screen:linpg.ImageSurface, chapterType:str, chapterId:int, projectName:str=None) -> None:
    #卸载音乐
    linpg.unload_all_music()
    MAP_EDITOR = MapEditor()
    MAP_EDITOR.load(screen, chapterType, chapterId, projectName)
    #改变标题
    linpg.display.set_caption("{0} ({1})".format(linpg.lang.get_text('General','game_title'),linpg.lang.get_text('General','map_editor')))
    if RPC is not None:
        RPC.update(details=linpg.lang.get_text("DiscordStatus","now_playing"),state=linpg.lang.get_text('General','map_editor'),large_image=LARGE_IMAGE)
    #战斗系统主要loop
    while MAP_EDITOR.is_playing():
        MAP_EDITOR.draw(screen)
        ALPHA_BUILD_WARNING.draw(screen)
        linpg.display.flip()
    #改变标题回主菜单的样式
    linpg.display.set_caption(linpg.lang.get_text('General','game_title'))
    if RPC is not None: RPC.update(state=linpg.lang.get_text("DiscordStatus","staying_at_main_menu"),large_image=LARGE_IMAGE)
