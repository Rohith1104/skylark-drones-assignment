from dataclasses import dataclass
from typing import Optional
import os

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(*args, **kwargs):
        return False


load_dotenv()


@dataclass
class Settings:
    monday_api_token: Optional[str] = os.getenv("MONDAY_API_TOKEN")
    monday_api_url: str = os.getenv("MONDAY_API_URL", "https://api.monday.com/v2")
    monday_deals_board_id: Optional[str] = os.getenv("MONDAY_DEALS_BOARD_ID")
    monday_work_orders_board_id: Optional[str] = os.getenv("MONDAY_WORK_ORDERS_BOARD_ID")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()
