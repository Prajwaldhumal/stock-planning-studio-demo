"""Shared presentation helpers and design system."""
from __future__ import annotations

import streamlit as st

NAVY = "#12304A"
BLUE = "#2563EB"
TEAL = "#0F766E"


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
        :root { --navy:#12304A; --blue:#2563EB; --teal:#0F766E; --ink:#172B3A; --muted:#647789; --line:#E3EAF0; }
        html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
        h1,h2,h3,h4 { font-family:'Manrope','DM Sans',sans-serif !important; letter-spacing:-.025em; }
        .stApp { background:linear-gradient(180deg,#F7FAFC 0%,#F3F7FA 65%,#F8FAFC 100%); color:var(--ink); }
        [data-testid="stHeader"] { background:rgba(247,250,252,.88); }
        [data-testid="stSidebar"] { background:#102B43; border-right:1px solid rgba(255,255,255,.08); }
        [data-testid="stSidebar"] * { color:#E6EEF5; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#BCCBD8; }
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] { border-radius:10px; padding:9px 12px; }
        [data-testid="stSidebar"] [aria-current="page"] { background:rgba(80,150,224,.22); }
        [data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.13); }
        .block-container { padding-top:1.5rem; padding-bottom:3rem; max-width:1500px; }
        [data-testid="stMetric"] { background:#FFFFFF; padding:15px 17px; border:1px solid var(--line); border-radius:14px; box-shadow:0 3px 12px rgba(20,45,70,.035); }
        [data-testid="stMetricLabel"] { color:#617487; font-weight:600; }
        [data-testid="stMetricValue"] { color:var(--navy); font-family:'Manrope',sans-serif; }
        div.stButton > button, div.stDownloadButton > button { border-radius:10px; min-height:42px; font-weight:700; border:1px solid #D8E1E9; transition:all .15s ease; }
        div.stButton > button[kind="primary"], div.stDownloadButton > button[kind="primary"] { background:var(--navy); border-color:var(--navy); color:white; }
        div.stButton > button:hover, div.stDownloadButton > button:hover { transform:translateY(-1px); border-color:#8CA8BE; }
        div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff; }
        div[data-testid="stExpander"] { background:#fff; border:1px solid var(--line); border-radius:12px; }
        div[data-testid="stFileUploader"] { background:#fff; border:1px dashed #B9C9D7; padding:12px; border-radius:14px; }
        .hero { background:linear-gradient(115deg,#112F49 0%,#1D4D6E 62%,#247B85 100%); border-radius:20px; padding:27px 30px; color:white; margin:4px 0 22px 0; box-shadow:0 12px 28px rgba(18,48,74,.13); }
        .hero h1 { color:#fff !important; font-size:2rem; margin:0 0 8px 0; }
        .hero p { color:#DAE8F2; margin:0; font-size:1rem; max-width:850px; }
        .eyebrow { text-transform:uppercase; font-weight:800; letter-spacing:.12em; font-size:.70rem; color:#9FC8DC; margin-bottom:8px; }
        .section-kicker { color:#6D8294; text-transform:uppercase; letter-spacing:.11em; font-size:.70rem; font-weight:800; margin:0 0 6px 0; }
        .info-card { background:#fff; border:1px solid var(--line); border-radius:15px; padding:18px 19px; height:100%; box-shadow:0 3px 10px rgba(30,56,78,.025); }
        .info-card h3 { color:var(--navy); font-size:1.02rem; margin:2px 0 7px 0; }
        .info-card p { color:#647789; font-size:.91rem; line-height:1.5; margin:0; }
        .status-pill { display:inline-block; border-radius:999px; padding:4px 9px; font-size:.72rem; font-weight:800; background:#E9F5F2; color:#14665A; }
        .warning-strip { background:#FFF8E7; border:1px solid #F4D78D; color:#7A5A15; padding:12px 15px; border-radius:11px; }
        .success-strip { background:#EAF7F2; border:1px solid #BDE7D6; color:#17664F; padding:12px 15px; border-radius:11px; }
        .muted { color:#65798B; font-size:.88rem; }
        .small-note { color:#718395; font-size:.78rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str = "STOCK PLANNING STUDIO") -> None:
    st.markdown(
        f"""<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{subtitle}</p></div>""",
        unsafe_allow_html=True,
    )


def section_title(title: str, helper: str | None = None) -> None:
    st.markdown(f"### {title}")
    if helper:
        st.caption(helper)


def require_stock_file() -> str | None:
    path = st.session_state.get("stock_file_path")
    if path:
        from pathlib import Path
        if Path(path).exists():
            return str(path)
    st.markdown(
        '<div class="warning-strip"><b>No Stock Statement selected.</b> Open <b>Upload & Data Validation</b> to add your stock workbook first.</div>',
        unsafe_allow_html=True,
    )
    return None
