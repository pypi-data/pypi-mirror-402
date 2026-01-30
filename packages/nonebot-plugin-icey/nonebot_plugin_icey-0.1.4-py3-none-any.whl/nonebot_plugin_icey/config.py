from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    # 你可以通过 .env 文件覆盖这些值
    welcome_message: str = "🎉 欢迎 {user} 加入本群！"
    goodbye_message: str = "很遗憾 {user} 已离开本群。"
    welcome_auto_delete_time: int = 30
    lang: str = "en"
