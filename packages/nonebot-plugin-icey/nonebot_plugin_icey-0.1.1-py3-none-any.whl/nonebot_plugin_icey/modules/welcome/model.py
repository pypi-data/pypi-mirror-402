from nonebot import get_plugin_config
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...common.models import BaseGroupConfig, GroupInfo  # 导入主表

# 1. 导入配置类
from ...config import Config

# 2. 获取配置实例
plugin_config = get_plugin_config(Config)


class WelcomeConfig(BaseGroupConfig):
    __tablename__ = "icey_welcome_config"

    # 关联到主表
    group_id: Mapped[str] = mapped_column(ForeignKey("icey_group_info.group_id"), primary_key=True)

    should_welcome: Mapped[bool] = mapped_column(default=False)  # 是否开启入群欢迎
    should_goodbye: Mapped[bool] = mapped_column(default=False)  # 是否开启退群通知
    # 3. 使用配置中的值作为数据库默认值
    # 这样当新群加入时，会自动使用 .env 中配置的文案
    welcome_message: Mapped[str] = mapped_column(default=plugin_config.welcome_message)
    goodbye_message: Mapped[str] = mapped_column(default=plugin_config.goodbye_message)
    auto_delete_time: Mapped[int] = mapped_column(default=plugin_config.welcome_auto_delete_time)

    # 建立关系，方便查询
    group: Mapped[GroupInfo] = relationship(lazy="joined")
