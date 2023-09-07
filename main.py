if __name__ == "__main__":
    # 导入核心组件
    from os.path import exists as EXISTS

    if EXISTS("src"):
        from src.Source import MainMenu, linpg  # type: ignore
    else:
        from Source import MainMenu, linpg

        # 读取并整理配置文件
        for folderPath in (
            r"Lang/*.yaml",
            r"Data/*.yaml",
            r"Data/main_chapter/*.yaml",
            r"Data/template/*.yaml",
        ):
            linpg.config.organize(folderPath)

    # 是否启动游戏
    GAME_START: bool = True

    # 游戏主进程
    if GAME_START is True:
        # 窗口标题图标
        linpg.display.set_icon(r"Assets/image/UI/icon.png")
        linpg.display.set_caption(linpg.lang.get_text("General", "game_title"))
        # compile all the dialogue scripts in Data directory
        # 编译Data文件夹内的所有原始视觉小说脚本文件
        linpg.ScriptCompiler.compile("Data")
        # 主菜单模块
        mainMenu = MainMenu(linpg.display.get_window())
        # 主循环
        while mainMenu.is_playing():
            mainMenu.draw(linpg.display.get_window())
            linpg.display.flip()

    # 释放内容占用
    exit()
