import os
import shutil

#先编译游戏本体的py文件
os.system("python compiler.py build_ext --inplace")

#检测pyinstaller是否需要升级
os.system("python -m pip install --upgrade pyinstaller")

#更新所有第三方库
#os.system("pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U")

#删除dist文件夹
if os.path.exists('dist'): shutil.rmtree('dist')

#打包main文件
dev_mode = input("If for dev purpose:")
if dev_mode.lower() == "y":
    os.system("pyinstaller -i icon.ico main.spec")
else:
    os.system("pyinstaller -i icon.ico --noconsole main.spec")

if os.path.exists('build'): shutil.rmtree('build')
if os.path.exists('logs'): shutil.rmtree('logs')
if os.path.exists('__pycache__'): shutil.rmtree('__pycache__')