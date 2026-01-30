from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from .matcher import cmd_help

__plugin_meta__ = PluginMetadata(
    name="Help",
    description="帮助",
    usage="/help",
)

logger.opt(colors=True).success(f'Succeeded to load icey plugin model "<m>{__name__}</m>"')

__all__ = [
    "cmd_help",
]
