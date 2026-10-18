# Stock Planning Studio

A professional Streamlit MVP for Sales teams to review shipment recommendations, revise monthly quantities, preview stock impact, save revision history, and export the existing Stock Statement workbook.

## What is included

- **Dashboard** – overview of uploaded files, plan status, and workflow links.
- **Upload & Validation** – upload a Stock Statement workbook and optional MANIANA, EDI, or SAP input files; inspect worksheets and detected part sections. A guided mapper supports an existing MANIANA workbook in wide (months as columns) or long (one row per part/month) format.
- **Generate Stock Plan** – choose the worksheet, part section, and planning start month; generate an 18-month draft plan.
- **Shipment Recommendations** – edit the proposed shipment quantities and use undo/redo or reset-to-suggestions.
- **Plan Revisions** – save 1st-day, 7th-day, 25th-day, or ad hoc revisions with status and notes.
- **Stock Preview & Editor** – inspect the familiar shipment, arrivals, demand, stock, pipeline and inventory-coverage rows under the active scenario.
- **Version History** – list, compare and restore saved quantity snapshots.
- **Reports & Export** – write approved quantities into a copy of the original workbook and download it.
- **Planning Rules & Settings** – configure lead time, coverage target, and a provisional rounding multiple.
- **MANIANA Generator · Phase 2** – a roadmap page for future EDI-to-MANIANA automation.

## Run locally

### Windows

1. Extract this project ZIP into a working folder.
2. Double-click `run_windows.bat`, or open PowerShell in the project folder and run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   streamlit run app.py
   ```

3. Open the local URL printed in the terminal, usually `http://localhost:8501`.

### Linux / Ubuntu

```bash
chmod +x run_linux.sh
./run_linux.sh
```

The first run requires access to a Python package index to install dependencies. In a company environment, use the organization's approved package mirror and software installation process.

## First workflow

1. Open **Upload & Validation** and upload the current Stock Statement workbook (`.xlsx`).
2. Select the correct worksheet. If you have the current MANIANA workbook, upload it, choose the header row and map the part-number/month/demand columns. Mapped demand will feed the stock statement's `Forecasted consumption at CAT` row for matching future months.
3. Open **Generate Stock Plan**, choose the part/stock-plan section and planning start month, then generate a draft. If MANIANA is not mapped, the app uses demand values already present in the Stock Statement.
4. Open **Shipment Recommendations**. Inspect every proposed value; edit `Approved shipment` where needed. Undo, redo, or reset to suggestions as required.
5. Use **Stock Preview & Editor** to review the active scenario.
6. Use **Plan Revisions** to save an initial, 7th-day, 25th-day or ad hoc revision.
7. Open **Reports & Export** and generate/download the workbook copy.

## Important assumptions and limitations

### Recommendation engine is provisional

The current recommendation engine is deliberately transparent but generic. It estimates a shipment gap from projected demand over the configured transit/coverage horizon and rounds up to a configurable multiple. **It does not yet implement the actual Bharat Forge rule for parts-per-container multiplied by the sales-selected factor (e.g. 2, 3, or 4).** Sales must confirm the exact logic and any part-specific exceptions before this app is used for operational planning. Recommendations require human review and approval.

### Excel formula calculation

The exporter keeps formula cells and asks Excel-compatible software to recalculate on open. The in-app preview evaluates simple arithmetic formulas; unsupported legacy formulas use saved cached results. Verify a downloaded workbook in desktop Excel or the company's supported spreadsheet application before operational use.

### Template support

The first release updates the existing `Shipment ex-BFL (Nos)` row for the active plan months. Revision history is stored in the app rather than inserting a new customer-facing row, so the original stock-sheet layout stays as close as possible to the source template. Formatting, merged cells, and formulas are retained by the workbook writer, but templates containing advanced Excel objects should be validated during rollout.

### Data storage and company security

Uploaded inputs, revision history, and generated files are stored locally under `data/`. These files are not automatically uploaded to a remote service by the application. For real customer or manufacturing data, run it only in a company-approved environment and apply company retention/access policies. The initial database is SQLite, appropriate for a local pilot; use a managed database and authentication/authorization for multi-user production deployment.

### Phase 1 versus Phase 2

Phase 1 starts from an existing MANIANA workbook (when supplied and mapped) and generates a Stock Statement copy. The mapping is column-based and currently matches the MANIANA part-number column directly to the internal part number found in the Stock Statement section title. If the Sales process uses separate customer/internal part aliases, add and approve a cross-reference table before production use. Automatic EDI-to-MANIANA generation and direct SAP integration are not implemented yet; they remain Phase 2/3 enhancements.

## Project structure

```text
stock-planning-studio/
├── app.py
├── pages/                 # Streamlit pages
├── src/
│   ├── workbook.py        # Worksheet/section discovery, formula-aware preview, export
│   ├── planning.py        # Draft recommendation and scenario preview
│   ├── history.py         # SQLite revision snapshots
│   ├── configuration.py   # Persisted planning settings and data paths
│   └── ui.py              # Shared styles and helpers
├── config/planning_rules.json
├── data/uploads/          # Local inputs; excluded from source control
├── data/versions/         # Generated workbook copies; excluded from source control
├── tests/
└── requirements.txt
```

## Tests

After installing dependencies:

```bash
pytest -q
```

The tests use synthetic workbooks and do not contain company data.
