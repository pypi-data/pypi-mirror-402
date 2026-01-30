from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.log import logger

# 请根据你的项目结构调整 admin_perm 的导入路径
from ...common.matcher import admin_perm
from .model import ReplyType
from .service import (
    add_filter,
    construct_reply,
    delete_all_filters,
    delete_filter,
    find_match,
    get_all_filters,
    parse_rose_args,
)

# 注册命令
cmd_filter = on_command("filter", aliases={"addfilter"}, permission=admin_perm, priority=30, block=False)
cmd_stop = on_command("stop", permission=admin_perm, priority=30, block=False)
cmd_stopall = on_command("stopall", permission=admin_perm, priority=30, block=False)
cmd_list = on_command("filters", permission=admin_perm, priority=30, block=False)

# 消息监听器：优先级较低，确保不干扰命令
msg_handler = on_message(priority=99, block=False)


@cmd_filter.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    raw_arg = args.extract_plain_text().strip()
    logger.debug(f"Filter received arg: |{raw_arg}|") # <--- 添加这行调试
    gid = str(event.group_id)

    # 1. 检查是否有 Reply (处理媒体素材)
    reply_ref = event.reply
    media_content = None
    reply_type = ReplyType.TEXT

    if reply_ref:
        for seg in reply_ref.message:
            # 获取图片 URL
            if seg.type == "image":
                media_content = seg.data.get("url") or seg.data.get("file")
                reply_type = ReplyType.IMAGE
                break
            # 可以扩展 sticker 判断，视 OneBot 实现而定

    # 2. 解析 Rose 风格参数
    triggers, text_reply = parse_rose_args(raw_arg)

    if not triggers:
        await cmd_filter.finish("Usage: /filter <trigger> <reply> (or reply to media)")

    # 3. 确定最终回复内容
    final_content = ""
    final_type = ReplyType.TEXT

    if media_content:
        # 回复图片/媒体模式
        final_content = media_content
        final_type = reply_type
    else:
        # 纯文本模式
        if not text_reply:
            await cmd_filter.finish("Please provide a reply message.")
        final_content = text_reply
        final_type = ReplyType.TEXT

    # 4. 保存所有规则
    count = 0
    for t in triggers:
        await add_filter(gid, t, final_content, final_type)
        count += 1

    await cmd_filter.finish(f"Saved {count} filter(s).")


@cmd_stop.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    raw_arg = args.extract_plain_text().strip()
    # 复用解析逻辑只取 triggers
    triggers, _ = parse_rose_args(raw_arg)

    if not triggers:
        if raw_arg:
            triggers = [raw_arg]
        else:
            await cmd_stop.finish("Usage: /stop <trigger>")

    count = 0
    gid = str(event.group_id)
    for t in triggers:
        if await delete_filter(gid, t):
            count += 1

    if count > 0:
        await cmd_stop.finish(f"Deleted {count} filter(s).")
    else:
        await cmd_stop.finish("No matching filters found.")


@cmd_stopall.handle()
async def _(event: GroupMessageEvent):
    gid = str(event.group_id)
    await delete_all_filters(gid)
    await cmd_stopall.finish("All filters in this chat have been removed.")


@cmd_list.handle()
async def _(event: GroupMessageEvent):
    gid = str(event.group_id)
    filters = await get_all_filters(gid)
    if not filters:
        await cmd_list.finish("No filters set in this chat.")

    msg = "Filters in this chat:\n"
    # 简单的格式化，每行显示一个 trigger
    for f in filters:
        msg += f"- {f}\n"
    await cmd_list.finish(msg)


@msg_handler.handle()
async def _(matcher: Matcher, bot: Bot, event: GroupMessageEvent):  # 添加 matcher 参数
    # 忽略自己的消息
    if event.user_id == int(bot.self_id):
        return

    gid = str(event.group_id)
    text = event.get_plaintext().strip()

    # 查找匹配
    rule = await find_match(gid, text)
    if rule:
        reply_msg = await construct_reply(bot, event, rule)
        await msg_handler.send(reply_msg)

        # === 修正: 使用注入的 matcher 实例 ===
        matcher.stop_propagation()
