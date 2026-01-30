import asyncio

from nonebot import on_command, on_message, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent, GroupMessageEvent, Message, MessageSegment
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from ...common.locales import LangManager
from ...common.matcher import admin_perm


# 还需要导入欢迎模块的发送消息函数（验证通过后欢迎）
# 注意：跨模块引用

# === 1. 新增导入：通用DAO和欢迎配置模型 ===
from ...common.dao import get_sub_config
from ..welcome.model import WelcomeConfig
from ..welcome.service import send_welcome_message

from .service import clean_verify_msgs, del_msg, get_config, kick_user, start_verification, update_config, verifying_users

# 1. 合并后的主命令 /verify [on/off]
cmd_verify = on_command("verify", priority=30, block=False, permission=admin_perm)

cmd_level_check = on_command("levelcheck", priority=30, block=False, permission=admin_perm)

cmd_join_level_set = on_command("levelset", priority=30, block=False, permission=admin_perm)

# 2. 设置时间的命令
cmd_set_verify_timeout = on_command("verifytime", priority=30, block=False, permission=admin_perm)

clear_group = on_command("clear", priority=30, block=False, permission=admin_perm)


# === 1. 入群监听器 ===
# 优先级设为(比欢迎模块的高)，确保先处理验证
verify_notice_handle = on_notice(priority=29, block=False)


@cmd_level_check.handle()
async def cmd_set_level_check_handle(event: GroupMessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().lower()
    gid = str(event.group_id)
    if arg in ["on", "开启"]:
        lang = await update_config(gid, level_checker=True)
        await cmd_level_check.finish(LangManager.get(lang, "level_checker_on"))

    elif arg in ["off", "关闭"]:
        lang = await update_config(gid, level_checker=False)
        await cmd_level_check.finish(LangManager.get(lang, "level_checker_off"))

    # 如果没有参数或参数不对，提示用法
    else:
        await cmd_level_check.finish("Usage: /levelcheck [on|off]")


@cmd_join_level_set.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    msg = int(args.extract_plain_text().strip())
    conf = await get_config(str(event.group_id))
    if msg is False:
        await cmd_join_level_set.finish(LangManager.get(conf.group.language, "err_no_content"))
    await update_config(str(event.group_id), allowed_level=msg)
    await cmd_join_level_set.finish(LangManager.get(conf.group.language, "set_qq_level", check_level=msg))


@clear_group.handle()
async def clear_group_handle(bot: Bot, event: GroupMessageEvent):
    gid = event.group_id
    # bot.send_group_msg(group_id=gid,)
    gid_str = str(event.group_id)
    uid = event.user_id
    conf = await get_config(gid_str)
    lang = conf.group.language
    try:
        group_user_list = await bot.get_group_member_list(group_id=gid)
        for i in group_user_list:
            logger.debug(i)
            uid = i.get("user_id", None)
            if uid:
                user_info = await bot.get_stranger_info(user_id=uid, no_cache=True)
                qq_level = int(user_info.get("qqLevel", None) or user_info.get("level", 0))
                at_seg = MessageSegment.at(uid)
                if qq_level < conf.allowed_level:
                    qq_level_check = LangManager.get(lang, "qq_level_check", at_user=at_seg, qq_level=qq_level, check_level=conf.allowed_level)
                    await clear_group.send(qq_level_check)
                    # await kick_user(bot, event.group_id, uid, qq_level_check.extract_plain_text())
    except Exception as e:
        logger.error(e)
        pass
    pass


@verify_notice_handle.handle()
async def _(matcher: Matcher, bot: Bot, event: GroupIncreaseNoticeEvent):
    gid_str = str(event.group_id)
    uid = event.user_id
    if uid == int(bot.self_id):
        return
    conf = await get_config(gid_str)
    lang = conf.group.language
    at_seg = MessageSegment.at(uid)
    if conf.level_checker:
        user_info = await bot.get_stranger_info(user_id=event.user_id, no_cache=True)
        qq_level = int(user_info.get("qqLevel", None) or user_info.get("level", 0))
        if qq_level < conf.allowed_level:
            qq_level_check = LangManager.get(lang, "qq_level_check", at_user=at_seg)
            await verify_notice_handle.send(qq_level_check)
            await kick_user(bot, event.group_id, uid, qq_level_check.extract_plain_text())
            return
    # 如果开启了验证
    if conf.verify_enabled:
        # 启动验证流程
        await start_verification(bot, event.group_id, uid)
        # 关键：阻止事件继续传播，这样欢迎模块就不会收到这个事件
        # 从而避免在验证还没通过时就发送欢迎语
        matcher.stop_propagation()


# === 2. 验证消息监听器 ===
# Rule: 检查发送者是否在验证名单里
async def is_verifying(event: GroupMessageEvent) -> bool:
    return (str(event.group_id), event.user_id) in verifying_users


# 优先级 1，block=True，确保验证者的消息被拦截，不会触发其他命令
verify_msg = on_message(rule=is_verifying, priority=29, block=True)


@verify_msg.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    gid_str = str(event.group_id)
    gid_int = event.group_id
    uid = event.user_id
    user_msg = event.get_plaintext().strip()

    state = verifying_users[(gid_str, uid)]

    # === 新增：记录用户发送的这条消息 ID ===
    state.user_msg_ids.append(event.message_id)

    conf = await get_config(gid_str)

    # 获取欢迎配置
    wel_conf = await get_sub_config(gid_str, WelcomeConfig)
    # 获取配置的时间
    delay_time = wel_conf.auto_delete_time
    # 逻辑保护：
    # 如果 auto_delete_time 为 0 (表示欢迎消息永久保留)
    # 我们不能让"验证通过"和"算术题"这些垃圾消息也永久保留
    # 所以如果为0，我们给一个默认清理时间 (例如 10秒)
    # 如果大于0，则跟欢迎消息保持一致
    wait_seconds = delay_time if delay_time > 0 else 10

    lang = conf.group.language
    at_seg = MessageSegment.at(uid)

    # 1. 验证成功
    if user_msg == state.answer:
        state.timeout_task.cancel()  # 取消倒计时
        del verifying_users[(gid_str, uid)]  # 移除状态

        # 发送通过提示
        pass_msg = LangManager.get(lang, "verify_pass", at_user=at_seg)
        pass_msg_id = await verify_msg.send(pass_msg)

        # 验证通过后，发送欢迎消息
        # 注意：这里我们获取了 wel_msg_id，但不再立即放入清理列表
        await send_welcome_message(bot, gid_int, uid, flag="verify")

        # === 优化后的清理流程 ===
        # 等待一小会儿，让用户看到“验证通过”
        await asyncio.sleep(wait_seconds)

        # 执行批量清理：清理问题、用户的所有回答、以及“验证通过”的提示
        # 注意：这里没有放入 wel_msg_id，所以欢迎消息会保留
        await clean_verify_msgs(bot, state, extra_msgs=[pass_msg_id])

        # 如果你希望欢迎消息在很久之后（比如60秒）自动消失，可以开启下面这个任务
        # 如果希望永久保留，则删除下面两行
        # asyncio.create_task(delay_delete(bot, wel_msg_id, 60))

    # 2. 验证失败
    else:
        state.remaining_attempts -= 1
        # 次数用完 -> 踢人
        if state.remaining_attempts <= 0:
            state.timeout_task.cancel()
            del verifying_users[(gid_str, uid)]

            fail_msg = LangManager.get(lang, "verify_fail_kick", at_user=at_seg)
            fail_msg_id = await verify_msg.send(fail_msg)
            await kick_user(bot, gid_int, uid, fail_msg.extract_plain_text())

            # 踢人后，清理所有痕迹（问题、回答、失败提示）
            await asyncio.sleep(wait_seconds)
            await clean_verify_msgs(bot, state, extra_msgs=[fail_msg_id])

        # 次数未用完 -> 提示重试
        else:
            retry_msg = LangManager.get(lang, "verify_fail_retry", at_user=at_seg, remaining=state.remaining_attempts)
            retry_msg_id = await verify_msg.send(retry_msg)

            # 提示重试的消息可以稍后撤回，或者留在那里最后一起撤回
            # 为了版面整洁，建议短暂停留后撤回提示，但用户的错误答案留在记录里最后一起撤
            await asyncio.sleep(wait_seconds)
            await del_msg(bot, retry_msg_id)


@cmd_verify.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    # 提取参数并转小写
    arg = args.extract_plain_text().strip().lower()
    gid = str(event.group_id)

    # 分支 1: 无参数 -> 显示状态面板
    if not arg:
        conf = await get_config(gid)
        lang = conf.group.language

        msg = LangManager.get(
            lang,
            "verify_status",
            lang=lang,
            set_level_check="ON" if conf.level_checker else "OFF",
            level=conf.allowed_level,
            ver_status="ON" if conf.verify_enabled else "OFF",
            timeout=conf.verify_timeout,
            attempts=conf.verify_attempts,
            mode="Math" if conf.verify_mode == 1 else "Unknown",
        )
        await cmd_verify.finish(msg)

    # 分支 2: on/off -> 切换开关
    if arg in ["on", "开启"]:
        lang = await update_config(gid, verify_enabled=True)
        await cmd_verify.finish(LangManager.get(lang, "verify_on"))

    elif arg in ["off", "关闭"]:
        lang = await update_config(gid, verify_enabled=False)
        await cmd_verify.finish(LangManager.get(lang, "verify_off"))

    # 分支 3: 参数错误
    else:
        await cmd_verify.finish("Usage: /verify [on|off]")


@cmd_set_verify_timeout.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    gid = str(event.group_id)

    try:
        sec = int(arg)
        if sec <= 0:
            raise ValueError

        # 使用 update_config 更新时间
        lang = await update_config(gid, verify_timeout=sec)
        await cmd_set_verify_timeout.finish(LangManager.get(lang, "set_verify_time", time=sec))

    except ValueError:
        # 获取当前配置以确定回复语言
        conf = await get_config(gid)
        await cmd_set_verify_timeout.finish(LangManager.get(conf.group.language, "err_time_format"))
