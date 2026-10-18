# Stock Planning Studio


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
