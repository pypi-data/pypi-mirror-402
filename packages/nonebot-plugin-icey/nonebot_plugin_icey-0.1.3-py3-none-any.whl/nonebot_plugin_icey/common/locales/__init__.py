# sesametk/plugins/icey/common/locales/__init__.py
import sys
from pathlib import Path
import time
from typing import Any, Dict, List
from ...config import Config
from nonebot import get_plugin_config, logger
from nonebot.adapters.onebot.v11 import Message

plugin_config = get_plugin_config(Config)

# 兼容性处理：Python 3.11+ 使用内置库，旧版本使用 tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class LangManager:
    # 内存缓存：{"zh": {...}, "en": {...}}
    _data: Dict[str, Dict[str, Any]] = {}
    DEFAULT_LANG = plugin_config.lang
    _last_check_time = 0

    @classmethod
    def load_data(cls):
        """扫描并加载所有 .toml 文件"""
        cls._data.clear()
        current_dir = Path(__file__).parent

        # 查找所有 .toml 文件
        loaded = []
        for file in current_dir.glob("*.toml"):
            lang_code = file.stem  # zh.toml -> zh
            try:
                with open(file, "rb") as f:
                    cls._data[lang_code] = tomllib.load(f)
                loaded.append(lang_code)
            except Exception as e:
                logger.error(f"[LangManager] Failed to load {file.name}: {e}")

        logger.info(f"[LangManager] Loaded languages: {loaded}")
        cls._last_load_time = time.time()

    @classmethod
    def get_available_langs(cls) -> List[str]:
        """获取当前可用的语言列表"""
        if not cls._data:
            cls.load_data()
        return list(cls._data.keys())

    @classmethod
    def get(cls, lang_code: str, key: str, **kwargs: Any) -> Message:
        """
        获取并格式化文本
        """
        # 懒加载：第一次调用时读取文件
        if not cls._data:
            cls.load_data()

        # 1. 获取目标语言包
        lang_data = cls._data.get(lang_code)

        # 2. 回退到默认语言
        if not lang_data:
            lang_data = cls._data.get(cls.DEFAULT_LANG, {})

        # 3. 获取模板字符串
        template = lang_data.get(key)

        # 4. 键不存在时的回退
        if template is None:
            # 尝试从默认语言找
            default_data = cls._data.get(cls.DEFAULT_LANG, {})
            template = default_data.get(key, f"[{key}]")

        # 5. 格式化
        # 格式化并包装
        try:
            formatted_str = template.format(**kwargs)
            # 2. 核心修改：在这里直接返回 Message 对象
            # Message() 构造函数会自动解析字符串中的 [CQ:...] 码
            return Message(formatted_str)
        except Exception as e:
            # 出错时也返回 Message，防止类型不一致
            return Message(f"{template} (FmtErr: {e})")


# 可选：在导入时立即加载，或者保持上面的懒加载模式
# LangManager.load_data()
