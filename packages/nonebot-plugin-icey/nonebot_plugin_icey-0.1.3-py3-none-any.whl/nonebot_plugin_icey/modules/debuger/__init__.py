from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.adapters import Bot
from nonebot.log import logger

logger.opt(colors=True).success(f'Succeeded to load icey plugin model "<m>{__name__}</m>"')
debug_msg = on_message(priority=50, block=False)


@debug_msg.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.user_id
    info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
    logger.debug(f"debug:{info}")
