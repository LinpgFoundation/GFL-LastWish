import os
import shutil
from distutils.core import setup
from glob import glob
from Cython.Build import cythonize

# 参数
debug_c: bool = False
folder_for_build: str = "Source_pyd"

# 生成用于存放pyd文件的文件夹
if os.path.exists(folder_for_build):
    shutil.rmtree(folder_for_build)
os.makedirs(folder_for_build)

# 生成游戏本体源代码的c和pyd文件
for path in glob(r"Source/*.py"):
    setup(ext_modules=cythonize(path, language_level="3"))
    # 删除.c文件
    if not debug_c:
        os.remove(path.replace(".py", ".c"))
# 把pyd文件移动文件夹中
for path in glob(r"*.pyd"):
    shutil.move(path, folder_for_build)

# 移除旧的gamemode文件夹
if os.path.exists("gamemode"):
    shutil.rmtree("gamemode")
# 生成游戏本体源代码的c和pyd文件
for path in glob(r"Source/gamemode/*.py"):
    setup(ext_modules=cythonize(path))
    # 删除.c文件
    if not debug_c:
        os.remove(path.replace(".py", ".c"))
# 把文件夹移到Source_pyd中
shutil.move("gamemode", folder_for_build)

# 删除build文件夹
if os.path.exists("build"):
    shutil.rmtree("build")
