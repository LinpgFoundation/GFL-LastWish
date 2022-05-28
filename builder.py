from os import path as PATH
from shutil import move as MOVE
from subprocess import check_call
import pkg_resources
from linpg import Builder  # type: ignore

# 编译游戏本体
Builder.delete_file_if_exist(PATH.join("Source_pyd"))
Builder.delete_file_if_exist(PATH.join("src"))
Builder.compile("Source")

# 确认是否想要打包
if input("Do you want to generate a package for the game(Y/n):") == "Y":
    # 更新所有第三方库
    for pkg in pkg_resources.working_set:
        check_call(["pip", "install", "--upgrade", pkg.project_name], shell=True)

    # 删除dist文件夹
    Builder.delete_file_if_exist("dist")

    # 打包main文件
    dev_mode = input("If for dev purpose:")
    if dev_mode.lower() == "y":
        check_call(["pyinstaller", "main.spec"])
    else:
        check_call(["pyinstaller", "--noconsole", "main.spec"])

    # 重命名文件
    MOVE(PATH.join("dist", "main"), PATH.join("dist", "GirlsFrontLine-LastWish"))

    # 移除移除的缓存文件
    folders_need_remove: tuple[str, ...] = ("build", "logs", "__pycache__", "Source_pyd")
    for folder_p in folders_need_remove:
        Builder.delete_file_if_exist(folder_p)
