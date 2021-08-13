import os
import shutil

# 先编译游戏本体的py文件
os.system("python compiler.py build_ext --inplace")

# 确认是否想要打包
if input("Do you want to generate a package for the game(Y/n):") == "Y":

    # 检测pyinstaller是否需要升级
    os.system("python -m pip install --upgrade pyinstaller")

    # 更新所有第三方库
    # os.system("pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U")

    # 删除dist文件夹
    if os.path.exists("dist"):
        shutil.rmtree("dist")

    # 打包main文件
    dev_mode = input("If for dev purpose:")
    if dev_mode.lower() == "y":
        os.system("pyinstaller main.spec")
    else:
        os.system("pyinstaller --noconsole main.spec")

    # 移除移除的缓存文件
    folders_need_remove: tuple[str] = ("build", "logs", "__pycache__")
    for folder_p in folders_need_remove:
        if os.path.exists(folder_p):
            shutil.rmtree(folder_p)
