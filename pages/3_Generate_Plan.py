from datetime import date, datetime
from pathlib import Path

import streamlit as st

from src.configuration import load_settings
from src.demand import extract_demand_by_part
from src.planning import create_recommendations
from src.ui import page_header, section_title
from src.workbook import inspect_stock_workbook

page_header(
    "Create a reviewable shipment plan.",
    "Choose the correct worksheet and part section, select the first planning month, then generate a provisional shipment plan for Sales to review.",
    "PLAN GENERATION",
)
path = st.session_state.get("stock_file_path")
if not path or not Path(path).exists():
    st.warning("Upload the current Stock Statement workbook first.")
    st.page_link("pages/2_Upload_Validate.py", label="Go to Upload & Validation", icon=":material/cloud_upload:")
    st.stop()

try:
    metadata = inspect_stock_workbook(path)
except Exception as exc:
    st.error(f"Could not inspect the Stock Statement: {exc}")
    st.stop()

sheet_names = metadata["sheets"]
current_sheet = st.session_state.get("selected_sheet")
sheet_index = sheet_names.index(current_sheet) if current_sheet in sheet_names else 0
sheet = st.selectbox("Stock Statement worksheet", sheet_names, index=sheet_index, key="generate_sheet_select")
section_meta = inspect_stock_workbook(path, sheet)
sections = section_meta["sections"]
if not sections:
    st.error("No complete stock-plan sections were detected on this worksheet. Select a different worksheet on this page or review the source workbook.")
    st.stop()

def section_label(s):
    return f"{s.part_number}  |  {s.title}  |  shipment row {s.shipment_row}"
selected_id = st.selectbox("Part / stock-plan section", [s.section_id for s in sections],
                           format_func=lambda value: section_label(next(s for s in sections if s.section_id == value)),
                           index=next((i for i, s in enumerate(sections) if s.section_id == st.session_state.get("selected_section_id")), 0))
section = next(s for s in sections if s.section_id == selected_id)
month_options = [m.label for m in section.months]
today = date.today()
def month_distance(label):
    m = next(x for x in section.months if x.label == label)
    return abs((m.period.year - today.year) * 12 + (m.period.month - today.month))
default_month = min(month_options, key=month_distance)
saved_month = st.session_state.get("planning_month")
month_index = month_options.index(saved_month) if saved_month in month_options else month_options.index(default_month)
planning_month = st.selectbox("Plan starts from month", month_options, index=month_index, help="Earlier months remain unchanged when the approved plan is exported.")
settings = st.session_state.get("settings", load_settings())

left, right = st.columns([1.1, 1], gap="large")
with left:
    section_title("Selected planning context")
    st.markdown(f"**Part:** {section.part_number}  \n**Section:** {section.title}  \n**Source worksheet:** {sheet}")
    st.caption(f"Detected {len(section.months)} month columns from {section.months[0].label} to {section.months[-1].label}.")
with right:
    section_title("Recommendation settings")
    m1, m2 = st.columns(2)
    m1.metric("Transit delay", f"{settings['transit_months']} months")
    m2.metric("Target coverage", f"{settings['target_coverage_months']} month(s)")
    st.caption(f"Rounding multiple: {settings['rounding_multiple']:,} parts")

st.markdown("<div class='warning-strip'><b>Draft recommendation:</b> the current engine uses projected demand, stock in pipeline, a configurable transit delay and target coverage. It is not yet the company-approved container × multiplier rule.</div>", unsafe_allow_html=True)

if st.session_state.get("maniana_file_path") and not st.session_state.get("maniana_mapping"):
    st.info("A MANIANA file is uploaded but not mapped yet. The current demand row in the Stock Statement will be used until a mapping is saved on Upload & Validation.")

if st.button("Generate draft shipment plan", type="primary", use_container_width=True):
    try:
        demand_overrides = {}
        demand_source = "Stock Statement demand row"
        maniana_path = st.session_state.get("maniana_file_path")
        mapping = st.session_state.get("maniana_mapping")
        if maniana_path and mapping:
            if mapping.get("source_path") != maniana_path:
                raise ValueError("The saved MANIANA mapping belongs to a different uploaded file. Re-save the mapping on Upload & Validation.")
            imported_demand, matched_rows = extract_demand_by_part(maniana_path, mapping, section.part_number)
            if matched_rows == 0:
                raise ValueError(f"No rows matched part {section.part_number} in the configured MANIANA part-number column. Check the mapping or source part-number convention.")
            start_idx = next((i for i, m in enumerate(section.months) if m.label == planning_month), 0)
            future_months = {m.label for m in section.months[start_idx:]}
            demand_overrides = {m: float(v) for m, v in imported_demand.items() if m in future_months}
            if not demand_overrides:
                raise ValueError("Matching part rows were found, but there are no mapped demand months overlapping the selected planning horizon. Check the header row and month columns.")
            demand_source = f"MANIANA · {Path(maniana_path).name} · {matched_rows} matching row(s)"
        draft = create_recommendations(path, sheet, section, planning_month, settings, horizon_months=18, demand_overrides=demand_overrides)
        st.session_state.selected_sheet = sheet
        st.session_state.selected_section_id = section.section_id
        st.session_state.planning_month = planning_month
        st.session_state.draft_plan_df = draft
        st.session_state.active_quantities = {str(row["Month"]): int(row["Approved shipment"]) for _, row in draft.iterrows()}
        st.session_state.active_demand_overrides = demand_overrides
        st.session_state.demand_source = demand_source
        st.session_state.plan_status = "Draft generated"
        st.session_state.plan_revision_label = "Initial draft"
        st.session_state.pop("last_export_path", None)
        st.session_state.pop("last_export_name", None)
        st.session_state.source_workbook_name = Path(path).name
        st.session_state.shipment_editor_version = int(st.session_state.get("shipment_editor_version", 0)) + 1
        st.session_state.pop("recommendation_last_editor_values", None)
        st.session_state.recommendation_undo_stack = []
        st.session_state.recommendation_redo_stack = []
        st.success(f"Generated a draft recommendation for {len(draft)} months. Review the quantities before approval.")
    except Exception as exc:
        st.error(f"Plan generation failed: {exc}")

if st.session_state.get("draft_plan_df") is not None:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    section_title("Draft overview")
    df = st.session_state.draft_plan_df
    c1, c2, c3 = st.columns(3)
    c1.metric("Plan horizon", f"{len(df)} months")
    c2.metric("Suggested parts", f"{int(df['Suggested shipment'].sum()):,}")
    c3.metric("Months with positive suggestion", int((df["Suggested shipment"] > 0).sum()))
    st.caption(f"Demand source: {st.session_state.get('demand_source', 'Stock Statement demand row')}")
    st.dataframe(df[["Month", "Customer demand", "Existing shipment", "Pipeline before plan", "Suggested shipment", "Approved shipment"]], use_container_width=True, hide_index=True)
    st.page_link("pages/4_Shipment_Recommendations.py", label="Review and edit recommendations", icon=":material/arrow_forward:")
