import asyncio

from nonebot import get_plugin_config, on_command, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupDecreaseNoticeEvent, GroupIncreaseNoticeEvent, GroupMessageEvent, Message
from nonebot.params import CommandArg

from ...common.locales import LangManager
from ...common.matcher import admin_perm
from ...config import Config
from .service import get_config, send_goodbye_message, send_welcome_message, update_config

# === 1. 合并后的主命令 ===
# /welcome [on/off]
cmd_welcome = on_command("welcome", priority=30, block=False, permission=admin_perm)
# /goodbye [on/off]
cmd_goodbye = on_command("goodbye", priority=30, block=False, permission=admin_perm)

cmd_set_welcome = on_command("setwelcome", priority=30, block=False, permission=admin_perm)
cmd_set_goodbye = on_command("setgoodbye", priority=30, block=False, permission=admin_perm)
cmd_reset_welcome = on_command("resetwelcome", priority=30, block=False, permission=admin_perm)
cmd_reset_goodbye = on_command("resetgoodbye", priority=30, block=False, permission=admin_perm)
cmd_cleanwelcome = on_command("cleanwelcometime ", priority=30, block=False, permission=admin_perm)

# === 新增：入群/退群事件监听 ===

welcome_notice_handle = on_notice(priority=30, block=False)

plugin_config = get_plugin_config(Config)


@welcome_notice_handle.handle()
async def handle_group_increase(bot: Bot, event: GroupIncreaseNoticeEvent):
    # 如果是 Bot 自己进群，忽略
    if event.user_id == int(bot.self_id):
        return

    # 直接调用 service 发送欢迎
    # 注意：这里我们不需要判断"是否开启了验证"，
    # 因为如果开启了验证，Verify 模块的监听器(priority=4)会先运行并拦截事件
    await send_welcome_message(bot, event.group_id, event.user_id)


@welcome_notice_handle.handle()
async def handle_group_decrease(bot: Bot, event: GroupDecreaseNoticeEvent):
    "退群监听"
    if event.user_id == int(bot.self_id):
        return

    # 获取配置检查是否开启退群通知
    conf = await get_config(str(event.group_id))
    if not conf.should_goodbye:
        return

    await send_goodbye_message(bot, group_id=event.group_id, user_id=event.user_id)


@cmd_welcome.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 提取参数并转小写
    arg = args.extract_plain_text().strip().lower()
    gid = str(event.group_id)

    # 1. 如果没有参数 -> 显示状态面板
    if not arg:
        conf = await get_config(gid)
        lang = conf.group.language

        msg = LangManager.get(
            lang,
            "welcome_status",
            lang=lang,
            wel_status="ON" if conf.should_welcome else "OFF",
            bye_status="ON" if conf.should_goodbye else "OFF",
            autodel=f"{conf.auto_delete_time}s" if conf.auto_delete_time > 0 else "OFF",
            wel_msg=conf.welcome_message,
            bye_msg=conf.goodbye_message,
        )
        if conf.auto_delete_time > 0:
            msg_id = await cmd_welcome.send(msg)
            await asyncio.sleep(conf.auto_delete_time)
            try:
                await bot.delete_msg(message_id=msg_id["message_id"])
            except Exception:
                pass
            return
        else:
            await cmd_welcome.finish(msg)

    # 2. 如果参数是 on/off -> 切换开关
    if arg in ["on", "开启"]:
        lang = await update_config(gid, should_welcome=True)
        await cmd_welcome.finish(LangManager.get(lang, "welcome_on"))

    elif arg in ["off", "关闭"]:
        lang = await update_config(gid, should_welcome=False)
        await cmd_welcome.finish(LangManager.get(lang, "welcome_off"))

    # 3. 如果参数无法识别
    else:
        await cmd_welcome.finish("Usage: /welcome [on|off]")


@cmd_goodbye.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().lower()
    gid = str(event.group_id)
    if arg in ["on", "开启"]:
        lang = await update_config(gid, should_goodbye=True)
        await cmd_goodbye.finish(LangManager.get(lang, "goodbye_on"))

    elif arg in ["off", "关闭"]:
        lang = await update_config(gid, should_goodbye=False)
        await cmd_goodbye.finish(LangManager.get(lang, "goodbye_off"))

    # 如果没有参数或参数不对，提示用法
    else:
        await cmd_goodbye.finish("Usage: /goodbye [on|off]")


# === 下面是保持不变的 Set/Reset 命令 ===


@cmd_set_welcome.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    msg = args.extract_plain_text().strip()
    if not msg:
        conf = await get_config(str(event.group_id))
        await cmd_set_welcome.finish(LangManager.get(conf.group.language, "err_no_content"))
    await update_config(str(event.group_id), welcome_message=msg)
    await cmd_set_welcome.finish(f"✅ OK:\n{msg}")


@cmd_set_goodbye.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    msg = args.extract_plain_text().strip()
    if not msg:
        conf = await get_config(str(event.group_id))
        await cmd_set_goodbye.finish(LangManager.get(conf.group.language, "err_no_content"))

    await update_config(str(event.group_id), goodbye_message=msg)
    await cmd_set_goodbye.finish(f"✅ OK:\n{msg}")


@cmd_cleanwelcome.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    try:
        sec = int(args.extract_plain_text().strip())
        lang = await update_config(str(event.group_id), auto_delete_time=sec)

        key = "set_autodel_off" if sec == 0 else "set_autodel"
        await cmd_cleanwelcome.finish(LangManager.get(lang, key, time=sec))
    except ValueError:
        conf = await get_config(str(event.group_id))
        await cmd_cleanwelcome.finish(LangManager.get(conf.group.language, "err_time_format"))


@cmd_reset_welcome.handle()
async def _(event: GroupMessageEvent):
    await update_config(str(event.group_id), welcome_message=plugin_config.welcome_message)
    await cmd_reset_welcome.finish("✅ Reset Welcome Message")


@cmd_reset_goodbye.handle()
async def _(event: GroupMessageEvent):
    await update_config(str(event.group_id), goodbye_message=plugin_config.goodbye_message)
    await cmd_reset_goodbye.finish("✅ Reset Goodbye Message")
