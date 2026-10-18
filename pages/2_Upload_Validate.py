from datetime import datetime
from pathlib import Path
import re

import streamlit as st

from src.configuration import UPLOAD_DIR, ensure_directories
from src.ui import page_header, section_title
from src.workbook import inspect_stock_workbook

page_header(
    "Bring the planning inputs together.",
    "Upload the existing Stock Statement and optional supporting files. The original inputs are kept unchanged; edits are applied to a generated copy.",
    "INPUT MANAGEMENT",
)
ensure_directories()


def save_upload(uploaded, slot: str) -> str | None:
    if uploaded is None:
        return None
    safe_name = re.sub(r"[^A-Za-z0-9._ -]", "_", uploaded.name).strip().replace(" ", "_")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = UPLOAD_DIR / f"{stamp}_{safe_name}"
    path.write_bytes(uploaded.getvalue())
    st.session_state[f"{slot}_file_path"] = str(path)
    st.session_state[f"{slot}_original_name"] = uploaded.name
    if slot == "maniana":
        st.session_state.maniana_mapping = None
        st.session_state.active_demand_overrides = {}
        st.session_state.draft_plan_df = None
        st.session_state.active_quantities = {}
        st.session_state.plan_status = "MANIANA input changed · regenerate plan"
        st.session_state.demand_source = "Stock Statement demand row"
        st.session_state.pop("last_export_path", None)
        st.session_state.pop("last_export_name", None)
    return str(path)

section_title("Required input", "Start with the latest approved Stock Statement workbook.")
stock_upload = st.file_uploader("Stock Statement workbook (.xlsx)", type=["xlsx"], key="stock_upload_widget", help="Use the existing formatted stock statement workbook that Sales currently updates.")
if stock_upload is not None:
    if st.button("Use uploaded Stock Statement", type="primary", use_container_width=False):
        try:
            path = save_upload(stock_upload, "stock")
            metadata = inspect_stock_workbook(path)
            # Prefer the monthly sheet matching the uploaded workbook period, then the newest dated CAT sheet.
            period_match = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[ _-]?(\d{2})", stock_upload.name, re.I)
            exact = None
            if period_match:
                month_token = period_match.group(1).lower()
                year_token = period_match.group(2)
                exact = next((name for name in metadata["sheets"] if month_token in name.lower() and year_token in name), None)
            dated = []
            month_num = {"jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
            for name in metadata["sheets"]:
                match = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[ _-]?(\d{2})", name, re.I)
                if match and "cat" in name.lower():
                    dated.append((int(match.group(2)), month_num[match.group(1).lower()], name))
            newest = max(dated)[2] if dated else metadata["sheets"][0]
            st.session_state.selected_sheet = exact or newest
            st.session_state.selected_section_id = None
            st.session_state.draft_plan_df = None
            st.session_state.active_quantities = {}
            st.session_state.plan_status = "Not generated"
            st.success(f"Loaded {Path(path).name}. Found {len(metadata['sheets'])} worksheets.")
        except Exception as exc:
            st.error(f"Could not read this workbook: {exc}")

current = st.session_state.get("stock_file_path")
if current and Path(current).exists():
    try:
        info = inspect_stock_workbook(current, st.session_state.get("selected_sheet"))
        a, b, c = st.columns(3)
        a.metric("Active workbook", "Loaded")
        b.metric("Worksheets", len(info["sheets"]))
        c.metric("File size", f"{info['size_bytes'] / 1024 / 1024:.1f} MB")
        st.success(f"Active source: **{Path(current).name}**")
        selected_sheet = st.selectbox("Inspect worksheet", info["sheets"], index=info["sheets"].index(info["selected_sheet"]) if info["selected_sheet"] in info["sheets"] else 0)
        section_info = inspect_stock_workbook(current, selected_sheet)
        sections = section_info["sections"]
        st.caption(f"Detected {len(sections)} stock-plan sections in **{selected_sheet}**.")
        if sections:
            st.dataframe([{"Part number": s.part_number, "Section": s.title, "Shipment row": s.shipment_row, "Monthly columns": len(s.months)} for s in sections], use_container_width=True, hide_index=True)
        else:
            st.warning("No complete stock-plan sections were detected on this worksheet. Choose another sheet or review the source layout.")
        if st.button("Set worksheet as active", type="primary"):
            st.session_state.selected_sheet = selected_sheet
            st.session_state.selected_section_id = None
            st.session_state.draft_plan_df = None
            st.session_state.active_quantities = {}
            st.success(f"Active worksheet set to {selected_sheet}.")
    except Exception as exc:
        st.error(f"Workbook inspection failed: {exc}")
else:
    st.info("No active Stock Statement yet. Upload and select a workbook above.")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
section_title("Supporting inputs", "These are optional in the first release; Phase 1 uses the existing MANIANA and Stock Statement. EDI and SAP integration can be expanded later.")
col1, col2 = st.columns(2)
with col1:
    maniana = st.file_uploader("MANIANA workbook (optional)", type=["xlsx", "xlsm", "csv"], key="maniana_upload_widget")
    if maniana and st.button("Save MANIANA input"):
        st.success(f"Saved {Path(save_upload(maniana, 'maniana')).name}")
    edi = st.file_uploader("Customer EDI file (optional)", type=["csv", "txt", "xlsx"], key="edi_upload_widget")
    if edi and st.button("Save EDI input"):
        st.success(f"Saved {Path(save_upload(edi, 'edi')).name}")
with col2:
    sap = st.file_uploader("SAP actuals export (optional)", type=["xlsx", "xlsm", "csv"], key="sap_upload_widget")
    if sap and st.button("Save SAP actuals"):
        st.success(f"Saved {Path(save_upload(sap, 'sap')).name}")
    st.markdown("<div class='info-card'><h3>Data handling</h3><p>Uploads are saved to this app’s local <code>data/uploads</code> folder for the current workspace. Use only company-approved storage and deployment environments for production files.</p></div>", unsafe_allow_html=True)

# Guided mapper for an existing MANIANA workbook. Full MANIANA generation is a later phase.
maniana_path = st.session_state.get("maniana_file_path")
if maniana_path and Path(maniana_path).exists():
    from src.demand import detect_month_columns, list_source_sheets, printable_column, read_demand_frame
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    section_title("Map MANIANA demand to the Stock Statement", "Choose the source worksheet, part-number column, and monthly demand columns. Mapped demand populates the existing Forecasted consumption at CAT row for matching months.")
    try:
        source_sheets = list_source_sheets(maniana_path)
        previous = st.session_state.get("maniana_mapping") or {}
        prior_sheet = previous.get("sheet_name") if previous.get("source_path") == maniana_path else None
        sheet_default = source_sheets.index(prior_sheet) if prior_sheet in source_sheets else 0
        maniana_sheet = st.selectbox("MANIANA worksheet", source_sheets, index=sheet_default, key="maniana_map_sheet")
        prior_header = int(previous.get("header_row", 1)) if previous.get("source_path") == maniana_path else 1
        header_row = st.number_input("Header row number", min_value=1, max_value=50, value=prior_header, step=1, help="Use this if the worksheet has title rows above its column headings.")
        frame = read_demand_frame(maniana_path, maniana_sheet, int(header_row))
        if frame.empty or len(frame.columns) < 2:
            st.warning("This worksheet appears empty or has too few columns. Choose another worksheet or header row.")
        else:
            st.caption(f"Preview: {len(frame):,} data rows · {len(frame.columns)} columns")
            st.dataframe(frame.head(8), use_container_width=True, hide_index=True)
            month_columns = detect_month_columns(frame.columns)
            column_options = list(range(len(frame.columns)))
            col_labels = {i: printable_column(col, i) for i, col in enumerate(frame.columns)}
            def guess_index(tokens, default=0):
                for idx, col in enumerate(frame.columns):
                    if any(token in str(col).lower() for token in tokens):
                        return idx
                return min(default, len(frame.columns)-1)
            previous_part = int(previous.get("part_column_index", guess_index(["part", "item", "material", "component", "number"]))) if previous.get("source_path") == maniana_path else guess_index(["part", "item", "material", "component", "number"])
            part_index = st.selectbox("Part-number column", column_options, index=min(previous_part, len(column_options)-1), format_func=lambda i: col_labels[i], key="maniana_part_column")
            layout_options = ["Wide · months in columns", "Long · one row per part and month"]
            prior_layout = previous.get("layout", "wide") if previous.get("source_path") == maniana_path else "wide"
            layout_index = 1 if prior_layout == "long" else 0
            layout_label = st.radio("Demand layout", layout_options, index=layout_index, horizontal=True, key="maniana_layout")
            layout = "wide" if layout_label.startswith("Wide") else "long"
            proposed_mapping = None
            if layout == "wide":
                if not month_columns:
                    st.warning("No month/date column headings were detected. Set the correct header row or choose Long format if months are stored as row values.")
                else:
                    option_map = {item["option"]: item for item in month_columns}
                    options = list(option_map)
                    prior_indices = {int(x.get("index", -1)) for x in previous.get("month_columns", [])} if previous.get("source_path") == maniana_path else set()
                    defaults = [opt for opt, item in option_map.items() if item["index"] in prior_indices] or options
                    selected_month_options = st.multiselect("Monthly demand columns", options, default=defaults, help="Each selected column is converted to a month and mapped to the matching stock-sheet month.")
                    proposed_mapping = {
                        "source_path": maniana_path, "sheet_name": maniana_sheet, "header_row": int(header_row),
                        "layout": "wide", "part_column_index": int(part_index),
                        "month_columns": [{"label": option_map[o]["label"], "index": int(option_map[o]["index"])} for o in selected_month_options],
                    }
            else:
                prior_date = int(previous.get("date_column_index", guess_index(["month", "date", "period", "week"]))) if previous.get("source_path") == maniana_path else guess_index(["month", "date", "period", "week"])
                prior_qty = int(previous.get("quantity_column_index", guess_index(["demand", "quantity", "qty", "forecast", "requirement", "order"]))) if previous.get("source_path") == maniana_path else guess_index(["demand", "quantity", "qty", "forecast", "requirement", "order"])
                cols2, cols3 = st.columns(2)
                with cols2:
                    date_index = st.selectbox("Month/date column", column_options, index=min(prior_date, len(column_options)-1), format_func=lambda i: col_labels[i], key="maniana_date_column")
                with cols3:
                    quantity_options = [i for i in column_options if i != date_index]
                    quantity_index = st.selectbox("Demand quantity column", quantity_options, index=quantity_options.index(prior_qty) if prior_qty in quantity_options else min(guess_index(["demand", "quantity", "qty", "forecast", "requirement", "order"], 1), len(quantity_options)-1), format_func=lambda i: col_labels[i], key="maniana_quantity_column")
                proposed_mapping = {
                    "source_path": maniana_path, "sheet_name": maniana_sheet, "header_row": int(header_row),
                    "layout": "long", "part_column_index": int(part_index),
                    "date_column_index": int(date_index), "quantity_column_index": int(quantity_index),
                }
            if proposed_mapping is not None:
                if st.button("Save MANIANA demand mapping", type="primary", key="save_maniana_mapping"):
                    st.session_state.maniana_mapping = proposed_mapping
                    st.session_state.active_demand_overrides = {}
                    st.session_state.draft_plan_df = None
                    st.session_state.active_quantities = {}
                    st.session_state.plan_status = "MANIANA mapping changed · regenerate plan"
                    st.session_state.demand_source = "MANIANA mapping saved · regenerate plan"
                    st.session_state.pop("last_export_path", None)
                    st.session_state.pop("last_export_name", None)
                    st.success("MANIANA mapping saved. Generate a new plan to apply the mapped demand.")
            if previous and previous.get("source_path") == maniana_path:
                st.markdown("<div class='success-strip'><b>Mapping status:</b> a mapping is saved. Generate a stock plan to validate that the selected part number matches the MANIANA data.</div>", unsafe_allow_html=True)
    except Exception as exc:
        st.error(f"Could not inspect the MANIANA source: {exc}")

