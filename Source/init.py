# cython: language_level=3
import glob
import os
import shutil
import time
import pygame
#from linpgdev import linpg
import linpg

#加载版本信息
version_info:dict = linpg.loadConfig("Data/version.yaml")
VERSION:int = version_info["version"]
REVISION:int = version_info["revision"]
PATCH:int = version_info["patch"]
del version_info