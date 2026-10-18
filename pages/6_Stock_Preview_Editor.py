from pathlib import Path

import streamlit as st

from src.ui import page_header, section_title
from src.workbook import inspect_stock_workbook, get_section
from src.planning import create_scenario_preview

page_header(
    "See the stock impact before you export.",
    "Preview the seven familiar stock rows across the planning horizon using the active shipment quantities. The source workbook remains unchanged.",
    "STOCK STATEMENT PREVIEW",
)
path = st.session_state.get("stock_file_path")
sheet = st.session_state.get("selected_sheet")
section_id = st.session_state.get("selected_section_id")
month = st.session_state.get("planning_month")
quantities = st.session_state.get("active_quantities", {}) or {}
if not path or not Path(path).exists():
    st.warning("Upload a Stock Statement workbook first.")
    st.page_link("pages/2_Upload_Validate.py", label="Go to Upload & Validation", icon=":material/cloud_upload:")
    st.stop()
if not sheet or not section_id or not month:
    st.info("Generate a draft plan first so the preview has a worksheet, part section and start month.")
    st.page_link("pages/3_Generate_Plan.py", label="Generate a stock plan", icon=":material/calculate:")
    st.stop()
try:
    section = get_section(path, sheet, section_id)
    preview = create_scenario_preview(path, sheet, section, quantities, month,
                                      demand_overrides=st.session_state.get("active_demand_overrides", {}))
except Exception as exc:
    st.error(f"Could not create the preview: {exc}")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Part", section.part_number)
c2.metric("Planning start", month)
c3.metric("Shipment months adjusted", sum(1 for m in section.months if m.label in quantities))
section_title("Stock statement preview", f"{section.title} · worksheet: {sheet}")
st.dataframe(preview, use_container_width=True, hide_index=True, height=360)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
left, right = st.columns(2)
with left:
    st.markdown("<div class='info-card'><h3>Editable inputs</h3><p>Update shipment quantities on Shipment Recommendations. This preview then reflects those active quantities.</p></div>", unsafe_allow_html=True)
    st.page_link("pages/4_Shipment_Recommendations.py", label="Edit shipment quantities", icon=":material/edit:")
with right:
    st.markdown("<div class='info-card'><h3>Export-ready workbook</h3><p>The exported file retains source formulas and formatting. Excel is requested to recalculate formulas when the file is opened.</p></div>", unsafe_allow_html=True)
    st.page_link("pages/8_Reports_Export.py", label="Review and download Excel", icon=":material/file_download:")

st.caption(f"Demand source: {st.session_state.get('demand_source', 'Stock Statement demand row')}. Preview calculation note: simple arithmetic formulas are recalculated in-app using the active shipment and demand overrides. Unsupported legacy formulas use the source workbook's cached value in preview; the exported workbook requests a full recalculation in Excel.")
