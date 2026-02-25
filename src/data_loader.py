from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import settings
from src.monday_client import MondayClient


def _read_csv_if_exists(path: str) -> pd.DataFrame:
    file = Path(path)
    if not file.exists():
        return pd.DataFrame()

    df = pd.read_csv(file)
    unnamed_ratio = (
        sum(str(c).strip().lower().startswith("unnamed") for c in df.columns) / max(len(df.columns), 1)
    )

    # Some exports contain an empty first row; if many unnamed columns exist, treat row 2 as header.
    if unnamed_ratio > 0.5:
        df = pd.read_csv(file, header=1)

    return df


def load_from_monday() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not settings.monday_api_token:
        raise ValueError("MONDAY_API_TOKEN is missing")
    if not settings.monday_deals_board_id or not settings.monday_work_orders_board_id:
        raise ValueError("MONDAY_DEALS_BOARD_ID and MONDAY_WORK_ORDERS_BOARD_ID are required")

    client = MondayClient(settings.monday_api_token, settings.monday_api_url)
    deals_rows = client.fetch_board_items(settings.monday_deals_board_id)
    work_orders_rows = client.fetch_board_items(settings.monday_work_orders_board_id)
    return pd.DataFrame(deals_rows), pd.DataFrame(work_orders_rows)


def load_data(mode: str = "monday") -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if mode == "csv":
        deals = _read_csv_if_exists("Deal_funnel_Data.csv")
        work_orders = _read_csv_if_exists("Work_Order_Tracker_Data.csv")
        return deals, work_orders, "csv"

    deals, work_orders = load_from_monday()
    return deals, work_orders, "monday"
