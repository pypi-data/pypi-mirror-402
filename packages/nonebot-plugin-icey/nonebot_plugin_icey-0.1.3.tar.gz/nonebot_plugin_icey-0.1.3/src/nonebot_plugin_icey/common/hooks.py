from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.exception import IgnoredException
from nonebot.matcher import Matcher
from nonebot.message import run_preprocessor

from .matcher import admin_perm


@run_preprocessor
async def check_admin_privilege(matcher: Matcher, bot: Bot, event: GroupMessageEvent):
    """
    运行预处理器：
    拦截所有带有 `require_admin=True` 状态的命令
    """
    # 1. 检查当前触发的命令，是否包含我们自定义的标记
    # matcher.state 来自 on_command(..., state={...})
    if not matcher.state.get("require_admin"):
        return

    # 2. 如果有标记，说明这是个敏感命令，开始查票
    has_perm = await admin_perm(bot, event)

    if has_perm:
        return  # 主要是管理员，放行

    # 3. 权限不足：开始惩罚
    try:
        # 尝试禁言 10 分钟 (600秒)
        # 注意：Bot 必须是管理员，且不能禁言群主/其他管理员，否则会报错
        await bot.set_group_ban(
            group_id=event.group_id, user_id=event.user_id, duration=600
        )
        await matcher.send(
            "⚠️ 权限不足，非法调用管理指令，禁言 10 分钟。", at_sender=True
        )
    except Exception:
        # 如果禁言失败（比如对方是群主，或者Bot没权限），仅警告
        await matcher.send("⚠️ 权限不足，请勿越权操作。", at_sender=True)

    # 4. 核心步骤：直接掐断后续逻辑
    # 抛出这个异常后，你的 on_command 下面的 handle 函数绝对不会被执行
    raise IgnoredException("Admin privilege check failed")
