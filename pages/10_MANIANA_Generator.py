import streamlit as st

from src.ui import page_header, section_title

page_header(
    "MANIANA generation is planned for Phase 2.",
    "The first release focuses on reliable MANIANA-to-Stock Statement conversion. This page reserves a clear home for full demand intake once the first workflow is validated.",
    "PHASE 2 ROADMAP",
)
st.markdown("<div class='info-card'><div class='section-kicker'>FUTURE CAPABILITY</div><h3>Generate MANIANA from customer source files</h3><p>Phase 2 will standardize customer EDI and other order schedules, apply part-number mappings, consolidate demand by month and create a reviewable MANIANA workbook.</p></div>", unsafe_allow_html=True)
section_title("Planned functions")
for item in [
    "Import customer EDI/Excel demand files and recognize different layouts.",
    "Map customer part numbers to Bharat Forge part numbers.",
    "Separate firm orders from forecast demand and aggregate demand by month.",
    "Flag duplicate releases, unmapped parts, cancelled lines and unusual quantities.",
    "Preview and approve MANIANA before it feeds the Stock Statement generator.",
]:
    st.markdown(f"- {item}")
st.info("This page is intentionally a roadmap placeholder; it does not yet generate a MANIANA workbook.")
