try:
    from Source_pyd.mainMenu import MainMenu, linpg, pygame
except:
    print("Cannot import from Source_pyd")
    from Source.mainMenu import MainMenu, linpg, pygame

#读取并整理配置文件
folders = ['Lang/*.yaml','Data/*.yaml','Data/main_chapter/*.yaml']
for folderPath in folders:
    #pass
    linpg.organizeConfigInFolder(folderPath)

#是否启动游戏
GAMESTART:bool = True

#游戏主进程
if GAMESTART is True and __name__ == "__main__":
    #创建窗口
    screen = linpg.display.init_screen(
        pygame.DOUBLEBUF | pygame.SCALED | pygame.FULLSCREEN if linpg.get_setting("FullScreen") is True else pygame.SCALED
        )
    #窗口标题图标
    linpg.display.set_icon("Assets/image/UI/icon.png")
    linpg.display.set_caption(linpg.get_lang('General','game_title'))
    #初始化选项菜单
    linpg.init_option_menu(screen.get_width()*0.25,screen.get_height()*0.15,screen.get_width()*0.5,screen.get_height()*0.7)
    #主菜单模块
    mainMenu = MainMenu(screen)
    #主循环
    while mainMenu.is_playing():
        mainMenu.draw(screen)
        linpg.display.flip()
    #释放内容占用
    linpg.display.quit()
