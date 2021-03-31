from distutils.core import setup
from Cython.Build import cythonize
from glob import glob
import os
import shutil

#py setup.py build_ext --inplace
#pyinstaller -i icon.ico main.py
#pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U

debug_c = False

#生成游戏本体源代码的c和pyd文件
for path in glob(r'Source/*.py'):
    setup(ext_modules=cythonize(path))
    #删除.c文件
    if not debug_c: os.remove(path.replace(".pyx",".c"))

#删除build文件夹
if os.path.exists('build'): shutil.rmtree('build')