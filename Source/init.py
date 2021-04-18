# cython: language_level=3
import glob, os, shutil, time
#from linpgdev import linpg, pygame
import linpg, pygame
try:
    from pypresence import Presence
    RPC = Presence("831417008734208011") 
    RPC.connect()
    RPC.update(state=linpg.get_lang("DiscordStatus","game_is_initializing"),large_image="test")
except:
    RPC = None

#加载版本信息
version_info:dict = linpg.loadConfig("Data/version.yaml")
VERSION:int = version_info["version"]
REVISION:int = version_info["revision"]
PATCH:int = version_info["patch"]
del version_info

#设置引擎的标准文字大小
linpg.set_standard_font_size(int(linpg.display.get_width()/40),"medium")

#alpha构建警告
ALPHA_BUILD_WARNING = linpg.TextSurface(
    linpg.fontRender(linpg.get_lang("alpha_build_warning"),"white",linpg.get_standard_font_size("medium")/2),0,0
    )
ALPHA_BUILD_WARNING.set_centerx(linpg.display.get_width()/2)
ALPHA_BUILD_WARNING.set_bottom(linpg.display.get_height()-ALPHA_BUILD_WARNING.get_height())
ALPHA_BUILD_WARNING.set_alpha(200)