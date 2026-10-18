import pandas as pd
import streamlit as st

from src.planning import active_quantities_from_df
from src.ui import page_header, section_title

page_header(
    "Review every recommendation before it becomes a plan.",
    "The suggested quantity is a draft. Edit the approved shipment values, apply your manufacturing updates and inspect differences before approval.",
    "SALES REVIEW",
)
draft = st.session_state.get("draft_plan_df")
if draft is None or not isinstance(draft, pd.DataFrame) or draft.empty:
    st.info("No draft plan is available yet. Generate one first.")
    st.page_link("pages/3_Generate_Plan.py", label="Generate a stock plan", icon=":material/calculate:")
    st.stop()

# Make sure state has the latest edited quantities as the user navigates across pages.
view_cols = ["Month", "Customer demand", "Existing shipment", "Pipeline before plan", "Suggested shipment", "Approved shipment"]
visible = draft[view_cols].copy()
visible["Approved shipment"] = pd.to_numeric(visible["Approved shipment"], errors="coerce").fillna(0).clip(lower=0).round().astype(int)

def quantity_map(frame):
    return {str(row["Month"]): int(round(float(row["Approved shipment"]))) for _, row in frame.iterrows()}

initial_map = quantity_map(visible)
if "recommendation_last_editor_values" not in st.session_state:
    st.session_state.recommendation_last_editor_values = initial_map.copy()
if "recommendation_undo_stack" not in st.session_state:
    st.session_state.recommendation_undo_stack = []
if "recommendation_redo_stack" not in st.session_state:
    st.session_state.recommendation_redo_stack = []

qty_multiple = max(1, int(st.session_state.get("settings", {}).get("rounding_multiple", 1)))
section_title("Shipment plan", "Only the Approved shipment column is editable. Change values to reflect the actual manufacturing position or approved Sales adjustments.")
config = {
    "Month": st.column_config.TextColumn("Month", disabled=True, width="small"),
    "Customer demand": st.column_config.NumberColumn("Customer demand", disabled=True, format="localized"),
    "Existing shipment": st.column_config.NumberColumn("Existing shipment", disabled=True, format="localized"),
    "Pipeline before plan": st.column_config.NumberColumn("Pipeline before plan", disabled=True, format="localized"),
    "Suggested shipment": st.column_config.NumberColumn("Suggested shipment", disabled=True, format="localized"),
    "Approved shipment": st.column_config.NumberColumn("Approved shipment", min_value=0, step=qty_multiple, format="localized", help="Enter the quantity Sales wants to use for this month."),
}
editor_version = int(st.session_state.get("shipment_editor_version", 0))
editor_key = f"shipment_recommendations_editor_{editor_version}"
edited = st.data_editor(
    visible,
    key=editor_key,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config=config,
)

# Track edits as reversible operations. Only quantity values are added to the undo stack.
updated = draft.copy()
new_values = pd.to_numeric(edited["Approved shipment"], errors="coerce").fillna(0).clip(lower=0).round().astype(int).values
updated["Approved shipment"] = new_values
new_map = quantity_map(updated)
last_map = st.session_state.recommendation_last_editor_values
if new_map != last_map:
    st.session_state.recommendation_undo_stack.append(last_map.copy())
    st.session_state.recommendation_undo_stack = st.session_state.recommendation_undo_stack[-50:]
    st.session_state.recommendation_redo_stack = []
    st.session_state.recommendation_last_editor_values = new_map.copy()
    st.session_state.plan_status = "Draft edited"
    st.session_state.pop("last_export_path", None)
    st.session_state.pop("last_export_name", None)
st.session_state.draft_plan_df = updated
quantities = active_quantities_from_df(updated)
st.session_state.active_quantities = quantities

changed = updated["Approved shipment"].astype(float) != updated["Suggested shipment"].astype(float)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Months in plan", len(updated))
col2.metric("Suggested total", f"{int(updated['Suggested shipment'].sum()):,}")
col3.metric("Approved total", f"{sum(quantities.values()):,}")
col4.metric("Manually adjusted months", int(changed.sum()))

undo_col, redo_col, save_col, reset_col = st.columns([0.8, 0.8, 1.25, 1.25], gap="small")
with undo_col:
    if st.button("↶ Undo", disabled=not st.session_state.recommendation_undo_stack, use_container_width=True):
        previous = st.session_state.recommendation_undo_stack.pop()
        st.session_state.recommendation_redo_stack.append(quantity_map(updated))
        updated["Approved shipment"] = updated["Month"].map(previous).fillna(updated["Approved shipment"]).astype(int)
        st.session_state.draft_plan_df = updated
        st.session_state.active_quantities = active_quantities_from_df(updated)
        st.session_state.recommendation_last_editor_values = previous.copy()
        st.session_state.plan_status = "Draft edited · undo applied"
        st.session_state.shipment_editor_version = int(st.session_state.get("shipment_editor_version", 0)) + 1
        st.rerun()
with redo_col:
    if st.button("↷ Redo", disabled=not st.session_state.recommendation_redo_stack, use_container_width=True):
        next_values = st.session_state.recommendation_redo_stack.pop()
        st.session_state.recommendation_undo_stack.append(quantity_map(updated))
        updated["Approved shipment"] = updated["Month"].map(next_values).fillna(updated["Approved shipment"]).astype(int)
        st.session_state.draft_plan_df = updated
        st.session_state.active_quantities = active_quantities_from_df(updated)
        st.session_state.recommendation_last_editor_values = next_values.copy()
        st.session_state.plan_status = "Draft edited · redo applied"
        st.session_state.shipment_editor_version = int(st.session_state.get("shipment_editor_version", 0)) + 1
        st.rerun()
with save_col:
    if st.button("Save working edits", type="primary", use_container_width=True):
        st.session_state.active_quantities = quantities
        st.session_state.plan_status = "Draft edited"
        st.success("Edits are saved to the current working plan. Use Plan Revisions to save a permanent revision.")
with reset_col:
    if st.button("Reset to suggestions", use_container_width=True):
        st.session_state.recommendation_undo_stack.append(quantity_map(updated))
        updated["Approved shipment"] = updated["Suggested shipment"].astype(int)
        st.session_state.draft_plan_df = updated
        st.session_state.active_quantities = active_quantities_from_df(updated)
        st.session_state.recommendation_last_editor_values = quantity_map(updated)
        st.session_state.recommendation_redo_stack = []
        st.session_state.plan_status = "Draft reset to suggestions"
        st.session_state.shipment_editor_version = int(st.session_state.get("shipment_editor_version", 0)) + 1
        st.rerun()

with st.expander("How recommendations are calculated"):
    st.markdown(
        "The provisional engine compares projected demand over the configured transit and target-coverage horizon against current stock in pipeline, then rounds the gap to the configured multiple. The approved quantity is editable. This rule is a placeholder to support application testing; Sales must confirm the actual container and multiplier policy before production use."
    )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.page_link("pages/6_Stock_Preview_Editor.py", label="Preview the impact on the Stock Statement", icon=":material/table_chart:")
st.page_link("pages/5_Plan_Revisions.py", label="Save this as a dated revision", icon=":material/event_repeat:")
