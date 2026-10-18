from __future__ import annotations

import streamlit as st

from src.configuration import ensure_directories, load_settings
from src.history import init_db
from src.ui import apply_theme

st.set_page_config(
    page_title="Stock Planning Studio",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)
ensure_directories()
init_db()
apply_theme()

if "settings" not in st.session_state:
    st.session_state.settings = load_settings()
for key, default in {
    "stock_file_path": None,
    "edi_file_path": None,
    "maniana_file_path": None,
    "sap_file_path": None,
    "selected_sheet": None,
    "selected_section_id": None,
    "planning_month": None,
    "draft_plan_df": None,
    "active_quantities": {},
    "active_demand_overrides": {},
    "demand_source": "Stock Statement demand row",
    "maniana_mapping": None,
    "plan_status": "Not generated",
    "plan_revision_label": "Initial draft",
    "source_workbook_name": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

with st.sidebar:
    st.markdown(
        """
        <div style="padding:8px 4px 18px 4px;">
          <div style="display:flex;align-items:center;gap:11px;">
            <div style="background:linear-gradient(145deg,#2B7790,#173C5A);width:43px;height:43px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;box-shadow:0 5px 12px #071b2c55;">🏭</div>
            <div>
              <div style="font-family:Manrope,sans-serif;font-size:17px;font-weight:800;color:#FFFFFF;line-height:1.1;">Stock Planning</div>
              <div style="font-family:Manrope,sans-serif;font-size:17px;font-weight:800;color:#8BC8DC;line-height:1.1;">Studio</div>
            </div>
          </div>
          <div style="color:#AFC4D4;font-size:11px;letter-spacing:.13em;text-transform:uppercase;margin:14px 0 0 2px;">Sales Operations Workspace</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

pages = {
    "Workspace": [
        st.Page("pages/1_Dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page("pages/2_Upload_Validate.py", title="Upload & Validation", icon=":material/cloud_upload:"),
        st.Page("pages/3_Generate_Plan.py", title="Generate Stock Plan", icon=":material/calculate:"),
        st.Page("pages/4_Shipment_Recommendations.py", title="Shipment Recommendations", icon=":material/playlist_add_check:"),
        st.Page("pages/5_Plan_Revisions.py", title="Plan Revisions", icon=":material/event_repeat:"),
        st.Page("pages/6_Stock_Preview_Editor.py", title="Stock Preview & Editor", icon=":material/table_chart:"),
    ],
    "Control & Reporting": [
        st.Page("pages/7_Version_History.py", title="Version History", icon=":material/history:"),
        st.Page("pages/8_Reports_Export.py", title="Reports & Export", icon=":material/file_download:"),
        st.Page("pages/9_Planning_Settings.py", title="Planning Rules & Settings", icon=":material/tune:"),
    ],
    "Roadmap": [
        st.Page("pages/10_MANIANA_Generator.py", title="MANIANA Generator · Phase 2", icon=":material/auto_awesome:"),
    ],
}

pg = st.navigation(pages, position="sidebar", expanded=True)
with st.sidebar:
    st.divider()
    status = "Workbook loaded" if st.session_state.get("stock_file_path") else "Awaiting stock workbook"
    dot = "🟢" if st.session_state.get("stock_file_path") else "⚪"
    st.markdown(f"**{dot} Workspace status**")
    st.caption(status)
    st.caption("MVP · Local workspace")
    st.divider()
    st.markdown("<div style='font-size:11px;color:#AFC4D4;line-height:1.5;'>Planning recommendations are drafts. Sales approval is required before export.</div>", unsafe_allow_html=True)

pg.run()
