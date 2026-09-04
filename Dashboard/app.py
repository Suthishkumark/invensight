import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components
import duckdb
import pandas as pd
import os
import sys
import uuid

# ─── Path Setup ───────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config.settings import (
    load_config, save_config, validate_config,
    load_business_profiles, get_ui_labels,
    REQUIRED_FIELDS, OPTIONAL_FIELDS,
)
from auth.auth import (
    init_db, register_user, login_user, log_activity,
    get_all_users, get_activity_log, get_user_activity,
    toggle_user_active, get_usage_summary, new_session_id,
    change_password,
)

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InvenSight | Smart Stock Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Init Auth DB (once) ─────────────────────────────────────────────────────
init_db()

# ─── Load Config ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _load_cfg():
    return load_config(BASE_DIR)

@st.cache_data(show_spinner=False)
def _load_profiles():
    return load_business_profiles(BASE_DIR)

cfg      = _load_cfg()
L        = get_ui_labels(BASE_DIR, cfg)
PROFILES = _load_profiles()

# ─── Aurora Pro Theme ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons');

:root {
    --bg:        #03050f;
    --surface:   rgba(255,255,255,0.032);
    --elevated:  rgba(255,255,255,0.058);
    --border:    rgba(255,255,255,0.07);
    --border-hi: rgba(255,255,255,0.13);
    --indigo:    #6366f1;
    --violet:    #8b5cf6;
    --cyan:      #06b6d4;
    --emerald:   #10b981;
    --amber:     #f59e0b;
    --rose:      #f43f5e;
    --tx:        #f1f5f9;
    --tx2:       #94a3b8;
    --tx3:       #475569;
    --g-indigo:  linear-gradient(135deg,#6366f1,#8b5cf6);
    --g-cyan:    linear-gradient(135deg,#06b6d4,#6366f1);
    --g-success: linear-gradient(135deg,#10b981,#06b6d4);
    --g-warn:    linear-gradient(135deg,#f59e0b,#ef4444);
    --r-md:      14px;
    --r-lg:      20px;
    --r-pill:    999px;
    --sh-card:   0 0 0 1px rgba(255,255,255,0.06),0 8px 32px rgba(0,0,0,0.55);
    --sh-lg:     0 8px 40px rgba(0,0,0,0.65),0 4px 12px rgba(0,0,0,0.5);
}

/* ── Text High Contrast & Readability ── */
html,body{background:var(--bg)!important;}
.stApp{background:transparent!important;}
p,label,small,input,textarea,select,button{font-family:'Inter',-apple-system,sans-serif;}
h1,h2,h3,h4,h5,h6{font-family:'Sora',sans-serif!important;letter-spacing:-0.025em!important;color:#ffffff!important;}

/* ── Material Icons / Streamlit Ligatures Fix ── */
[data-testid*="Icon"],[data-testid="stIconMaterial"],.material-icons,.material-symbols-rounded,.material-symbols-outlined,[data-testid="stTextInput"] button,[data-testid="stTextInput"] button *{
    font-family:'Material Symbols Rounded','Material Symbols Outlined','Material Icons'!important;
    font-weight:normal!important;
    font-style:normal!important;
    font-size:20px!important;
    line-height:1!important;
    display:inline-block!important;
    white-space:nowrap!important;
    text-transform:none!important;
    letter-spacing:normal!important;
    word-wrap:normal!important;
    direction:ltr!important;
    -webkit-font-feature-settings:'liga' 1!important;
    font-feature-settings:'liga' 1!important;
    -webkit-font-smoothing:antialiased!important;
    color:#94a3b8!important;
}
[data-testid="stTextInput"] button:hover *{
    color:#818cf8!important;
}

#MainMenu,footer,header{display:none!important;}
.stDeployButton,[data-testid="stToolbar"],[data-testid="stSidebarCollapseButton"],[data-testid="collapsedControl"],[data-testid="stDecoration"]{display:none!important;}
.block-container{padding:2rem 2.5rem 5rem!important;max-width:1480px!important;}

[data-testid="stSidebar"]{background:rgba(3,5,15,0.96)!important;border-right:1px solid var(--border)!important;backdrop-filter:blur(40px) saturate(1.5)!important;}
[data-testid="stSidebar"]>div{background:transparent!important;}
[data-testid="stSidebarContent"]{padding:1rem 0.8rem!important;}
[data-testid="stSidebar"] *{color:#f1f5f9!important;}

/* ── Radio & Navigation ── */
[data-testid="stRadio"]>div{gap:4px!important;flex-direction:column!important;}
[data-testid="stRadio"] label{background:transparent!important;border:1px solid transparent!important;border-radius:var(--r-md)!important;padding:0.7rem 1rem!important;transition:all 0.2s cubic-bezier(0.4,0,0.2,1)!important;cursor:pointer!important;font-size:0.875rem!important;font-weight:500!important;color:#94a3b8!important;width:100%!important;}
[data-testid="stRadio"] label:hover{background:var(--surface)!important;border-color:var(--border-hi)!important;color:#ffffff!important;transform:translateX(3px)!important;}
[data-testid="stRadio"] label:has(input:checked){background:rgba(99,102,241,0.14)!important;border-color:rgba(99,102,241,0.45)!important;color:#c7d2fe!important;box-shadow:0 0 28px rgba(99,102,241,0.22)!important;}

/* ── Form Inputs & Password Toggle Fix ── */
[data-testid="stSelectbox"]>div>div,[data-testid="stMultiSelect"]>div>div{background-color:#0d1326!important;background:#0d1326!important;border:1px solid rgba(99,102,241,0.35)!important;border-radius:12px!important;backdrop-filter:blur(10px)!important;}
[data-testid="stSelectbox"]>div>div:focus-within,[data-testid="stMultiSelect"]>div>div:focus-within{border-color:#818cf8!important;box-shadow:0 0 0 3px rgba(99,102,241,0.25)!important;}

[data-testid="stTextInput"]>div,[data-testid="stTextInput"]>div>div,[data-testid="stTextInput"] div[data-baseweb="base-input"],[data-testid="stTextInput"] div[data-baseweb="input"],[data-testid="stTextArea"]>div,[data-testid="stTextArea"]>div>div,[data-testid="stTextArea"] div[data-baseweb="textarea"],[data-testid="stNumberInput"]>div,[data-testid="stNumberInput"]>div>div{background-color:#0d1326!important;background:#0d1326!important;border:1px solid rgba(99,102,241,0.35)!important;border-radius:12px!important;overflow:hidden!important;transition:all 0.2s cubic-bezier(0.4,0,0.2,1)!important;box-shadow:0 2px 8px rgba(0,0,0,0.4) inset!important;}
[data-testid="stTextInput"]>div:focus-within,[data-testid="stTextArea"]>div:focus-within,[data-testid="stNumberInput"]>div:focus-within{border-color:#818cf8!important;box-shadow:0 0 0 3px rgba(99,102,241,0.25),0 0 20px rgba(99,102,241,0.2)!important;background-color:#121934!important;background:#121934!important;}

[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input{background-color:transparent!important;background:transparent!important;border:none!important;box-shadow:none!important;color:#ffffff!important;padding:0.75rem 1rem!important;font-size:0.92rem!important;font-family:'Inter',sans-serif!important;}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder{color:#64748b!important;}

/* Hide 'Press Enter to apply' popup instruction completely */
[data-testid="InputInstructions"],
div[data-testid="InputInstructions"],
[data-testid="stTextInput"] [data-testid="InputInstructions"],
[data-testid="stTextArea"] [data-testid="InputInstructions"],
[data-testid="stNumberInput"] [data-testid="InputInstructions"] {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    pointer-events: none !important;
}

/* Password Visibility Button SVG Mask (Guaranteed Pure SVG Eye Icon) */
[data-testid="stTextInput"] button[aria-label*="password"],
[data-testid="stTextInput"] button[aria-label*="Password"],
[data-testid="stTextInput"] button {
    position: relative !important;
    overflow: hidden !important;
    width: 36px !important;
    min-width: 36px !important;
    height: 36px !important;
    padding: 0 !important;
    margin: 0 !important;
    background: transparent !important;
    border: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}
[data-testid="stTextInput"] button span {
    font-size: 0 !important;
    color: transparent !important;
    display: none !important;
    visibility: hidden !important;
}
[data-testid="stTextInput"] button::after {
    content: '' !important;
    display: block !important;
    width: 18px !important;
    height: 18px !important;
    background-color: #94a3b8 !important;
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M15 12a3 3 0 11-6 0 3 3 0 016 0z'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z'/%3E%3C/svg%3E") no-repeat center / contain !important;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M15 12a3 3 0 11-6 0 3 3 0 016 0z'/%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z'/%3E%3C/svg%3E") no-repeat center / contain !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}
[data-testid="stTextInput"] button:hover::after {
    background-color: #818cf8 !important;
    filter: drop-shadow(0 0 6px rgba(129, 140, 248, 0.8)) !important;
}

/* ── Buttons ── */
[data-testid="stButton"] button{background:var(--g-indigo)!important;color:#ffffff!important;border:none!important;border-radius:var(--r-pill)!important;font-weight:600!important;font-size:0.875rem!important;padding:0.65rem 1.6rem!important;transition:all 0.22s cubic-bezier(0.4,0,0.2,1)!important;box-shadow:0 4px 18px rgba(99,102,241,0.4)!important;}
[data-testid="stButton"] button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 28px rgba(99,102,241,0.55)!important;filter:brightness(1.1)!important;}
[data-testid="stButton"] button:active{transform:translateY(0)!important;}
[data-testid="stDownloadButton"] button{background:var(--g-success)!important;color:#ffffff!important;border:none!important;border-radius:var(--r-pill)!important;font-weight:600!important;padding:0.65rem 1.6rem!important;box-shadow:0 4px 18px rgba(16,185,129,0.35)!important;transition:all 0.22s ease!important;}
[data-testid="stDownloadButton"] button:hover{transform:translateY(-2px)!important;box-shadow:0 8px 28px rgba(16,185,129,0.5)!important;}

/* ── High-Contrast DataFrames & Tables ── */
[data-testid="stDataFrame"],[data-testid="stDataFrameResizable"]{border-radius:var(--r-lg)!important;overflow:hidden!important;border:1px solid var(--border-hi)!important;box-shadow:var(--sh-card)!important;}
[data-testid="stDataFrame"] *{font-family:'Inter',sans-serif!important;}

/* ── Charts (Seamless Dark Theme) ── */
[data-testid="stVegaLiteChart"],[data-testid="stArrowVegaLiteChart"],[data-testid="stPlotlyChart"]{background:rgba(10,15,30,0.6)!important;border:1px solid var(--border-hi)!important;border-radius:var(--r-lg)!important;overflow:hidden!important;padding:0.75rem!important;}
.vega-embed,.js-plotly-plot{background:transparent!important;}
.vega-embed svg{background:transparent!important;}
.vega-embed text{fill:#cbd5e1!important;font-family:'Inter',sans-serif!important;}
.vega-embed line,.vega-embed path.domain{stroke:rgba(255,255,255,0.12)!important;}

[data-testid="stExpander"]{background:var(--surface)!important;border:1px solid var(--border-hi)!important;border-radius:var(--r-lg)!important;backdrop-filter:blur(10px)!important;overflow:hidden!important;}
[data-testid="stFileUploader"]{background:rgba(99,102,241,0.04)!important;border:2px dashed rgba(99,102,241,0.25)!important;border-radius:var(--r-lg)!important;transition:all 0.2s ease!important;}

hr{border:none!important;height:1px!important;background:linear-gradient(90deg,transparent,var(--border-hi),transparent)!important;margin:2rem 0!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:rgba(99,102,241,0.28);border-radius:5px;}
::-webkit-scrollbar-thumb:hover{background:rgba(99,102,241,0.55);}
[data-testid="stMarkdownContainer"] p{color:#cbd5e1!important;}
.stAlert{border-radius:var(--r-md)!important;}

/* ── Auth Card (Ultra Modern SaaS Aesthetic) ── */
[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-inner) {
    max-width: 480px !important;
    margin: 2rem auto !important;
    background: rgba(10, 15, 30, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-top: 1px solid rgba(129, 140, 248, 0.45) !important;
    border-radius: 24px !important;
    box-shadow: 0 24px 64px rgba(0, 0, 0, 0.7), 0 0 50px rgba(99, 102, 241, 0.18) !important;
    backdrop-filter: blur(28px) !important;
    padding: 0.8rem 1rem 1.4rem !important;
}
.auth-header{text-align:center;padding:1.2rem 1rem 0.6rem;}
.auth-logo-icon{display:inline-flex;align-items:center;justify-content:center;width:72px;height:72px;border-radius:22px;font-size:2.6rem;background:linear-gradient(135deg,rgba(99,102,241,0.28),rgba(139,92,246,0.2));border:1px solid rgba(129,140,248,0.4);box-shadow:0 8px 30px rgba(99,102,241,0.35);margin-bottom:0.9rem;}
.auth-title{font-family:'Sora',sans-serif!important;font-size:2.2rem!important;font-weight:800!important;margin:0 0 0.25rem 0!important;letter-spacing:-0.035em!important;color:#ffffff!important;background:linear-gradient(180deg,#ffffff 40%,#cbd5e1 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.auth-subtitle{color:#94a3b8!important;font-size:0.875rem!important;margin:0 0 0.8rem 0!important;}
.auth-footer-pills{display:flex;justify-content:center;gap:14px;margin-top:1.5rem;padding-top:1.2rem;border-top:1px solid rgba(255,255,255,0.06);font-size:0.75rem;color:#94a3b8;flex-wrap:wrap;}
.auth-footer-pills span{display:inline-flex;align-items:center;gap:4px;}
.currency-badge{display:inline-flex;align-items:center;gap:0.4rem;padding:0.35rem 0.75rem;background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.3);border-radius:999px;font-size:0.75rem;font-weight:700;color:#c7d2fe;}

/* ── KPI Card ── */
.kpi-card{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:1.5rem 1.4rem 1.3rem;overflow:hidden;transition:all 0.3s cubic-bezier(0.4,0,0.2,1);backdrop-filter:blur(16px);box-shadow:var(--sh-card);}
.kpi-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:var(--r-lg) var(--r-lg) 0 0;}
.kpi-card::after{content:'';position:absolute;top:-40px;right:-20px;width:90px;height:90px;border-radius:50%;opacity:0.08;}
.kpi-card:hover{transform:translateY(-5px);border-color:rgba(99,102,241,0.38);box-shadow:var(--sh-lg),0 0 28px rgba(99,102,241,0.22);}
.kpi-card.ci::before{background:var(--g-indigo);}.kpi-card.ci::after{background:var(--indigo);}
.kpi-card.cc::before{background:var(--g-cyan);}.kpi-card.cc::after{background:var(--cyan);}
.kpi-card.ce::before{background:var(--g-success);}.kpi-card.ce::after{background:var(--emerald);}
.kpi-card.ca::before{background:var(--g-warn);}.kpi-card.ca::after{background:var(--amber);}
.kpi-card.cr::before{background:linear-gradient(135deg,#f43f5e,#f59e0b);}.kpi-card.cr::after{background:var(--rose);}
.kpi-label{font-size:0.68rem;font-weight:700;color:var(--tx3);text-transform:uppercase;letter-spacing:0.11em;margin-bottom:0.65rem;display:flex;align-items:center;gap:0.4rem;}
.kpi-value{font-family:'Sora',sans-serif;font-size:2rem;font-weight:700;color:var(--tx);letter-spacing:-0.04em;line-height:1;}
.kpi-delta{margin-top:0.55rem;font-size:0.775rem;font-weight:600;display:flex;align-items:center;gap:0.3rem;}
.kpi-delta.up{color:#34d399;}.kpi-delta.down{color:#fb7185;}

/* ── Page header ── */
.pg-header{margin-bottom:2rem;padding-bottom:1.5rem;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;gap:1rem;}
.pg-header-bar{width:3px;min-height:52px;border-radius:3px;margin-top:4px;flex-shrink:0;}
.pg-header h1{font-family:'Sora',sans-serif!important;font-size:2rem!important;font-weight:700!important;margin:0!important;letter-spacing:-0.035em!important;color:var(--tx)!important;line-height:1.15!important;}
.pg-header p{margin:0.35rem 0 0!important;font-size:0.875rem!important;color:var(--tx2)!important;font-weight:400!important;}

/* ── Section title ── */
.sec-title{display:flex;align-items:center;gap:0.6rem;margin:2rem 0 0.9rem;}
.sec-bar{width:3px;height:18px;border-radius:3px;flex-shrink:0;}
.sec-title h3{margin:0!important;font-family:'Sora',sans-serif!important;font-size:0.875rem!important;font-weight:600!important;color:var(--tx2)!important;}

/* ── Step header ── */
.step-row{display:flex;align-items:center;gap:0.75rem;margin:2rem 0 1rem;}
.step-num{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;background:var(--g-indigo);color:#fff;font-weight:700;font-size:0.78rem;font-family:'Sora',sans-serif;box-shadow:0 0 14px rgba(99,102,241,0.45);flex-shrink:0;}
.step-row h3{margin:0!important;font-family:'Sora',sans-serif!important;font-size:1rem!important;font-weight:600!important;color:var(--tx)!important;}

/* ── Banners ── */
.banner{padding:0.85rem 1.1rem;border-radius:var(--r-md);font-size:0.875rem;font-weight:500;margin:0.5rem 0;}
.banner.ok{background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.22);color:#34d399;}
.banner.err{background:rgba(244,63,94,0.08);border:1px solid rgba(244,63,94,0.22);color:#fb7185;}
.banner.inf{background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.22);color:#a5b4fc;}
.banner.wrn{background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.22);color:#fbbf24;}

/* ── Badge ── */
.badge{display:inline-flex;align-items:center;gap:0.25rem;padding:3px 12px;border-radius:var(--r-pill);font-size:0.68rem;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;}
.badge.healthy{background:rgba(16,185,129,0.12);color:#34d399;border:1px solid rgba(16,185,129,0.25);}
.badge.under{background:rgba(244,63,94,0.12);color:#fb7185;border:1px solid rgba(244,63,94,0.25);}
.badge.over{background:rgba(245,158,11,0.12);color:#fbbf24;border:1px solid rgba(245,158,11,0.25);}
.badge.unknown{background:rgba(148,163,184,0.08);color:#94a3b8;border:1px solid rgba(148,163,184,0.15);}

/* ── User pill ── */
.user-pill{display:inline-flex;align-items:center;gap:0.5rem;padding:0.4rem 0.8rem;background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);border-radius:var(--r-pill);font-size:0.78rem;font-weight:600;color:#a5b4fc;}
.admin-pill{background:rgba(245,158,11,0.1)!important;border-color:rgba(245,158,11,0.25)!important;color:#fbbf24!important;}
</style>
""", unsafe_allow_html=True)

# ─── Aurora Pro Interactive Particle Network & Aesthetic Background ──────────
components.html("""
<script>
(function() {
    var d = window.parent.document;
    if (!d.getElementById('mat-symbols-link')) {
        var l = d.createElement('link');
        l.id = 'mat-symbols-link';
        l.rel = 'stylesheet';
        l.href = 'https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0';
        d.head.appendChild(l);
    }

    if (!d.getElementById('ap-styles')) {
        var s = d.createElement('style'); s.id = 'ap-styles';
        var c = '';
        c += 'body{background:#020512!important;overflow-x:hidden;}';
        c += '[data-testid="InputInstructions"],div[data-testid="InputInstructions"]{display:none!important;visibility:hidden!important;opacity:0!important;height:0!important;padding:0!important;margin:0!important;}';
        c += '.material-symbols-rounded,.material-symbols-outlined,[data-testid*="Icon"]{font-family:"Material Symbols Rounded","Material Symbols Outlined"!important;font-size:20px!important;line-height:1!important;letter-spacing:normal!important;text-transform:none!important;display:inline-block!important;white-space:nowrap!important;-webkit-font-feature-settings:"liga"!important;font-feature-settings:"liga"!important;}';

        c += '#ap-canvas{position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:1;}';

        /* Smooth Radial Aurora Background Gradients */
        c += '#ap-o1{position:fixed;top:-120px;left:-100px;width:650px;height:650px;border-radius:50%;background:radial-gradient(circle,rgba(99,102,241,0.22) 0%,transparent 70%);filter:blur(90px);pointer-events:none;z-index:0;animation:ao1 16s ease-in-out infinite alternate;}';
        c += '#ap-o2{position:fixed;bottom:-120px;right:-100px;width:650px;height:650px;border-radius:50%;background:radial-gradient(circle,rgba(6,182,212,0.20) 0%,transparent 70%);filter:blur(90px);pointer-events:none;z-index:0;animation:ao2 20s ease-in-out infinite alternate;}';
        c += '#ap-spot{position:fixed;top:40%;left:50%;transform:translate(-50%,-50%);width:800px;height:600px;background:radial-gradient(ellipse at center,rgba(139,92,246,0.16) 0%,transparent 70%);filter:blur(80px);pointer-events:none;z-index:0;animation:aspot 12s ease-in-out infinite alternate;}';

        c += '@keyframes ao1{0%{transform:translate(0,0) scale(1);}100%{transform:translate(80px,60px) scale(1.1);}}';
        c += '@keyframes ao2{0%{transform:translate(0,0) scale(1);}100%{transform:translate(-80px,-60px) scale(1.1);}}';
        c += '@keyframes aspot{0%{transform:translate(-50%,-50%) scale(0.95);}100%{transform:translate(-50%,-50%) scale(1.1);}}';

        c += '#ap-tl{position:fixed;top:0;left:0;right:0;height:2px;z-index:99999;pointer-events:none;background:linear-gradient(90deg,transparent,#6366f1 25%,#8b5cf6 50%,#06b6d4 75%,transparent);background-size:250% 100%;animation:atl 4s linear infinite;}';
        c += '@keyframes atl{0%{background-position:200% 0}100%{background-position:-200% 0}}';

        c += 'section[data-testid="stSidebar"]>div:first-child{background:rgba(2,5,18,0.96)!important;backdrop-filter:blur(40px) saturate(1.5)!important;-webkit-backdrop-filter:blur(40px) saturate(1.5)!important;border-right:1px solid rgba(255,255,255,0.07)!important;}';
        c += '[data-testid="stSidebarCollapseButton"],[data-testid="collapsedControl"]{display:none!important;}';
        c += '[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-inner){position:relative;z-index:10!important;}';
        s.textContent = c; d.head.appendChild(s);
    }

    ['ap-o1','ap-o2','ap-spot','ap-tl'].forEach(function(id){
        if(!d.getElementById(id)){var e=d.createElement('div');e.id=id;d.body.insertBefore(e,d.body.firstChild);}
    });

    /* Live HTML5 Particle & Neural Network Animation Canvas */
    if (!d.getElementById('ap-canvas')) {
        var cv = d.createElement('canvas');
        cv.id = 'ap-canvas';
        d.body.insertBefore(cv, d.body.firstChild);

        var ctx = cv.getContext('2d');
        var W, H;
        var particles = [];
        var numP = 75;
        var mouse = {x: null, y: null, maxDist: 140};

        function resize() {
            W = cv.width = window.parent.innerWidth;
            H = cv.height = window.parent.innerHeight;
        }
        resize();
        window.parent.addEventListener('resize', resize);

        window.parent.addEventListener('mousemove', function(e) {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
        });
        window.parent.addEventListener('mouseout', function() {
            mouse.x = null;
            mouse.y = null;
        });

        var colors = [
            'rgba(99, 102, 241, ',   // Indigo
            'rgba(6, 182, 212, ',    // Cyan
            'rgba(168, 85, 247, ',   // Violet
            'rgba(16, 185, 129, '    // Emerald
        ];

        for (var i = 0; i < numP; i++) {
            particles.push({
                x: Math.random() * W,
                y: Math.random() * H,
                vx: (Math.random() - 0.5) * 1.2,
                vy: (Math.random() - 0.5) * 1.2,
                r: Math.random() * 2.2 + 1.2,
                color: colors[Math.floor(Math.random() * colors.length)],
                pulse: Math.random() * Math.PI,
                pulseSpeed: Math.random() * 0.03 + 0.015
            });
        }

        function draw() {
            ctx.clearRect(0, 0, W, H);

            // Update & draw particles
            for (var i = 0; i < particles.length; i++) {
                var p = particles[i];
                p.x += p.vx;
                p.y += p.vy;
                p.pulse += p.pulseSpeed;

                if (p.x < 0 || p.x > W) p.vx *= -1;
                if (p.y < 0 || p.y > H) p.vy *= -1;

                var alpha = 0.5 + Math.sin(p.pulse) * 0.35;
                var currentR = p.r + Math.sin(p.pulse) * 0.6;

                // Particle glow
                ctx.beginPath();
                ctx.arc(p.x, p.y, currentR, 0, Math.PI * 2);
                ctx.fillStyle = p.color + alpha + ')';
                ctx.shadowBlur = 12;
                ctx.shadowColor = p.color + '0.9)';
                ctx.fill();
                ctx.shadowBlur = 0;

                // Connect particles to nearby particles
                for (var j = i + 1; j < particles.length; j++) {
                    var p2 = particles[j];
                    var dx = p.x - p2.x;
                    var dy = p.y - p2.y;
                    var dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < 125) {
                        var lineAlpha = (1 - dist / 125) * 0.28;
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = p.color + lineAlpha + ')';
                        ctx.lineWidth = 0.9;
                        ctx.stroke();
                    }
                }

                // Interactive mouse connection
                if (mouse.x !== null && mouse.y !== null) {
                    var mdx = p.x - mouse.x;
                    var mdy = p.y - mouse.y;
                    var mdist = Math.sqrt(mdx * mdx + mdy * mdy);

                    if (mdist < mouse.maxDist) {
                        var mAlpha = (1 - mdist / mouse.maxDist) * 0.45;
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(mouse.x, mouse.y);
                        ctx.strokeStyle = 'rgba(129, 140, 248, ' + mAlpha + ')';
                        ctx.lineWidth = 1.2;
                        ctx.stroke();
                    }
                }
            }

            requestAnimationFrame(draw);
        }
        draw();
    }
})();
</script>
""", height=0)

# ─── Store Categories Datasets Catalog ────────────────────────────────────────
STORE_DATASETS = {
    "🏪 General Retail (73.1K rows)": ("retail_store.csv", "general"),
    "🛒 Supermarket & Grocery (15.0K rows)": ("supermarket_grocery_store.csv", "grocery"),
    "📱 Electronics & Gadgets (12.0K rows)": ("electronics_gadgets_store.csv", "electronics"),
}

def get_active_csv_path():
    fname = st.session_state.get("dataset_file", "retail_store.csv")
    if os.path.isabs(fname):
        return fname
    return os.path.join(BASE_DIR, "Data", fname)

# ─── Dynamic DuckDB Data Loaders (Works with any store category CSV) ──────────
@st.cache_data(show_spinner=False)
def load_sales(csv_path):
    con = duckdb.connect()
    df_raw = pd.read_csv(csv_path)
    con.register("raw_csv", df_raw)
    res = con.execute("""
        WITH cleaned AS (
            SELECT 
                CAST(strptime(CAST("Date" AS VARCHAR), '%d-%m-%Y') AS DATE) AS sale_date,
                CAST("Store ID" AS VARCHAR) AS store_id,
                CAST("Product ID" AS VARCHAR) AS product_id,
                CAST("Category" AS VARCHAR) AS category,
                CAST("Inventory Level" AS INTEGER) AS inventory_level,
                CAST("Units Sold" AS INTEGER) AS units_sold,
                CAST("Price" AS DOUBLE) AS price,
                CAST(COALESCE("Discount", 0) AS DOUBLE) AS discount
            FROM raw_csv
        ),
        fct AS (
            SELECT 
                sale_date, store_id, product_id, category,
                (units_sold * price * (1.0 - discount / 100.0)) AS revenue,
                units_sold,
                GREATEST(0, units_sold - inventory_level) AS stock_gap,
                (units_sold * 1.0 / NULLIF(units_sold + GREATEST(0, units_sold - inventory_level), 0)) AS fulfillment_rate
            FROM cleaned
        )
        SELECT 
            sale_date, store_id, category,
            SUM(revenue) AS total_revenue,
            SUM(units_sold) AS total_units,
            AVG(stock_gap) AS avg_stock_gap,
            AVG(COALESCE(fulfillment_rate, 1.0)) AS avg_fulfillment
        FROM fct
        GROUP BY 1, 2, 3
    """).df()
    con.close()
    return res

@st.cache_data(show_spinner=False)
def load_alerts(csv_path):
    con = duckdb.connect()
    df_raw = pd.read_csv(csv_path)
    con.register("raw_csv", df_raw)
    res = con.execute("""
        WITH daily AS (
            SELECT 
                CAST("Store ID" AS VARCHAR) AS store_id,
                CAST("Product ID" AS VARCHAR) AS product_id,
                CAST("Category" AS VARCHAR) AS category,
                AVG(CAST("Inventory Level" AS DOUBLE)) AS avg_inventory,
                AVG(CAST("Units Sold" AS DOUBLE)) AS avg_units_sold,
                SUM(CAST("Units Sold" AS DOUBLE) * CAST("Price" AS DOUBLE) * (1.0 - CAST(COALESCE("Discount", 0) AS DOUBLE) / 100.0)) AS total_revenue,
                AVG(CAST("Units Sold" AS DOUBLE) * 1.0 / NULLIF(CAST("Units Sold" AS DOUBLE) + GREATEST(0, CAST("Units Sold" AS DOUBLE) - CAST("Inventory Level" AS DOUBLE)), 0)) AS avg_fulfillment
            FROM raw_csv
            GROUP BY 1, 2, 3
        ),
        metrics AS (
            SELECT *,
                (avg_inventory / NULLIF(avg_units_sold, 0)) AS days_of_stock,
                (1.0 - COALESCE(avg_fulfillment, 1.0)) * 100.0 AS urgency_score,
                CASE 
                    WHEN (avg_inventory / NULLIF(avg_units_sold, 0)) < 30 THEN 'UNDERSTOCK'
                    WHEN (avg_inventory / NULLIF(avg_units_sold, 0)) > 120 THEN 'OVERSTOCK'
                    ELSE 'HEALTHY'
                END AS alert_status
            FROM daily
        )
        SELECT * FROM metrics
    """).df()
    con.close()
    return res

@st.cache_data(show_spinner=False)
def load_forecast(csv_path):
    con = duckdb.connect()
    df_raw = pd.read_csv(csv_path)
    con.register("raw_csv", df_raw)
    res = con.execute("""
        SELECT 
            CAST(strptime(CAST("Date" AS VARCHAR), '%d-%m-%Y') AS DATE) AS sale_date,
            CAST("Category" AS VARCHAR) AS category,
            CAST(COALESCE("Seasonality", 'All') AS VARCHAR) AS seasonality,
            CAST(COALESCE("Weather Condition", 'Normal') AS VARCHAR) AS weather_condition,
            CAST(COALESCE("Holiday/Promotion", 0) AS INTEGER) AS holiday_promotion,
            SUM(CAST("Units Sold" AS DOUBLE)) AS actual_units,
            SUM(CAST(COALESCE("Demand Forecast", "Units Sold") AS DOUBLE)) AS forecasted_units,
            AVG(CAST("Units Sold" AS DOUBLE) - CAST(COALESCE("Demand Forecast", "Units Sold") AS DOUBLE)) AS forecast_error,
            AVG(CAST("Units Sold" AS DOUBLE) * 1.0 / NULLIF(CAST("Units Sold" AS DOUBLE) + GREATEST(0, CAST("Units Sold" AS DOUBLE) - CAST("Inventory Level" AS DOUBLE)), 0)) AS avg_fulfillment
        FROM raw_csv
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY sale_date
    """).df()
    con.close()
    return res

# ─── UI Helpers ───────────────────────────────────────────────────────────────
def format_curr_val(amount, cur):
    """Smart human-readable formatting for currency values."""
    if amount >= 1e12:
        return f"{cur}{amount/1e12:,.2f}T"
    elif amount >= 1e9:
        return f"{cur}{amount/1e9:,.2f}B"
    elif amount >= 1e6:
        return f"{cur}{amount/1e6:,.2f}M"
    elif amount >= 1e3:
        return f"{cur}{amount/1e3:,.1f}K"
    else:
        return f"{cur}{amount:,.2f}"
def page_header(title, subtitle, color="#6366f1"):
    st.markdown(f"""
    <div class="pg-header">
        <div class="pg-header-bar" style="background:linear-gradient(180deg,{color},{color}00);box-shadow:0 0 14px {color}55;"></div>
        <div><h1>{title}</h1><p>{subtitle}</p></div>
    </div>""", unsafe_allow_html=True)

def kpi_card(label, value, delta="", icon="", color_cls="ci", delta_up=True):
    d_html = f'<div class="kpi-delta {"up" if delta_up else "down"}>{"▲" if delta_up else "▼"} {delta}</div>' if delta else ""
    st.markdown(f'<div class="kpi-card {color_cls}"><div class="kpi-label">{icon} {label}</div><div class="kpi-value">{value}</div>{d_html}</div>', unsafe_allow_html=True)

def section_title(text, color="#6366f1"):
    st.markdown(f'<div class="sec-title"><div class="sec-bar" style="background:linear-gradient(180deg,{color},{color}44);box-shadow:0 0 8px {color}66;"></div><h3>{text}</h3></div>', unsafe_allow_html=True)

def step_header(num, title):
    st.markdown(f'<div class="step-row"><span class="step-num">{num}</span><h3>{title}</h3></div>', unsafe_allow_html=True)

def alert_badge(status):
    cls  = {"UNDERSTOCK":"under","OVERSTOCK":"over","HEALTHY":"healthy"}.get(status,"unknown")
    icon = {"UNDERSTOCK":"⚠","OVERSTOCK":"📦","HEALTHY":"✓"}.get(status,"?")
    return f'<span class="badge {cls}">{icon} {status}</span>'

def banner(msg, kind="inf"):
    st.markdown(f'<div class="banner {kind}">{msg}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH GATE — Show login/register if not logged in
# ══════════════════════════════════════════════════════════════════════════════
def show_auth_page():
    """Centered, beautifully structured login / register page."""
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        with st.container(border=True):
            st.markdown("""
            <div class="auth-card-inner">
                <div class="auth-header">
                    <div class="auth-logo-icon">📦</div>
                    <h1 class="auth-title">InvenSight</h1>
                    <p class="auth-subtitle">Smart Retail Stock Analytics & Demand Forecasting</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            tab = st.session_state.get("auth_tab", "login")

            col_l, col_r = st.columns(2)
            with col_l:
                if st.button("🔑  Login", use_container_width=True,
                             type="primary" if tab == "login" else "secondary",
                             key="tab_login_btn"):
                    st.session_state["auth_tab"] = "login"
                    st.rerun()
            with col_r:
                if st.button("✨  Create Account", use_container_width=True,
                             type="primary" if tab == "register" else "secondary",
                             key="tab_register_btn"):
                    st.session_state["auth_tab"] = "register"
                    st.rerun()

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            if tab == "login":
                st.markdown('<p style="color:#cbd5e1;font-size:0.85rem;margin-bottom:0.8rem;text-align:center;">Enter your credentials to access store analytics.</p>', unsafe_allow_html=True)
                email    = st.text_input("Email Address", placeholder="name@example.com", key="login_email")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                if st.button("Sign In to Dashboard →", use_container_width=True, key="login_submit"):
                    if not email or not password:
                        banner("Please fill in both email and password.", "err")
                    else:
                        result = login_user(email, password)
                        if result["ok"]:
                            user = result["user"]
                            st.session_state["user"]       = user
                            st.session_state["session_id"] = new_session_id()
                            log_activity(user["id"], "Login", "User logged in", st.session_state["session_id"])
                            st.rerun()
                        else:
                            banner(f"❌ {result['error']}", "err")

                st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
                st.markdown('<p style="color:#64748b;font-size:0.8rem;text-align:center;margin:0;">New here? Click <strong style="color:#818cf8;">Create Account</strong> above.</p>', unsafe_allow_html=True)

            else:  # register
                st.markdown('<p style="color:#cbd5e1;font-size:0.85rem;margin-bottom:0.8rem;text-align:center;">Register an account for retail insights.</p>', unsafe_allow_html=True)
                name     = st.text_input("Full Name", placeholder="Enter your full name", key="reg_name")
                email    = st.text_input("Email Address", placeholder="name@example.com", key="reg_email")
                password = st.text_input("Password (min 6 chars)", type="password", placeholder="Choose a secure password", key="reg_pass")
                password2 = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="reg_pass2")
                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                if st.button("Create Account & Enter →", use_container_width=True, key="reg_submit"):
                    if not name or not email or not password:
                        banner("Please fill in all fields.", "err")
                    elif password != password2:
                        banner("❌ Passwords do not match.", "err")
                    else:
                        result = register_user(name, email, password)
                        if result["ok"]:
                            user = result["user"]
                            st.session_state["user"]       = user
                            st.session_state["session_id"] = new_session_id()
                            log_activity(user["id"], "Register", "New account created", st.session_state["session_id"])
                            banner("✅ Account created successfully! Welcome.", "ok")
                            st.rerun()
                        else:
                            banner(f"❌ {result['error']}", "err")

            st.markdown("""
            <div class="auth-footer-pills">
                <span>⚡ Live Stock Telemetry</span>
                <span>•</span>
                <span>🤖 AI Demand Models</span>
                <span>•</span>
                <span>🛡️ Enterprise Security</span>
            </div>
            """, unsafe_allow_html=True)


# ─── Check session ────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    show_auth_page()
    st.stop()

# ─── Logged-in user shortcuts ─────────────────────────────────────────────────
CURRENT_USER = st.session_state["user"]
IS_ADMIN     = CURRENT_USER.get("role") == "admin"
SESSION_ID   = st.session_state.get("session_id", "")


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR (only shown after login)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    biz_icon = L.get("icon", "📦")
    biz_name = L.get("business_name", "InvenSight")
    biz_type = L.get("business_type", "Smart Stock Analytics")

    st.markdown(f"""
    <div style="text-align:center;padding:1.4rem 0 1.5rem;">
        <div style="display:inline-flex;align-items:center;justify-content:center;width:56px;height:56px;border-radius:16px;font-size:1.8rem;background:linear-gradient(135deg,rgba(99,102,241,0.18),rgba(139,92,246,0.12));border:1px solid rgba(99,102,241,0.3);margin-bottom:0.8rem;box-shadow:0 4px 24px rgba(99,102,241,0.22);">{biz_icon}</div>
        <h2 style="font-family:'Sora',sans-serif;font-size:1.1rem;font-weight:700;margin:0;letter-spacing:-0.03em;color:#f1f5f9;">{biz_name}</h2>
        <p style="color:#475569;font-size:0.68rem;margin:0.25rem 0 0.8rem;font-family:'Inter',sans-serif;">{biz_type}</p>
        <div style="width:28px;height:1.5px;margin:0 auto;background:linear-gradient(90deg,#6366f1,#06b6d4);border-radius:2px;"></div>
    </div>
    """, unsafe_allow_html=True)

    # Logged-in user pill
    role_cls  = "admin-pill" if IS_ADMIN else ""
    role_icon = "👑" if IS_ADMIN else "👤"
    st.markdown(f'<div class="user-pill {role_cls}" style="margin-bottom:1rem;">{role_icon} {CURRENT_USER["name"]}</div>', unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.6rem;color:#334155;text-transform:uppercase;letter-spacing:0.15em;margin-bottom:0.4rem;font-weight:700;font-family:Inter,sans-serif;">Navigation</p>', unsafe_allow_html=True)

    nav_options = [
        "📈  Sales Overview",
        "🚨  Stock Alerts",
        "📊  Demand Forecast",
        "⚙️  Setup & Configure",
    ]
    if IS_ADMIN:
        nav_options.append("🛡️  Admin Panel")

    page = st.radio("nav", nav_options, label_visibility="collapsed")

    # ── Currency Mode Selector (Single Line Row) ──
    c_col1, c_col2 = st.columns([1, 1.35])
    with c_col1:
        st.markdown('<div style="padding-top:0.35rem;font-size:0.75rem;color:#cbd5e1;font-weight:700;font-family:Inter,sans-serif;">💱 Currency</div>', unsafe_allow_html=True)
    with c_col2:
        currency_options = ["₹ INR (₹)", "$ USD ($)", "€ EUR (€)", "£ GBP (£)"]
        default_curr = st.session_state.get("active_currency", "₹")
        default_idx = 0 if default_curr == "₹" else (1 if default_curr == "$" else (2 if default_curr == "€" else 3))
        selected_curr_str = st.selectbox("Currency Mode", currency_options, index=default_idx, label_visibility="collapsed", key="curr_selector_sidebar")
        cur = selected_curr_str.split()[0]
        st.session_state["active_currency"] = cur

    # ── Active Dataset Pill & Switcher ──
    d_name = st.session_state.get("dataset_name", "Sample Retail Dataset")
    d_rows = st.session_state.get("dataset_rows", 73100)
    st.markdown(f'<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.25);border-radius:12px;padding:0.6rem 0.8rem;margin:1rem 0 0.5rem;font-size:0.75rem;"><div style="color:#94a3b8;font-size:0.65rem;text-transform:uppercase;font-weight:700;">Active Dataset</div><div style="color:#f1f5f9;font-weight:600;margin:0.2rem 0;">📄 {d_name[:22]}</div><div style="color:#34d399;font-size:0.7rem;">● {d_rows:,} rows loaded</div></div>', unsafe_allow_html=True)
    if st.button("🔄  Upload / Change Dataset", key="switch_dataset_sidebar_btn", use_container_width=True):
        st.session_state["dataset_loaded"] = False
        st.rerun()

    st.markdown("---")

    if st.button("🚪  Logout", key="logout_btn"):
        log_activity(CURRENT_USER["id"], "Logout", "User logged out", SESSION_ID)
        for k in ["user","session_id","auth_tab","dataset_loaded","dataset_name"]:
            st.session_state.pop(k, None)
        st.rerun()


# ─── Dataset Gateway Check ───────────────────────────────────────────────────
if not st.session_state.get("dataset_loaded", False):
    page_header("Data Gateway", "Upload your custom retail dataset or select from 7 pre-built store category datasets.", "#6366f1")
    
    col_u, col_s = st.columns(2)
    with col_u:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align:center;padding:1rem 0.5rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">📤</div>
                <h3 style="margin:0 0 0.4rem;color:#f1f5f9;">Upload Custom Store CSV</h3>
                <p style="color:#94a3b8;font-size:0.82rem;margin-bottom:1rem;">Upload any store transaction CSV to generate custom sales telemetry and stock alerts.</p>
            </div>
            """, unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="gateway_csv_uploader")
            if uploaded_file is not None:
                try:
                    df_up = pd.read_csv(uploaded_file)
                    save_path = os.path.join(BASE_DIR, "Data", uploaded_file.name)
                    df_up.to_csv(save_path, index=False)
                    st.session_state["dataset_loaded"] = True
                    st.session_state["dataset_name"] = uploaded_file.name
                    st.session_state["dataset_file"] = uploaded_file.name
                    st.session_state["dataset_rows"] = len(df_up)
                    st.session_state["dataset_type"] = "uploaded"
                    st.success(f"✅ Successfully loaded {uploaded_file.name} ({len(df_up):,} rows)!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error loading CSV: {e}")

    with col_s:
        with st.container(border=True):
            st.markdown("""
            <div style="text-align:center;padding:1rem 0.5rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">🏪</div>
                <h3 style="margin:0 0 0.4rem;color:#f1f5f9;">Choose Store Category Dataset</h3>
                <p style="color:#94a3b8;font-size:0.82rem;margin-bottom:1rem;">Select from 7 authentic pre-built Kaggle store category datasets to test analytics models.</p>
            </div>
            """, unsafe_allow_html=True)
            
            cat_choice = st.selectbox("Store Category Dataset", list(STORE_DATASETS.keys()), key="store_cat_choice_gateway")
            chosen_file, chosen_profile = STORE_DATASETS[cat_choice]
            
            if st.button(f"🚀  Load {cat_choice.split()[0]} {cat_choice.split()[1]} Dataset →", use_container_width=True, type="primary", key="load_category_dataset_btn"):
                st.session_state["dataset_loaded"] = True
                st.session_state["dataset_name"] = cat_choice
                st.session_state["dataset_file"] = chosen_file
                st.session_state["dataset_profile"] = chosen_profile
                st.session_state["selected_profile_type"] = chosen_profile
                st.session_state["dataset_rows"] = sum(1 for _ in open(os.path.join(BASE_DIR, "Data", chosen_file))) - 1
                st.rerun()
    st.stop()


# ─── Active Currency & Exchange Rates ─────────────────────────────────────────
CURRENCY_RATES = {
    "₹": 83.50,    # 1 USD = 83.50 INR
    "$": 1.00,     # Base USD
    "€": 0.92,     # 1 USD = 0.92 EUR
    "£": 0.79      # 1 USD = 0.79 GBP
}
CUR = st.session_state.get("active_currency", "₹")
RATE = CURRENCY_RATES.get(CUR, 83.50)
log_activity(CURRENT_USER["id"], page, f"Viewed in {CUR}", SESSION_ID)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — SALES OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "📈  Sales Overview":
    cur = CUR
    page_header("Sales Overview",
        f"{L['revenue']}, volume, and fulfilment performance across all {L['stores']} and {L['category'].lower()}s (in {cur}).",
        "#6366f1")
    with st.spinner("Loading..."):
        df = load_sales(get_active_csv_path()).copy()
        df['total_revenue'] = df['total_revenue'] * RATE

    col1,col2,col3,col4 = st.columns(4)
    with col1: kpi_card(f"Total {L['revenue']}", format_curr_val(df['total_revenue'].sum(), cur), icon="💰", color_cls="ci")
    with col2: kpi_card(f"{L['units']} Sold", f"{df['total_units'].sum()/1e6:,.1f}M", icon="📦", color_cls="cc")
    with col3: kpi_card("Avg Fulfillment", f"{df['avg_fulfillment'].mean():.1%}", icon="✅", color_cls="ce")
    with col4: kpi_card("Avg Stock Gap", f"{df['avg_stock_gap'].mean():.0f} u", icon="📉", color_cls="ca")

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    col1,col2 = st.columns([3,2])
    with col1:
        section_title(f"Daily {L['revenue']} Trend ({cur}M)","#6366f1")
        daily = df.groupby('sale_date')['total_revenue'].sum().reset_index()
        daily[f'Revenue ({cur}M)'] = (daily['total_revenue'] / 1e6).round(2)
        st.line_chart(daily.set_index('sale_date')[[f'Revenue ({cur}M)']], color="#6366f1", height=320)
    with col2:
        section_title(f"{L['revenue']} by {L['category']} ({cur}M)","#06b6d4")
        cat = df.groupby('category')['total_revenue'].sum().sort_values().reset_index()
        cat[f'Revenue ({cur}M)'] = (cat['total_revenue'] / 1e6).round(2)
        st.bar_chart(cat.set_index('category')[[f'Revenue ({cur}M)']], color="#06b6d4", height=320)

    section_title(f"{L['store']} Performance Breakdown", "#f59e0b")
    store = df.groupby('store_id').agg(Revenue=('total_revenue','sum'),Units=('total_units','sum'),Fulfilment=('avg_fulfillment','mean')).reset_index()
    store[f'{L["revenue"]} ({cur}M)'] = (store['Revenue']/1e6).round(2)
    store['Fulfilment %'] = (store['Fulfilment']*100).round(1)
    store[f'{L["units"]} (M)'] = (store['Units']/1e6).round(2)
    st.dataframe(
        store[['store_id',f'{L["revenue"]} ({cur}M)',f'{L["units"]} (M)','Fulfilment %']]
             .rename(columns={'store_id':L['store']}).sort_values(f'{L["revenue"]} ({cur}M)',ascending=False).reset_index(drop=True)
             .style.background_gradient(subset=[f'{L["revenue"]} ({cur}M)'],cmap='Blues')
                   .background_gradient(subset=['Fulfilment %'],cmap='Greens')
                   .format({f'{L["revenue"]} ({cur}M)':'{:.2f}',f'{L["units"]} (M)':'{:.2f}','Fulfilment %':'{:.1f}%'}),
        width='stretch',hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — STOCK ALERTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🚨  Stock Alerts":
    cur = CUR
    page_header(f"{L['inventory']} Alert Monitor",
        f"UNDERSTOCK: < 30 days supply  ·  OVERSTOCK: > 120 days supply  ·  Amounts in {cur}",
        "#f43f5e")
    with st.spinner("Loading..."):
        alerts = load_alerts(get_active_csv_path()).copy()
        if 'total_revenue' in alerts.columns:
            alerts['total_revenue'] = alerts['total_revenue'] * RATE

    total=len(alerts); under=(alerts['alert_status']=='UNDERSTOCK').sum(); over=(alerts['alert_status']=='OVERSTOCK').sum(); healthy=(alerts['alert_status']=='HEALTHY').sum()
    col1,col2,col3,col4 = st.columns(4)
    with col1: kpi_card(f"Total {L['products']}",f"{total:,}",icon="🗂️",color_cls="ci")
    with col2: kpi_card("Understock",f"{under:,}",f"{under/total:.1%} of total",icon="🔴",color_cls="cr",delta_up=False)
    with col3: kpi_card("Overstock",f"{over:,}",f"{over/total:.1%} of total",icon="🟡",color_cls="ca",delta_up=False)
    with col4: kpi_card("Healthy",f"{healthy:,}",f"{healthy/total:.1%} of total",icon="🟢",color_cls="ce",delta_up=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    col1,col2,col3 = st.columns([1,1,2])
    with col1: status_filter=st.selectbox("Alert Status",["All","UNDERSTOCK","OVERSTOCK","HEALTHY","UNKNOWN"])
    with col2: store_filter=st.selectbox(L['store'],["All"]+sorted(alerts['store_id'].dropna().unique().tolist()))
    with col3: cat_filter=st.multiselect(L['category'],sorted(alerts['category'].dropna().unique().tolist()),default=[])

    filtered=alerts.copy()
    if status_filter!="All": filtered=filtered[filtered['alert_status']==status_filter]
    if store_filter!="All":  filtered=filtered[filtered['store_id']==store_filter]
    if cat_filter:           filtered=filtered[filtered['category'].isin(cat_filter)]

    st.markdown(f'<p style="color:#94a3b8;font-size:0.85rem;margin:0.5rem 0;">{len(filtered):,} {L["products"].lower()} match your filters</p>', unsafe_allow_html=True)
    display=filtered[['store_id','product_id','category','alert_status','days_of_stock','avg_inventory','avg_units_sold','urgency_score','avg_fulfillment','total_revenue']].copy()
    display.columns=[L['store'],L['product'],L['category'],'Status','Days of Stock',f'Avg {L["inventory"]}',f'Avg {L["units"]} Sold','Urgency Score','Fulfilment Rate',f'{L["revenue"]} ({cur})']
    def colour_status(v):
        return {
            'UNDERSTOCK': 'background-color:rgba(244,63,94,0.22);color:#fb7185;font-weight:700',
            'OVERSTOCK':  'background-color:rgba(245,158,11,0.22);color:#fbbf24;font-weight:700',
            'HEALTHY':    'background-color:rgba(16,185,129,0.22);color:#4ade80;font-weight:700',
            'UNKNOWN':    'background-color:rgba(148,163,184,0.15);color:#e2e8f0;font-weight:600',
        }.get(v,'')
    st.dataframe(display.style.map(colour_status,subset=['Status']).background_gradient(subset=['Urgency Score'],cmap='Reds').format({'Days of Stock':'{:.1f}',f'Avg {L["inventory"]}':'{:.0f}',f'Avg {L["units"]} Sold':'{:.0f}','Urgency Score':'{:.1f}','Fulfilment Rate':'{:.1%}',f'{L["revenue"]} ({cur})':'{:,.0f}'}),width='stretch',height=380,hide_index=True)

    st.markdown("---")
    col1,col2=st.columns(2)
    with col1:
        section_title(f"Alert Distribution by {L['category']}","#f43f5e")
        pivot=alerts.groupby(['category','alert_status']).size().unstack(fill_value=0)
        st.bar_chart(pivot,height=260)
    with col2:
        section_title("Top 10 Most Urgent (Understock)","#f59e0b")
        top=alerts[alerts['alert_status']=='UNDERSTOCK'].nsmallest(10,'days_of_stock')[['product_id','store_id','category','days_of_stock','urgency_score']].reset_index(drop=True)
        top.columns=[L['product'],L['store'],L['category'],'Days of Stock','Urgency Score']
        if top.empty: banner("No understock products — great news! 🎉","ok")
        else: st.dataframe(top.style.background_gradient(subset=['Urgency Score'],cmap='Reds').format({'Days of Stock':'{:.1f}','Urgency Score':'{:.1f}'}),width='stretch',height=260,hide_index=True)

    st.markdown("---")
    csv=filtered[['store_id','product_id','category','alert_status','days_of_stock','urgency_score','avg_fulfillment','total_revenue']].to_csv(index=False).encode('utf-8')
    st.download_button("⬇️  Download Alert Report (CSV)",data=csv,file_name="invensight_stock_alerts.csv",mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — DEMAND FORECAST
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊  Demand Forecast":
    cur = CUR
    page_header("Demand Forecast Analysis",
        f"Actual vs forecasted {L['units'].lower()} sold — with seasonal, weather, and holiday breakdowns ({cur}).",
        "#06b6d4")
    with st.spinner("Loading..."):
        df=load_forecast(get_active_csv_path()).copy()
    df['sale_date']=pd.to_datetime(df['sale_date'])
    total_actual=df['actual_units'].sum(); total_forecast=df['forecasted_units'].sum()
    accuracy=1-abs(total_actual-total_forecast)/(total_forecast or 1); avg_error=df['forecast_error'].mean()

    col1,col2,col3,col4=st.columns(4)
    with col1: kpi_card(f"Actual {L['units']} Sold",f"{total_actual/1e6:.2f}M",icon="📦",color_cls="cc")
    with col2: kpi_card(f"Forecasted {L['units']}",f"{total_forecast/1e6:.2f}M",icon="🎯",color_cls="ce")
    with col3: kpi_card("Forecast Accuracy",f"{accuracy:.1%}",icon="✅",color_cls="ci")
    with col4: kpi_card("Avg Daily Error",f"{avg_error:+.0f} units",delta="+ = under-forecast (stockout risk)",icon="📉",color_cls="ca",delta_up=avg_error>=0)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    section_title(f"Actual vs Forecasted {L['units']} — Weekly Trend (M)","#06b6d4")
    trend=df.set_index('sale_date')[['actual_units','forecasted_units']].resample('W').sum()
    trend[f'Actual {L["units"]} (M)'] = (trend['actual_units']/1e6).round(2)
    trend['Demand Forecast (M)'] = (trend['forecasted_units']/1e6).round(2)
    st.line_chart(trend[[f'Actual {L["units"]} (M)', 'Demand Forecast (M)']], height=320, color=["#06b6d4","#6366f1"])

    st.markdown("---")
    col1,col2=st.columns(2)
    with col1:
        section_title("Avg Units by Season","#8b5cf6")
        season=df.groupby('seasonality')[['actual_units','forecasted_units']].mean().rename(columns={'actual_units':'Actual','forecasted_units':'Forecast'})
        season_reset = season.reset_index()
        season_melt = season_reset.melt(id_vars='seasonality', var_name='Type', value_name='Avg Units')
        fig_s = px.bar(season_melt, x='Avg Units', y='seasonality', color='Type',
                       orientation='h', barmode='group', height=280,
                       color_discrete_map={'Actual': '#8b5cf6', 'Forecast': '#06b6d4'})
        fig_s.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font_color='#94a3b8', margin=dict(l=0, r=10, t=10, b=10),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                            yaxis=dict(gridcolor='rgba(0,0,0,0)', title=''),
                            legend=dict(orientation='h', yanchor='bottom', y=-0.3))
        st.plotly_chart(fig_s, use_container_width=True)
    with col2:
        section_title("Avg Units by Weather","#8b5cf6")
        weather=df.groupby('weather_condition')[['actual_units','forecasted_units']].mean().rename(columns={'actual_units':'Actual','forecasted_units':'Forecast'})
        weather_reset = weather.reset_index()
        weather_melt = weather_reset.melt(id_vars='weather_condition', var_name='Type', value_name='Avg Units')
        fig_w = px.bar(weather_melt, x='Avg Units', y='weather_condition', color='Type',
                       orientation='h', barmode='group', height=280,
                       color_discrete_map={'Actual': '#8b5cf6', 'Forecast': '#06b6d4'})
        fig_w.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font_color='#94a3b8', margin=dict(l=0, r=10, t=10, b=10),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                            yaxis=dict(gridcolor='rgba(0,0,0,0)', title=''),
                            legend=dict(orientation='h', yanchor='bottom', y=-0.3))
        st.plotly_chart(fig_w, use_container_width=True)

    st.markdown("---")
    section_title("Holiday / Promotion Impact","#f59e0b")
    holiday=df.groupby('holiday_promotion')[['actual_units','forecasted_units','avg_fulfillment']].mean()
    holiday.index=holiday.index.map({0:'Regular Day',1:'Holiday / Promo'})
    holiday.columns=[f'Actual {L["units"]}','Demand Forecast','Fulfillment Rate']
    col1,col2=st.columns([1,2])
    with col1:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.dataframe(holiday.style.background_gradient(subset=[f'Actual {L["units"]}'],cmap='Oranges').format({f'Actual {L["units"]}':'{:.0f}','Demand Forecast':'{:.0f}','Fulfillment Rate':'{:.1%}'}),width='stretch')
    with col2:
        hol_plot = holiday[[f'Actual {L["units"]}','Demand Forecast']].reset_index()
        hol_melt = hol_plot.melt(id_vars='holiday_promotion', var_name='Type', value_name='Value')
        fig_h = px.bar(hol_melt, x='Value', y='holiday_promotion', color='Type',
                       orientation='h', barmode='group', height=200,
                       color_discrete_map={f'Actual {L["units"]}': '#f59e0b', 'Demand Forecast': '#6366f1'})
        fig_h.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font_color='#94a3b8', margin=dict(l=0, r=10, t=10, b=10),
                            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                            yaxis=dict(gridcolor='rgba(0,0,0,0)', title=''),
                            legend=dict(orientation='h', yanchor='bottom', y=-0.3))
        st.plotly_chart(fig_h, use_container_width=True)

    st.markdown("---")
    section_title("Daily Forecast Error Trend (Weekly Avg)","#f43f5e")
    _err_series = df.set_index('sale_date')['forecast_error'].resample('W').mean().reset_index()
    _err_series.columns = ['Date', 'Forecast Error']
    import plotly.graph_objects as go
    fig_err = go.Figure()
    fig_err.add_trace(go.Scatter(
        x=_err_series['Date'], y=_err_series['Forecast Error'],
        fill='tozeroy',
        line=dict(color='#f43f5e', width=1.5),
        fillcolor='rgba(244,63,94,0.25)',
        mode='lines',
        name='Forecast Error'
    ))
    fig_err.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8', height=220,
        margin=dict(l=0, r=10, t=10, b=10),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True,
                   autorange=True, zeroline=True,
                   zerolinecolor='rgba(255,255,255,0.2)', zerolinewidth=1),
        showlegend=False
    )
    st.plotly_chart(fig_err, use_container_width=True)
    st.markdown('<p style="color:#94a3b8;font-size:0.82rem;">Positive = actual > forecast (under-stocking risk). Negative = actual < forecast (over-stocking risk).</p>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 4 — SETUP & CONFIGURE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️  Setup & Configure":
    page_header("Setup & Configure",
        "Adapt InvenSight to your business — pick your store type, map your data columns, and save.",
        "#6366f1")
    from config.settings import load_config as _lc, save_config as _sc
    current_cfg=_lc(BASE_DIR)

    step_header(1,"Choose Your Business Type")
    profile_keys=list(PROFILES.keys()); current_type=current_cfg.get("business",{}).get("type","general")
    selected_type=st.session_state.get("selected_profile_type",current_type)
    for row in [profile_keys[i:i+4] for i in range(0,len(profile_keys),4)]:
        cols=st.columns(len(row))
        for col,key in zip(cols,row):
            p=PROFILES[key]; is_active=(selected_type==key)
            bc="rgba(99,102,241,0.7)" if is_active else "rgba(255,255,255,0.08)"
            bg="linear-gradient(135deg,rgba(99,102,241,0.2),rgba(20,184,166,0.12))" if is_active else "rgba(255,255,255,0.04)"
            with col:
                st.markdown(f'<div style="background:{bg};border:1.5px solid {bc};border-radius:14px;padding:1rem;text-align:center;transition:all 0.2s ease;margin-bottom:0.5rem;"><div style="font-size:2rem;margin-bottom:0.3rem;">{p["icon"]}</div><div style="font-weight:600;font-size:0.9rem;color:#e2e8f0;">{p["name"]}</div><div style="font-size:0.72rem;color:#64748b;margin-top:0.25rem;line-height:1.3;">{p["description"][:60]}…</div></div>',unsafe_allow_html=True)
                if st.button("Select",key=f"profile_btn_{key}"):
                    st.session_state["selected_profile_type"]=key; st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    selected_profile=PROFILES.get(selected_type,PROFILES.get("general",{}))
    if selected_type:
        cats=selected_profile.get("typical_categories",[])
        banner(f"<strong>{selected_profile.get('icon','')} {selected_profile.get('name','')}</strong> selected &nbsp;·&nbsp; Typical categories: {', '.join(cats[:4])}{'…' if len(cats)>4 else ''}","inf")

    step_header(2,"Business Details")
    col1,col2,col3=st.columns([2,1,1])
    with col1: biz_name_input=st.text_input("Business / Store Name",value=current_cfg.get("business",{}).get("name","My Retail Store"),placeholder="e.g. My Store…",key="biz_name_input")
    with col2: currency_input=st.text_input("Currency Symbol",value=current_cfg.get("business",{}).get("currency_symbol", CUR),placeholder="₹, $, €, £",max_chars=3,key="biz_currency_input")
    with col3:
        st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        st.markdown(f'<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:0.68rem 1rem;font-size:0.9rem;color:#94a3b8;">Preview: <strong style="color:#f1f5f9;">{currency_input or "₹"}1,234.56</strong></div>',unsafe_allow_html=True)

    step_header(3,"Data Source")
    source_mode=st.radio("Source type",["📁  File Path (CSV)","⬆️  Upload CSV"],horizontal=True,key="source_mode")
    csv_headers=[]; uploaded_path=None
    if source_mode=="📁  File Path (CSV)":
        csv_path_input=st.text_input("CSV File Path",value=current_cfg.get("source",{}).get("file","Data/retail_store.csv"),placeholder="Data/my_store.csv",key="csv_path_input")
        date_fmt_input=st.text_input("Date Format",value=current_cfg.get("source",{}).get("date_format","dd-MM-yyyy"),placeholder="dd-MM-yyyy",key="date_fmt_input")
        resolved=csv_path_input if os.path.isabs(csv_path_input) else os.path.join(BASE_DIR,csv_path_input)
        if os.path.isfile(resolved):
            try: csv_headers=list(pd.read_csv(resolved,nrows=0).columns); banner(f"✅ File found — {len(csv_headers)} columns detected","ok")
            except Exception as e: banner(f"❌ Could not read file: {e}","err")
        else: banner("⚠️ File not found at that path.","err")
        uploaded_path=csv_path_input
    else:
        uploaded_file=st.file_uploader("Upload your CSV file",type=["csv"],key="csv_uploader")
        date_fmt_input=st.text_input("Date Format",value=current_cfg.get("source",{}).get("date_format","dd-MM-yyyy"),placeholder="dd-MM-yyyy",key="date_fmt_upload")
        if uploaded_file is not None:
            try:
                csv_headers=list(pd.read_csv(uploaded_file,nrows=0).columns)
                save_dest=os.path.join(BASE_DIR,"Data",uploaded_file.name); uploaded_file.seek(0)
                with open(save_dest,"wb") as f_out: f_out.write(uploaded_file.read())
                uploaded_path=f"Data/{uploaded_file.name}"; banner(f"✅ Uploaded — {len(csv_headers)} columns · Saved to Data/{uploaded_file.name}","ok")
            except Exception as e: banner(f"❌ Could not parse CSV: {e}","err")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 5 — ADMIN PANEL (admin only)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🛡️  Admin Panel" and IS_ADMIN:
    page_header("Admin Panel",
        "User management, activity logs, and usage analytics across all registered users.",
        "#f59e0b")

    # ── Summary KPIs ─────────────────────────────────────────────────────────
    stats = get_usage_summary()
    col1,col2,col3,col4 = st.columns(4)
    with col1: kpi_card("Total Users",     str(stats["total_users"]),    icon="👥", color_cls="ci")
    with col2: kpi_card("Active Users",    str(stats["active_users"]),   icon="✅", color_cls="ce")
    with col3: kpi_card("Total Sessions",  str(stats["total_sessions"]), icon="🔗", color_cls="cc")
    with col4: kpi_card("Total Actions",   str(stats["total_actions"]),  icon="📋", color_cls="ca")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Page Popularity ───────────────────────────────────────────────────────
    if stats["page_stats"]:
        section_title("Most Visited Pages", "#6366f1")
        pg_df = pd.DataFrame(stats["page_stats"])
        fig_pages = px.bar(
            pg_df.sort_values('visits', ascending=True),
            x='visits', y='page', orientation='h',
            color_discrete_sequence=['#6366f1'],
            height=260
        )
        fig_pages.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#94a3b8',
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title='Visits'),
            yaxis=dict(gridcolor='rgba(0,0,0,0)', title=''),
            margin=dict(l=0, r=10, t=10, b=10),
            showlegend=False
        )
        fig_pages.update_traces(marker_color='#6366f1', marker_line_width=0)
        st.plotly_chart(fig_pages, use_container_width=True)

    st.markdown("---")

    # ── User Management ───────────────────────────────────────────────────────
    section_title("All Registered Users", "#06b6d4")
    users = get_all_users()
    if not users:
        banner("No users registered yet.", "inf")
    else:
        users_df = pd.DataFrame(users)
        users_df["Status"] = users_df["is_active"].map({1: "✅ Active", 0: "❌ Disabled"})
        users_df["Role"]   = users_df["role"].map({"admin": "👑 Admin", "user": "👤 User"})
        display_cols = ["name", "email", "Role", "Status", "created_at", "last_login"]
        display_df   = users_df[display_cols].rename(columns={
            "name": "Name", "email": "Email",
            "created_at": "Registered", "last_login": "Last Login"
        })
        st.dataframe(display_df, hide_index=True, width="stretch")

        # Toggle active/disabled
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        section_title("Enable / Disable User", "#f43f5e")
        non_admin_users = [u for u in users if u["role"] != "admin"]
        if non_admin_users:
            user_choices = {f"{u['name']} ({u['email']})": u["id"] for u in non_admin_users}
            selected_user_label = st.selectbox("Select User", list(user_choices.keys()), key="admin_toggle_user")
            selected_uid = user_choices[selected_user_label]
            selected_u   = next(u for u in non_admin_users if u["id"] == selected_uid)
            current_status = "Active ✅" if selected_u["is_active"] else "Disabled ❌"
            col1, col2 = st.columns([1, 3])
            with col1:
                action_label = "🔴 Disable" if selected_u["is_active"] else "🟢 Enable"
                if st.button(f"{action_label} User", key="admin_toggle_btn"):
                    toggle_user_active(selected_uid)
                    log_activity(CURRENT_USER["id"], "Admin Panel", f"Toggled user {selected_uid}", SESSION_ID)
                    banner(f"User status updated.", "ok")
                    st.rerun()
            with col2:
                st.markdown(f'<div style="padding:0.65rem;color:#94a3b8;font-size:0.875rem;">Current status: <strong>{current_status}</strong></div>', unsafe_allow_html=True)

        else:
            st.markdown(
                '<div style="background:rgba(99,102,241,0.08);border:1px dashed rgba(99,102,241,0.3);border-radius:10px;padding:1.2rem;text-align:center;color:#64748b;">'
                '<p style="font-size:1.5rem;margin:0">&#128100;</p>'
                '<p style="margin:0.5rem 0 0;font-size:0.9rem;">No non-admin users yet.<br><span style="font-size:0.8rem;color:#475569;">Users who sign up will appear here.</span></p>'
                '</div>',
                unsafe_allow_html=True
            )

    st.markdown("---")

    # ── Activity Log ──────────────────────────────────────────────────────────
    section_title("Recent Activity Log", "#8b5cf6")
    col1, col2 = st.columns([2, 1])
    with col1: log_filter = st.text_input("Filter by user name or page…", key="log_filter")
    with col2: log_limit  = st.selectbox("Show last", [100, 250, 500], key="log_limit")

    activity = get_activity_log(limit=log_limit)
    if activity:
        log_df = pd.DataFrame(activity)
        if log_filter:
            mask = (log_df["name"].str.contains(log_filter, case=False, na=False) |
                    log_df["page"].str.contains(log_filter, case=False, na=False))
            log_df = log_df[mask]
        display_log = log_df[["name","email","page","action","timestamp"]].rename(columns={
            "name":"User","email":"Email","page":"Page","action":"Action","timestamp":"Time"
        })
        st.dataframe(display_log, hide_index=True, width="stretch", height=380)

        # Download
        csv_log = log_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️  Download Activity Log (CSV)", data=csv_log,
                           file_name="invensight_activity_log.csv", mime="text/csv")
    else:
        banner("No activity logged yet.", "inf")

    st.markdown("---")

    # ── Per-User Drill-Down ───────────────────────────────────────────────────
    section_title("Per-User Activity Drill-Down", "#f59e0b")
    all_users_list = get_all_users()
    user_map = {f"{u['name']} ({u['email']})": u["id"] for u in all_users_list if u["role"] != "admin"}
    if user_map:
        drill_user = st.selectbox("Select user to inspect", list(user_map.keys()), key="drill_user")
        drill_uid  = user_map[drill_user]
        drill_data = get_user_activity(drill_uid)
        if drill_data:
            drill_df = pd.DataFrame(drill_data)
            drill_df.columns = ["Page", "Action", "Time"]
            st.dataframe(drill_df, hide_index=True, width="stretch", height=260)

            # Page visit count for this user
            page_counts = drill_df["Page"].value_counts().reset_index()
            page_counts.columns = ["Page", "Visits"]
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(page_counts, hide_index=True, width="stretch")
            with col2:
                st.bar_chart(page_counts.set_index("Page"), height=200, color="#f59e0b")
        else:
            banner(f"No activity recorded for this user yet.", "inf")
    else:
        banner("No non-admin users registered yet.", "inf")

    st.markdown("---")

    # ── Admin Profile & Password Settings ─────────────────────────────────────
    section_title("Admin Security Settings", "#10b981")
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f'<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:1rem;margin-bottom:1rem;"><p style="margin:0;font-size:0.78rem;color:#64748b;text-transform:uppercase;font-weight:700;">Current Admin Profile</p><h4 style="margin:0.4rem 0 0.2rem;color:#f1f5f9;">{CURRENT_USER["name"]}</h4><p style="margin:0;color:#94a3b8;font-size:0.85rem;">{CURRENT_USER["email"]}</p></div>', unsafe_allow_html=True)
    with col2:
        with st.expander("🔑 Change Admin Password", expanded=False):
            old_p = st.text_input("Current Password", type="password", key="chg_old_p")
            new_p = st.text_input("New Password (min 6 chars)", type="password", key="chg_new_p")
            new_p2 = st.text_input("Confirm New Password", type="password", key="chg_new_p2")
            if st.button("Update Password", key="chg_p_btn"):
                if not old_p or not new_p:
                    banner("Please fill in all password fields.", "err")
                elif new_p != new_p2:
                    banner("❌ New passwords do not match.", "err")
                else:
                    res = change_password(CURRENT_USER["id"], old_p, new_p)
                    if res["ok"]:
                        banner("✅ Password updated successfully!", "ok")
                    else:
                        banner(f"❌ {res['error']}", "err")
