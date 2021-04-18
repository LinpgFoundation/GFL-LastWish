try:
    from Source_pyd.mainMenu import MainMenu, linpg, pygame, RPC
except:
    print("Cannot import from Source_pyd")
    from Source.mainMenu import MainMenu, linpg, pygame, RPC

#读取并整理配置文件
#linpg.optimizeCNContenInFolder("剧本/*.yaml")
folders = ['Lang/*.yaml','Data/*.yaml','Data/main_chapter/*.yaml',"剧本/*.yaml"]
for folderPath in folders:
    #pass
    linpg.organizeConfigInFolder(folderPath)

GAMESTART:bool = True

#游戏主进程
if GAMESTART and __name__ == "__main__":
    #屏幕设置
    flags = pygame.DOUBLEBUF | pygame.SCALED | pygame.FULLSCREEN if linpg.get_setting("FullScreen") is True else pygame.SCALED
    # 创建窗口
    screen = linpg.display.init_screen(flags)
    mainMenu = MainMenu(screen)
    while mainMenu.is_playing():
        mainMenu.draw(screen)
        linpg.display.flip()
    
    linpg.display.quit()
    RPC.close()
