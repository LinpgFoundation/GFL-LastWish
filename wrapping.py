if __name__ == "__main__":
    from os import path as PATH
    import shutil

    from linpgtoolbox.builder import Builder, PackageInstaller, PyInstaller

    # 编译游戏本体
    if (
        not PATH.exists("src")
        or input("Do you want to recompile source files (Y/n):") == "Y"
    ):
        Builder.remove("src")
        Builder.compile("Source")

    # 更新所有第三方库
    if input("Do you want to update all third party packages (Y/n):") == "Y":
        PackageInstaller.upgrade()

    # 删除dist文件夹
    Builder.remove("dist")

    # 打包main文件
    PyInstaller.pack("main.spec")

    # 移动素材
    _ADDITIONAL_ASSETS: tuple[str, ...] = ("Assets", "Data", "Lang")
    for additional_dir in _ADDITIONAL_ASSETS:
        shutil.copytree(
            PATH.join(".", additional_dir), PATH.join("dist", "main", additional_dir)
        )

    # 重命名文件
    shutil.move(PATH.join("dist", "main"), PATH.join("dist", "GirlsFrontLine-LastWish"))

    # 移除移除的缓存文件
    folders_need_remove: tuple[str, ...] = ("build", "logs", "__pycache__")
    for folder_p in folders_need_remove:
        Builder.remove(folder_p)
