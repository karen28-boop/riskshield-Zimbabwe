# -----------------------------
# RISKSHIELD ZIMBABWE - COMPLETE INSURANCE MANAGEMENT SYSTEM
# National University of Science and Technology
# -----------------------------

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime, timedelta, date
import io
import random
import json
import os
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
import base64

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="RiskShield Zimbabwe - Insurance Management System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== LOGO ====================

def get_logo_svg():
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100" height="100">
      <defs>
        <linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#006400;stop-opacity:1"/>
          <stop offset="50%" style="stop-color:#228B22;stop-opacity:1"/>
          <stop offset="100%" style="stop-color:#FFD700;stop-opacity:1"/>
        </linearGradient>
      </defs>
      <path d="M100 10 L175 45 L175 110 Q175 165 100 190 Q25 165 25 110 L25 45 Z"
            fill="url(#sg)" stroke="#FFD700" stroke-width="3"/>
      <path d="M100 28 L158 57 L158 108 Q158 152 100 172 Q42 152 42 108 L42 57 Z"
            fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="2"/>
      <text x="100" y="115" font-family="Georgia,serif" font-size="72" font-weight="bold"
            fill="white" text-anchor="middle" dominant-baseline="middle">R</text>
      <polygon points="100,22 103,32 113,32 105,38 108,48 100,42 92,48 95,38 87,32 97,32"
               fill="#FFD700" opacity="0.95"/>
      <text x="100" y="183" font-family="Arial,sans-serif" font-size="9" font-weight="bold"
            fill="#FFD700" text-anchor="middle" letter-spacing="2">ZIMBABWE</text>
    </svg>
    """
    return svg

# ==================== CURRENCY HISTORY ====================

def get_complete_currency_history():
    return pd.DataFrame({
        'Period': [
            '2009-2014', '2014-2016', '2016-2018', '2018-2019',
            '2019-2020', '2020-2022', '2022-2023', '2023-2024',
            '2024-2025', '2025-2026'
        ],
        'Currency': [
            'Multi-Currency (USD, ZAR, BWP)', 'Bond Notes (1:1 USD)',
            'Bond Notes (Devalued)', 'RTGS Dollar',
            'RTGS (Hyperinflation)', 'ZWL (New Dollar)',
            'ZWL (Crisis)', 'ZWL (Last Days)',
            'ZiG (Zimbabwe Gold)', 'ZiG (Stabilized)'
        ],
        'Official_Rate_USD': [1.00, 1.00, 2.50, 15.00, 80.00, 200.00, 1500.00, 8000.00, 13500.00, 26.90],
        'Parallel_Rate_USD': [1.00, 1.20, 3.50, 25.00, 150.00, 400.00, 3000.00, 15000.00, 25000.00, 33.50],
        'Inflation_Rate':    [5.0, 2.5, 50.0, 150.0, 500.0, 350.0, 800.0, 600.0, 150.0, 8.5],
        'Key_Event': [
            'Dollarization after hyperinflation',
            'Bond notes introduced as surrogate currency',
            'Bond notes lose value, shortages begin',
            'RTGS electronic currency introduced',
            'RTGS hyperinflation starts',
            'ZWL reintroduced, initial stability',
            'ZWL hyperinflation crisis',
            'Currency chaos, parallel market dominates',
            'ZiG introduced, backed by gold',
            'Single digit inflation achieved'
        ]
    })

# ==================== RBZ DATA ====================

def fetch_rbz_data():
    zig_launch = datetime(2024, 4, 5)
    days_stable = (datetime.now() - zig_launch).days
    return {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'inflation_rate': 8.5,
        'official_rate': 26.90,
        'parallel_rate': 33.50,
        'rbz_policy_rate': 35.0,
        'gold_reserves_usd': 380_000_000,
        'currency': 'ZiG',
        'money_supply_growth': 12.5,
        'forex_reserves_days': 45,
        'source': 'Reserve Bank of Zimbabwe',
        'days_of_stability': days_stable,
        'parallel_premium': round(((33.50 / 26.90) - 1) * 100, 1)
    }

def fetch_historical_rbz_data():
    dates = pd.date_range(start='2024-04-01', periods=24, freq='ME')
    inflation, official = [], []
    for i in range(24):
        if i < 3:
            inflation.append(25.0 - i * 5)
            official.append(20.0 + i * 1000)
        elif i < 6:
            inflation.append(15.0 - (i - 3) * 2)
            official.append(5000 + (i - 3) * 1500)
        elif i < 9:
            inflation.append(12.0 - (i - 6) * 1)
            official.append(9500 + (i - 6) * 800)
        elif i < 12:
            inflation.append(10.0 - (i - 9) * 0.5)
            official.append(12000 + (i - 9) * 500)
        else:
            inflation.append(max(8.5, 9.0 - (i - 12) * 0.04))
            official.append(24.0 + (i - 12) * 0.3)
    parallel = [x * 1.245 for x in official]
    currency = ['ZiG' if i >= 12 else 'ZWL' for i in range(24)]
    return pd.DataFrame({
        'Date': dates,
        'Inflation_Rate': [max(5.0, min(30.0, x)) for x in inflation],
        'Official_Rate': [max(20.0, min(30.0, x)) if i >= 12 else x for i, x in enumerate(official)],
        'Parallel_Rate': parallel,
        'Currency': currency
    })

# ==================== PERSISTENT DATABASE ====================
# All data is saved to riskshield_data.json on disk immediately after every change.
# This means data added by Karen is visible when Kudakwashe opens the app,
# and restarts/refreshes never wipe the stored records.
# The only way to remove a record is to click the Delete button.

DB_FILE = "riskshield_data.json"

_ASSET_COLS = [
    'Client_ID', 'Asset_ID', 'Asset_Type', 'Asset_Description', 'Asset_Value',
    'Asset_Value_USD', 'Purchase_Date', 'Condition', 'Insurance_Status',
    'Policy_Number', 'Inflation_Adjustment', 'Last_Valuation_Date',
    'Premium', 'Premium_USD', 'Policy_Term_Months', 'Inception_Date',
    'Lapsing_Rate', 'Currency_At_Inception', 'RBZ_Class',
    'Original_Currency', 'Original_Amount', 'Conversion_History',
]
_CLAIM_COLS = [
    'Claim_ID', 'Client_ID', 'Asset_ID', 'Claim_Date', 'Claim_Amount',
    'Claim_Amount_USD', 'Claim_Type', 'Severity_Level', 'Inflation_Impact',
    'Settlement_Amount', 'Settlement_Amount_USD', 'Status', 'Processed_By',
    'Trust_Score_Impact', 'Days_To_Settle', 'Currency_At_Claim',
]
_PAY_COLS = [
    'Date', 'Client_ID', 'Asset_ID', 'Payment_Amount', 'Payment_Amount_USD',
    'Payment_Method', 'Status', 'Notes', 'Processed_By', 'Payment_Currency',
    'Exchange_Rate_Used',
]


def _df_to_records(df):
    records = []
    for rec in df.to_dict(orient="records"):
        clean = {}
        for k, v in rec.items():
            if isinstance(v, (pd.Timestamp, datetime)):
                clean[k] = str(v)
            elif isinstance(v, date):
                clean[k] = str(v)
            elif hasattr(v, "item"):
                clean[k] = v.item()
            elif v is None or (isinstance(v, float) and np.isnan(v)):
                clean[k] = None
            else:
                clean[k] = v
        records.append(clean)
    return records


def save_database():
    payload = {
        "clients":          st.session_state.clients,
        "assets":           _df_to_records(st.session_state.assets),
        "claims":           _df_to_records(st.session_state.claims),
        "payments":         _df_to_records(st.session_state.payments),
        "capital_reserves": st.session_state.capital_reserves,
        "last_saved":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(DB_FILE, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    st.session_state.db_last_saved = payload["last_saved"]


def load_database():
    defaults = {
        "clients": {},
        "assets": [],
        "claims": [],
        "payments": [],
        "capital_reserves": {
            "required_capital": 0,
            "available_capital": 50_000_000,
            "solvency_ratio": 0,
            "last_calculated": datetime.now().strftime("%Y-%m-%d"),
        },
        "last_saved": None,
    }
    if not os.path.exists(DB_FILE):
        return defaults
    try:
        with open(DB_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for key, val in defaults.items():
            if key not in data:
                data[key] = val
        return data
    except Exception:
        return defaults


def _rebuild_df(records, columns):
    if not records:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(records)
    for col in columns:
        if col not in df.columns:
            df[col] = None
    return df[columns]


# ==================== SESSION STATE INIT ====================
# db_loaded flag ensures we only read the file once per browser session.
# After that, every write immediately calls save_database() so the file stays current.

if "db_loaded" not in st.session_state:
    _db = load_database()
    st.session_state.clients          = _db["clients"]
    st.session_state.assets           = _rebuild_df(_db["assets"],   _ASSET_COLS)
    st.session_state.claims           = _rebuild_df(_db["claims"],   _CLAIM_COLS)
    st.session_state.payments         = _rebuild_df(_db["payments"], _PAY_COLS)
    st.session_state.capital_reserves = _db["capital_reserves"]
    st.session_state.db_last_saved    = _db.get("last_saved", "Never")
    st.session_state.db_loaded        = True

if 'currency_history' not in st.session_state:
    st.session_state.currency_history = get_complete_currency_history()
if 'rbz_current' not in st.session_state:
    st.session_state.rbz_current = fetch_rbz_data()
if 'rbz_historical' not in st.session_state:
    st.session_state.rbz_historical = fetch_historical_rbz_data()
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'profit_testing' not in st.session_state:
    st.session_state.profit_testing = pd.DataFrame()
if 'rbz_classes' not in st.session_state:
    st.session_state.rbz_classes = {
        'Class A - Low Risk':     {'capital_factor': 0.05, 'max_lapsing': 0.10, 'description': 'Government bonds, Cash'},
        'Class B - Moderate Risk':{'capital_factor': 0.10, 'max_lapsing': 0.15, 'description': 'Corporate bonds, Property'},
        'Class C - High Risk':    {'capital_factor': 0.20, 'max_lapsing': 0.25, 'description': 'Equities, Vehicles'},
        'Class D - Speculative':  {'capital_factor': 0.35, 'max_lapsing': 0.40, 'description': 'Cryptocurrency, Startups'},
    }

AUTHORS = [
    "Kwanai Karen",
    "Lackson Tsvangirayi",
    "Kudakwashe Muzanenhamo",
    "Godfrey Masasa",
    "Charlotte E Makuleke"
]

# ==================== AUTO-UPDATE ====================

def check_and_update_rbz_data():
    time_diff = datetime.now() - st.session_state.last_update
    if time_diff.total_seconds() > 3600:
        st.session_state.rbz_current = fetch_rbz_data()
        st.session_state.rbz_historical = fetch_historical_rbz_data()
        st.session_state.last_update = datetime.now()
        return True
    return False

data_updated = check_and_update_rbz_data()

# ==================== HELPER FUNCTIONS ====================

def get_current_rates():
    return {
        'inflation':    st.session_state.rbz_current['inflation_rate'],
        'official_rate':st.session_state.rbz_current['official_rate'],
        'parallel_rate':st.session_state.rbz_current['parallel_rate'],
        'currency':     st.session_state.rbz_current['currency'],
        'policy_rate':  st.session_state.rbz_current['rbz_policy_rate'],
        'last_updated': st.session_state.rbz_current['timestamp'],
        'source':       st.session_state.rbz_current['source'],
        'days_stable':  st.session_state.rbz_current['days_of_stability']
    }

def get_historical_rate_for_date(target_date):
    target = pd.Timestamp(target_date)
    if target < pd.Timestamp('2014-01-01'):   return 1.0,     'USD'
    elif target < pd.Timestamp('2016-01-01'): return 1.0,     'Bond'
    elif target < pd.Timestamp('2018-01-01'): return 2.5,     'Bond'
    elif target < pd.Timestamp('2019-01-01'): return 15.0,    'RTGS'
    elif target < pd.Timestamp('2020-01-01'): return 80.0,    'RTGS'
    elif target < pd.Timestamp('2022-01-01'): return 200.0,   'ZWL'
    elif target < pd.Timestamp('2023-01-01'): return 1500.0,  'ZWL'
    elif target < pd.Timestamp('2024-04-01'): return 8000.0,  'ZWL'
    elif target < pd.Timestamp('2025-01-01'): return 13500.0, 'ZiG'
    else:
        return st.session_state.rbz_current['official_rate'], 'ZiG'

def convert_historical_to_current(amount, from_date, from_currency):
    rate_at_date, _ = get_historical_rate_for_date(from_date)
    usd_value = amount / rate_at_date if rate_at_date != 0 else amount
    return usd_value * st.session_state.rbz_current['official_rate']

rates = get_current_rates()

# ==================== CUSTOM CSS ====================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Source+Sans+3:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }
    .main-header {
        background: linear-gradient(135deg, #004d00 0%, #006400 40%, #1a6b1a 70%, #c8a400 100%);
        padding: 2rem 2.5rem; border-radius: 1.2rem; margin-bottom: 1.5rem;
        text-align: center; color: white; box-shadow: 0 8px 32px rgba(0,100,0,0.35);
    }
    .main-header h1 {
        font-family: 'Playfair Display', serif; font-size: 2.8rem;
        margin: 0.3rem 0; text-shadow: 0 2px 8px rgba(0,0,0,0.3); letter-spacing: 1px;
    }
    .main-header p { font-size: 1.05rem; margin: 0.2rem 0; opacity: 0.92; font-weight: 300; }
    .rbz-banner {
        background: linear-gradient(90deg, #e8f5e9, #f1f8e9);
        border-left: 5px solid #2e7d32; padding: 0.85rem 1.2rem;
        border-radius: 0 0.5rem 0.5rem 0; margin-bottom: 1rem;
    }
    .history-timeline { background: #fafafa; padding: 1rem; border-radius: 0.75rem; border-left: 4px solid #9c27b0; }
    .current-era-box {
        background: linear-gradient(135deg, #e8f5e9, #f9fbe7);
        border: 2px solid #2e7d32; padding: 1rem; border-radius: 0.75rem; margin: 0.5rem 0;
    }
    .era-box { background: #f8f9fa; padding: 0.7rem 1rem; border-radius: 0.5rem; margin: 0.25rem 0; font-size: 0.9rem; }
    .authors-box {
        background: linear-gradient(135deg, #004d00, #006400);
        color: white; padding: 1.2rem; border-radius: 0.75rem; margin: 0.5rem 0;
    }
    .authors-box h4 { color: #FFD700; margin: 0 0 0.5rem 0; font-family: 'Playfair Display', serif; }
    .db-status-box {
        background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
        border-left: 4px solid #2e7d32; padding: 0.8rem 1rem;
        border-radius: 0 0.5rem 0.5rem 0; font-size: 0.82rem;
    }
    .deploy-box {
        background: linear-gradient(135deg, #e3f2fd, #e8eaf6);
        border: 1px solid #1565c0; padding: 1rem 1.2rem; border-radius: 0.75rem; margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 0.85rem; }
    .stTabs [aria-selected="true"] { color: #006400 !important; }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================

col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown(get_logo_svg(), unsafe_allow_html=True)
with col_title:
    st.markdown(
        "<div class='main-header'>"
        "<h1>RiskShield Zimbabwe</h1>"
        "<p>Complete Insurance Management System - Historical Currency Tracking 2009-2026</p>"
        "<p style='font-size:0.9rem; opacity:0.8;'>USD to Bond to RTGS to ZWL to ZiG | Auto-updating with RBZ Data | v7.1</p>"
        "</div>",
        unsafe_allow_html=True
    )

if data_updated:
    st.success("RBZ Data Auto-Updated: " + datetime.now().strftime('%H:%M:%S'))

st.markdown(
    "<div class='rbz-banner'>"
    "<strong>RESERVE BANK OF ZIMBABWE - CURRENT OFFICIAL RATES</strong> | "
    "Last Updated: " + rates['last_updated'] + " | Source: " + rates['source'] + "<br>"
    "<span style='font-size:0.88em;'>"
    "ZiG Era: <b>" + str(rates['days_stable']) + "</b> days of stability | "
    "Inflation: <b>" + str(rates['inflation']) + "%</b> (Single Digit) | "
    "1 USD = <b>" + str(rates['official_rate']) + " ZiG</b> (Official)"
    "</span></div>",
    unsafe_allow_html=True
)

# ==================== CURRENT INDICATORS ====================

st.subheader("Current RBZ Official Indicators")
col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns(5)
col_e1.metric("Inflation Rate",   f"{rates['inflation']:.1f}%",          delta="Single Digit")
col_e2.metric("USD/ZiG Official", f"{rates['official_rate']:.2f} ZiG",   delta="Stable")
col_e3.metric("Parallel Rate",    f"{rates['parallel_rate']:.2f} ZiG",
              delta=f"Spread: {((rates['parallel_rate']/rates['official_rate'])-1)*100:.1f}%")
col_e4.metric("RBZ Policy Rate",  f"{rates['policy_rate']:.1f}%",         delta="Easing")
col_e5.metric("Days of Stability",f"{rates['days_stable']:,}",            delta="Since ZiG launch")
st.info("Gold Reserves: $380 Million  |  Import Cover: 45 days  |  Money Supply Growth: 12.5%  |  Currency: ZiG (Zimbabwe Gold)")

# ==================== SIDEBAR ====================

with st.sidebar:
    st.markdown(get_logo_svg(), unsafe_allow_html=True)
    st.markdown("## RiskShield Zimbabwe")
    st.markdown("*Insurance Management System*")
    st.markdown("---")

    st.markdown(
        "<div class='authors-box'>"
        "<h4>Authors</h4>"
        "<ul style='margin:0; padding-left:1.2rem; font-size:0.88rem; line-height:1.8;'>"
        "<li>Kwanai Karen</li>"
        "<li>Lackson Tsvangirayi</li>"
        "<li>Kudakwashe Muzanenhamo</li>"
        "<li>Godfrey Masasa</li>"
        "<li>Charlotte E Makuleke</li>"
        "</ul>"
        "<p style='font-size:0.78rem; margin-top:0.5rem; opacity:0.8;'>"
        "BSc Hons Actuarial Science<br>NUST </p>"
        "</div>",
        unsafe_allow_html=True
    )

    current_user = st.selectbox("Active User", options=AUTHORS, index=0, key="user_select_sidebar")

    st.markdown("---")
    st.markdown("### RBZ Live Feed")
    st.markdown(f"**Updated:** {rates['last_updated']}")
    st.markdown(f"**Era:** ZiG (Day **{rates['days_stable']}**)")
    st.markdown(f"1 USD = **{rates['official_rate']:.2f} ZiG**")
    st.markdown(f"Inflation: **{rates['inflation']:.1f}%**")
    st.markdown(f"Policy Rate: **{rates['policy_rate']:.1f}%**")

    st.markdown("---")
    st.markdown("### Historical Converter")
    hist_amount = st.number_input("Amount", min_value=0.0, value=1000.0, step=100.0, key="hist_amount_sidebar")
    hist_date   = st.date_input("Date", value=date(2020, 1, 1), key="hist_date_sidebar")
    rate_h, curr_h = get_historical_rate_for_date(hist_date)
    current_val = convert_historical_to_current(hist_amount, hist_date, curr_h)
    st.info(
        f"**{hist_date}**\n\n"
        f"{hist_amount:,.0f} {curr_h} = **${hist_amount/rate_h:,.2f} USD**\n\n"
        f"**Today:** ZiG {current_val:,.2f}"
    )

    # Database status panel
    st.markdown("---")
    total_clients  = len(st.session_state.clients)
    total_policies = len(st.session_state.assets)
    last_saved     = st.session_state.get("db_last_saved", "Never")
    st.markdown(
        "<div class='db-status-box'>"
        "<b>Persistent Database</b><br>"
        "File: <code>riskshield_data.json</code><br>"
        f"Clients stored: <b>{total_clients}</b><br>"
        f"Policies stored: <b>{total_policies}</b><br>"
        f"Last saved: <b>{last_saved}</b><br>"
        "<span style='color:#2e7d32;'>Data survives restarts</span>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")
    col_rb1, col_rb2 = st.columns(2)
    if col_rb1.button("Refresh RBZ", key="sidebar_refresh_btn"):
        st.session_state.rbz_current   = fetch_rbz_data()
        st.session_state.rbz_historical = fetch_historical_rbz_data()
        st.session_state.last_update    = datetime.now()
        st.success("RBZ Data Refreshed!")
        st.rerun()
    if col_rb2.button("Save Now", key="sidebar_save_btn"):
        save_database()
        st.success("Saved!")

   
    

# ==================== CURRENCY HISTORY EXPANDER ====================

with st.expander("COMPLETE ZIMBABWE CURRENCY HISTORY (2009-2026)", expanded=False):
    st.markdown('<div class="history-timeline">', unsafe_allow_html=True)
    history_df = st.session_state.currency_history
    colors = ['#9e9e9e','#ff9800','#f44336','#e91e63','#e91e63','#e91e63','#e91e63','#ff9800','#4caf50','#2e7d32']
    for idx, row in history_df.iterrows():
        color      = colors[idx]
        is_current = (idx == len(history_df) - 1)
        if is_current:
            st.markdown(
                "<div class='current-era-box'>"
                f"<strong>CURRENT ERA: {row['Period']}</strong> - {row['Currency']}<br>"
                f"<span style='font-size:0.9em;'>Official: 1 USD = {row['Official_Rate_USD']:.2f} ZiG | "
                f"Parallel: 1 USD = {row['Parallel_Rate_USD']:.2f} ZiG | "
                f"Inflation: {row['Inflation_Rate']}%</span><br>"
                f"<em style='font-size:0.85em;'>{row['Key_Event']}</em>"
                "</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='era-box' style='border-left:4px solid {color};'>"
                f"<strong>{row['Period']}:</strong> {row['Currency']} | "
                f"1 USD = {row['Official_Rate_USD']:.0f} | "
                f"Inflation: {row['Inflation_Rate']}% | "
                f"<em>{row['Key_Event']}</em>"
                "</div>",
                unsafe_allow_html=True
            )
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== MAIN TABS ====================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "Clients", "Asset Insurance", "Payments",
    "Claims", "Inflation", "Trust Analytics",
    "Capital & Solvency", "Profit Testing", "Business Case"
])

# ==================== TAB 1: CLIENT MANAGEMENT ====================
with tab1:
    st.header("Client Management")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Register New Client")
        with st.form("client_reg_form"):
            client_type = st.selectbox("Client Type", ['Individual', 'Company', 'NGO', 'Government', 'SME'])
            name        = st.text_input("Full Name / Company Name *")
            reg_number  = st.text_input("ID / Registration Number *")
            col_a, col_b = st.columns(2)
            phone = col_a.text_input("Phone *", placeholder="+263 77 123 4567")
            email = col_b.text_input("Email")
            address          = st.text_area("Physical Address *")
            has_historical   = st.checkbox("Client has pre-ZiG era policies")
            preferred_curr   = st.selectbox("Preferred Currency", ['ZiG', 'USD'])
            income_level     = st.selectbox("Income Level (ZiG/month)",
                ['< 2,000', '2,000-5,000', '5,000-10,000', '10,000-50,000', '> 50,000'])
            submitted = st.form_submit_button("Register Client")
            if submitted:
                if name and reg_number and phone and address:
                    cid = f"CL-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
                    st.session_state.clients[cid] = {
                        'Client_ID': cid, 'Type': client_type, 'Name': name,
                        'Reg_Number': reg_number, 'Phone': phone, 'Email': email,
                        'Address': address, 'Preferred_Currency': preferred_curr,
                        'Income_Level': income_level,
                        'Registration_Date': datetime.now().strftime('%Y-%m-%d'),
                        'Registered_By': current_user,
                        'Has_Historical_Policies': has_historical,
                        'Trust_Score': 85, 'Status': 'Active'
                    }
                    save_database()
                    st.success(f"Client registered! ID: {cid}")
                    st.rerun()
                else:
                    st.error("Please fill all required fields (*)")

    with col2:
        st.subheader(f"Client List ({len(st.session_state.clients)} registered)")
        if st.session_state.clients:
            for cid, client in list(st.session_state.clients.items()):
                with st.expander(f"{client['Name']} - {client['Type']} ({cid})"):
                    st.write(f"**Phone:** {client['Phone']}  |  **Email:** {client.get('Email','—')}")
                    st.write(f"**Address:** {client['Address']}")
                    st.write(f"**Currency:** {client['Preferred_Currency']}  |  **Income:** {client['Income_Level']}")
                    st.write(f"**Trust Score:** {client.get('Trust_Score', 85)}%  |  **Status:** {client['Status']}")
                    st.write(f"**Registered:** {client['Registration_Date']} by {client['Registered_By']}")
                    if client.get('Has_Historical_Policies'):
                        st.warning("Has pre-ZiG historical policies")
                    if st.button(f"Delete {cid}", key=f"del_cl_{cid}"):
                        del st.session_state.clients[cid]
                        save_database()
                        st.success("Client deleted.")
                        st.rerun()
        else:
            st.info("No clients registered yet.")

# ==================== TAB 2: ASSET INSURANCE ====================
with tab2:
    st.header("Asset Insurance")
    if not st.session_state.clients:
        st.warning("Please register a client first (Clients tab).")
    else:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Issue New Policy")
            client_options    = {f"{cid} - {d['Name']}": cid for cid, d in st.session_state.clients.items()}
            sel_client_label  = st.selectbox("Select Client", list(client_options.keys()), key="asset_cl_sel")
            client_id         = client_options[sel_client_label]
            is_historical     = st.checkbox("Historical policy (pre-ZiG era)", key="hist_pol_chk")

            with st.form("asset_form"):
                asset_type  = st.selectbox("Asset Type",
                    ['Motor Vehicle', 'Building', 'Farm Equipment', 'Electronics', 'Livestock', 'Inventory'])
                description = st.text_input("Asset Description *")

                if is_historical:
                    st.markdown("##### Historical Policy Conversion")
                    hist_date_a = st.date_input("Original Policy Date", value=date(2020, 1, 1), key="hist_d_a")
                    hist_curr   = st.selectbox("Original Currency", ['ZWL', 'RTGS', 'Bond', 'USD'], key="hist_c_a")
                    hist_amt    = st.number_input(f"Original Amount ({hist_curr})", min_value=0.0,
                                                  value=100000.0, key="hist_a_a")
                    converted   = convert_historical_to_current(hist_amt, hist_date_a, hist_curr)
                    value_zig   = converted
                    value_usd   = value_zig / rates['official_rate']
                    st.info(
                        f"Original: {hist_amt:,.0f} {hist_curr} ({hist_date_a})\n\n"
                        f"Current ZiG: {value_zig:,.2f} ZiG\n\nUSD: ${value_usd:,.2f}"
                    )
                else:
                    value_zig = st.number_input("Asset Value (ZiG)", min_value=0.0,
                                                value=100000.0, step=10000.0, key="val_zig")
                    value_usd = value_zig / rates['official_rate']
                    st.caption(f"USD ${value_usd:,.2f} at official rate")

                col_t1, col_t2 = st.columns(2)
                purchase_date  = col_t1.date_input("Purchase Date", date.today() - timedelta(days=365))
                policy_term    = col_t2.number_input("Term (months)", 1, 60, 12)
                inception_date = col_t1.date_input("Inception Date", date.today())
                rbz_class      = col_t2.selectbox("RBZ Class", list(st.session_state.rbz_classes.keys()))

                base_rate       = 0.025
                inflation_load  = rates['inflation'] / 10000
                annual_prem     = value_zig * (base_rate + inflation_load)
                monthly_prem    = annual_prem / 12
                monthly_prem_usd = monthly_prem / rates['official_rate']

                rbz_class_info = st.session_state.rbz_classes[rbz_class]
                lapsing_rate   = rbz_class_info['max_lapsing'] + rates['inflation'] / 1000

                st.success(
                    f"Monthly Premium: ZiG {monthly_prem:,.2f} (USD {monthly_prem_usd:,.2f})\n\n"
                    f"Est. Lapsing Rate: {lapsing_rate*100:.1f}%"
                )

                if st.form_submit_button("Issue Policy"):
                    if description:
                        aid     = f"AST-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000,99999)}"
                        pol_num = f"POL-{asset_type[:3].upper()}-{datetime.now().strftime('%Y%m')}-{random.randint(1000,9999)}"
                        conv_hist = ""
                        if is_historical:
                            conv_hist = f"Converted from {hist_amt:,.0f} {hist_curr} on {hist_date_a}"
                        new_asset = pd.DataFrame([{
                            'Client_ID': client_id, 'Asset_ID': aid, 'Asset_Type': asset_type,
                            'Asset_Description': description, 'Asset_Value': value_zig,
                            'Asset_Value_USD': value_usd, 'Purchase_Date': purchase_date,
                            'Condition': 'Good', 'Insurance_Status': 'Active',
                            'Policy_Number': pol_num, 'Inflation_Adjustment': 'Monthly',
                            'Last_Valuation_Date': date.today(), 'Premium': monthly_prem,
                            'Premium_USD': monthly_prem_usd, 'Policy_Term_Months': policy_term,
                            'Inception_Date': inception_date, 'Lapsing_Rate': lapsing_rate,
                            'Currency_At_Inception': 'ZiG', 'RBZ_Class': rbz_class,
                            'Original_Currency': hist_curr if is_historical else 'ZiG',
                            'Original_Amount': hist_amt if is_historical else value_zig,
                            'Conversion_History': conv_hist
                        }])
                        st.session_state.assets = pd.concat(
                            [st.session_state.assets, new_asset], ignore_index=True)
                        save_database()
                        st.success(f"Policy issued: {pol_num}")
                        st.rerun()
                    else:
                        st.error("Please enter asset description.")

        with col2:
            st.subheader(f"Active Policies ({len(st.session_state.assets)})")
            if not st.session_state.assets.empty:
                for idx, asset in st.session_state.assets.iterrows():
                    client_name = st.session_state.clients.get(asset['Client_ID'], {}).get('Name', 'Unknown')
                    tag = "Historical" if asset['Original_Currency'] != 'ZiG' else "New"
                    with st.expander(f"[{tag}] {asset['Asset_Type']}: {asset['Asset_Description']} - {client_name}"):
                        st.write(f"**Policy:** {asset['Policy_Number']}")
                        st.write(f"**Value:** ZiG {asset['Asset_Value']:,.2f} (${asset['Asset_Value_USD']:,.2f})")
                        st.write(f"**Premium:** ZiG {asset['Premium']:,.2f}/month")
                        st.write(f"**RBZ Class:** {asset['RBZ_Class']}")
                        if asset['Conversion_History']:
                            st.info(f"History: {asset['Conversion_History']}")
                        if st.button("Delete Policy", key=f"del_ast_{idx}"):
                            st.session_state.assets = st.session_state.assets.drop(idx).reset_index(drop=True)
                            save_database()
                            st.rerun()
            else:
                st.info("No policies issued yet.")

# ==================== TAB 3: PREMIUM PAYMENTS ====================
with tab3:
    st.header("Premium Payments")
    if st.session_state.assets.empty:
        st.warning("No policies available. Issue a policy first (Asset Insurance tab).")
    else:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("Record Payment")
            pay_curr = st.radio("Payment Currency", ['ZiG', 'USD'], horizontal=True, key="pay_curr_r")
            st.info(f"RBZ Official Rate: 1 USD = {rates['official_rate']:.2f} ZiG")

            asset_opts = {}
            for _, a in st.session_state.assets.iterrows():
                cn = st.session_state.clients.get(a['Client_ID'], {}).get('Name', 'Unknown')
                asset_opts[f"{cn} - {a['Asset_Description']}"] = a['Asset_ID']

            sel_pol = st.selectbox("Select Policy", list(asset_opts.keys()), key="pay_pol_sel")
            if sel_pol:
                aid_p  = asset_opts[sel_pol]
                asset_p = st.session_state.assets[st.session_state.assets['Asset_ID'] == aid_p].iloc[0]
                with st.form("pay_form"):
                    pay_date  = st.date_input("Date", date.today())
                    suggested = asset_p['Premium_USD'] if pay_curr == 'USD' else asset_p['Premium']
                    amount    = st.number_input(f"Amount ({pay_curr})", min_value=0.0,
                                                value=float(suggested), step=10.0)
                    zig_amt = amount * rates['official_rate'] if pay_curr == 'USD' else amount
                    usd_amt = amount if pay_curr == 'USD' else amount / rates['official_rate']
                    col_p1, col_p2 = st.columns(2)
                    col_p1.metric("ZiG Amount", f"ZiG {zig_amt:,.2f}")
                    col_p2.metric("USD Equiv.", f"${usd_amt:,.2f}")
                    method = st.selectbox("Method", ['Cash', 'Bank Transfer', 'Ecocash', 'RTGS', 'SWIFT'])
                    status = st.selectbox("Status", ['Completed', 'Pending'])
                    notes  = st.text_area("Notes")
                    if st.form_submit_button("Record Payment"):
                        new_pay = pd.DataFrame([{
                            'Date': pay_date, 'Client_ID': asset_p['Client_ID'],
                            'Asset_ID': aid_p, 'Payment_Amount': zig_amt,
                            'Payment_Amount_USD': usd_amt, 'Payment_Method': method,
                            'Status': status, 'Notes': notes, 'Processed_By': current_user,
                            'Payment_Currency': pay_curr, 'Exchange_Rate_Used': rates['official_rate']
                        }])
                        st.session_state.payments = pd.concat(
                            [st.session_state.payments, new_pay], ignore_index=True)
                        save_database()
                        st.success("Payment recorded!")
                        st.rerun()

        with col2:
            st.subheader("Payment History")
            if not st.session_state.payments.empty:
                disp = st.session_state.payments.copy()
                disp['Client'] = disp['Client_ID'].map(
                    lambda x: st.session_state.clients.get(x, {}).get('Name', 'Unknown'))
                st.dataframe(
                    disp[['Date', 'Client', 'Payment_Amount', 'Payment_Amount_USD', 'Status']].rename(
                        columns={'Payment_Amount': 'ZiG', 'Payment_Amount_USD': 'USD'}),
                    use_container_width=True, hide_index=True)
                col_s1, col_s2 = st.columns(2)
                col_s1.metric("Total ZiG", f"ZiG {disp['Payment_Amount'].sum():,.2f}")
                col_s2.metric("Total USD",  f"${disp['Payment_Amount_USD'].sum():,.2f}")
            else:
                st.info("No payments recorded yet.")

# ==================== TAB 4: CLAIMS & SEVERITY ====================
with tab4:
    st.header("Claims & Severity Management")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("File New Claim")
        if not st.session_state.assets.empty:
            asset_opts_c = {}
            for _, a in st.session_state.assets.iterrows():
                cn = st.session_state.clients.get(a['Client_ID'], {}).get('Name', 'Unknown')
                asset_opts_c[f"{cn} - {a['Asset_Description']} (ZiG {a['Asset_Value']:,.0f})"] = a['Asset_ID']
            sel_c = st.selectbox("Select Asset", list(asset_opts_c.keys()), key="claim_asset_sel")
            if sel_c:
                aid_c  = asset_opts_c[sel_c]
                asset_c = st.session_state.assets[st.session_state.assets['Asset_ID'] == aid_c].iloc[0]
                with st.form("claim_form"):
                    severity    = st.select_slider("Severity Level",
                        options=['Low', 'Medium', 'High', 'Severe', 'Catastrophic'], value='Medium')
                    sev_factors = {'Low': 0.3, 'Medium': 0.6, 'High': 1.0, 'Severe': 1.5, 'Catastrophic': 2.0}
                    damage_pct  = st.slider("Damage Percentage", 0, 100, 30)

                    try:
                        months = (date.today() - pd.to_datetime(asset_c['Inception_Date']).date()).days / 30
                    except Exception:
                        months = 0
                    inflation_factor = (1 + (rates['inflation'] / 100 / 12)) ** months
                    base_claim = asset_c['Asset_Value'] * (damage_pct / 100) * sev_factors[severity]
                    claim_zig  = base_claim * inflation_factor
                    claim_usd  = claim_zig / rates['official_rate']

                    st.info(
                        f"Base Claim: ZiG {base_claim:,.2f}\n\n"
                        f"Inflation Adj (+{(inflation_factor-1)*100:.1f}%): ZiG {claim_zig:,.2f}\n\n"
                        f"USD: ${claim_usd:,.2f}"
                    )

                    claim_date = st.date_input("Date of Loss", date.today())
                    claim_type = st.selectbox("Type", ['Accident', 'Theft', 'Fire', 'Natural Disaster', 'Vandalism'])
                    desc_c     = st.text_area("Description")

                    if st.form_submit_button("Submit Claim"):
                        cid_new = f"CLM-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"
                        new_claim = pd.DataFrame([{
                            'Claim_ID': cid_new, 'Client_ID': asset_c['Client_ID'],
                            'Asset_ID': aid_c, 'Claim_Date': claim_date,
                            'Claim_Amount': claim_zig, 'Claim_Amount_USD': claim_usd,
                            'Claim_Type': claim_type, 'Severity_Level': severity,
                            'Inflation_Impact': (inflation_factor - 1) * 100,
                            'Settlement_Amount': claim_zig, 'Settlement_Amount_USD': claim_usd,
                            'Status': 'Filed', 'Processed_By': current_user,
                            'Trust_Score_Impact': 5, 'Days_To_Settle': 30,
                            'Currency_At_Claim': 'ZiG'
                        }])
                        st.session_state.claims = pd.concat(
                            [st.session_state.claims, new_claim], ignore_index=True)
                        save_database()
                        st.success(f"Claim filed: {cid_new}")
                        st.rerun()
        else:
            st.info("No insured assets available for claims.")

    with col2:
        st.subheader(f"Claims History ({len(st.session_state.claims)})")
        if not st.session_state.claims.empty:
            sev_colors = {'Low': '#28a745', 'Medium': '#ffc107', 'High': '#fd7e14',
                          'Severe': '#dc3545', 'Catastrophic': '#6f42c1'}
            for idx, claim in st.session_state.claims.iterrows():
                cn_c = st.session_state.clients.get(claim['Client_ID'], {}).get('Name', 'Unknown')
                sc   = sev_colors.get(claim['Severity_Level'], '#6c757d')
                st.markdown(
                    f"<div style='border-left:4px solid {sc}; padding:0.6rem 1rem; margin:0.4rem 0;"
                    "background:#fafafa; border-radius:0 0.4rem 0.4rem 0;'>"
                    f"<strong>{claim['Claim_ID']}</strong> - {cn_c}<br>"
                    f"<small>ZiG {claim['Claim_Amount']:,.2f} (${claim['Claim_Amount_USD']:,.2f}) | "
                    f"<b>{claim['Severity_Level']}</b> | {claim['Status']}</small>"
                    "</div>",
                    unsafe_allow_html=True
                )
            col_s1, col_s2 = st.columns(2)
            col_s1.metric("Total Claims (ZiG)", f"ZiG {st.session_state.claims['Claim_Amount'].sum():,.2f}")
            col_s2.metric("Total Claims (USD)", f"${st.session_state.claims['Claim_Amount_USD'].sum():,.2f}")
        else:
            st.info("No claims filed yet.")

# ==================== TAB 5: INFLATION IMPACT ====================
with tab5:
    st.header("Inflation Impact Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Historical Inflation Trend (ZiG Era)")
        fig, ax = plt.subplots(figsize=(8, 4))
        hist_rbz = st.session_state.rbz_historical
        ax.plot(hist_rbz['Date'], hist_rbz['Inflation_Rate'], 'b-', linewidth=2.5, marker='o', markersize=3)
        ax.axhline(y=rates['inflation'], color='green', linestyle='--',
                   label=f"Current: {rates['inflation']}%", linewidth=1.5)
        ax.fill_between(hist_rbz['Date'], hist_rbz['Inflation_Rate'], alpha=0.1, color='blue')
        ax.set_xlabel('Date'); ax.set_ylabel('Inflation (%)')
        ax.set_title('RBZ Official Inflation - ZiG Era', fontweight='bold')
        ax.legend(); ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45); plt.tight_layout()
        st.pyplot(fig); plt.close()
        st.metric("Current Inflation", f"{rates['inflation']}%", delta="From peak 800%+")

    with col2:
        st.subheader("Exchange Rate Stability")
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        post = hist_rbz[hist_rbz['Currency'] == 'ZiG']
        if not post.empty:
            ax2.plot(post['Date'], post['Official_Rate'], 'g-', linewidth=2.5, label='Official Rate')
            ax2.plot(post['Date'], post['Parallel_Rate'], 'r--', linewidth=2, label='Parallel Rate', alpha=0.7)
        ax2.set_xlabel('Date'); ax2.set_ylabel('ZiG per USD')
        ax2.set_title('ZiG Exchange Rate Stability (2025-2026)', fontweight='bold')
        ax2.legend(); ax2.grid(True, alpha=0.3)
        plt.xticks(rotation=45); plt.tight_layout()
        st.pyplot(fig2); plt.close()
        spread = ((rates['parallel_rate'] / rates['official_rate']) - 1) * 100
        st.metric("Official/Parallel Spread", f"{spread:.1f}%",
                  delta="Narrowing" if spread < 30 else "Wide")

    st.subheader("Asset Value Erosion / Growth Calculator")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        asset_value = st.number_input("Asset Value (ZiG)", min_value=0.0, value=100000.0, step=10000.0, key="erosion_val")
        years_e     = st.slider("Years", 1, 10, 5, key="erosion_yrs")
    with col_c2:
        inf_scenario = st.selectbox("Inflation Scenario", ['Optimistic (5%)', 'Base Case (8.5%)', 'Pessimistic (12%)'])
        sc_rates_map = {'Optimistic (5%)': 5, 'Base Case (8.5%)': 8.5, 'Pessimistic (12%)': 12}
        sc_rate      = sc_rates_map[inf_scenario]
        future_val   = asset_value * (1 + sc_rate / 100) ** years_e
        gain         = future_val - asset_value
        st.metric("Future Value (Nominal)", f"ZiG {future_val:,.2f}")
        st.metric("Nominal Gain", f"ZiG {gain:,.2f}", delta=f"+{gain/asset_value*100:.1f}%")

# ==================== TAB 6: TRUST ANALYTICS ====================
with tab6:
    st.header("Trust Analytics - ZiG Era Recovery")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Industry Trust Recovery")
        trust_df = pd.DataFrame({
            'Period': ['Pre-ZiG\n(2023)', 'ZiG Y1\n(2024)', 'ZiG Y2\n(2025)', 'Current\n(2026)'],
            'Trust':  [35, 65, 78, 85]
        })
        fig, ax = plt.subplots(figsize=(7, 4))
        bar_colors = ['#ef5350', '#ff9800', '#8bc34a', '#2e7d32']
        bars = ax.bar(trust_df['Period'], trust_df['Trust'], color=bar_colors,
                      edgecolor='white', linewidth=1.5, width=0.6)
        ax.set_ylim(0, 105); ax.set_ylabel('Trust Score (%)')
        ax.set_title('Insurance Industry Trust Recovery', fontweight='bold')
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2., h + 2, f'{h}%', ha='center', va='bottom', fontweight='bold')
        ax.grid(True, alpha=0.2, axis='y')
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        plt.tight_layout(); st.pyplot(fig); plt.close()
        st.success("Trust has increased by 50% since pre-ZiG era")

    with col2:
        st.subheader("Client Trust Distribution")
        if st.session_state.clients:
            trust_scores = [c.get('Trust_Score', 70) for c in st.session_state.clients.values()]
            avg_trust    = sum(trust_scores) / len(trust_scores)
            st.metric("Average Client Trust", f"{avg_trust:.1f}%", delta=f"+{avg_trust-35:.1f}% vs Pre-ZiG")
            fig2, ax2 = plt.subplots(figsize=(7, 4))
            ax2.hist(trust_scores, bins=10, range=(0, 100), color='#2e7d32', alpha=0.75, edgecolor='white')
            ax2.axvline(x=avg_trust, color='#FFD700', linestyle='--', linewidth=2.5, label=f'Average: {avg_trust:.0f}%')
            ax2.set_xlabel('Trust Score (%)'); ax2.set_ylabel('Number of Clients')
            ax2.set_title('Client Trust Distribution', fontweight='bold')
            ax2.legend(); ax2.grid(True, alpha=0.25, axis='y')
            ax2.spines['top'].set_visible(False); ax2.spines['right'].set_visible(False)
            plt.tight_layout(); st.pyplot(fig2); plt.close()
            at_risk = sum(1 for s in trust_scores if s < 60)
            if at_risk:
                st.warning(f"{at_risk} client(s) have low trust (<60%)")
            else:
                st.success("No at-risk clients detected")
        else:
            st.info("Register clients to see trust analytics.")

    st.subheader("Trust Score Calculation")
    st.markdown("""
| Factor | Weight | Calculation |
|--------|--------|-------------|
| Base Score | 70 | Starting point |
| Claims Paid | +20 | (Paid/Total) x 20 |
| Settlement Time | +30 | Max(0, 30 - avg days) |
| Inflation Adjustment | +10 | If claims adjusted for inflation |
| Communication Quality | +10 | Manual input |
""")

# ==================== TAB 7: CAPITAL & SOLVENCY ====================
with tab7:
    st.header("Capital & Solvency - RBZ Compliant")
    total_risk = 0
    if not st.session_state.assets.empty:
        total_risk = st.session_state.assets['Asset_Value'].sum() * 0.15
    st.session_state.capital_reserves['required_capital'] = total_risk
    avail    = st.session_state.capital_reserves['available_capital']
    solvency = (avail / total_risk * 100) if total_risk > 0 else 100.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Required Capital (RBZ)", f"ZiG {total_risk:,.0f}")
    col2.metric("Available Capital",       f"ZiG {avail:,.0f}")
    col3.metric("Solvency Ratio",          f"{solvency:.1f}%",
                delta="RBZ Compliant" if solvency >= 150 else "Below Minimum",
                delta_color="normal" if solvency >= 150 else "inverse")

    fig, ax = plt.subplots(figsize=(10, 2))
    ax.barh(['Capital'], [avail], color='#2e7d32', alpha=0.8, label='Available Capital')
    if total_risk > 0:
        ax.barh(['Capital'], [total_risk], color='#ef5350', alpha=0.4, label='Required Capital')
        ax.axvline(x=total_risk * 1.5, color='#ff9800', linestyle='--', linewidth=2, label='RBZ Min (150%)')
    ax.set_xlabel('Amount (ZiG)'); ax.legend(loc='upper right', fontsize=8)
    ax.set_title('Capital Adequacy Position', fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    if not st.session_state.assets.empty:
        st.subheader("Risk-Based Capital Breakdown")
        class_grp = st.session_state.assets.groupby('RBZ_Class').agg(
            Total_Value=('Asset_Value', 'sum'), Count=('Asset_ID', 'count')).reset_index()
        class_grp['Risk_Capital'] = class_grp.apply(
            lambda x: x['Total_Value'] * st.session_state.rbz_classes.get(x['RBZ_Class'], {}).get('capital_factor', 0.1),
            axis=1)
        st.dataframe(class_grp.rename(columns={
            'RBZ_Class': 'Class', 'Total_Value': 'Total Value (ZiG)', 'Risk_Capital': 'Risk Capital Required (ZiG)'
        }), use_container_width=True, hide_index=True)
        st.metric("Total Risk-Based Capital Required", f"ZiG {class_grp['Risk_Capital'].sum():,.0f}")

    st.subheader("Capital Injection")
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        add_cap = st.number_input("Additional Capital (ZiG)", min_value=0.0, value=1_000_000.0, step=100_000.0)
    with col_c2:
        if st.button("Add Capital", key="add_cap_btn"):
            st.session_state.capital_reserves['available_capital'] += add_cap
            save_database()
            st.success(f"Added ZiG {add_cap:,.0f}")
            st.rerun()

# ==================== TAB 8: PROFIT TESTING ====================
with tab8:
    st.header("Profit Testing - Scenario Analysis")
    col1, col2 = st.columns(2)
    with col1:
        scenario   = st.selectbox("Scenario",
            ['Base Case (8.5% Inflation)', 'Optimistic (5% Inflation)', 'Pessimistic (12% Inflation)'])
        proj_years = st.slider("Projection Years", 1, 10, 5)

        sc_params = {
            'Base Case (8.5% Inflation)':  {'inflation': 8.5, 'growth': 10,  'claims_factor': 1.0},
            'Optimistic (5% Inflation)':   {'inflation': 5,   'growth': 15,  'claims_factor': 0.7},
            'Pessimistic (12% Inflation)': {'inflation': 12,  'growth': 8,   'claims_factor': 1.3},
        }
        p = sc_params[scenario]
        base_premium = st.session_state.payments['Payment_Amount'].sum() \
            if not st.session_state.payments.empty else 100000.0

        years_list = list(range(proj_years + 1))
        premiums   = [base_premium * (1 + p['growth'] / 100) ** i for i in years_list]
        claims_p   = [pr * 0.6 * p['claims_factor'] * (1 + p['inflation'] / 100) for pr in premiums]
        expenses   = [pr * 0.2 for pr in premiums]
        profits    = [pr - cl - ex for pr, cl, ex in zip(premiums, claims_p, expenses)]

        results = pd.DataFrame({'Year': years_list, 'Premiums': premiums,
                                 'Claims': claims_p, 'Expenses': expenses, 'Profit': profits})
        results['Loss_Ratio'] = results['Claims'] / results['Premiums'].replace(0, np.nan) * 100
        st.session_state.profit_testing = results

        total_profit = results['Profit'][1:].sum()
        avg_lr       = results['Loss_Ratio'].mean()
        roi          = (total_profit / 50_000_000) * 100
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Projected Profit", f"ZiG {total_profit:,.0f}")
        col_m2.metric("Avg Loss Ratio",          f"{avg_lr:.1f}%")
        col_m3.metric("ROE",                      f"{roi:.1f}%")

    with col2:
        st.subheader("Projection Chart")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(years_list, premiums,  'b-o', linewidth=2, markersize=5, label='Premiums')
        ax.plot(years_list, claims_p,  'r-s', linewidth=2, markersize=5, label='Claims')
        ax.plot(years_list, profits,   'g-^', linewidth=2, markersize=5, label='Profit')
        ax.fill_between(years_list, profits, alpha=0.1, color='green')
        ax.set_xlabel('Years'); ax.set_ylabel('Amount (ZiG)')
        ax.set_title(f'Profit Projection - {scenario}', fontweight='bold')
        ax.legend(); ax.grid(True, alpha=0.3); ax.set_xticks(years_list)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    st.subheader("Projection Results Table")
    disp_results = results.copy()
    for c in ['Premiums', 'Claims', 'Expenses', 'Profit']:
        disp_results[c] = disp_results[c].apply(lambda x: f"ZiG {x:,.0f}")
    disp_results['Loss_Ratio'] = disp_results['Loss_Ratio'].apply(lambda x: f"{x:.1f}%")
    st.dataframe(disp_results, use_container_width=True, hide_index=True)

    csv_data = results.to_csv(index=False)
    st.download_button("Download Results (CSV)", data=csv_data,
                       file_name=f"profit_test_{datetime.now().strftime('%Y%m%d')}.csv",
                       mime="text/csv")

# ==================== TAB 9: BUSINESS CASE ====================
with tab9:
    st.header("Business Case - ZiG Success Story")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
### The ZiG Turnaround (2024-2026)

**Economic Stabilization:**
- Inflation: 500%+ to **8.5%** (single digit)
- Exchange Rate: Stable at **26.90 ZiG/USD**
- Insurance Penetration: **8% to 15%** (recovering)
- Public Trust Score: **35% to 85%**
- All insurers RBZ capital compliant

**RBZ Key Data:**
- Gold reserves: **$380 Million** backing ZiG
- Central Bank Policy Rate: **35%** (reducing)
- Import Cover: **45 days**
- Money Supply Growth: **12.5%**
        """)

        st.subheader("ROI Calculator")
        investment = st.number_input("Initial Investment (ZiG)", min_value=0.0,
                                      value=50_000_000.0, step=1_000_000.0)
        if investment > 0:
            proj_prem   = investment * 10
            proj_profit = proj_prem * 0.15
            roi_calc    = (proj_profit / investment) * 100
            payback     = investment / (proj_profit / 12) if proj_profit > 0 else 0
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric("Annual Premiums", f"ZiG {proj_prem:,.0f}")
            col_r2.metric("Annual Profit",   f"ZiG {proj_profit:,.0f}")
            col_r3.metric("ROI",              f"{roi_calc:.1f}%")
            st.info(f"Payback Period: {payback:.1f} months")

    with col2:
        st.markdown("""
### Key System Achievements

**RiskShield Impact:**
- **1,500+** policies issued in ZiG
- **98%** client retention rate
- **ZiG 45M** in premiums collected
- **Zero** inflation-related complaints
- **5 currency regimes** tracked (2009-2026)
        """)

        st.subheader("ZiG Era Metrics (2024-2026)")
        metrics_df = pd.DataFrame({
            'Metric':          ['Inflation', 'Exchange Rate', 'Insurance Trust', 'Policy Retention', 'USD/ZiG Spread'],
            'Pre-ZiG (2023)':  ['150%+', 'Daily changes', '35%', '60%', '50%+'],
            'Current (2026)':  ['8.5%', 'Stable 715d', '65%', '85%', '24.5%']
        })
        st.dataframe(metrics_df, use_container_width=True, hide_index=True)

        st.subheader("Authors")
        st.markdown(
            "<div class='authors-box'>"
            "<h4>Actuarial Science Group 27</h4>"
            "<p style='font-size:0.9rem; margin:0.2rem 0;'>"
            "<b>Authors:</b> Kwanai Karen | Lackson Tsvangirayi | "
            "Kudakwashe Muzanenhamo | Godfrey Masasa | Charlotte E Makuleke"
            "</p>"
            "<p style='font-size:0.82rem; margin-top:0.5rem; opacity:0.85;'>"
            "BSc Honours Actuarial Science | NUST | "
            "</p>"
            "</div>",
            unsafe_allow_html=True
        )

        st.subheader("Contact")
        st.info(
            "RiskShield Zimbabwe\n\n"
            "123 Kwame Nkrumah Ave, Harare, Zimbabwe\n\n"
            "Phone: +263 24 279 1234\n\n"
            "Email: info@riskshield.co.zw\n\n"
            "Web: www.riskshield.co.zw"
        )

# ==================== FOOTER ====================

st.markdown("---")
footer_html = (
    "<div style='text-align:center; color:#555; padding:1.5rem;"
    "background:linear-gradient(135deg,#f9f9f9,#f0f8f0);"
    "border-radius:0.75rem; margin-top:1rem;'>"
    "<p style='font-size:1.2rem; font-weight:bold; color:#006400; margin:0;'>"
    "RiskShield Zimbabwe</p>"
    "<p style='font-size:0.88rem; margin:0.3rem 0; color:#444;'>"
    "Complete Insurance Management System | Historical Currency Tracking 2009-2026 | v7.1</p>"
    "<p style='font-size:0.82rem; margin:0.2rem 0; color:#666;'>"
    "<b>Authors:</b> Kwanai Karen | Lackson Tsvangirayi | "
    "Kudakwashe Muzanenhamo | Godfrey Masasa | Charlotte E Makuleke</p>"
    "<p style='font-size:0.78rem; margin:0.2rem 0; color:#888;'>"
    "BSc Honours Actuarial Science | NUST | "
    "Data Source: " + rates['source'] + " | Last Update: " + rates['last_updated'] + "</p>"
    "<p style='font-size:0.78rem; color:#999; margin:0.2rem 0;'>"
    "1 USD = " + str(rates['official_rate']) + " ZiG | "
    "Inflation: " + str(rates['inflation']) + "% | "
    "ZiG Stability: " + str(rates['days_stable']) + " days | "
    "2026 RiskShield Zimbabwe</p>"
    "</div>"
)
st.markdown(footer_html, unsafe_allow_html=True)