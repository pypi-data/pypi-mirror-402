from nonebot.log import logger
from nonebot.plugin import PluginMetadata

# === 关键：必须导入 matcher 让装饰器执行 ===
from .matcher import on_request

__plugin_meta__ = PluginMetadata(
    name="JoinGroupRequest",
    description="接管入群申请",
    usage="",
)

logger.opt(colors=True).success(f'Succeeded to load icey plugin model "<m>{__name__}</m>"')
__all__ = [
    "on_request",
]
