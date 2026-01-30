from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .locales import LangManager
from .service import update_language


async def admin_perm(bot: Bot, event: GroupMessageEvent) -> bool:
    """
    ## 检查管理权限
    ## CheckAdminPermission

    检查消息是否为管理员/群主/机器人超级用户所发出<br>
    Check if the message is sent by the administrator/group owner/robot super user

    :param Bot bot: bot实例
    :param GroupMessageEvent event: 消息实例
    :param check_admin: 是否检查管理员
    :param check_owenr: 是否检查为群组所有者
    :return bool: 是否为真
    """
    if await GROUP_OWNER(bot, event):
        return True
    if await GROUP_ADMIN(bot, event):
        return True
    if await SUPERUSER(bot, event):
        return True
    return False


# === 新增：惩罚逻辑 ===
async def check_admin_or_punish(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    """依赖注入：检查权限，如果没有权限则禁言并结束"""
    has_perm = await admin_perm(bot, event)

    if not has_perm:
        # 1. 执行禁言 (例如 60 秒)
        try:
            # 注意：Bot 必须是管理员才能禁言别人
            await bot.set_group_ban(group_id=event.group_id, user_id=event.user_id, duration=60 * 10)
            await matcher.send("⚠️ 权限不足，非法调用管理指令，禁言 10 分钟。")
        except Exception:
            # 如果 Bot 没权限禁言，或者禁言失败（例如对方也是管理），只发提示
            await matcher.send("⚠️ 权限不足。")

        # 2. 阻断后续逻辑
        await matcher.finish()


# === 新增：自定义命令包装器 ===
def on_admin_command(*args, **kwargs):
    """
    创建一个会自动检查管理员权限的命令。
    如果权限不足，会自动禁言用户。
    替代原始的 on_command 使用。
    """
    # 强制移除 permission 参数，确保命令能被触发，从而进入我们的惩罚逻辑
    kwargs.pop("permission", None)

    # 创建 Matcher
    matcher = on_command(*args, **kwargs)

    # 关键点：将检查逻辑注册为第一个 Handler
    # NoneBot 按注册顺序执行 Handler，这个会最先运行
    matcher.handle()(check_admin_or_punish)

    return matcher


cmd_set_lang = on_command("setlang", priority=30, block=False, permission=admin_perm)


@cmd_set_lang.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().lower()
    available = LangManager.get_available_langs()  # ['zh', 'en', 'jp'...]
    if not arg:
        lang_list = ", ".join(available)
        await cmd_set_lang.finish(f"Available languages: {lang_list}\nUsage: /setlang <lang>")

    # 2. 检查输入是否有效
    # 这里做一个简单的别名映射（可选）
    alias = {"english": "en", "chinese": "zh"}

    target_lang = alias.get(arg, arg)

    if target_lang not in available:
        lang_list = ", ".join(available)
        await cmd_set_lang.finish(f"❌ Invalid language: {arg}\nAvailable: {lang_list}")
    # update setting
    gid = str(event.group_id)
    await update_language(gid, target_lang)
    # 4. 用新语言回复
    await cmd_set_lang.finish(LangManager.get(target_lang, "set_lang"))
