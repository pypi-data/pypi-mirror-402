from nonebot.log import logger
from nonebot.plugin import PluginMetadata

# === 关键：必须导入 matcher 让装饰器执行 ===
from .matcher import cmd_verify, cmd_level_check, cmd_join_level_set, cmd_set_verify_timeout, clear_group, verify_notice_handle,verify_msg

__plugin_meta__ = PluginMetadata(
    name="verify",
    description="入群验证",
    usage="",
)

logger.opt(colors=True).success(f'Succeeded to load icey plugin model "<m>{__name__}</m>"')
__all__ = [
    "cmd_verify",
    "cmd_level_check",
    "cmd_join_level_set",
    "cmd_set_verify_timeout",
    "clear_group",
    "verify_notice_handle",
    "verify_msg",
]
