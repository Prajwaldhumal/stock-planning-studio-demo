from datetime import datetime
from pathlib import Path
import re

import pandas as pd
import streamlit as st

from src.configuration import VERSION_DIR
from src.planning import active_quantities_from_df
from src.ui import page_header, section_title
from src.workbook import get_section, write_stock_output

page_header(
    "Validate the plan and export the workbook.",
    "Generate a copy of the original Stock Statement with the active shipment quantities written into the selected section. Formula cells and template formatting are retained.",
    "OUTPUT & REPORTING",
)
path = st.session_state.get("stock_file_path")
sheet = st.session_state.get("selected_sheet")
section_id = st.session_state.get("selected_section_id")
month = st.session_state.get("planning_month")
draft = st.session_state.get("draft_plan_df")
if not path or not Path(path).exists():
    st.warning("Upload a Stock Statement workbook before exporting.")
    st.page_link("pages/2_Upload_Validate.py", label="Go to Upload & Validation", icon=":material/cloud_upload:")
    st.stop()
if not sheet or not section_id or draft is None or not isinstance(draft, pd.DataFrame) or draft.empty:
    st.info("Generate and review a plan before export.")
    st.page_link("pages/3_Generate_Plan.py", label="Generate stock plan", icon=":material/calculate:")
    st.stop()

quantities = active_quantities_from_df(draft)
st.session_state.active_quantities = quantities
try:
    section = get_section(path, sheet, section_id)
except Exception as exc:
    st.error(f"Selected stock section is no longer available: {exc}")
    st.stop()

section_title("Export summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Output worksheet", sheet)
col2.metric("Part", section.part_number)
col3.metric("Months with active quantities", len(quantities))
col4.metric("Total shipment quantity", f"{sum(quantities.values()):,}")

changed_rows = draft[draft["Approved shipment"].astype(float) != draft["Suggested shipment"].astype(float)]
st.markdown(f"**Manual adjustments vs. suggestion:** {len(changed_rows)} month(s)")
if not changed_rows.empty:
    st.dataframe(changed_rows[["Month", "Suggested shipment", "Approved shipment"]], use_container_width=True, hide_index=True)
else:
    st.caption("No manual quantity changes from the generated suggestions.")

status = st.session_state.get("plan_status", "Draft generated")
if status.lower().startswith("approved"):
    st.markdown("<div class='success-strip'><b>Approval status:</b> this plan is marked approved in the workspace.</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='warning-strip'><b>Approval status:</b> {status}. Confirm business approval before using this workbook operationally.</div>", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
if st.button("Build final Stock Statement copy", type="primary", use_container_width=True):
    try:
        safe_sheet = re.sub(r"[^A-Za-z0-9_-]+", "_", sheet)[:50]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name = f"Stock_Statement_{safe_sheet}_{stamp}.xlsx"
        out_path = VERSION_DIR / out_name
        write_stock_output(path, sheet, section, quantities, out_path,
                           demand_quantities=st.session_state.get("active_demand_overrides", {}))
        st.session_state.last_export_path = str(out_path)
        st.session_state.last_export_name = out_name
        st.success("Export created. Review the workbook before sending it to stakeholders.")
    except Exception as exc:
        st.error(f"Export failed: {exc}")

output_path = st.session_state.get("last_export_path")
if output_path and Path(output_path).exists():
    output_path = Path(output_path)
    st.download_button(
        "Download Stock Statement (.xlsx)",
        data=output_path.read_bytes(),
        file_name=output_path.name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
    st.caption(f"Generated file: {output_path.name} · {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    st.markdown("<div class='small-note'>The app writes approved shipment values into the existing shipment row for the months in the active plan. It does not add an extra revision row to the customer-facing workbook; revision history stays inside the application.</div>", unsafe_allow_html=True)
