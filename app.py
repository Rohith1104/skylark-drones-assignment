from __future__ import annotations

import streamlit as st

from src.agent import answer_question
from src.data_loader import load_data
from src.normalization import normalize_deals, normalize_work_orders


st.set_page_config(page_title="Skylark BI Agent", page_icon="??", layout="wide")
st.title("Monday.com BI Agent")
st.caption("Founder-level analytics across Deals and Work Orders boards")

with st.sidebar:
    st.subheader("Data source")
    mode = st.selectbox(
        "Load data from",
        options=["monday", "csv"],
        index=0,
        help="Use monday for assignment-compliant mode. CSV is local fallback for demo only.",
    )
    st.markdown("Environment variables required for monday mode:")
    st.code("MONDAY_API_TOKEN\nMONDAY_DEALS_BOARD_ID\nMONDAY_WORK_ORDERS_BOARD_ID")


@st.cache_data(ttl=300)
def _load(mode: str):
    deals_raw, work_orders_raw, source = load_data(mode=mode)
    deals = normalize_deals(deals_raw)
    work_orders = normalize_work_orders(work_orders_raw)
    return deals, work_orders, source


try:
    deals_df, work_orders_df, source = _load(mode)
except Exception as exc:
    st.error(f"Failed to load data: {exc}")
    st.stop()

st.success(f"Loaded data source: {source}")
col1, col2 = st.columns(2)
col1.metric("Deals rows", len(deals_df))
col2.metric("Work Orders rows", len(work_orders_df))

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Ask a business question, e.g. `How is our mining pipeline this quarter?`",
        }
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask about pipeline, revenue, collections, operations, or leadership updates")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = answer_question(prompt, deals_df, work_orders_df)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
