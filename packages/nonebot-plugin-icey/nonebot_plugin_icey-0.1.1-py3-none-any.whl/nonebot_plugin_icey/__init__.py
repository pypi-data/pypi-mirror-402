from nonebot import get_plugin_config, require
from nonebot.plugin import PluginMetadata


# === 依赖声明 必须放在最前===
require("nonebot_plugin_orm")


from .config import Config

# === 导入功能模块 ===
# 所有的 import 都放在 require 之前，彻底解决 E402 报错
from .common import matcher as common_matcher
from .common import models as common_models

# 注意：根据之前的代码，文件夹名应为 "filter"(单数)。
# 如果您改为了 "filters"，请将下方改为 `from .modules import filters as filter_module`
from .modules import help as help_module
from .modules import request as request_module
from .modules import verify as verify_module
from .modules import welcome as welcome_module
from .modules import filters as filters_module


__version__ = "0.1.1"

__plugin_meta__ = PluginMetadata(
    name="IceyGroupManager",
    description="Icey QQ群管助手",
    usage="请使用 /help 查看详细指令",
    type="application",
    homepage="https://github.com/Fansirsqi/nonebot-plugin-icey",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={"author": "owner <fansir.code@gmail.com>"},
)

# 实例化配置
plugin_config = get_plugin_config(Config)

# === 显式导出 ===
# 通过 __all__ 声明导出的模块，解决 F401 (Imported but unused) 警告
__all__ = [
    "Config",
    "plugin_config",
    "common_matcher",
    "common_models",
    "help_module",
    "request_module",
    "verify_module",
    "welcome_module",
    "filters_module",
]
