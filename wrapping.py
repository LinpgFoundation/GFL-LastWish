if __name__ == "__main__":
    from os import path as PATH
    from shutil import move as MOVE
    import subprocess
    import pkg_resources
    import linpg  # type: ignore

    # 编译游戏本体
    if (
        not PATH.exists("src")
        or input("Do you want to recompile source files (Y/n):") == "Y"
    ):
        linpg.Builder.delete_file_if_exist("src")
        linpg.Builder.compile("Source")

    # 更新所有第三方库
    if input("Do you want to update all third party packages (Y/n):") == "Y":
        for pkg in pkg_resources.working_set:
            try:
                subprocess.check_call(
                    ["pip", "install", "--upgrade", pkg.project_name], shell=True
                )
            except subprocess.CalledProcessError:
                pass

    # 删除dist文件夹
    linpg.Builder.delete_file_if_exist("dist")

    # 打包main文件
    dev_mode = input("If for dev purpose:")
    if dev_mode.lower() == "y":
        subprocess.check_call(["pyinstaller", "main.spec"])
    else:
        subprocess.check_call(["pyinstaller", "--noconsole", "main.spec"])

    # 重命名文件
    MOVE(PATH.join("dist", "main"), PATH.join("dist", "GirlsFrontLine-LastWish"))

    # 移除移除的缓存文件
    folders_need_remove: tuple[str, ...] = ("build", "logs", "__pycache__")
    for folder_p in folders_need_remove:
        linpg.Builder.delete_file_if_exist(folder_p)
