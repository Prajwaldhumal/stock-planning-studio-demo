from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from src.ui import page_header, section_title
from src.workbook import inspect_stock_workbook

page_header(
    "Sales planning, without the spreadsheet grind.",
    "A controlled workspace to build a shipment plan, update manufacturing quantities, review stock impact and export the familiar Stock Statement workbook.",
    "PLANNING OVERVIEW",
)

stock_path = st.session_state.get("stock_file_path")
plan_df = st.session_state.get("draft_plan_df")
active_qty = st.session_state.get("active_quantities", {}) or {}

col1, col2, col3, col4 = st.columns(4)
col1.metric("Stock workbook", "Ready" if stock_path and Path(stock_path).exists() else "Not uploaded")
col2.metric("Plan status", st.session_state.get("plan_status", "Not generated"))
col3.metric("Months in plan", len(plan_df) if plan_df is not None else 0)
col4.metric("Shipment quantity", f"{sum(active_qty.values()):,.0f}" if active_qty else "—")

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
section_title("Your planning workflow", "Move through the steps in order. Existing plans are kept intact until you export a revised workbook.")
cols = st.columns(3, gap="medium")
steps = [
    ("01", "Upload & validate", "Load the Stock Statement and supporting source files. Check worksheet and part mappings.", "pages/2_Upload_Validate.py", "Open uploads"),
    ("02", "Generate a plan", "Select a worksheet, part section and start month to produce a draft shipment recommendation.", "pages/3_Generate_Plan.py", "Generate plan"),
    ("03", "Review & export", "Edit approved quantities, preview recalculated stock rows, then download the finished workbook.", "pages/4_Shipment_Recommendations.py", "Review quantities"),
]
for c, (num, title, body, target, label) in zip(cols, steps):
    with c:
        st.markdown(f"<div class='info-card'><div class='section-kicker'>STEP {num}</div><h3>{title}</h3><p>{body}</p></div>", unsafe_allow_html=True)
        st.page_link(target, label=label, icon=":material/arrow_forward:")

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
left, right = st.columns([1.15, 1], gap="large")
with left:
    section_title("Workspace files")
    file_rows = []
    for label, key in [
        ("Stock Statement", "stock_file_path"),
        ("MANIANA workbook", "maniana_file_path"),
        ("Customer EDI", "edi_file_path"),
        ("SAP actuals", "sap_file_path"),
    ]:
        path = st.session_state.get(key)
        file_rows.append({"Input": label, "Status": "Loaded" if path and Path(path).exists() else "Not added", "File": Path(path).name if path and Path(path).exists() else "—"})
    st.dataframe(pd.DataFrame(file_rows), use_container_width=True, hide_index=True)
with right:
    section_title("Current plan")
    if plan_df is None or not hasattr(plan_df, "empty") or plan_df.empty:
        st.info("No draft plan yet. Start by uploading your current Stock Statement.")
        st.page_link("pages/2_Upload_Validate.py", label="Go to Upload & Validation", icon=":material/cloud_upload:")
    else:
        show_cols = [c for c in ["Month", "Existing shipment", "Suggested shipment", "Approved shipment"] if c in plan_df.columns]
        st.dataframe(plan_df[show_cols].head(7), use_container_width=True, hide_index=True)
        st.caption("Showing the first seven months in the active draft.")

st.markdown("<div class='warning-strip'><b>Planning logic status:</b> The current shipment recommendation is a transparent, configurable coverage heuristic. Replace it with Sales’ approved container and multiplier rules before operational use.</div>", unsafe_allow_html=True)
