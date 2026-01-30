from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
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


cmd_set_lang = on_command(
    "setlang", priority=30, block=False, state={"require_admin": True}
)


@cmd_set_lang.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip().lower()
    available = LangManager.get_available_langs()  # ['zh', 'en', 'jp'...]
    if not arg:
        lang_list = ", ".join(available)
        await cmd_set_lang.finish(
            f"Available languages: {lang_list}\nUsage: /setlang <lang>"
        )

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
