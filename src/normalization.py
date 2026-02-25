from __future__ import annotations

import re
from typing import Iterable

import pandas as pd


_NULL_TOKENS = {"", "none", "null", "nan", "na", "n/a", "-", "--"}


def _norm_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).strip().lower())


def _choose_column(columns: Iterable[str], aliases: list[str]) -> str | None:
    lookup = {_norm_key(c): c for c in columns}
    for alias in aliases:
        col = lookup.get(_norm_key(alias))
        if col:
            return col
    return None


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _NULL_TOKENS:
        return None
    return text


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace(list(_NULL_TOKENS), pd.NA), errors="coerce")


def _to_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def normalize_deals(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame()

    raw_df = raw_df.copy()
    raw_df.columns = [str(c).strip() for c in raw_df.columns]

    out = pd.DataFrame()
    out["deal_name"] = raw_df.get(_choose_column(raw_df.columns, ["Deal Name", "item_name"]))
    out["owner_code"] = raw_df.get(_choose_column(raw_df.columns, ["Owner code", "Owner", "Account Owner"]))
    out["client_code"] = raw_df.get(_choose_column(raw_df.columns, ["Client Code", "Customer", "Customer Name Code"]))
    out["deal_status"] = raw_df.get(_choose_column(raw_df.columns, ["Deal Status", "Status"]))
    out["close_probability"] = raw_df.get(_choose_column(raw_df.columns, ["Closure Probability", "Probability"]))
    out["deal_value"] = raw_df.get(_choose_column(raw_df.columns, ["Masked Deal value", "Deal value", "Value"]))
    out["tentative_close_date"] = raw_df.get(_choose_column(raw_df.columns, ["Tentative Close Date", "Close Date", "Expected Close Date"]))
    out["close_date"] = raw_df.get(_choose_column(raw_df.columns, ["Close Date (A)", "Close Date", "Actual Close Date"]))
    out["deal_stage"] = raw_df.get(_choose_column(raw_df.columns, ["Deal Stage", "Stage"]))
    out["product_deal"] = raw_df.get(_choose_column(raw_df.columns, ["Product deal", "Product"]))
    out["sector"] = raw_df.get(_choose_column(raw_df.columns, ["Sector/service", "Sector", "Industry"]))
    out["created_date"] = raw_df.get(_choose_column(raw_df.columns, ["Created Date", "item_created_at"]))

    for col in out.columns:
        if out[col].dtype == "object":
            out[col] = out[col].map(_clean_text)

    out["deal_value"] = _to_numeric(out["deal_value"])
    out["tentative_close_date"] = _to_date(out["tentative_close_date"])
    out["close_date"] = _to_date(out["close_date"])
    out["created_date"] = _to_date(out["created_date"])

    out["sector_norm"] = out["sector"].fillna("Unknown").str.strip().str.lower()
    out["deal_status_norm"] = out["deal_status"].fillna("Unknown").str.strip().str.lower()

    return out


def normalize_work_orders(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame()

    df = raw_df.copy()

    # Some exports include a blank first row; remove rows that are entirely empty.
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    out = pd.DataFrame()
    out["deal_name"] = df.get(_choose_column(df.columns, ["Deal name masked", "Deal Name", "item_name"]))
    out["customer_code"] = df.get(_choose_column(df.columns, ["Customer Name Code", "Customer", "Client Code"]))
    out["serial_no"] = df.get(_choose_column(df.columns, ["Serial #", "Serial"]))
    out["nature_of_work"] = df.get(_choose_column(df.columns, ["Nature of Work", "Work Type"]))
    out["execution_status"] = df.get(_choose_column(df.columns, ["Execution Status", "WO Status", "Status"]))
    out["sector"] = df.get(_choose_column(df.columns, ["Sector", "Sector/service", "Industry"]))
    out["type_of_work"] = df.get(_choose_column(df.columns, ["Type of Work", "Work Category"]))
    out["owner_code"] = df.get(_choose_column(df.columns, ["BD/KAM Personnel code", "Owner code", "Owner"]))
    out["probable_start_date"] = df.get(_choose_column(df.columns, ["Probable Start Date", "Start Date"]))
    out["probable_end_date"] = df.get(_choose_column(df.columns, ["Probable End Date", "End Date"]))
    out["invoice_status"] = df.get(_choose_column(df.columns, ["Invoice Status", "Billing Status"]))
    out["billing_status"] = df.get(_choose_column(df.columns, ["Billing Status", "WO Status (billed)"]))
    out["collection_status"] = df.get(_choose_column(df.columns, ["Collection status", "Collection Status"]))
    out["billed_value_incl_gst"] = df.get(
        _choose_column(df.columns, ["Billed Value in Rupees (Incl of GST.) (Masked)", "Billed Value"])
    )
    out["collected_amount_incl_gst"] = df.get(
        _choose_column(df.columns, ["Collected Amount in Rupees (Incl of GST.) (Masked)", "Collected Amount"])
    )
    out["amount_receivable"] = df.get(_choose_column(df.columns, ["Amount Receivable (Masked)", "Amount Receivable"]))

    for col in out.columns:
        if out[col].dtype == "object":
            out[col] = out[col].map(_clean_text)

    numeric_cols = ["billed_value_incl_gst", "collected_amount_incl_gst", "amount_receivable"]
    for col in numeric_cols:
        out[col] = _to_numeric(out[col])

    out["probable_start_date"] = _to_date(out["probable_start_date"])
    out["probable_end_date"] = _to_date(out["probable_end_date"])
    out["sector_norm"] = out["sector"].fillna("Unknown").str.strip().str.lower()

    return out


def data_quality_report(df: pd.DataFrame, critical_columns: list[str]) -> dict[str, object]:
    if df.empty:
        return {"row_count": 0, "missing": {}, "note": "No rows available"}

    missing = {}
    for col in critical_columns:
        if col in df.columns:
            pct = float(df[col].isna().mean() * 100)
            missing[col] = round(pct, 1)

    return {
        "row_count": int(len(df)),
        "missing": missing,
    }
