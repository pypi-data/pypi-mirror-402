from typing import TYPE_CHECKING

from nonebot_plugin_orm import Model
from sqlalchemy.orm import Mapped, mapped_column


# 这是主表，只存最基础的信息
class GroupInfo(Model):
    __tablename__ = "icey_group_info"

    group_id: Mapped[str] = mapped_column(primary_key=True)
    language: Mapped[str] = mapped_column(default="zh")

    # 注意：这里我们不再显式定义 relationship 到子表
    # 让子表自己去定义 ForeignKey，减少耦合，防止循环导入


# === 新增这个基类 ===
class BaseGroupConfig(Model):
    """所有配置表的抽象基类，用于通过类型检查"""

    __abstract__ = True

    # 这里定义类型提示，告诉 Pylance 这些字段一定存在
    # 子类会用真实的 Column 覆盖它们，所以不用担心冲突
    group_id: Mapped[str]

    if TYPE_CHECKING:
        # 这一行只给 Pylance 看，运行时不会执行，避免循环导入
        group: Mapped["GroupInfo"]
