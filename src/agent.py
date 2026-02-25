from __future__ import annotations

import json
from typing import Any

from src.config import settings
from src.metrics import (
    QueryIntent,
    leadership_update,
    operations_metrics,
    parse_intent,
    pipeline_metrics,
    revenue_metrics,
)
from src.normalization import data_quality_report


def _render_dict(d: dict[str, Any]) -> str:
    return "\n".join([f"- {k}: {v}" for k, v in d.items()]) if d else "- No breakdown available"


def _llm_parse_intent(question: str) -> QueryIntent:
    if not settings.openai_api_key:
        return parse_intent(question)

    try:
        from openai import OpenAI
    except Exception:
        return parse_intent(question)

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = (
        "Extract business query intent as JSON with keys metric, sector, period. "
        "metric in [pipeline,revenue,collections,operations,leadership_update,general], "
        "period in [this_quarter,this_month,this_year,null]."
    )

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        return QueryIntent(
            metric=payload.get("metric") or "general",
            sector=payload.get("sector"),
            period=payload.get("period"),
        )
    except Exception:
        # Keep the app functional when OpenAI key/model is invalid or unavailable.
        return parse_intent(question)


def answer_question(question: str, deals_df, work_orders_df) -> str:
    intent = _llm_parse_intent(question)
    metric = intent.metric

    if metric == "pipeline":
        result = pipeline_metrics(deals_df, intent.sector, intent.period)
        summary = [
            "Pipeline snapshot",
            f"- Open deals: {result.get('open_deals', 0)}",
            f"- Total open pipeline value: Rs {result.get('total_pipeline', 0):,.2f}",
            f"- Median deal size: Rs {result.get('median_deal', 0):,.2f}",
            "- Top stages by value:",
            _render_dict(result.get("top_stages", {})),
        ]
    elif metric in {"revenue", "collections"}:
        result = revenue_metrics(work_orders_df, intent.sector, intent.period)
        summary = [
            "Revenue & collections snapshot",
            f"- Work orders in scope: {result.get('work_orders', 0)}",
            f"- Billed (incl GST): Rs {result.get('billed_incl_gst', 0):,.2f}",
            f"- Collected (incl GST): Rs {result.get('collected_incl_gst', 0):,.2f}",
            f"- Receivable: Rs {result.get('receivable', 0):,.2f}",
            f"- Collection efficiency: {result.get('collection_efficiency_pct')}%",
        ]
    elif metric == "operations":
        result = operations_metrics(work_orders_df, intent.sector, intent.period)
        summary = [
            "Operations snapshot",
            f"- Work orders in scope: {result.get('work_orders', 0)}",
            "- Execution status mix:",
            _render_dict(result.get("execution_status", {})),
            "- Billing status mix:",
            _render_dict(result.get("billing_status", {})),
        ]
    elif metric == "leadership_update":
        result = leadership_update(deals_df, work_orders_df)
        summary = [
            "Leadership update draft (current quarter)",
            "- Pipeline:",
            _render_dict(result.get("pipeline", {})),
            "- Revenue:",
            _render_dict(result.get("revenue", {})),
            "- Operations:",
            _render_dict(result.get("operations", {})),
        ]
    else:
        return (
            "I can help with pipeline, revenue, collections, operations, or leadership updates. "
            "Please include a metric and optional scope like sector and time period.\n"
            "Example: `How is the powerline pipeline this quarter?`"
        )

    deals_quality = data_quality_report(
        deals_df,
        ["deal_value", "deal_status", "tentative_close_date", "sector"],
    )
    wo_quality = data_quality_report(
        work_orders_df,
        ["billed_value_incl_gst", "collected_amount_incl_gst", "amount_receivable", "execution_status"],
    )

    caveats = [
        "",
        "Data quality caveats",
        f"- Deals rows: {deals_quality.get('row_count', 0)} | Missing critical fields (%): {deals_quality.get('missing', {})}",
        f"- Work order rows: {wo_quality.get('row_count', 0)} | Missing critical fields (%): {wo_quality.get('missing', {})}",
    ]

    return "\n".join(summary + caveats)
