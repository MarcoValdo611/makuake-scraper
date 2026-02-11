import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    # 直接抓取项目的 hero widget（其中包含实时金额和支持者人数）
    # 如需改回主项目页，可再调整 parser 中的 XPath。
    target_url: str = "https://www.makuake.com/widget/project/iflytek_aiwtch/hero/"
    # PostgreSQL 连接串，例如：
    # postgresql://user:password@host:port/dbname
    database_url: str = os.getenv("DATABASE_URL", "")
    timezone: str = os.getenv("TZ", "Asia/Shanghai")
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "15"))


settings = Settings()

