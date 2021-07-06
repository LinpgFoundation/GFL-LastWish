#导入核心组件
try:
    from Source_pyd.mainMenu import MainMenu, linpg
except Exception:
    print("Cannot import from Source_pyd")
    from Source.mainMenu import MainMenu, linpg

#读取并整理配置文件
for folderPath in (r'Lang/*.yaml', r'Data/*.yaml', r'Data/main_chapter/*.yaml'):
    #pass
    linpg.config.organize(folderPath)

#是否启动游戏
GAMESTART:bool = True

#游戏主进程
if GAMESTART is True and __name__ == "__main__":
    #创建窗口
    screen = linpg.display.init()
    #窗口标题图标
    linpg.display.set_icon(r"Assets/image/UI/icon.png")
    linpg.display.set_caption(linpg.lang.get_text('General', 'game_title'))
    #初始化选项菜单
    linpg.init_option_menu(
        int(screen.get_width()*0.25),
        int(screen.get_height()*0.15),
        int(screen.get_width()*0.5),
        int(screen.get_height()*0.7)
        )
    #主菜单模块
    mainMenu = MainMenu(screen)
    #主循环
    while mainMenu.is_playing():
        mainMenu.draw(screen)
        linpg.display.flip()

#释放内容占用
linpg.display.quit()
