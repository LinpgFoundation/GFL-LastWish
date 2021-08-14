import os
import shutil
from distutils.core import setup
from glob import glob
from Cython.Build import cythonize

# 参数
debug_c: bool = False
folder_contain_source: str = "Source"
folder_for_build: str = "Source_pyd"

# 生成用于存放pyd文件的文件夹
if os.path.exists(folder_for_build):
    shutil.rmtree(folder_for_build)
os.makedirs(folder_for_build)

# 将所有即将需要编译的py文件复制过去
for path in glob(os.path.join(folder_contain_source, "*")):
    if os.path.isdir(path) and "experimental" not in path and "pycache" not in path:
        shutil.copytree(path, os.path.join(folder_for_build, os.path.basename(path)))
    elif path.endswith(".py"):
        shutil.copy(path, folder_for_build)

# 生成游戏本体源代码的c和pyd文件
for path in glob(os.path.join(folder_for_build, "*")):
    if os.path.isdir(path):
        for file_path in glob(os.path.join(path, "*.py")):
            setup(ext_modules=cythonize(file_path, language_level="3"))
            # 删除py文件
            os.remove(file_path)
            # 删除.c文件
            if not debug_c:
                os.remove(file_path.replace(".py", ".c"))
    elif path.endswith(".py"):
        setup(ext_modules=cythonize(path, language_level="3"))
        # 删除py文件
        os.remove(path)
        # 删除.c文件
        if not debug_c:
            os.remove(path.replace(".py", ".c"))

# 删除build文件夹
if os.path.exists("build"):
    shutil.rmtree("build")
