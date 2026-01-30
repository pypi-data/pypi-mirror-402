import asyncio
import re

from nonebot import on_request
from nonebot.adapters.onebot.v11 import Bot, GroupRequestEvent
from nonebot.log import logger
from nonebot.matcher import Matcher

join_group = on_request(priority=10, block=True)


@join_group.handle()
async def join_group_handel(bot: Bot, matcher: Matcher, event: GroupRequestEvent):
    logger.debug(event)
    flag = event.flag
    sub_type = event.sub_type
    if sub_type == "add":  # 加群请求
        comment = event.comment
        word = re.findall(re.compile("答案：(.*)"), comment) if comment else []
        word = word[0] if word else (comment or "")
        msg_id = await join_group.send(f"检测到用户 {event.user_id} 的入群申请，3s后自动通过")
        await asyncio.sleep(3)
        await bot.delete_msg(message_id=msg_id["message_id"])
        await bot.set_group_add_request(flag=flag, sub_type=sub_type, approve=True, reason="默认同意")
    elif sub_type == "invite":  # 邀请机器人入群
        await event.approve(bot)
    else:
        pass
