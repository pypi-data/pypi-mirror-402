from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...common.models import BaseGroupConfig, GroupInfo  # 导入主表


class VerifyConfig(BaseGroupConfig):
    __tablename__ = "icey_verify_config"

    group_id: Mapped[str] = mapped_column(ForeignKey("icey_group_info.group_id"), primary_key=True)

    # 验证配置
    verify_enabled: Mapped[bool] = mapped_column(default=False)  # 是否开启入群验证
    verify_timeout: Mapped[int] = mapped_column(default=60)  # 验证超时时间
    verify_attempts: Mapped[int] = mapped_column(default=3)  # 最大尝试次数
    verify_mode: Mapped[int] = mapped_column(default=1)  # 验证模式

    level_checker: Mapped[bool] = mapped_column(default=False)  # 是否开启等级验证
    allowed_level: Mapped[int] = mapped_column(default=0)  # 加群等级
    # 建立关系，方便查询
    group: Mapped[GroupInfo] = relationship(lazy="joined")
