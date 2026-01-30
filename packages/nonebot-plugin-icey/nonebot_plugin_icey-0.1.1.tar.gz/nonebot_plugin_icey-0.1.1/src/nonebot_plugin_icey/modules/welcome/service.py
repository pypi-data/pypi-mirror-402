# sesametk/plugins/icey/modules/welcome/service.py
import asyncio

from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.log import logger
from ...common.dao import get_sub_config, update_sub_config
from .model import WelcomeConfig


async def get_config(group_id: str) -> WelcomeConfig:
    return await get_sub_config(group_id, WelcomeConfig)


async def update_config(group_id: str, **kwargs) -> str:
    return await update_sub_config(group_id, WelcomeConfig, **kwargs)


async def send_welcome_message(bot: Bot, group_id: int, user_id: int, flag=None):
    """发送欢迎消息业务逻辑

    :param Bot bot: _description_
    :param int group_id: _description_
    :param int user_id: _description_
    :param _type_ flag: fromtag, defaults to None
    """
    gid_str = str(group_id)
    conf = await get_config(gid_str)

    if not conf.should_welcome:
        return

    at_seg = MessageSegment.at(user_id)
    msg = conf.welcome_message.replace("{user}", str(at_seg))

    msg_id = await bot.send_group_msg(group_id=group_id, message=msg)

    if conf.auto_delete_time > 0:
        if flag == "verify":
            await asyncio.sleep(conf.auto_delete_time + 60)
        else:
            await asyncio.sleep(conf.auto_delete_time)
        try:
            await bot.delete_msg(message_id=msg_id["message_id"])
        except Exception:
            pass


async def send_goodbye_message(bot: Bot, group_id: int, user_id: int):
    """发送退群消息"""
    gid_str = str(group_id)
    conf = await get_config(gid_str)

    if not conf.should_goodbye:
        return
    at_seg = MessageSegment.at(user_id)
    msg = conf.goodbye_message.replace("{user}", str(at_seg)) + " uid:" + str(user_id)
    # 发送
    msg_id = await bot.send_group_msg(group_id=group_id, message=msg)
    # 处理自动撤回 (复用同一个配置时间，或者你也可以在数据库加个 goodbye_auto_delete_time)
    if conf.auto_delete_time > 0:
        await asyncio.sleep(conf.auto_delete_time)
        try:
            await bot.delete_msg(message_id=msg_id["message_id"])
        except Exception as e:
            logger.error(f"撤回错误:{msg_id} {e}")
            pass
