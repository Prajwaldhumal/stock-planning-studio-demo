from pathlib import Path

import pandas as pd
import streamlit as st

from src.history import save_revision, list_revisions
from src.planning import active_quantities_from_df
from src.ui import page_header, section_title

page_header(
    "Keep every planning decision traceable.",
    "Save an initial plan, a manufacturing update, or a later monthly revision without losing the previous approved quantities.",
    "REVISION CONTROL",
)
draft = st.session_state.get("draft_plan_df")
quantities = st.session_state.get("active_quantities", {}) or {}
if draft is not None and isinstance(draft, pd.DataFrame) and not draft.empty:
    quantities = active_quantities_from_df(draft)
    st.session_state.active_quantities = quantities
if not quantities:
    st.info("Generate a stock plan and review the suggested quantities before saving a revision.")
    st.page_link("pages/3_Generate_Plan.py", label="Generate a stock plan", icon=":material/calculate:")
    st.stop()

stock_path = st.session_state.get("stock_file_path")
sheet = st.session_state.get("selected_sheet") or ""
section_id = st.session_state.get("selected_section_id") or ""
planning_month = st.session_state.get("planning_month") or (next(iter(quantities), ""))
status_default = st.session_state.get("plan_status", "Draft")

col1, col2, col3 = st.columns(3)
col1.metric("Months captured", len(quantities))
col2.metric("Total active shipments", f"{sum(quantities.values()):,}")
col3.metric("Current state", status_default)

section_title("Save a revision", "Choose the business event that explains why quantities changed. Each save creates a new immutable history entry.")
with st.form("save_revision_form", clear_on_submit=False):
    rev_type = st.selectbox("Revision stage", ["Initial Plan — 1st", "Manufacturing Update — 7th", "Monthly Revision — 25th", "Ad hoc correction"])
    status = st.selectbox("Revision status", ["Draft", "Submitted for approval", "Approved"], index=0)
    notes = st.text_area("Change note", placeholder="Example: Updated October shipment quantities after manufacturing confirmation.", height=90)
    submitted = st.form_submit_button("Save revision to history", type="primary", use_container_width=True)
    if submitted:
        try:
            # Identify title/part metadata from the current selected section when possible.
            from src.workbook import get_section
            section = get_section(stock_path, sheet, section_id) if stock_path and section_id else None
            title = section.title if section else "Unknown section"
            part = section.part_number if section else "Unknown part"
            revision_id = save_revision(
                workbook_name=Path(stock_path).name if stock_path else "Unknown workbook",
                sheet_name=sheet,
                section_title=title,
                part_number=part,
                planning_month=planning_month,
                revision_type=rev_type,
                status=status,
                notes=(notes.strip() + (f"\nDemand source: {st.session_state.get('demand_source')}" if st.session_state.get("active_demand_overrides") else "")),
                quantities=quantities,
                demand_overrides=st.session_state.get("active_demand_overrides", {}),
            )
            st.session_state.plan_status = status
            st.session_state.plan_revision_label = rev_type
            st.success(f"Revision saved successfully. Reference: {revision_id}")
        except Exception as exc:
            st.error(f"Could not save the revision: {exc}")

section_title("Recent revisions")
rows = list_revisions(limit=12)
if rows:
    history_df = pd.DataFrame([{
        "Created": r["created_at"].replace("T", " "),
        "Reference": r["revision_id"],
        "Part": r["part_number"],
        "Planning month": r["planning_month"],
        "Stage": r["revision_type"],
        "Status": r["status"],
        "Notes": r["notes"] or "—",
    } for r in rows])
    st.dataframe(history_df, use_container_width=True, hide_index=True)
else:
    st.caption("No revisions have been saved in this workspace yet.")

st.markdown("<div class='warning-strip'><b>Important:</b> Saving a revision records the active month-to-quantity plan and its metadata. The Stock Statement file is updated only when you generate an export.</div>", unsafe_allow_html=True)
