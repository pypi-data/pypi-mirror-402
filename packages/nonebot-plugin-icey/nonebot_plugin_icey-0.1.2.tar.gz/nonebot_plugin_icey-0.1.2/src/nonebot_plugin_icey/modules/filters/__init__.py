from nonebot.log import logger
from nonebot.plugin import PluginMetadata

# === 关键：必须导入 matcher 让装饰器执行 ===
from .matcher import cmd_filter, cmd_list, cmd_stop, cmd_stopall, msg_handler

__plugin_meta__ = PluginMetadata(
    name="Filter",
    description="关键词自动回复 (Rose Style)",
    usage="/filter <trigger> <reply>",
)

logger.opt(colors=True).success(f'Succeeded to load icey plugin model "<m>{__name__}</m>"')
__all__ = [
    "cmd_filter",
    "cmd_list",
    "cmd_stop",
    "cmd_stopall",
    "msg_handler",
]
