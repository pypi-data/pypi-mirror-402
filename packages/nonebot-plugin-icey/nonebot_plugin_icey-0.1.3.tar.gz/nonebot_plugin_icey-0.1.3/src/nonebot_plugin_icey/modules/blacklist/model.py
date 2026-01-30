from nonebot_plugin_orm import Model
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

class Blacklist(Model):
    __tablename__ = "icey_blacklist"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(ForeignKey("icey_group_info.group_id"))
    
    target_qq: Mapped[str] = mapped_column() # 被拉黑的QQ
    reason: Mapped[str] = mapped_column(default="违反群规")
    operator: Mapped[str] = mapped_column()  # 操作人