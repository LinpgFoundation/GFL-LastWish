import os
from glob import glob

import linpg

# 初始化
linpg.display.init()

# 加载版本信息
version_info: dict = linpg.config.load("Data/version.yaml")

# 确认linpg的版本是推荐版本
linpg.LinpgVersionChecker(
    ">=",
    version_info["recommended_linpg_revision"],
    version_info["recommended_linpg_patch"],
)

__all__ = ["linpg", "os", "glob", "ALPHA_BUILD_WARNING"]

# 设置引擎的标准文字大小
linpg.font.set_global_font("medium", int(linpg.display.get_width() / 40))

# alpha构建警告
ALPHA_BUILD_WARNING = linpg.load.text(
    linpg.lang.get_text("alpha_build_warning"),
    "white",
    (0, 0),
    int(linpg.display.get_width() / 80),
)
ALPHA_BUILD_WARNING.set_centerx(linpg.display.get_width() / 2)
ALPHA_BUILD_WARNING.set_bottom(
    linpg.display.get_height() - ALPHA_BUILD_WARNING.get_height()
)
ALPHA_BUILD_WARNING.set_alpha(200)
