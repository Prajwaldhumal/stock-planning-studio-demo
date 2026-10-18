"""Guided import of an existing MANIANA-style demand workbook or CSV."""
from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

MONTH_FORMATS = (
    "%b-%y", "%B-%y", "%b %y", "%B %y", "%b %Y", "%B %Y",
    "%Y-%m", "%Y/%m", "%Y-%m-%d", "%Y/%m/%d", "%d-%b-%y",
    "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d",
)


def list_source_sheets(path: str | Path) -> list[str]:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return ["CSV"]
    return list(pd.ExcelFile(path, engine="openpyxl").sheet_names)


def read_demand_frame(path: str | Path, sheet_name: str = "CSV", header_row: int = 1) -> pd.DataFrame:
    path = Path(path)
    header = max(0, int(header_row) - 1)
    if path.suffix.lower() == ".csv":
        try:
            df = pd.read_csv(path, header=header, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(path, header=header, encoding="cp1252")
    else:
        df = pd.read_excel(path, sheet_name=sheet_name, header=header, engine="openpyxl")
    # Keep original column objects for date parsing, but make text headings easier to select.
    renamed = []
    for i, col in enumerate(df.columns):
        if isinstance(col, (datetime, date, pd.Timestamp)):
            renamed.append(pd.Timestamp(col).to_pydatetime())
        else:
            label = str(col).strip()
            renamed.append(label if label else f"Unnamed column {i + 1}")
    df.columns = renamed
    # Remove completely empty rows, but preserve non-empty rows even if some mapped fields are blank.
    return df.dropna(how="all").reset_index(drop=True)


def printable_column(column: Any, index: int) -> str:
    if isinstance(column, (datetime, date, pd.Timestamp)):
        label = pd.Timestamp(column).strftime("%b-%y")
    else:
        label = str(column)
    return f"{label} · column {index + 1}"


def parse_month(value: Any) -> str | None:
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return pd.Timestamp(value).strftime("%b-%y")
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    # Handle Excel EDI-style YYYYMMDD values and common month headers.
    compact = re.sub(r"\.0$", "", text)
    candidates = [compact, compact.replace("_", "-")]
    for candidate in candidates:
        for fmt in MONTH_FORMATS:
            try:
                return datetime.strptime(candidate, fmt).strftime("%b-%y")
            except ValueError:
                continue
    # Handle headings like "Forecast Oct-26" or "Demand for 2026-10".
    match = re.search(r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s_-]+(\d{2,4})", text, re.I)
    if match:
        yr = int(match.group(2))
        if yr < 100:
            yr += 2000
        try:
            return datetime(yr, datetime.strptime(match.group(1)[:3].title(), "%b").month, 1).strftime("%b-%y")
        except ValueError:
            return None
    return None


def detect_month_columns(columns: list[Any] | pd.Index) -> list[dict[str, Any]]:
    result = []
    for index, column in enumerate(columns):
        label = parse_month(column)
        if label:
            result.append({"label": label, "index": index, "option": printable_column(column, index)})
    return result


def normalise_part(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip().upper()
    text = re.sub(r"\.0$", "", text)
    return re.sub(r"[^A-Z0-9]", "", text)


def _number(value: Any) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "—", "N/A", "NA"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def extract_demand_by_part(path: str | Path, mapping: dict[str, Any], part_number: str) -> tuple[dict[str, float], int]:
    """Return monthly demand for a part using a saved wide- or long-format mapping.

    For wide data, selected month columns are summed over matching part rows.
    For long data, rows are grouped by parsed month and summed. Duplicate source rows
    are therefore transparent aggregates and should be checked when mapping is first set.
    """
    frame = read_demand_frame(path, mapping.get("sheet_name", "CSV"), int(mapping.get("header_row", 1)))
    part_index = int(mapping["part_column_index"])
    if part_index < 0 or part_index >= len(frame.columns):
        raise ValueError("The configured part-number column is no longer present. Reconfigure the MANIANA mapping.")
    part_values = frame.iloc[:, part_index].map(normalise_part)
    target = normalise_part(part_number)
    matched = frame.loc[part_values == target]
    if matched.empty:
        return {}, 0

    demand: dict[str, float] = {}
    layout = mapping.get("layout", "wide")
    if layout == "wide":
        month_columns = mapping.get("month_columns", [])
        for item in month_columns:
            label, index = item.get("label"), int(item.get("index", -1))
            if not label or index < 0 or index >= len(frame.columns):
                continue
            total = sum(_number(v) for v in matched.iloc[:, index].tolist())
            demand[label] = demand.get(label, 0.0) + total
    else:
        date_index = int(mapping["date_column_index"])
        quantity_index = int(mapping["quantity_column_index"])
        if max(date_index, quantity_index) >= len(frame.columns):
            raise ValueError("The configured date or demand column is no longer present. Reconfigure the MANIANA mapping.")
        for _, row in matched.iterrows():
            label = parse_month(row.iloc[date_index])
            if label:
                demand[label] = demand.get(label, 0.0) + _number(row.iloc[quantity_index])
    return {month: max(0.0, qty) for month, qty in demand.items()}, len(matched)
