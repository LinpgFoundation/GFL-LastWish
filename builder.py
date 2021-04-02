import os

#先编译游戏本体的py文件
os.system("python compiler.py build_ext --inplace")

#检测pyinstaller是否需要升级
os.system("python -m pip install --upgrade pyinstaller")