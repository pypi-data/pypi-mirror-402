from enum import IntEnum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...common.models import BaseGroupConfig, GroupInfo

class MatchMode(IntEnum):
    CONTAINS = 0  # 包含 (默认)
    EXACT = 1     # 全匹配 (exact:)
    PREFIX = 2    # 前缀 (prefix:)

class ReplyType(IntEnum):
    TEXT = 0
    IMAGE = 1
    STICKER = 2

class FilterRule(BaseGroupConfig):
    __tablename__ = "icey_filter_rules"

    # 独立主键
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 外键关联
    group_id: Mapped[str] = mapped_column(ForeignKey("icey_group_info.group_id"), index=True)
    
    # 规则内容
    trigger: Mapped[str] = mapped_column(String(255))
    match_mode: Mapped[int] = mapped_column(default=int(MatchMode.CONTAINS))
    reply_type: Mapped[int] = mapped_column(default=int(ReplyType.TEXT))
    reply_content: Mapped[str] = mapped_column(Text)

    # 关系定义 (自动加载 GroupInfo)
    group: Mapped[GroupInfo] = relationship(lazy="selectin")