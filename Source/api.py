import os
from glob import glob

if not os.path.exists(r"dev.key"):
    import linpg  # type: ignore
else:
    import sys

    # 从开发key中读取linpg开发版本的路径
    with open(r"dev.key") as f:
        sys.path.append(f.readline().rstrip())

    # 导入linpg开发版本
    import linpg

    # 移除相对路径
    sys.path.pop()
    # 启用开发模式
    linpg.debug.set_developer_mode(True)

# 初始化
linpg.display.init()

# 加载版本信息
version_info: dict = linpg.config.load("Data/version.yaml")

# 确认linpg的版本是推荐版本
linpg.LinpgVersionChecker("==", version_info["recommended_linpg_revision"], version_info["recommended_linpg_patch"])

__all__ = ["linpg", "os", "glob", "RPC", "ALPHA_BUILD_WARNING", "LARGE_IMAGE"]

# 本游戏的客户端ID
_CLIENT_ID: int = 831417008734208011
LARGE_IMAGE: str = "test"
# discord接口 - 如果不想要展示Discord的Rich Presence
if linpg.setting.try_get("DiscordRichPresence") is True:
    # 尝试连接Discord
    try:
        from pypresence import Presence  # type: ignore

        RPC = Presence(str(_CLIENT_ID))
        RPC.connect()
        RPC.update(
            state=linpg.lang.get_text("DiscordStatus", "game_is_initializing"),
            large_image=LARGE_IMAGE,
        )
    except Exception:
        RPC = None
else:
    RPC = None

# 设置引擎的标准文字大小
linpg.font.set_global_font("medium", int(linpg.display.get_width() / 40))

# alpha构建警告
ALPHA_BUILD_WARNING = linpg.load.static_text(
    linpg.lang.get_text("alpha_build_warning"), "white", (0, 0), int(linpg.display.get_width() / 80)
)
ALPHA_BUILD_WARNING.set_centerx(linpg.display.get_width() / 2)
ALPHA_BUILD_WARNING.set_bottom(linpg.display.get_height() - ALPHA_BUILD_WARNING.get_height())
ALPHA_BUILD_WARNING.set_alpha(200)
