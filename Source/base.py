import os
from glob import glob

# import linpg
from linpgdev import linpg

__all__ = ["linpg", "os", "glob", "RPC", "ALPHA_BUILD_WARNING", "LARGE_IMAGE"]

# 本游戏的客户端ID
_CLIENT_ID: int = 831417008734208011
LARGE_IMAGE: str = "test"
# discord接口
RPC: object
# 如果不想要展示Discord的Rich Presence
if linpg.setting.try_get("DiscordRichPresence") is False:
    RPC = None
else:
    # 尝试连接Discord
    try:
        from pypresence import Presence

        RPC = Presence(str(_CLIENT_ID))
        RPC.connect()
        RPC.update(
            state=linpg.lang.get_text("DiscordStatus", "game_is_initializing"),
            large_image=LARGE_IMAGE,
        )
    except Exception:
        RPC = None

# 加载版本信息
version_info: dict = linpg.config.load("Data/version.yaml")
VERSION: int = version_info["version"]
REVISION: int = version_info["revision"]
PATCH: int = version_info["patch"]
del version_info

# 设置引擎的标准文字大小
linpg.font.set_global_font("medium", int(linpg.display.get_width() / 40))

# alpha构建警告
ALPHA_BUILD_WARNING = linpg.TextSurface(
    linpg.font.render(
        linpg.lang.get_text("alpha_build_warning"),
        "white",
        int(linpg.display.get_width() / 80),
    ),
    0,
    0,
)
ALPHA_BUILD_WARNING.set_centerx(linpg.display.get_width() / 2)
ALPHA_BUILD_WARNING.set_bottom(linpg.display.get_height() - ALPHA_BUILD_WARNING.get_height())
ALPHA_BUILD_WARNING.set_alpha(200)
