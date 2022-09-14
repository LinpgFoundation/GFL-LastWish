if __name__ == "__main__":
    # 导入核心组件
    from os.path import exists as EXISTS

    if EXISTS("src"):
        from src.Source import MainMenu, linpg  # type: ignore
    else:
        from Source import MainMenu, linpg

    # 读取并整理配置文件
    for folderPath in (r"Lang/*.yaml", r"Data/*.yaml", r"Data/main_chapter/*.yaml"):
        linpg.config.organize(folderPath)

    # 是否启动游戏
    GAMESTART: bool = True

    # 游戏主进程
    if GAMESTART is True:
        # 窗口标题图标
        linpg.display.set_icon(r"Assets/image/UI/icon.png")
        linpg.display.set_caption(linpg.lang.get_text("General", "game_title"))
        # 主菜单模块
        mainMenu = MainMenu(linpg.display.get_window())
        # 主循环
        while mainMenu.is_playing():
            mainMenu.draw(linpg.display.get_window())
            linpg.display.flip()

    # 释放内容占用
    linpg.display.quit()
