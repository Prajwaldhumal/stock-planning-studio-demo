import streamlit as st

from src.configuration import load_settings, save_settings
from src.ui import page_header, section_title

page_header(
    "Configure the rules behind each recommendation.",
    "Keep planning parameters visible and controlled. Changes here affect future draft recommendations, not existing saved revisions.",
    "PLANNING CONFIGURATION",
)
settings = st.session_state.get("settings", load_settings())
section_title("Shipment planning parameters", "The default values are placeholders for the MVP. Confirm operational values with Sales before using recommendations for real shipment decisions.")
with st.form("planning_settings_form"):
    transit = st.number_input("Shipment transit delay (months)", min_value=0, max_value=12, value=int(settings.get("transit_months", 2)), help="Your current description indicates around two months from shipment to warehouse/customer-side arrival.")
    coverage = st.number_input("Target pipeline coverage after lead time (months)", min_value=1, max_value=12, value=int(settings.get("target_coverage_months", 1)), help="The draft engine uses this as a buffer target. Confirm the proper level with Sales.")
    multiple = st.number_input("Rounding multiple in parts", min_value=1, max_value=1000000, value=int(settings.get("rounding_multiple", 1)), help="Set to the relevant parts-per-container multiple when the rule is confirmed. Default 1 means no rounding assumption.")
    method = st.selectbox("Recommendation method", ["Coverage-based draft"], index=0, help="Company-specific container × multiplier recommendations will replace this draft method after rules are confirmed.")
    show_detail = st.checkbox("Show calculation explanation in recommendations", value=bool(settings.get("show_calculation_details", True)))
    save = st.form_submit_button("Save planning rules", type="primary", use_container_width=True)
    if save:
        updated = {
            "transit_months": int(transit),
            "target_coverage_months": int(coverage),
            "rounding_multiple": int(multiple),
            "recommendation_method": method,
            "show_calculation_details": bool(show_detail),
        }
        save_settings(updated)
        st.session_state.settings = updated
        st.success("Planning settings saved. Generate a new draft to apply these values.")

section_title("Rules to confirm with Sales")
for title, description in [
    ("Container quantity", "Parts per container for each part number and whether that value varies by die or customer."),
    ("Shipment multiplier selection", "How the team chooses 2, 3, 4 or another multiplier on the 1st of the month."),
    ("7th-day update", "Which SAP/manufacturing fields determine the new quantity, and whether partial containers are allowed."),
    ("25th-day revision", "Whether the revision replans only the remaining months or also replaces earlier forecast cells."),
    ("Stock buffer", "Minimum desired inventory level, negative-stock handling, and any customer-specific limits."),
]:
    with st.expander(title):
        st.write(description)

st.markdown("<div class='warning-strip'><b>Governance:</b> settings can change the draft recommendation engine. Keep an owner and effective date for company-approved rules before production rollout.</div>", unsafe_allow_html=True)
