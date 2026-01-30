# sesametk/plugins/icey/common/dao.py
from typing import Type, TypeVar

from nonebot_plugin_orm import get_session
from sqlalchemy import select, update

from .models import BaseGroupConfig, GroupInfo

# 定义一个泛型 T，它必须是 Model 的子类
T = TypeVar("T", bound=BaseGroupConfig)


async def ensure_group_exist(group_id: str) -> GroupInfo:
    """确保主表存在"""
    async with get_session() as session:
        result = await session.execute(select(GroupInfo).where(GroupInfo.group_id == group_id))
        info = result.scalar_one_or_none()
        if not info:
            info = GroupInfo(group_id=group_id, language="zh")
            session.add(info)
            await session.commit()
            await session.refresh(info)
        return info


async def get_sub_config(group_id: str, model_cls: Type[T]) -> T:
    """
    通用获取子配置函数
    :param group_id: 群号
    :param model_cls: 配置表的类名 (如 WelcomeConfig)
    """
    async with get_session() as session:
        # 使用传入的类进行查询
        result = await session.execute(select(model_cls).where(model_cls.group_id == group_id))
        conf = result.scalar_one_or_none()

        if not conf:
            # 1. 确保主表存在
            await ensure_group_exist(group_id)
            # 2. 实例化传入的类
            conf = model_cls(group_id=group_id)
            session.add(conf)
            await session.commit()
            # 3. 刷新以加载关联数据 (如 .group)
            await session.refresh(conf)

        return conf


async def update_sub_config(group_id: str, model_cls: Type[T], **kwargs) -> str:
    """
    通用更新函数
    :return: 当前群语言 (用于回复)
    """
    async with get_session() as session:
        # 1. 确保存在 (调用上面的通用 get)
        # 注意：这里调用的是同一个文件里的函数，直接 await
        conf = await get_sub_config(group_id, model_cls)

        # 2. 执行更新
        stmt = update(model_cls).where(model_cls.group_id == group_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()

        # 3. 返回语言
        # 因为 get_sub_config 里做了 refresh，且 model 定义了 lazy="joined"
        # 所以这里可以直接访问 .group.language
        return conf.group.language
