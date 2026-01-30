# sesametk/plugins/icey/modules/verify/service.py
import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, List

from nonebot.adapters.onebot.v11 import Bot, MessageSegment
from nonebot.log import logger

from ...common.dao import get_sub_config, update_sub_config
from ...common.locales import LangManager  # 导入语言管理器
from .model import VerifyConfig


@dataclass
class VerifyState:
    answer: str
    remaining_attempts: int
    timeout_task: asyncio.Task
    question_msg_id: int
    # 新增：记录用户发送的验证消息ID列表，使用field初始化空列表
    user_msg_ids: List[int] = field(default_factory=list)


# 内存状态
verifying_users: Dict[tuple[str, int], VerifyState] = {}


# === 包装 ===


# 辅助函数：延迟撤回（可选，用于处理欢迎消息）
async def delay_delete(bot: Bot, msg_id, delay: int):
    await asyncio.sleep(delay)
    await del_msg(bot, msg_id)


async def get_config(group_id: str) -> VerifyConfig:
    return await get_sub_config(group_id, VerifyConfig)


async def update_config(group_id: str, **kwargs) -> str:
    return await update_sub_config(group_id, VerifyConfig, **kwargs)


def generate_math_question() -> tuple[str, str]:
    a, b = random.randint(1, 20), random.randint(1, 20)
    op = random.choice(["+", "-"])
    ans = a + b if op == "+" else a - b
    # 保证非负（可选）
    if op == "-" and ans < 0:
        a, b = b, a
        ans = a - b
    return f"{a} {op} {b} = ?", str(ans)


async def kick_user(bot: Bot, group_id: int, user_id: int, reason: str):
    if user_id == int(bot.self_id):
        return
    try:
        await bot.set_group_kick(group_id=group_id, user_id=user_id, reject_add_request=False)
        logger.info(f"Kicked {user_id}: {reason}")
    except Exception as e:
        logger.error(f"Kick failed: {e}")


async def start_verification(bot: Bot, group_id: int, user_id: int):
    """
    业务逻辑：开启验证流程
    """
    gid_str = str(group_id)
    conf = await get_config(gid_str)

    # 1. 生成题目
    q_text, ans = generate_math_question()

    # 2. 构造消息
    at_seg = MessageSegment.at(user_id)
    msg = LangManager.get(conf.group.language, "verify_start", at_user=at_seg, timeout=conf.verify_timeout, question=q_text, attempts=conf.verify_attempts)

    # 3. 发送题目
    question = await bot.send_group_msg(group_id=group_id, message=msg)

    # 4. 定义超时回调
    async def timeout_cb():
        await asyncio.sleep(conf.verify_timeout)

        # 检查是否还在验证列表中（如果在，说明超时了）
        if (gid_str, user_id) in verifying_users:
            # 先获取状态对象以便后续清理
            state = verifying_users[(gid_str, user_id)]
            del verifying_users[(gid_str, user_id)]

            # 发送超时提示
            timeout_msg = LangManager.get(conf.group.language, "verify_timeout", at_user=at_seg)
            byebye_msg = await bot.send_group_msg(group_id=group_id, message=timeout_msg)

            # 踢人
            await kick_user(bot, group_id, user_id, "Verify Timeout")

            # 使用新函数统一清理：题目 + 用户的所有发言（如果有）+ 超时提示
            # 注意：byebye_msg 是字典，需要取 message_id 或者依赖 del_msg 的兼容性（但 clean_verify_msgs 预期是 int 列表，虽然 del_msg 兼容，最好传 id）
            await clean_verify_msgs(bot, state, extra_msgs=[byebye_msg["message_id"]])

    # 5. 启动任务并记录状态
    task = asyncio.create_task(timeout_cb())

    verifying_users[(gid_str, user_id)] = VerifyState(
        answer=ans,
        remaining_attempts=conf.verify_attempts,
        timeout_task=task,
        question_msg_id=question["message_id"],
        user_msg_ids=[],  # 显式初始化为空列表
    )


async def del_msg(bot: Bot, msg):
    "撤回消息"
    if not msg:
        return  # 安全检查
    msg_id = msg if isinstance(msg, int) else msg.get("message_id")
    try:
        await bot.delete_msg(message_id=msg_id)
    except Exception as e:
        # 忽略撤回失败（可能已经被撤回或过期）
        pass


async def clean_verify_msgs(bot: Bot, state: VerifyState, extra_msgs: list | None = None):
    """
    新增：批量清理验证相关消息
    包括：机器人的提问、用户的回答历史、额外的提示消息
    """
    # 1. 撤回机器人的提问
    if state.question_msg_id:
        await del_msg(bot, state.question_msg_id)

    # 2. 撤回用户发送的所有尝试消息
    for uid_msg in state.user_msg_ids:
        await del_msg(bot, uid_msg)
        await asyncio.sleep(0.2)  # 防止撤回太快风控

    # 3. 撤回额外的提示消息（如通过提示、重试提示等）
    if extra_msgs:
        for m in extra_msgs:
            await del_msg(bot, m)
