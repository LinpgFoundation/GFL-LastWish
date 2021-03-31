# cython: language_level=3
import glob
import os
import shutil
import time
import pygame
import linpgdev as linpg

#加载版本信息
version_info = linpg.loadConfig("Data/version.yaml")
VERSION = version_info["version"]
REVISION = version_info["revision"]
del version_info