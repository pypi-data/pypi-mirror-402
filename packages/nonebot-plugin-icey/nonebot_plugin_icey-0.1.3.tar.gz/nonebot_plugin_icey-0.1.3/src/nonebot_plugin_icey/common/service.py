# sesametk/plugins/icey/common/service.py
from nonebot_plugin_orm import get_session

from sqlalchemy import update
from .models import GroupInfo
from .dao import ensure_group_exist


async def update_language(group_id: str, lang: str):
    """更新群语言"""
    async with get_session() as session:
        await ensure_group_exist(group_id)  # 确保存在
        stmt = update(GroupInfo).where(GroupInfo.group_id == group_id).values(language=lang)
        await session.execute(stmt)
        await session.commit()
