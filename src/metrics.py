from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

import pandas as pd


@dataclass
class QueryIntent:
    metric: str
    sector: str | None = None
    period: str | None = None


def parse_intent(question: str) -> QueryIntent:
    q = question.lower().strip()
    sector_match = re.search(r"(?:for|in)\s+([a-z\-\s]+?)\s+(?:sector|industry)", q)
    sector = sector_match.group(1).strip() if sector_match else None

    period = None
    if "this quarter" in q or "current quarter" in q:
        period = "this_quarter"
    elif "this month" in q or "current month" in q:
        period = "this_month"
    elif "this year" in q or "current year" in q:
        period = "this_year"

    if "leadership update" in q or "leadership" in q:
        metric = "leadership_update"
    elif any(k in q for k in ["pipeline", "deal", "funnel"]):
        metric = "pipeline"
    elif any(k in q for k in ["revenue", "billing", "billed"]):
        metric = "revenue"
    elif any(k in q for k in ["collection", "receivable", "ar"]):
        metric = "collections"
    elif any(k in q for k in ["execution", "ops", "operational", "work order"]):
        metric = "operations"
    else:
        metric = "general"

    return QueryIntent(metric=metric, sector=sector, period=period)


def _quarter_bounds(ref: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    quarter = (ref.month - 1) // 3 + 1
    start_month = 3 * (quarter - 1) + 1
    start = pd.Timestamp(date(ref.year, start_month, 1))
    end = start + pd.offsets.QuarterEnd()
    return start, end


def _filter_period(df: pd.DataFrame, date_col: str, period: str | None, today: date | None = None) -> pd.DataFrame:
    if period is None or date_col not in df.columns:
        return df

    if today is None:
        today = date.today()

    if period == "this_quarter":
        start, end = _quarter_bounds(today)
    elif period == "this_month":
        start = pd.Timestamp(date(today.year, today.month, 1))
        end = start + pd.offsets.MonthEnd()
    elif period == "this_year":
        start = pd.Timestamp(date(today.year, 1, 1))
        end = pd.Timestamp(date(today.year, 12, 31))
    else:
        return df

    return df[df[date_col].between(start, end, inclusive="both")]


def _apply_sector_filter(df: pd.DataFrame, sector: str | None) -> pd.DataFrame:
    if not sector or "sector_norm" not in df.columns:
        return df
    sector_norm = sector.strip().lower()
    return df[df["sector_norm"].str.contains(sector_norm, na=False)]


def pipeline_metrics(deals_df: pd.DataFrame, sector: str | None, period: str | None) -> dict[str, object]:
    if deals_df.empty:
        return {"note": "No deals data available."}

    df = deals_df.copy()
    df = _apply_sector_filter(df, sector)
    df = _filter_period(df, "tentative_close_date", period)

    open_df = df[df["deal_status_norm"].str.contains("open", na=False)] if "deal_status_norm" in df.columns else df
    total_pipeline = float(open_df["deal_value"].fillna(0).sum()) if "deal_value" in open_df.columns else 0.0
    median_deal = float(open_df["deal_value"].dropna().median()) if "deal_value" in open_df.columns and not open_df["deal_value"].dropna().empty else 0.0

    by_stage = (
        open_df.groupby("deal_stage", dropna=False)["deal_value"].sum().sort_values(ascending=False).head(5).to_dict()
        if "deal_stage" in open_df.columns and "deal_value" in open_df.columns
        else {}
    )

    return {
        "open_deals": int(len(open_df)),
        "total_pipeline": round(total_pipeline, 2),
        "median_deal": round(median_deal, 2),
        "top_stages": {str(k): round(float(v), 2) for k, v in by_stage.items()},
    }


def revenue_metrics(work_orders_df: pd.DataFrame, sector: str | None, period: str | None) -> dict[str, object]:
    if work_orders_df.empty:
        return {"note": "No work orders data available."}

    df = work_orders_df.copy()
    df = _apply_sector_filter(df, sector)
    df = _filter_period(df, "probable_end_date", period)

    billed = float(df["billed_value_incl_gst"].fillna(0).sum()) if "billed_value_incl_gst" in df.columns else 0.0
    collected = float(df["collected_amount_incl_gst"].fillna(0).sum()) if "collected_amount_incl_gst" in df.columns else 0.0
    receivable = float(df["amount_receivable"].fillna(0).sum()) if "amount_receivable" in df.columns else 0.0

    return {
        "work_orders": int(len(df)),
        "billed_incl_gst": round(billed, 2),
        "collected_incl_gst": round(collected, 2),
        "receivable": round(receivable, 2),
        "collection_efficiency_pct": round((collected / billed * 100.0), 1) if billed > 0 else None,
    }


def operations_metrics(work_orders_df: pd.DataFrame, sector: str | None, period: str | None) -> dict[str, object]:
    if work_orders_df.empty:
        return {"note": "No work orders data available."}

    df = _apply_sector_filter(work_orders_df, sector)
    df = _filter_period(df, "probable_end_date", period)

    status_dist = (
        df["execution_status"].fillna("Unknown").value_counts().head(6).to_dict()
        if "execution_status" in df.columns
        else {}
    )
    billing_dist = (
        df["billing_status"].fillna("Unknown").value_counts().head(6).to_dict()
        if "billing_status" in df.columns
        else {}
    )

    return {
        "work_orders": int(len(df)),
        "execution_status": {str(k): int(v) for k, v in status_dist.items()},
        "billing_status": {str(k): int(v) for k, v in billing_dist.items()},
    }


def leadership_update(deals_df: pd.DataFrame, work_orders_df: pd.DataFrame) -> dict[str, object]:
    return {
        "pipeline": pipeline_metrics(deals_df, sector=None, period="this_quarter"),
        "revenue": revenue_metrics(work_orders_df, sector=None, period="this_quarter"),
        "operations": operations_metrics(work_orders_df, sector=None, period="this_quarter"),
    }
