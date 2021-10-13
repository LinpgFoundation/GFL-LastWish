import os
from glob import glob

if os.path.exists("dev.key"):
    from linpgdev import linpg

    linpg.setting.set_developer_mode(True)
else:
    import linpg

# 加载版本信息
version_info: dict = linpg.config.load("Data/version.yaml")

if not linpg.info.ensure_linpg_version(
    "==", version_info["recommended_linpg_revision"], version_info["recommended_linpg_patch"]
):
    warn_y = linpg.Message(
        linpg.lang.get_text("Global", "warning"),
        linpg.lang.get_text("LinpgVersionIncorrect", "message").format(
            "3.{0}.{1}".format(version_info["recommended_linpg_revision"], version_info["recommended_linpg_patch"]),
            linpg.info.current_version,
        ),
        (
            linpg.lang.get_text("LinpgVersionIncorrect", "exit_button"),
            linpg.lang.get_text("LinpgVersionIncorrect", "continue_button"),
        ),
        error=True,
        return_button=0,
        escape_button=0,
    )
    if warn_y.show() == 0:
        linpg.display.quit()

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

# 设置引擎的标准文字大小
linpg.font.set_global_font("medium", int(linpg.display.get_width() / 40))

# alpha构建警告
ALPHA_BUILD_WARNING = linpg.load.text(
    linpg.lang.get_text("alpha_build_warning"), "white", (0, 0), int(linpg.display.get_width() / 80)
)
ALPHA_BUILD_WARNING.set_centerx(linpg.display.get_width() / 2)
ALPHA_BUILD_WARNING.set_bottom(linpg.display.get_height() - ALPHA_BUILD_WARNING.get_height())
ALPHA_BUILD_WARNING.set_alpha(200)
