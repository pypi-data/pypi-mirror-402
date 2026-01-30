from nonebot import on_command
# # ...

# cmd_ban = on_command("ban_user", aliases={"拉黑"}, ...)

# @cmd_ban.handle()
# async def _(event: GroupMessageEvent):
#     # 这里写拉黑的逻辑，写入 Blacklist 表
#     pass