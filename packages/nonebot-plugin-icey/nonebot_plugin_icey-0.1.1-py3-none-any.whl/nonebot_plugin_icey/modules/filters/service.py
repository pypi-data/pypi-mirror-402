import re
import shlex
from typing import List, Optional, Tuple, Union, cast

from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot_plugin_orm import get_session
from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult

from .model import FilterRule, MatchMode, ReplyType
from ...common.dao import ensure_group_exist


# === 核心逻辑：指令参数解析 ===
def parse_rose_args(raw_text: str) -> Tuple[List[str], str]:
    """
    解析 Rose 风格的参数。
    支持:
    word reply
    "phrase" reply
    (word1, "phrase 2") reply
    """
    raw_text = raw_text.strip()
    triggers = []
    reply = ""
    multi_match = re.match(r"^\((.*?)\)\s*(.*)$", raw_text, re.DOTALL)
    if multi_match:
        trigger_block = multi_match.group(1)
        reply = multi_match.group(2)
        try:
            raw_items = [t.strip() for t in trigger_block.split(",")]
            for item in raw_items:
                if (item.startswith('"') and item.endswith('"')) or (item.startswith("'") and item.endswith("'")):
                    triggers.append(item[1:-1])
                else:
                    triggers.append(item)
        except ValueError:
            triggers = []
    else:
        try:
            parts = shlex.split(raw_text)
            if parts:
                triggers = [parts[0]]
                is_quoted = raw_text.startswith('"') or raw_text.startswith("'")
                if is_quoted:
                    quote_char = raw_text[0]
                    end_idx = raw_text.find(quote_char, 1)
                    if end_idx != -1:
                        reply = raw_text[end_idx + 1 :].strip()
                else:
                    first_space = raw_text.find(" ")
                    if first_space != -1:
                        reply = raw_text[first_space + 1 :].strip()
                    else:
                        reply = ""
        except ValueError:
            return [], ""
    clean_triggers = [t for t in triggers if t]
    return clean_triggers, reply.strip()


def process_trigger_mode(trigger: str) -> Tuple[str, MatchMode]:
    """处理 prefix: 和 exact: 前缀"""
    if trigger.startswith("prefix:"):
        return trigger[7:], MatchMode.PREFIX
    elif trigger.startswith("exact:"):
        return trigger[6:], MatchMode.EXACT
    return trigger, MatchMode.CONTAINS


# === 数据库操作 ===


async def add_filter(group_id: str, trigger: str, reply: str, r_type: ReplyType):
    """
    添加过滤规则
    注意：这里不能使用 dao.update_sub_config，因为是一对多关系
    """
    trigger_content, mode = process_trigger_mode(trigger)
    if not trigger_content:
        return

    # 1. 确保主表存在 (这是关键，防止外键报错)
    await ensure_group_exist(group_id)

    async with get_session() as session:
        # 2. 删除旧规则 (覆盖逻辑)
        stmt = delete(FilterRule).where(FilterRule.group_id == group_id, FilterRule.trigger == trigger_content)
        await session.execute(stmt)

        # 3. 插入新规则
        new_rule = FilterRule(group_id=group_id, trigger=trigger_content, match_mode=mode, reply_type=r_type, reply_content=reply)
        session.add(new_rule)
        await session.commit()


async def delete_filter(group_id: str, trigger: str) -> bool:
    t_content, _ = process_trigger_mode(trigger)

    async with get_session() as session:
        stmt = delete(FilterRule).where(FilterRule.group_id == group_id, FilterRule.trigger == t_content)
        result = cast(CursorResult, await session.execute(stmt))
        await session.commit()
        return result.rowcount > 0


async def delete_all_filters(group_id: str):
    async with get_session() as session:
        stmt = delete(FilterRule).where(FilterRule.group_id == group_id)
        await session.execute(stmt)
        await session.commit()


async def get_all_filters(group_id: str) -> List[str]:
    async with get_session() as session:
        stmt = select(FilterRule.trigger).where(FilterRule.group_id == group_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def find_match(group_id: str, text: str) -> Optional[FilterRule]:
    if not text:
        return None

    # 这里是一次性取出所有规则，如果规则很多，建议优化为 SQL 匹配
    # 但考虑到正则/前缀逻辑，内存匹配最灵活
    async with get_session() as session:
        stmt = select(FilterRule).where(FilterRule.group_id == group_id)
        result = await session.execute(stmt)
        rules = result.scalars().all()

    # 逻辑保持不变
    for rule in rules:
        if rule.match_mode == MatchMode.EXACT:
            if rule.trigger == text:
                return rule

    for rule in rules:
        if rule.match_mode == MatchMode.PREFIX:
            if text.startswith(rule.trigger):
                return rule

    contains_rules = [r for r in rules if r.match_mode == MatchMode.CONTAINS]
    contains_rules.sort(key=lambda x: len(x.trigger), reverse=True)

    for rule in contains_rules:
        if rule.trigger in text:
            return rule
    return None


# === 消息构造 ===


async def construct_reply(bot: Bot, event: GroupMessageEvent, rule: FilterRule) -> Union[str, Message, MessageSegment]:
    if rule.reply_type == ReplyType.IMAGE:
        return MessageSegment.image(file=rule.reply_content)
    if rule.reply_type == ReplyType.STICKER:
        return MessageSegment.image(file=rule.reply_content)

    text = rule.reply_content
    target_user_id: int = event.user_id

    has_reply_tag = "{replytag}" in text
    reply_ref = event.reply

    if has_reply_tag:
        if reply_ref and reply_ref.sender and reply_ref.sender.user_id:
            target_user_id = reply_ref.sender.user_id
        text = text.replace("{replytag}", "")

    if "{user}" in text:
        try:
            user_info = await bot.get_group_member_info(group_id=event.group_id, user_id=target_user_id)
            name = user_info.get("card") or user_info.get("nickname") or str(target_user_id)
            text = text.replace("{user}", name)
        except Exception:
            text = text.replace("{user}", str(target_user_id))

    msg = Message()
    msg.append(text)
    return msg
