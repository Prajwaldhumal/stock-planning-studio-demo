from pathlib import Path

import pandas as pd
import streamlit as st

from src.history import list_revisions, get_revision, quantities_from_revision
from src.ui import page_header, section_title

page_header(
    "Compare plans. Restore safely.",
    "Review previous revisions, compare quantities month by month, and restore a saved plan into the current working draft.",
    "AUDIT TRAIL",
)
rows = list_revisions(limit=100)
if not rows:
    st.info("No saved revisions yet. Use Plan Revisions to save the first snapshot.")
    st.page_link("pages/5_Plan_Revisions.py", label="Save a plan revision", icon=":material/event_repeat:")
    st.stop()

summary = pd.DataFrame([{
    "Created": r["created_at"].replace("T", " "),
    "Reference": r["revision_id"],
    "Part": r["part_number"],
    "Worksheet": r["sheet_name"],
    "Planning month": r["planning_month"],
    "Stage": r["revision_type"],
    "Status": r["status"],
    "Notes": r["notes"] or "—",
} for r in rows])
section_title("Saved revision register")
st.dataframe(summary, use_container_width=True, hide_index=True)

options = [r["revision_id"] for r in rows]
def option_text(revision_id: str) -> str:
    r = next(x for x in rows if x["revision_id"] == revision_id)
    return f"{r['created_at'][:16].replace('T',' ')} · {r['part_number']} · {r['revision_type']} · {r['status']} · {r['revision_id']}"

section_title("Compare two revisions")
col1, col2 = st.columns(2)
with col1:
    first_id = st.selectbox("Earlier / baseline revision", options, index=min(1, len(options)-1), format_func=option_text, key="history_baseline")
with col2:
    second_id = st.selectbox("Later / comparison revision", options, index=0, format_func=option_text, key="history_comparison")
first = get_revision(first_id)
second = get_revision(second_id)
if first and second:
    if first["part_number"] != second["part_number"] or first["sheet_name"] != second["sheet_name"]:
        st.warning("Choose revisions for the same part and worksheet to compare quantities meaningfully.")
    else:
        q1, q2 = quantities_from_revision(first), quantities_from_revision(second)
        all_months = list(dict.fromkeys(list(q1.keys()) + list(q2.keys())))
        comparison = pd.DataFrame([{
            "Month": m,
            "Baseline quantity": q1.get(m, 0),
            "Comparison quantity": q2.get(m, 0),
            "Change": q2.get(m, 0) - q1.get(m, 0),
        } for m in all_months])
        st.dataframe(comparison, use_container_width=True, hide_index=True)
        st.metric("Net quantity change", f"{sum(q2.values()) - sum(q1.values()):+,}")

section_title("Restore a revision")
restore_id = st.selectbox("Revision to restore", options, format_func=option_text, key="restore_select")
restore = get_revision(restore_id)
current_path = st.session_state.get("stock_file_path")
current_sheet = st.session_state.get("selected_sheet")
current_section = st.session_state.get("selected_section_id")
current_part = None
if current_path and current_sheet and current_section:
    try:
        from src.workbook import get_section
        current_part = get_section(current_path, current_sheet, current_section).part_number
    except Exception:
        current_part = None
compatible = bool(restore and restore["sheet_name"] == current_sheet and restore["part_number"] == current_part and current_path and Path(current_path).exists())
if restore:
    st.caption(f"Source workbook recorded for this revision: {restore['workbook_name']}")
    if not compatible:
        st.warning("The saved revision belongs to a different worksheet or no active source workbook is loaded. Load the matching workbook and worksheet before restoring.")
    if st.button("Restore into current working plan", type="primary", disabled=not compatible):
        restored_quantities = quantities_from_revision(restore)
        st.session_state.active_quantities = restored_quantities
        st.session_state.active_demand_overrides = restore.get("demand_overrides", {})
        st.session_state.demand_source = "Restored revision demand snapshot" if restore.get("demand_overrides") else "Stock Statement demand row"
        st.session_state.planning_month = restore["planning_month"]
        st.session_state.plan_status = "Restored · review required"
        st.session_state.plan_revision_label = f"Restored {restore_id}"
        st.session_state.pop("last_export_path", None)
        st.session_state.pop("last_export_name", None)
        draft = st.session_state.get("draft_plan_df")
        if isinstance(draft, pd.DataFrame) and not draft.empty and "Approved shipment" in draft.columns:
            draft = draft.copy()
            draft["Approved shipment"] = draft["Month"].map(restored_quantities).fillna(draft["Approved shipment"]).astype(int)
            st.session_state.draft_plan_df = draft
        st.success("Revision restored into the working plan. Review the quantities and preview before exporting.")
        st.page_link("pages/6_Stock_Preview_Editor.py", label="Review restored stock preview", icon=":material/table_chart:")
