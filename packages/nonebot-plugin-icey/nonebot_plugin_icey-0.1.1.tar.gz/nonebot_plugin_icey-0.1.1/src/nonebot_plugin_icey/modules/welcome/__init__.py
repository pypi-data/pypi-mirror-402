from nonebot.log import logger
from nonebot.plugin import PluginMetadata

# === 关键：必须导入 matcher 让装饰器执行 ===
from .matcher import cmd_cleanwelcome, cmd_goodbye, cmd_reset_goodbye, cmd_reset_welcome, cmd_set_goodbye, cmd_set_welcome, cmd_welcome, welcome_notice_handle

__plugin_meta__ = PluginMetadata(
    name="verify",
    description="入群欢迎",
    usage="",
)

logger.opt(colors=True).success(f'Succeeded to load icey plugin model "<m>{__name__}</m>"')
__all__ = [
    "cmd_welcome",
    "cmd_goodbye",
    "cmd_set_welcome",
    "cmd_set_goodbye",
    "cmd_reset_welcome",
    "cmd_reset_goodbye",
    "cmd_cleanwelcome",
    "welcome_notice_handle",
]
