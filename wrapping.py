if __name__ == "__main__":
    from os import path as PATH
    from shutil import move as MOVE
    from subprocess import check_call
    from linpgtoolbox.builder import Builder, PackageInstaller, SmartAutoModuleCombineMode

    # 编译游戏本体
    if (
        not PATH.exists("src")
        or input("Do you want to recompile source files (Y/n):") == "Y"
    ):
        Builder.delete_file_if_exist("src")
        Builder.compile(
            "Source", smart_auto_module_combine=SmartAutoModuleCombineMode.ALL_INTO_ONE
        )

    # 更新所有第三方库
    if input("Do you want to update all third party packages (Y/n):") == "Y":
        PackageInstaller.upgrade_all()

    # 删除dist文件夹
    Builder.delete_file_if_exist("dist")

    # 打包main文件
    PackageInstaller.install("pyinstaller")
    if input("If for dev purpose:").lower() == "y":
        check_call(["pyinstaller", "main.spec"])
    else:
        check_call(["pyinstaller", "--noconsole", "main.spec"])

    # 重命名文件
    MOVE(PATH.join("dist", "main"), PATH.join("dist", "GirlsFrontLine-LastWish"))

    # 移除移除的缓存文件
    folders_need_remove: tuple[str, ...] = ("build", "logs", "__pycache__")
    for folder_p in folders_need_remove:
        Builder.delete_file_if_exist(folder_p)
