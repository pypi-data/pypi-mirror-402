from nonebot.log import logger
from nonebot.plugin import PluginMetadata

from .hooks import check_admin_privilege

# === 关键：必须导入 matcher 让装饰器执行 ===
from .matcher import admin_perm, cmd_set_lang

__plugin_meta__ = PluginMetadata(
    name="common",
    description="全局通用功能",
    usage="",
)

logger.opt(colors=True).success(
    f'Succeeded to load icey plugin model "<m>{__name__}</m>"'
)

__all__ = [
    "admin_perm",
    "check_admin_privilege",
    "cmd_set_lang",
]
