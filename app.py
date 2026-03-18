"""
Nyztrade Premium — Single File App  (v2)
=========================================
Four portals: Admin · Equity Member · Options Member · Research
Deploy directly to Streamlit Cloud with just this file + requirements.txt

CONFIGURE BEFORE DEPLOY:
  1. ADMIN_PASSWORD  — change "nyztrade2024" below
  2. DISCORD WEBHOOKS — replace YOUR_* placeholders
  3. TELEGRAM         — replace YOUR_* placeholders
"""

import os, sqlite3, hashlib, json, requests
from datetime import date, timedelta, datetime

import streamlit as st

# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════

ADMIN_USERNAME = "drniyas"
ADMIN_PASSWORD = "nyztrade2024"   # ← change before deploy

DISCORD_WEBHOOKS = {
    "equity":  "https://discord.com/api/webhooks/YOUR_EQUITY_WEBHOOK",
    "options": "https://discord.com/api/webhooks/YOUR_OPTIONS_WEBHOOK",
    "updates": "https://discord.com/api/webhooks/YOUR_UPDATES_WEBHOOK",
}

TG_BOT_TOKEN  = "YOUR_BOT_TOKEN"
TG_CHANNEL_ID = "@nyztrade_premium"
TG_ADMIN_ID   = "YOUR_TELEGRAM_CHAT_ID"

PLAN_AMOUNTS = {
    "Equity Monthly":    999,
    "Equity Quarterly":  2499,
    "Equity Annual":     7999,
    "Options Monthly":   1299,
    "Options Quarterly": 3299,
    "Options Annual":    9999,
    "Combo Monthly":     1799,
    "Combo Quarterly":   4499,
    "Combo Annual":      14999,
    "Trial":             0,
}

PLAN_ACCESS = {
    "Equity Monthly":    ["equity"],
    "Equity Quarterly":  ["equity"],
    "Equity Annual":     ["equity"],
    "Options Monthly":   ["options"],
    "Options Quarterly": ["options"],
    "Options Annual":    ["options"],
    "Combo Monthly":     ["equity", "options"],
    "Combo Quarterly":   ["equity", "options"],
    "Combo Annual":      ["equity", "options"],
    "Trial":             ["equity", "options"],
}

BROKER_HOUSES = [
    "Motilal Oswal", "ICICI Securities", "HDFC Securities", "Kotak Securities",
    "Axis Securities", "SBI Securities", "Sharekhan", "Angel One",
    "Geojit", "Edelweiss", "Nirmal Bang", "Emkay Global",
    "Prabhudas Lilladher", "JM Financial", "Nuvama", "Systematix",
    "BOB Capital", "Choice Broking", "Ventura Securities", "Other"
]

REPORT_CATEGORIES = [
    "Equity Research", "Options Strategy", "Sector Report",
    "Market Outlook", "IPO Note", "Result Update",
    "Initiating Coverage", "Price Target Revision", "Macro / Economy", "Other"
]

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Nyztrade Premium",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap');

/* ── MOBILE-FIRST RESET ── */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.stApp { background: #08070f; color: #e2d9f3; }

/* ── MOBILE VIEWPORT FIX ── */
@viewport { width: device-width; }
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

/* ── HIDE STREAMLIT CHROME on mobile ── */
#MainMenu, footer, header { visibility: hidden; height: 0; }
.stDeployButton { display: none; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0a1e 0%, #0a0715 100%) !important;
    border-right: 1px solid #2d1f4e !important;
    min-width: 220px !important;
}

/* ── MAIN CONTENT PADDING (mobile-safe) ── */
.block-container {
    padding: 1rem 1rem 2rem 1rem !important;
    max-width: 100% !important;
}
@media (min-width: 768px) {
    .block-container { padding: 1.5rem 2rem 3rem 2rem !important; }
}

/* ── METRIC CARDS ── */
.metric-card {
    background: #120d20; border: 1px solid #2d1f4e;
    border-radius: 14px; padding: 14px 10px; text-align: center; margin-bottom: 10px;
}
.metric-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: clamp(22px, 5vw, 36px); font-weight: 800; color: #a855f7;
}
.metric-label { font-size: 10px; color: #5a4870; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }

/* ── CALL CARDS ── */
.call-card {
    background: #0f0a1e; border-left: 3px solid #7c3aed;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 12px;
}
.call-card.buy    { border-left-color: #00ffb4; }
.call-card.sell   { border-left-color: #ff6b6b; }
.call-card.hold   { border-left-color: #ffd700; }
.call-card.closed { border-left-color: #3d2f5e; opacity: 0.75; }

/* ── BADGES ── */
.badge {
    display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 10px; font-weight: 700; margin-left: 5px; letter-spacing: 0.8px;
}
.badge-buy    { background: #00ffb422; color: #00ffb4; border: 1px solid #00ffb4; }
.badge-sell   { background: #ff6b6b22; color: #ff6b6b; border: 1px solid #ff6b6b; }
.badge-hold   { background: #ffd70022; color: #ffd700; border: 1px solid #ffd700; }
.badge-open   { background: #a855f722; color: #c084fc; border: 1px solid #a855f7; }
.badge-closed { background: #3d2f5e33; color: #7c6a9b; border: 1px solid #3d2f5e; }
.badge-ce     { background: #00ffb422; color: #00ffb4; border: 1px solid #00ffb4; }
.badge-pe     { background: #ff6b6b22; color: #ff6b6b; border: 1px solid #ff6b6b; }

/* ── SECTION HEADERS ── */
.section-header {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: clamp(20px, 5vw, 28px);
    font-weight: 800; color: #ffffff; margin-bottom: 4px;
}
.section-sub { font-size: 12px; color: #5a4870; margin-bottom: 18px; }

/* ── TAG ── */
.tag {
    display: inline-block; background: #a855f722; color: #c084fc;
    border: 1px solid #a855f744; border-radius: 20px; font-size: 10px;
    padding: 2px 8px; margin-right: 5px; font-weight: 600;
    letter-spacing: 0.8px; text-transform: uppercase;
}

/* ── CARDS ── */
.update-card {
    background: #0f0a1e; border: 1px solid #2d1f4e;
    border-radius: 12px; padding: 16px; margin-bottom: 14px;
}
.report-card {
    background: #0c0a18; border: 1px solid #2d1f4e;
    border-radius: 14px; padding: 18px; margin-bottom: 14px;
    position: relative; overflow: hidden;
}
.report-card:hover { border-color: #5b2fa0; }
.sub-card {
    background: linear-gradient(135deg, #120d20, #0f0a1e);
    border: 1px solid #3d1f6b; border-radius: 18px;
    padding: 20px; margin-bottom: 18px;
}
.pnl-pos { color: #00ffb4; font-weight: 700; }
.pnl-neg { color: #ff6b6b; font-weight: 700; }

/* ── BUTTONS (touch-friendly) ── */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
    color: #fff !important; font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
    border: none !important; border-radius: 10px !important;
    transition: all 0.2s !important;
    min-height: 44px !important;        /* iOS touch target */
    font-size: 14px !important;
}
.stButton > button:hover { opacity: 0.88 !important; }
.stButton > button:active { opacity: 0.75 !important; transform: scale(0.98) !important; }

/* ── FORMS (dark, mobile-sized inputs) ── */
div[data-testid="stForm"] {
    background: #0f0a1e; border: 1px solid #2d1f4e; border-radius: 14px; padding: 16px;
}
.stTextInput > div > div,
.stSelectbox > div,
.stTextArea > div > div,
.stNumberInput > div > div {
    background: #0a0715 !important; border-color: #2d1f4e !important;
    color: #e2d9f3 !important; border-radius: 8px !important;
    font-size: 15px !important;         /* prevents iOS zoom-in */
    min-height: 44px !important;
}
input, textarea, select {
    font-size: 16px !important;         /* iOS no-zoom rule */
}

/* ── RADIO (sidebar nav) ── */
[data-testid="stRadio"] > div { gap: 2px !important; }
[data-testid="stRadio"] label {
    font-size: 14px !important; padding: 8px 6px !important;
    border-radius: 8px !important; cursor: pointer;
}
[data-testid="stRadio"] label:hover { background: #1a0f30 !important; }

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background: #0f0a1e !important; border: 1px solid #2d1f4e !important;
    border-radius: 10px !important; margin-bottom: 10px !important;
}

/* ── WINRATE BADGE ── */
.winrate-badge {
    background: linear-gradient(135deg, #a855f722, #7c3aed22);
    border: 1px solid #a855f744; border-radius: 50px; padding: 6px 20px;
    font-family: 'Plus Jakarta Sans', sans-serif; font-size: 20px; font-weight: 800;
    color: #c084fc; display: inline-block;
}

/* ── VIDEO EMBED ── */
.video-embed-wrap {
    background: #041428; border: 1px solid #0a2040;
    border-radius: 12px; overflow: hidden; margin-bottom: 14px;
}
.video-embed-wrap iframe { width: 100%; border: none; display: block; }

/* ── MOBILE: collapse sidebar trigger ── */
@media (max-width: 767px) {
    [data-testid="stSidebar"] { min-width: 0 !important; }
    .block-container { padding: 0.75rem !important; }
    .section-header { font-size: 20px !important; }
    .metric-value { font-size: 22px !important; }
    .call-card { padding: 12px !important; }
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0a0715; }
::-webkit-scrollbar-thumb { background: #3d1f6b; border-radius: 3px; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)
# Mobile viewport + PWA meta tags
st.markdown('''<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#08070f">''', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nyztrade.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_db(conn):
    """
    Safe migration: add new columns to existing DBs without data loss.
    If the table has a fundamentally incompatible old schema (e.g. missing
    all new columns), drop and recreate it — old parsed-text data had no PDFs
    so nothing valuable is lost.
    """
    # Step 1: Always try to ADD new columns (silently skipped if they exist)
    add_cols = [
        "ALTER TABLE research_reports ADD COLUMN pdf_data BLOB",
        "ALTER TABLE research_reports ADD COLUMN pdf_filename TEXT",
        "ALTER TABLE research_reports ADD COLUMN notes TEXT",
        "ALTER TABLE research_reports ADD COLUMN visible_to TEXT DEFAULT 'all'",
        "ALTER TABLE research_reports ADD COLUMN analyst TEXT",
        "ALTER TABLE research_reports ADD COLUMN sector TEXT",
        "ALTER TABLE research_reports ADD COLUMN tags TEXT",
        "ALTER TABLE research_reports ADD COLUMN upside_pct REAL",
        "ALTER TABLE research_reports ADD COLUMN current_price REAL",
        "ALTER TABLE research_reports ADD COLUMN target_price REAL",
        "ALTER TABLE research_reports ADD COLUMN call_type TEXT",
        "ALTER TABLE research_reports ADD COLUMN symbol TEXT",
        "ALTER TABLE research_reports ADD COLUMN category TEXT",
        "ALTER TABLE research_reports ADD COLUMN broker_house TEXT",
        "ALTER TABLE research_reports ADD COLUMN report_date TEXT",
        # broker_calls table migrations
        "ALTER TABLE broker_calls ADD COLUMN upside_pct REAL",
        "ALTER TABLE broker_calls ADD COLUMN timeframe TEXT",
        "ALTER TABLE broker_calls ADD COLUMN analyst TEXT",
        "ALTER TABLE broker_calls ADD COLUMN status TEXT DEFAULT 'Active'",
        "ALTER TABLE broker_calls ADD COLUMN call_date TEXT",
    ]
    for sql in add_cols:
        try:
            conn.execute(sql)
        except Exception:
            pass

    # Step 2: Verify pdf_data column is actually queryable.
    # If CASE WHEN pdf_data fails, the table is corrupt — nuke and recreate.
    try:
        conn.execute("SELECT CASE WHEN pdf_data IS NOT NULL THEN 1 ELSE 0 END FROM research_reports LIMIT 1")
    except Exception:
        # Drop the old incompatible table — old parsed-text rows have no PDFs
        try:
            conn.execute("DROP TABLE IF EXISTS research_reports")
        except Exception:
            pass

    # Step 3: Fix NULL visible_to values in existing rows
    try:
        conn.execute("UPDATE research_reports SET visible_to='all' WHERE visible_to IS NULL")
    except Exception:
        pass

    conn.commit()


def init_db():
    conn = get_conn(); c = conn.cursor()
    # Run migrations first so old DBs get upgraded before we touch them
    _migrate_db(conn)
    c.execute("""CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
        discord_id TEXT, telegram_id TEXT, email TEXT, phone TEXT,
        plan TEXT DEFAULT 'Equity Monthly', status TEXT DEFAULT 'Active',
        joined_date TEXT, expiry_date TEXT, notes TEXT,
        reminder_sent INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER,
        amount REAL, currency TEXT DEFAULT 'INR',
        plan TEXT, status TEXT DEFAULT 'captured', payment_method TEXT,
        notes TEXT, payment_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(client_id) REFERENCES clients(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS equity_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
        call_type TEXT NOT NULL, entry_price REAL, target1 REAL,
        target2 REAL, stop_loss REAL, cmp REAL, status TEXT DEFAULT 'Open',
        rationale TEXT, result TEXT, exit_price REAL, pnl_pct REAL,
        posted_date TEXT, exit_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS options_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT, underlying TEXT NOT NULL,
        option_type TEXT, strike REAL, expiry TEXT, call_type TEXT,
        entry_premium REAL, target_premium REAL, stop_premium REAL,
        cmp_premium REAL, status TEXT DEFAULT 'Open', rationale TEXT,
        gex_note TEXT, exit_premium REAL, pnl_pct REAL, result TEXT,
        posted_date TEXT, exit_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS daily_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        category TEXT, content TEXT, video_url TEXT,
        tags TEXT, posted_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        category TEXT, description TEXT,
        embed_code TEXT,
        duration TEXT, posted_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    # Research reports — PDF stored as BLOB, rendered inline (no download)
    c.execute("""CREATE TABLE IF NOT EXISTS research_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        broker_house TEXT,
        category TEXT,
        symbol TEXT,
        call_type TEXT,
        target_price REAL,
        current_price REAL,
        upside_pct REAL,
        analyst TEXT,
        report_date TEXT,
        sector TEXT,
        tags TEXT,
        notes TEXT,
        visible_to TEXT DEFAULT 'all',
        pdf_data BLOB,
        pdf_filename TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    # Broker buy/sell calls (structured table)
    c.execute("""CREATE TABLE IF NOT EXISTS broker_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        broker_house TEXT NOT NULL,
        symbol TEXT NOT NULL,
        call_type TEXT NOT NULL,
        target_price REAL,
        stop_loss REAL,
        entry_price REAL,
        current_price REAL,
        upside_pct REAL,
        timeframe TEXT,
        rationale TEXT,
        analyst TEXT,
        status TEXT DEFAULT 'Active',
        call_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()

def verify_member(username, password):
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM clients WHERE username=? AND password_hash=? AND status='Active'",
        (username, hash_password(password))
    ).fetchone()
    conn.close()
    return row

def member_has_access(member, portal_type):
    """Check if member's plan gives access to equity or options portal."""
    plan    = member.get("plan", "")
    allowed = PLAN_ACCESS.get(plan, [])
    return portal_type in allowed

init_db()

# ══════════════════════════════════════════════════════════════════════
# SESSION PERSISTENCE  (JSON file — survives Streamlit reruns)
# ══════════════════════════════════════════════════════════════════════
#
# Streamlit's st.session_state resets when the browser tab is refreshed.
# We persist the login tokens (portal choice, member dict, admin flag)
# in a tiny JSON file on disk so users stay logged in across refreshes.
# The DB_PATH directory is writable on Streamlit Cloud (ephemeral FS).
# IMPORTANT: session file stores NO passwords — only username + plan metadata.

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".nyz_session.json")

def _load_session():
    """Load persisted session from disk into st.session_state (once per run)."""
    if st.session_state.get("_session_loaded"):
        return
    st.session_state["_session_loaded"] = True
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
            # Restore portal
            if "portal" not in st.session_state and data.get("portal"):
                st.session_state["portal"] = data["portal"]
            # Restore admin flag
            if not st.session_state.get("admin_logged_in") and data.get("admin_logged_in"):
                st.session_state["admin_logged_in"] = True
            # Restore member (re-verify from DB to ensure still active)
            if not st.session_state.get("member") and data.get("member_username"):
                conn = get_conn()
                row = conn.execute(
                    "SELECT * FROM clients WHERE username=? AND status='Active'",
                    (data["member_username"],)
                ).fetchone()
                conn.close()
                if row:
                    st.session_state["member"] = dict(row)
                    st.session_state["active_portal"] = data.get("active_portal", "equity")
    except Exception:
        pass  # corrupt file — start fresh

def _save_session():
    """Persist current session state to disk."""
    try:
        data = {
            "portal":          st.session_state.get("portal"),
            "admin_logged_in": bool(st.session_state.get("admin_logged_in")),
            "member_username": (st.session_state.get("member") or {}).get("username"),
            "active_portal":   st.session_state.get("active_portal"),
        }
        with open(SESSION_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def _clear_session():
    """Wipe persisted session (on logout)."""
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════
# DISCORD / TELEGRAM HELPERS
# ══════════════════════════════════════════════════════════════════════

def discord_embed(channel, title, description, color=0x00DDFF, fields=None):
    url = DISCORD_WEBHOOKS.get(channel, "")
    if "YOUR_" in url: return False, "Webhook not configured"
    embed = {"title": title, "description": description, "color": color,
             "timestamp": datetime.utcnow().isoformat(),
             "footer": {"text": "Nyztrade Premium | Dr. Niyas N"}}
    if fields: embed["fields"] = fields
    try:
        r = requests.post(url, json={"embeds": [embed]}, timeout=10)
        return (True, "✅ Discord") if r.status_code in (200, 204) else (False, f"HTTP {r.status_code}")
    except Exception as e: return False, str(e)

def discord_equity(call):
    color  = 0x00FFB4 if call["call_type"] == "BUY" else 0xFF6B6B
    fields = [
        {"name": "Entry",     "value": f"₹{call['entry_price']}", "inline": True},
        {"name": "Target 1",  "value": f"₹{call['target1']}",     "inline": True},
        {"name": "Stop Loss", "value": f"₹{call['stop_loss']}",   "inline": True},
    ]
    if call.get("target2"):   fields.append({"name": "Target 2",   "value": f"₹{call['target2']}", "inline": True})
    if call.get("rationale"): fields.append({"name": "📝 Analysis","value": call["rationale"],     "inline": False})
    icon = "🟢" if call["call_type"] == "BUY" else "🔴"
    return discord_embed("equity", f"{icon} EQUITY — {call['symbol']}", f"**{call['call_type']}**", color, fields)

def discord_options(call):
    color  = 0x00DDFF if call["call_type"] == "BUY" else 0xFF6B6B
    fields = [
        {"name": "Contract",       "value": f"{call['underlying']} {call['strike']} {call['option_type']} {call['expiry']}", "inline": False},
        {"name": "Entry Premium",  "value": f"₹{call['entry_premium']}",  "inline": True},
        {"name": "Target Premium", "value": f"₹{call['target_premium']}", "inline": True},
        {"name": "Stop Loss",      "value": f"₹{call['stop_premium']}",   "inline": True},
    ]
    if call.get("gex_note"): fields.append({"name": "📊 GEX", "value": call["gex_note"], "inline": False})
    icon = "⚡" if call["call_type"] == "BUY" else "🔻"
    return discord_embed("options", f"{icon} OPTIONS — {call['underlying']}", f"**{call['call_type']}** {call['option_type']}", color, fields)

def _tg_send(chat_id, text):
    if "YOUR_" in TG_BOT_TOKEN: return False, "Bot token not configured"
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True}, timeout=10)
        data = r.json()
        return (True, "✅ Telegram") if data.get("ok") else (False, data.get("description", "TG error"))
    except Exception as e: return False, str(e)

def tg_equity(call):
    t2   = f"\n📍 <b>Target 2:</b> ₹{call['target2']}" if call.get("target2") else ""
    rat  = f"\n\n📝 <i>{call['rationale']}</i>"         if call.get("rationale") else ""
    icon = "🟢" if call["call_type"] == "BUY" else "🔴"
    return _tg_send(TG_CHANNEL_ID,
        f"{icon} <b>EQUITY — {call['symbol']}</b>\n━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>{call['call_type']}</b>\n💰 Entry: ₹{call['entry_price']}\n"
        f"🎯 T1: ₹{call['target1']}{t2}\n🛡 SL: ₹{call['stop_loss']}\n"
        f"━━━━━━━━━━━━━━━━━{rat}\n\n<i>Nyztrade Premium | @drniyas</i>")

def tg_options(call):
    gex  = f"\n\n📊 <b>GEX:</b>\n<i>{call['gex_note']}</i>" if call.get("gex_note") else ""
    icon = "⚡" if call["call_type"] == "BUY" else "🔻"
    return _tg_send(TG_CHANNEL_ID,
        f"{icon} <b>OPTIONS — {call['underlying']}</b>\n━━━━━━━━━━━━━━━━━\n"
        f"📋 {call['underlying']} {call['strike']} {call['option_type']} {call['expiry']}\n"
        f"📌 {call['call_type']} | 💰 ₹{call['entry_premium']} | 🎯 ₹{call['target_premium']} | 🛡 ₹{call['stop_premium']}"
        f"{gex}\n\n<i>Nyztrade Premium | @drniyas</i>")

def tg_renewal_reminder(telegram_id, name, days_left, plan, expiry_date):
    urgency = "⚠️ URGENT" if days_left <= 2 else "🔔 Reminder"
    return _tg_send(telegram_id,
        f"{urgency} — <b>Subscription Expiring!</b>\n\nHi <b>{name}</b>,\n\n"
        f"Your <b>{plan}</b> expires in <b>{days_left} day{'s' if days_left!=1 else ''}</b> ({expiry_date}).\n\n"
        f"Contact Dr. Niyas N: 👉 https://linkedin.com/in/drniyas\n\n<i>Nyztrade Premium</i>")

def tg_welcome(telegram_id, name, username, password, plan):
    return _tg_send(telegram_id,
        f"🎉 <b>Welcome to Nyztrade Premium!</b>\n\nHi <b>{name}</b>,\n\n"
        f"━━━━━━━━━━━━━━━━━\n🔐 Username: <code>{username}</code>\n"
        f"Password: <code>{password}</code>\n━━━━━━━━━━━━━━━━━\n\n"
        f"Plan: <b>{plan}</b>\n\n<i>— Dr. Niyas N | Nyztrade Premium</i>")

# ══════════════════════════════════════════════════════════════════════
# CHART HELPERS
# ══════════════════════════════════════════════════════════════════════

def render_line_chart(title, labels, values, color="#00ffb4"):
    chart_id    = f"c{abs(hash(title))}"
    zero_colors = json.dumps(["#00ffb4" if v >= 0 else "#ff6b6b" for v in values])
    st.components.v1.html(f"""
    <div style="background:#041428;border:1px solid #0a2040;border-radius:12px;padding:20px;margin-bottom:20px">
      <div style="font-weight:700;color:#fff;margin-bottom:16px">{title}</div>
      <canvas id="{chart_id}" height="80"></canvas>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>(function(){{
      new Chart(document.getElementById('{chart_id}').getContext('2d'),{{
        type:'line',
        data:{{labels:{json.dumps(labels)},datasets:[{{data:{json.dumps(values)},
          borderColor:'{color}',backgroundColor:'{color}22',fill:true,tension:0.4,
          pointBackgroundColor:{zero_colors},pointRadius:4}}]}},
        options:{{responsive:true,plugins:{{legend:{{display:false}}}},
          scales:{{x:{{ticks:{{color:'#445566',maxTicksLimit:10}},grid:{{color:'#0a2040'}}}},
                   y:{{ticks:{{color:'#445566'}},grid:{{color:'#0a2040'}}}}}}}}
      }});
    }})();</script>""", height=260)

def render_bar_chart(title, labels, values, colors):
    chart_id = f"b{abs(hash(title))}"
    st.components.v1.html(f"""
    <div style="background:#041428;border:1px solid #0a2040;border-radius:12px;padding:20px;margin-bottom:20px">
      <div style="font-weight:700;color:#fff;margin-bottom:16px">{title}</div>
      <canvas id="{chart_id}" height="80"></canvas>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>(function(){{
      new Chart(document.getElementById('{chart_id}').getContext('2d'),{{
        type:'bar',
        data:{{labels:{json.dumps(labels)},datasets:[{{data:{json.dumps(values)},
          backgroundColor:{json.dumps(colors)},borderRadius:4}}]}},
        options:{{responsive:true,plugins:{{legend:{{display:false}}}},
          scales:{{x:{{ticks:{{color:'#445566'}},grid:{{color:'#0a2040'}}}},
                   y:{{ticks:{{color:'#445566'}},grid:{{color:'#0a2040'}}}}}}}}
      }});
    }})();</script>""", height=260)

# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# REPORT METADATA CARD + PDF VIEWER
# ══════════════════════════════════════════════════════════════════════

import base64

def _parse_notes_sections(notes_text):
    """Split stored notes into summary, positives, negatives sections."""
    summary = ""; positives = []; negatives = []
    if not notes_text:
        return summary, positives, negatives
    sections = notes_text.split("\n\n")
    for section in sections:
        s = section.strip()
        if s.upper().startswith("KEY POSITIVES:") or s.upper().startswith("KEY POSITIVES\n"):
            lines = s.split("\n")[1:]
            positives = [l.lstrip("•- ").strip() for l in lines if l.strip()]
        elif s.upper().startswith("KEY RISKS:") or s.upper().startswith("KEY RISKS\n"):
            lines = s.split("\n")[1:]
            negatives = [l.lstrip("•- ").strip() for l in lines if l.strip()]
        else:
            if s:
                summary = s
    # Fallback: if no structured sections, treat bullet lines as positives
    if not positives and not negatives and "\n•" in notes_text:
        for line in notes_text.split("\n"):
            stripped = line.lstrip("•- ").strip()
            if stripped:
                positives.append(stripped)
        summary = ""
    return summary, positives, negatives


def render_report_meta(r):
    """Renders the metadata header strip for a research report, including AI summary."""
    ct_color = {"BUY": "#00ffb4", "SELL": "#ff6b6b", "HOLD": "#ffd700",
                "ACCUMULATE": "#00ddff", "REDUCE": "#ff8c42",
                "NEUTRAL": "#9d8ab5", "UNDERPERFORM": "#ff6b6b"}.get(
                    (r.get("call_type") or "").upper(), "#9d8ab5")
    upside_html = ""
    if r.get("upside_pct") is not None:
        try:
            up_val = float(r["upside_pct"])
            up_col = "#00ffb4" if up_val >= 0 else "#ff6b6b"
            upside_html = f'<div style="background:{up_col}18;border:1px solid {up_col}44;border-radius:8px;padding:10px 16px;text-align:center"><div style="font-size:10px;color:#445566;text-transform:uppercase;letter-spacing:1px">Upside</div><div style="font-size:18px;font-weight:700;color:{up_col}">{up_val:+.1f}%</div></div>'
        except Exception:
            pass
    tags_html = " ".join(
        f'<span style="background:#a855f718;color:#c084fc;border:1px solid #a855f730;border-radius:20px;font-size:10px;padding:2px 10px;font-weight:600">{t.strip()}</span>'
        for t in (r.get("tags") or "").split(",") if t.strip()
    )

    # Parse notes into summary + positives + negatives
    notes_raw = r.get("notes") or ""
    summary, positives, negatives = _parse_notes_sections(notes_raw)

    # Build positives HTML
    pos_html = ""
    if positives:
        items = "".join(f'<div style="font-size:13px;color:#c0e8d0;padding:3px 0;border-left:2px solid #00ffb4;padding-left:10px;margin-bottom:4px">✅ {p}</div>' for p in positives)
        pos_html = f'<div style="margin-top:14px"><div style="font-size:10px;color:#00ffb4;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px">Key Positives</div>{items}</div>'

    # Build negatives HTML
    neg_html = ""
    if negatives:
        items = "".join(f'<div style="font-size:13px;color:#f0c8c8;padding:3px 0;border-left:2px solid #ff6b6b;padding-left:10px;margin-bottom:4px">⚠️ {n}</div>' for n in negatives)
        neg_html = f'<div style="margin-top:12px"><div style="font-size:10px;color:#ff6b6b;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px">Key Risks</div>{items}</div>'

    summary_html = f'<div style="margin-top:12px;font-size:13px;color:#9d8ab5;line-height:1.7">{summary}</div>' if summary else ""

    cmp_str    = f"₹{r['current_price']}" if r.get("current_price") else "—"
    target_str = f"₹{r['target_price']}"  if r.get("target_price")  else "—"
    analyst_html = f'<div style="font-size:11px;color:#9d8ab5;margin-top:3px">Analyst: {r["analyst"]}</div>' if r.get("analyst") else ""

    st.markdown(f"""
    <div class="report-card">
      <div style="position:absolute;top:0;left:0;right:0;height:3px;
           background:linear-gradient(90deg,transparent,{ct_color},transparent);"></div>

      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;margin-bottom:14px">
        <div>
          <div style="font-size:22px;font-weight:800;color:#fff">{r.get("symbol") or "—"}
            <span style="background:{ct_color}22;color:{ct_color};border:1px solid {ct_color}55;
                  border-radius:20px;padding:3px 12px;font-size:12px;font-weight:700;
                  margin-left:10px;letter-spacing:1px;text-transform:uppercase;vertical-align:middle">{r.get("call_type") or "—"}</span>
          </div>
          <div style="font-size:12px;color:#6b5a8a;margin-top:4px">{r.get("sector") or ""} &nbsp;·&nbsp; {r.get("category") or ""}</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:13px;font-weight:700;color:#c084fc">{r.get("broker_house") or "—"}</div>
          <div style="font-size:11px;color:#445566;margin-top:4px">{r.get("report_date") or ""}</div>
          {analyst_html}
        </div>
      </div>

      <div style="display:flex;gap:14px;flex-wrap:wrap;align-items:center">
        <div style="background:#0a0715;border:1px solid #2d1f4e;border-radius:8px;padding:10px 16px;text-align:center">
          <div style="font-size:10px;color:#445566;text-transform:uppercase;letter-spacing:1px">CMP</div>
          <div style="font-size:18px;font-weight:700;color:#fff">{cmp_str}</div>
        </div>
        <div style="background:#0a0715;border:1px solid #2d1f4e;border-radius:8px;padding:10px 16px;text-align:center">
          <div style="font-size:10px;color:#445566;text-transform:uppercase;letter-spacing:1px">Target</div>
          <div style="font-size:18px;font-weight:700;color:{ct_color}">{target_str}</div>
        </div>
        {upside_html}
      </div>

      {summary_html}
      {pos_html}
      {neg_html}

      {f'<div style="margin-top:12px;display:flex;gap:6px;flex-wrap:wrap">{tags_html}</div>' if tags_html else ""}

      <div style="margin-top:12px;font-size:10px;color:#3b2d55;letter-spacing:1px">
        🔒 PDF view-only · Right-click and print/save shortcuts disabled
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_pdf_viewer(pdf_bytes, report_id):
    """
    Renders a PDF inline using PDF.js via a sandboxed iframe.
    The PDF is embedded as a base64 data URI — no raw file URL is ever exposed.
    Download / print shortcuts are blocked. Context menu is disabled.
    """
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    viewer_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#0c0a18; overflow:hidden; font-family:sans-serif; }}
  #pdf-wrap {{ position:relative; width:100%; height:760px; user-select:none; -webkit-user-select:none; }}
  #pdf-canvas-container {{
    width:100%; height:760px; overflow-y:auto; background:#1a1530;
    scrollbar-width:thin; scrollbar-color:#3d1f6b #0c0a18;
  }}
  canvas {{ display:block; margin:8px auto; box-shadow:0 4px 20px #00000066; }}
  #no-right-click {{ position:absolute; top:40px; left:0; right:0; bottom:0; z-index:100; background:transparent; }}
  #toolbar {{
    display:flex; align-items:center; gap:8px; flex-wrap:wrap;
    background:#130d22; border-bottom:1px solid #2d1f4e; padding:7px 12px; height:40px;
  }}
  #toolbar button {{
    background:#3d1f6b; color:#c084fc; border:1px solid #5b2fa0;
    border-radius:6px; padding:3px 11px; font-size:12px; cursor:pointer;
  }}
  #toolbar button:hover {{ background:#5b2fa0; }}
  #page-info {{ color:#6b5a8a; font-size:11px; }}
  #lock-badge {{
    margin-left:auto; background:#ff6b6b18; color:#ff9999; border:1px solid #ff6b6b33;
    border-radius:12px; padding:2px 10px; font-size:10px; font-weight:600;
    letter-spacing:1px; text-transform:uppercase;
  }}
  #loading {{ color:#6b5a8a; font-size:13px; text-align:center; padding:40px; }}
</style>
</head>
<body>
<div id="toolbar">
  <button onclick="prevPage()">&#9664; Prev</button>
  <button onclick="nextPage()">Next &#9654;</button>
  <button onclick="zoomIn()">&#65291; Zoom</button>
  <button onclick="zoomOut()">&#65293; Zoom</button>
  <span id="page-info">Loading...</span>
  <span id="lock-badge">&#128274; View Only</span>
</div>
<div id="pdf-wrap">
  <div id="pdf-canvas-container"><div id="loading">Loading PDF...</div></div>
  <div id="no-right-click" oncontextmenu="return false;"></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
  const B64   = "{b64}";
  const raw   = atob(B64);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  let pdfDoc = null, pageNum = 1, scale = 1.35;
  const cont = document.getElementById('pdf-canvas-container');
  function renderPage(n) {{
    pdfDoc.getPage(n).then(page => {{
      cont.innerHTML = '';
      const vp = page.getViewport({{ scale }});
      const cv = document.createElement('canvas');
      cv.width = vp.width; cv.height = vp.height;
      cont.appendChild(cv);
      page.render({{ canvasContext: cv.getContext('2d'), viewport: vp }});
      document.getElementById('page-info').textContent = 'Page ' + n + ' / ' + pdfDoc.numPages;
    }});
  }}
  pdfjsLib.getDocument({{ data: bytes }}).promise.then(pdf => {{
    pdfDoc = pdf; renderPage(1);
  }}).catch(e => {{
    cont.innerHTML = '<div style="color:#ff6b6b;padding:30px">Error loading PDF: ' + e.message + '</div>';
  }});
  function prevPage() {{ if (pageNum > 1) {{ pageNum--; renderPage(pageNum); }} }}
  function nextPage() {{ if (pdfDoc && pageNum < pdfDoc.numPages) {{ pageNum++; renderPage(pageNum); }} }}
  function zoomIn()  {{ scale = Math.min(scale + 0.2, 3.2); renderPage(pageNum); }}
  function zoomOut() {{ scale = Math.max(scale - 0.2, 0.5); renderPage(pageNum); }}
  document.addEventListener('keydown', e => {{
    if ((e.ctrlKey || e.metaKey) && ['p','s','u','a'].includes(e.key.toLowerCase())) {{
      e.preventDefault(); return false;
    }}
  }});
  document.addEventListener('contextmenu', e => e.preventDefault());
</script>
</body>
</html>"""
    st.components.v1.html(viewer_html, height=810, scrolling=False)


def render_broker_call_card(r):
    ct_color = {"BUY": "#00ffb4", "SELL": "#ff6b6b", "HOLD": "#ffd700"}.get((r['call_type'] or "").upper(), "#9d8ab5")
    st_color = {"Active": "#00ffb4", "Closed": "#445566", "Target Hit": "#00ffb4", "Stop Hit": "#ff6b6b"}.get(r['status'], "#9d8ab5")
    upside   = f"<span style='color:{'#00ffb4' if (r['upside_pct'] or 0)>=0 else '#ff6b6b'};font-weight:700'>{r['upside_pct']:+.1f}%</span>" if r['upside_pct'] else ""
    st.markdown(f"""
    <div class="call-card {r['call_type'].lower()}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <span style="font-size:18px;font-weight:800;color:#fff">{r['symbol']}</span>
          <span style="background:{ct_color}22;color:{ct_color};border:1px solid {ct_color}55;
                border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700;margin-left:8px">{r['call_type']}</span>
          <span style="background:{st_color}18;color:{st_color};border:1px solid {st_color}33;
                border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600;margin-left:4px">{r['status']}</span>
        </div>
        <div style="text-align:right">
          <div style="font-size:13px;font-weight:700;color:#c084fc">{r['broker_house']}</div>
          <div style="font-size:11px;color:#445566">{r['call_date'] or ''}</div>
        </div>
      </div>
      <div style="display:flex;gap:24px;margin-top:12px;flex-wrap:wrap">
        <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Entry</div>
             <div style="font-weight:700;color:#fff">₹{r['entry_price'] or '—'}</div></div>
        <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Target</div>
             <div style="font-weight:700;color:{ct_color}">₹{r['target_price'] or '—'}</div></div>
        <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Stop Loss</div>
             <div style="font-weight:700;color:#ff6b6b">₹{r['stop_loss'] or '—'}</div></div>
        {f"<div><div style='font-size:10px;color:#445566;text-transform:uppercase'>Upside</div><div>{upside}</div></div>" if upside else ""}
        {f"<div><div style='font-size:10px;color:#445566;text-transform:uppercase'>Timeframe</div><div style='color:#9d8ab5;font-size:13px'>{r['timeframe']}</div></div>" if r['timeframe'] else ""}
      </div>
      {f"<div style='margin-top:10px;font-size:13px;color:#99aabb'><b style='color:#7b61ff'>Analyst:</b> {r['analyst']}</div>" if r['analyst'] else ""}
      {f"<div style='margin-top:6px;font-size:13px;color:#99aabb'>{r['rationale']}</div>" if r['rationale'] else ""}
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# PORTAL SELECTOR
# ══════════════════════════════════════════════════════════════════════

def select_portal():
    st.markdown('''<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">''', unsafe_allow_html=True)
    st.markdown('''<style>
    .stApp{background:linear-gradient(135deg,#0a0a12 0%,#10091e 60%,#0a0a12 100%)!important;}
    [data-testid="stSidebar"]{display:none!important;}
    .block-container{padding-top:0!important;max-width:1000px!important;}
    </style>''', unsafe_allow_html=True)

    st.markdown('''
    <div style="text-align:center;padding:40px 20px 28px;">
      <div style="font-family:Outfit,sans-serif;font-size:42px;font-weight:900;color:#c084fc;letter-spacing:-1.5px;margin-bottom:6px;">NYZTrade Premium</div>
      <div style="font-family:Space Grotesk,sans-serif;font-size:10px;font-weight:600;color:#4b3a6b;letter-spacing:6px;text-transform:uppercase;">Quantitative Trading Intelligence</div>
      <div style="font-size:13px;color:#5a4870;margin-top:8px;">GEX Analytics &nbsp;·&nbsp; Options Flows &nbsp;·&nbsp; Equity Research &nbsp;·&nbsp; Broker Reports</div>
    </div>
    ''', unsafe_allow_html=True)

    # Four portal cards
    card_data = [
        ("⚙️","ADMIN","Command Centre","Dr. Niyas N · Restricted","#3b1f6b","#7c3aed","#a855f7",
         ["Post equity & options calls","Manage premium members","Research reports & broker calls","Video library management","Performance analytics"],"admin"),
        ("📈","EQUITY","Equity Portal","Equity subscribers","#1a3a1a","#00ffb4","#00ffb4",
         ["Live equity trading calls","Equity research reports","Broker buy/sell calls","Market updates feed","Verified track record"],"equity"),
        ("⚡","OPTIONS","Options & GEX","Options subscribers","#1a1a3a","#7b61ff","#a855f7",
         ["Live options calls","Weekly GEX analysis maps","Options strategy videos","Broker options calls","GEX track record"],"options"),
        ("📄","RESEARCH","Research Hub","All subscribers","#1a1030","#ffd700","#c084fc",
         ["Broker research reports","Buy/Sell/Hold calls","Sector analysis","IPO notes & result updates","Price target revisions"],"research"),
    ]

    cols = st.columns(4)
    for col, (icon, tag, title, sub, bg_c, accent, txt_c, feats, portal_key) in zip(cols, card_data):
        with col:
            feats_html = "".join(f'<div style="font-size:11px;color:#9d8ab5;padding:3px 0;font-family:Space Grotesk,sans-serif;"><span style="color:{accent}">▸</span> {f}</div>' for f in feats)
            st.markdown(f"""
            <div style="background:linear-gradient(145deg,#140d24,#0d0818);border:1px solid {accent}44;
                 border-radius:22px;padding:26px 22px;position:relative;overflow:hidden;
                 box-shadow:0 4px 40px {accent}12;min-height:360px;">
              <div style="position:absolute;top:0;left:0;right:0;height:3px;
                   background:linear-gradient(90deg,transparent,{accent},transparent);"></div>
              <div style="display:inline-block;background:{accent}18;border:1px solid {accent}33;
                   border-radius:20px;padding:3px 12px;font-size:9px;font-weight:700;color:{txt_c};
                   letter-spacing:3px;text-transform:uppercase;margin-bottom:14px;font-family:Space Grotesk,sans-serif;">{tag}</div>
              <div style="font-size:32px;margin-bottom:12px;">{icon}</div>
              <div style="font-family:Outfit,sans-serif;font-size:20px;font-weight:800;color:#fff;margin-bottom:4px;">{title}</div>
              <div style="font-size:11px;color:#6b5a8a;margin-bottom:16px;letter-spacing:0.5px;">{sub}</div>
              <div style="height:1px;background:linear-gradient(90deg,{accent}44,transparent);margin-bottom:14px;"></div>
              {feats_html}
            </div>""", unsafe_allow_html=True)
            if st.button(f"Enter {title} →", key=f"btn_{portal_key}", use_container_width=True):
                st.session_state.portal = portal_key
                _save_session()
                st.rerun()

    st.markdown('''
    <div style="text-align:center;margin-top:24px;font-family:Space Grotesk,sans-serif;font-size:12px;color:#3b2d55;">
      Not subscribed yet? Contact Dr. Niyas N —
      <a href="https://linkedin.com/in/drniyas" target="_blank" style="color:#a855f7;text-decoration:none;font-weight:600;">linkedin.com/in/drniyas</a>
    </div>''', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# SHARED LOGIN PAGE (used for equity, options, research)
# ══════════════════════════════════════════════════════════════════════

def portal_login(portal_type):
    icons = {"equity": "📈", "options": "⚡", "research": "📄"}
    titles = {"equity": "Equity Portal", "options": "Options & GEX Portal", "research": "Research Hub"}
    accents = {"equity": "#00ffb4", "options": "#7b61ff", "research": "#ffd700"}
    icon   = icons.get(portal_type, "📈")
    title  = titles.get(portal_type, "Member Portal")
    accent = accents.get(portal_type, "#a855f7")

    st.markdown(f'''<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
    .stApp{{background:linear-gradient(135deg,#0a0a12 0%,#10091e 60%,#0a0a12 100%)!important;}}
    [data-testid="stSidebar"]{{display:none!important;}}
    .block-container{{padding-top:20px!important;max-width:520px!important;}}
    </style>''', unsafe_allow_html=True)

    st.markdown(f'''
    <div style="text-align:center;padding:24px 0 20px;">
      <div style="font-family:Outfit,sans-serif;font-size:30px;font-weight:900;color:#c084fc;letter-spacing:-0.5px;">NYZTrade Premium</div>
      <div style="font-family:Space Grotesk,sans-serif;font-size:10px;color:#4b3a6b;letter-spacing:6px;text-transform:uppercase;margin-top:6px;">{title}</div>
    </div>

    <div style="background:linear-gradient(145deg,#130d22,#0e0818);border:1px solid {accent}44;
         border-radius:24px;padding:28px 32px;position:relative;overflow:hidden;
         box-shadow:0 8px 48px {accent}18;margin-bottom:20px;">
      <div style="position:absolute;top:0;left:0;right:0;height:3px;
           background:linear-gradient(90deg,transparent,{accent},transparent);"></div>
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:20px;">
        <div style="width:48px;height:48px;background:{accent}18;border:1px solid {accent}30;
             border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:22px;">{icon}</div>
        <div>
          <div style="font-family:Outfit,sans-serif;font-size:20px;font-weight:800;color:#fff;">{title}</div>
          <div style="font-family:Space Grotesk,sans-serif;font-size:11px;color:#6b5a8a;margin-top:3px;">Enter your credentials below</div>
        </div>
      </div>
      <div style="height:1px;background:linear-gradient(90deg,{accent}44,transparent);margin-bottom:20px;"></div>
    </div>
    ''', unsafe_allow_html=True)

    with st.form(f"{portal_type}_login"):
        username  = st.text_input("Username", placeholder="Your login username")
        password  = st.text_input("Password", type="password", placeholder="Your password")
        submitted = st.form_submit_button(f"Access {title} →", use_container_width=True)
        if submitted:
            member = verify_member(username, password)
            if member:
                # Research hub is accessible to all active members
                if portal_type == "research" or member_has_access(dict(member), portal_type):
                    st.session_state.member = dict(member)
                    st.session_state.active_portal = portal_type
                    _save_session()
                    st.rerun()
                else:
                    st.error(f"Your plan ({member['plan']}) does not include {title}. Contact Dr. Niyas N to upgrade.")
            else:
                st.error("Invalid credentials or subscription inactive. Contact Dr. Niyas N.")

    if st.button("← Back to Portal Select", use_container_width=True):
        st.session_state.portal = None
        st.rerun()
    st.markdown(f'''
    <div style="text-align:center;font-family:Space Grotesk,sans-serif;font-size:12px;color:#3b2d55;margin-top:14px;">
      Not subscribed? — <a href="https://linkedin.com/in/drniyas" target="_blank" style="color:{accent};text-decoration:none;font-weight:600;">Contact Dr. Niyas N</a>
    </div>''', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# ADMIN LOGIN
# ══════════════════════════════════════════════════════════════════════

def admin_login():
    ADMIN_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
    st.markdown('''<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@700;900&family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
    .stApp{background:linear-gradient(135deg,#0a0a12 0%,#10091e 60%,#0a0a12 100%)!important;}
    [data-testid="stSidebar"]{display:none!important;}
    .block-container{padding-top:20px!important;max-width:520px!important;}
    </style>''', unsafe_allow_html=True)

    st.markdown('''
    <div style="text-align:center;padding:24px 0 20px;">
      <div style="font-family:Outfit,sans-serif;font-size:30px;font-weight:900;color:#c084fc;">NYZTrade Premium</div>
      <div style="font-family:Space Grotesk,sans-serif;font-size:10px;color:#4b3a6b;letter-spacing:5px;text-transform:uppercase;margin-top:8px;">Admin Command Centre</div>
    </div>
    <div style="background:linear-gradient(145deg,#130d22,#0e0818);border:1px solid #3b1f6b;
         border-radius:24px;padding:32px;position:relative;overflow:hidden;
         box-shadow:0 8px 48px #7c3aed20;margin-bottom:20px;">
      <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,#7c3aed,#c084fc,transparent);"></div>
      <div style="display:flex;align-items:center;gap:16px;">
        <div style="width:52px;height:52px;background:#3b1f6b22;border:1px solid #5b2fa033;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:26px;">⚙️</div>
        <div>
          <div style="font-family:Outfit,sans-serif;font-size:22px;font-weight:800;color:#fff;">Admin Portal</div>
          <div style="font-family:Space Grotesk,sans-serif;font-size:11px;color:#6b5a8a;margin-top:3px;">Restricted Access · Dr. Niyas N only</div>
        </div>
      </div>
    </div>''', unsafe_allow_html=True)

    with st.form("admin_login"):
        u = st.text_input("Username", placeholder="drniyas")
        p = st.text_input("Password", type="password", placeholder="••••••••")
        if st.form_submit_button("Enter Command Centre →", use_container_width=True):
            if u == ADMIN_USERNAME and hashlib.sha256(p.encode()).hexdigest() == ADMIN_HASH:
                st.session_state.admin_logged_in = True
                _save_session()
                st.rerun()
            else:
                st.error("Invalid credentials.")
    if st.button("← Back to Portal Select", use_container_width=True):
        st.session_state.portal = None
        st.rerun()

# ══════════════════════════════════════════════════════════════════════
# ADMIN — RESEARCH REPORTS
# ══════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════
# PDF AUTO-FILL HELPERS
# ══════════════════════════════════════════════════════════════════════

def _extract_pdf_text(pdf_bytes: bytes, max_chars: int = 12000) -> str:
    """Extract plain text from PDF bytes using PyMuPDF. Returns up to max_chars."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        parts = []
        total = 0
        for page in doc:
            t = page.get_text("text")
            parts.append(t)
            total += len(t)
            if total >= max_chars:
                break
        doc.close()
        text = "\n".join(parts)[:max_chars]
        return text.strip()
    except Exception as e:
        return ""


def _parse_report_with_claude(pdf_text: str, broker_houses: list, categories: list) -> dict:
    """
    Send extracted PDF text to Claude and get structured JSON back.
    Returns a dict with all form fields pre-filled.
    Falls back to empty dict on any error.
    """
    try:
        # Try to get API key from Streamlit secrets or environment
        api_key = None
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY") or st.secrets.get("anthropic_api_key")
        except Exception:
            pass
        if not api_key:
            import os
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key or api_key.startswith("YOUR_"):
            return {"_error": "no_api_key"}

        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        broker_list = ", ".join(broker_houses)
        cat_list    = ", ".join(categories)

        prompt = f"""You are a financial document analyst. Extract structured data from this broker research report text.

Return a JSON object with EXACTLY these keys (use null for anything not found):
{{
  "title": "exact report title or descriptive title",
  "broker_house": "one of: {broker_list}",
  "category": "one of: {cat_list}",
  "symbol": "NSE/BSE stock symbol e.g. RELIANCE",
  "sector": "sector e.g. Banking, IT, Auto, FMCG",
  "call_type": "one of: BUY, SELL, HOLD, ACCUMULATE, REDUCE, NEUTRAL, UNDERPERFORM",
  "target_price": number or null,
  "current_price": number or null,
  "analyst": "analyst name(s)",
  "report_date": "YYYY-MM-DD or null",
  "tags": "3-5 relevant comma-separated tags",
  "positives": ["point 1", "point 2", "point 3"],
  "negatives": ["risk 1", "risk 2"],
  "notes": "2-3 sentence executive summary of the report"
}}

Rules:
- broker_house MUST be one of the provided list; pick the closest match or "Other"
- category MUST be one of the provided list
- call_type MUST be one of the provided values (uppercase)
- For prices, extract numbers only (no ₹ or Rs symbols)
- positives: key investment arguments / why to buy (3-6 bullet points)
- negatives: key risks / concerns (2-4 bullet points)
- Return ONLY valid JSON, no markdown, no explanation

Report text:
---
{pdf_text}
---"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        import json as _json
        parsed = _json.loads(raw.strip())
        return parsed
    except Exception as e:
        return {"_error": str(e)}


def admin_research():
    st.markdown('<div class="section-header">📄 Research Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Upload broker PDFs — displayed inline, no download for members</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ Upload Report", "📋 All Reports", "🏦 Broker Calls"])

    with tab1:
        st.markdown("##### Upload Broker Research PDF")
        st.markdown("""
        <div style="background:#0a0715;border:1px solid #2d1f4e;border-radius:10px;padding:14px;margin-bottom:16px;font-size:13px;color:#9d8ab5;line-height:1.8">
        <b style="color:#c084fc">✨ AI Auto-Fill:</b> Upload a PDF and click <b style="color:#ffd700">Extract & Auto-Fill</b> —
        Claude AI will read the report and fill all fields including a summary, key positives and negatives.
        You can edit any field before saving. Max PDF size: <b style="color:#ffd700">15 MB</b>.
        <br><b style="color:#ff9999">Requires:</b> Set <code>ANTHROPIC_API_KEY</code> in Streamlit Secrets (App Settings → Secrets).
        </div>
        """, unsafe_allow_html=True)

        uploaded_pdf = st.file_uploader(
            "Select PDF file *", type=["pdf"],
            help="PDF will be stored securely and shown inline to members"
        )

        # ── Auto-extract button (outside form so it can update session state) ──
        ai_data = st.session_state.get("_ai_prefill", {})

        if uploaded_pdf is not None:
            col_btn, col_status = st.columns([2, 5])
            if col_btn.button("✨ Extract & Auto-Fill", type="primary", use_container_width=True):
                with st.spinner("📖 Reading PDF text..."):
                    pdf_bytes_preview = uploaded_pdf.read()
                    uploaded_pdf.seek(0)  # reset for later save
                    pdf_text = _extract_pdf_text(pdf_bytes_preview)

                if not pdf_text:
                    st.warning("⚠️ Could not extract text from this PDF (may be scanned image). Fill fields manually.")
                else:
                    with st.spinner("🤖 Claude is analysing the report..."):
                        parsed = _parse_report_with_claude(pdf_text, BROKER_HOUSES, REPORT_CATEGORIES)

                    if parsed.get("_error") == "no_api_key":
                        st.error("❌ ANTHROPIC_API_KEY not set. Add it in Streamlit App Settings → Secrets as: ANTHROPIC_API_KEY = \"sk-ant-...\"")
                    elif parsed.get("_error"):
                        st.warning(f"⚠️ AI parsing failed: {parsed['_error']}. Fill fields manually.")
                    else:
                        st.session_state["_ai_prefill"] = parsed
                        ai_data = parsed
                        st.success("✅ Fields auto-filled from PDF! Review and edit before saving.")
                        st.rerun()

        # ── Show extracted positives/negatives as a preview card ─────────
        if ai_data and not ai_data.get("_error"):
            pos = ai_data.get("positives") or []
            neg = ai_data.get("negatives") or []
            if pos or neg:
                st.markdown("""<div style="background:#0c0a18;border:1px solid #2d1f4e;border-radius:12px;padding:18px;margin-bottom:16px">
                <div style="font-size:12px;color:#445566;text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;font-weight:700">📊 AI-Extracted Summary</div>""", unsafe_allow_html=True)
                if pos:
                    st.markdown('<div style="font-size:11px;color:#00ffb4;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin-bottom:6px">✅ Key Positives</div>', unsafe_allow_html=True)
                    for p in pos:
                        st.markdown(f'<div style="font-size:13px;color:#c0d0e0;padding:3px 0 3px 12px;border-left:2px solid #00ffb4">• {p}</div>', unsafe_allow_html=True)
                if neg:
                    st.markdown('<div style="font-size:11px;color:#ff6b6b;text-transform:uppercase;letter-spacing:1px;font-weight:700;margin:12px 0 6px">⚠️ Key Risks / Negatives</div>', unsafe_allow_html=True)
                    for n in neg:
                        st.markdown(f'<div style="font-size:13px;color:#c0d0e0;padding:3px 0 3px 12px;border-left:2px solid #ff6b6b">• {n}</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # ── Helper: safe index lookup for selectboxes ─────────────────────
        def _idx(lst, val, default=0):
            try: return lst.index(val) if val in lst else default
            except: return default

        # ── Form with AI pre-filled defaults ─────────────────────────────
        CALL_TYPES = ["BUY","SELL","HOLD","ACCUMULATE","REDUCE","NEUTRAL","UNDERPERFORM"]
        ai_title    = ai_data.get("title", "")
        ai_broker   = ai_data.get("broker_house", BROKER_HOUSES[0])
        ai_cat      = ai_data.get("category", REPORT_CATEGORIES[0])
        ai_symbol   = ai_data.get("symbol", "")
        ai_sector   = ai_data.get("sector", "")
        ai_call     = ai_data.get("call_type", "BUY")
        ai_target   = float(ai_data.get("target_price") or 0)
        ai_cmp      = float(ai_data.get("current_price") or 0)
        ai_analyst  = ai_data.get("analyst", "")
        ai_tags     = ai_data.get("tags", "")
        ai_notes    = ai_data.get("notes", "")
        # Build positives/negatives into notes if notes is short
        pos_text = ""
        neg_text = ""
        pos_list = ai_data.get("positives") or []
        neg_list = ai_data.get("negatives") or []
        if pos_list:
            pos_text = "\n".join(f"• {p}" for p in pos_list)
        if neg_list:
            neg_text = "\n".join(f"• {n}" for n in neg_list)

        # Parse report_date safely
        ai_date = date.today()
        try:
            if ai_data.get("report_date"):
                from datetime import datetime as _dt
                ai_date = _dt.strptime(ai_data["report_date"], "%Y-%m-%d").date()
        except Exception:
            pass

        with st.form("report_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                title     = st.text_input("Report Title *",        value=ai_title)
                broker    = st.selectbox("Broker House *",          BROKER_HOUSES, index=_idx(BROKER_HOUSES, ai_broker))
                category  = st.selectbox("Category *",             REPORT_CATEGORIES, index=_idx(REPORT_CATEGORIES, ai_cat))
                symbol    = st.text_input("Stock Symbol",           value=ai_symbol, placeholder="RELIANCE, NIFTY...")
                sector    = st.text_input("Sector",                 value=ai_sector, placeholder="Banking, IT, Auto...")
            with c2:
                call_type     = st.selectbox("Rating / Call",       CALL_TYPES, index=_idx(CALL_TYPES, ai_call))
                target_price  = st.number_input("Target Price ₹",  min_value=0.0, step=0.5, value=ai_target)
                current_price = st.number_input("Current Price ₹", min_value=0.0, step=0.5, value=ai_cmp)
                analyst       = st.text_input("Analyst Name",      value=ai_analyst)
                report_date   = st.date_input("Report Date",       value=ai_date)
            with c3:
                upside_pct = round(((target_price - current_price) / current_price * 100), 2) if current_price and target_price else None
                if upside_pct is not None:
                    color = "#00ffb4" if upside_pct >= 0 else "#ff6b6b"
                    st.markdown(f'<div style="margin-top:28px;background:#0a0715;border:1px solid #2d1f4e;border-radius:10px;padding:16px;text-align:center"><div style="font-size:11px;color:#445566;text-transform:uppercase">Upside / Downside</div><div style="font-size:28px;font-weight:800;color:{color};margin-top:6px">{upside_pct:+.1f}%</div></div>', unsafe_allow_html=True)
                tags       = st.text_input("Tags", value=ai_tags, placeholder="largecap, Q3, results...")
                visible_to = st.selectbox("Visible To", ["all","equity","options"])

            notes = st.text_area("Executive Summary (AI-generated, editable)", height=100,
                value=ai_notes, placeholder="Brief context shown above the PDF viewer...")

            if pos_text or neg_text:
                st.markdown('<div style="font-size:11px;color:#445566;margin-bottom:4px;margin-top:8px">Key Positives (editable)</div>', unsafe_allow_html=True)
                positives_text = st.text_area("", value=pos_text, height=110, key="pos_text_field",
                    placeholder="• Key reason 1\n• Key reason 2", label_visibility="collapsed")
                st.markdown('<div style="font-size:11px;color:#445566;margin-bottom:4px;margin-top:8px">Key Risks / Negatives (editable)</div>', unsafe_allow_html=True)
                negatives_text = st.text_area("", value=neg_text, height=80, key="neg_text_field",
                    placeholder="• Risk 1\n• Risk 2", label_visibility="collapsed")
            else:
                positives_text = st.text_area("Key Positives (optional)", height=90,
                    placeholder="• Strong revenue growth\n• Market leader position")
                negatives_text = st.text_area("Key Risks / Negatives (optional)", height=70,
                    placeholder="• Regulatory risk\n• Margin pressure")

            save_col, clear_col = st.columns([4, 1])
            submitted = save_col.form_submit_button("💾 Upload & Save Report →", use_container_width=True)
            cleared   = clear_col.form_submit_button("🔄 Clear AI Fill", use_container_width=True)

            if cleared:
                st.session_state.pop("_ai_prefill", None)
                st.rerun()

            if submitted:
                if not title or not broker:
                    st.error("Title and broker house are required.")
                elif uploaded_pdf is None:
                    st.error("Please select and upload a PDF file.")
                else:
                    uploaded_pdf.seek(0)
                    pdf_bytes = uploaded_pdf.read()
                    size_mb   = len(pdf_bytes) / (1024 * 1024)
                    if size_mb > 15:
                        st.error(f"PDF is {size_mb:.1f} MB — please keep under 15 MB.")
                    else:
                        # Combine notes + positives + negatives into the notes field
                        full_notes_parts = []
                        if notes.strip(): full_notes_parts.append(notes.strip())
                        if positives_text.strip():
                            full_notes_parts.append("KEY POSITIVES:\n" + positives_text.strip())
                        if negatives_text.strip():
                            full_notes_parts.append("KEY RISKS:\n" + negatives_text.strip())
                        full_notes = "\n\n".join(full_notes_parts)

                        conn = get_conn()
                        conn.execute("""INSERT INTO research_reports
                            (title, broker_house, category, symbol, call_type,
                             target_price, current_price, upside_pct, analyst,
                             report_date, sector, tags, notes, visible_to,
                             pdf_data, pdf_filename)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (title, broker, category,
                             symbol.upper().strip() if symbol else None,
                             call_type, target_price or None, current_price or None,
                             upside_pct, analyst, str(report_date), sector, tags,
                             full_notes, visible_to, pdf_bytes, uploaded_pdf.name))
                        conn.commit(); conn.close()
                        st.session_state.pop("_ai_prefill", None)
                        st.success(f"✅ '{title}' uploaded ({size_mb:.2f} MB) — available to members immediately.")

    with tab2:
        conn = get_conn()
        f1, f2, f3 = st.columns(3)
        broker_f = f1.selectbox("Broker", ["All"] + BROKER_HOUSES, key="adm_broker_f")
        cat_f    = f2.selectbox("Category", ["All"] + REPORT_CATEGORIES, key="adm_cat_f")
        call_f   = f3.selectbox("Rating", ["All","BUY","SELL","HOLD","ACCUMULATE","NEUTRAL"], key="adm_call_f")
        # Safe query that works on old and new schemas
        def _admin_fetch_reports(conn, broker_f, cat_f, call_f):
            try:
                q = """SELECT id, title,
                              COALESCE(broker_house,'') as broker_house,
                              COALESCE(category,'') as category,
                              COALESCE(symbol,'') as symbol,
                              COALESCE(call_type,'') as call_type,
                              COALESCE(target_price,0) as target_price,
                              COALESCE(current_price,0) as current_price,
                              COALESCE(upside_pct,0) as upside_pct,
                              COALESCE(analyst,'') as analyst,
                              COALESCE(report_date,'') as report_date,
                              COALESCE(sector,'') as sector,
                              COALESCE(tags,'') as tags,
                              COALESCE(notes,'') as notes,
                              COALESCE(visible_to,'all') as visible_to,
                              COALESCE(pdf_filename,'') as pdf_filename,
                              created_at,
                              CASE WHEN pdf_data IS NOT NULL THEN 1 ELSE 0 END AS has_pdf
                       FROM research_reports WHERE 1=1"""
                params = []
                if broker_f != "All": q += " AND broker_house=?"; params.append(broker_f)
                if cat_f    != "All": q += " AND category=?";     params.append(cat_f)
                if call_f   != "All": q += " AND call_type=?";    params.append(call_f)
                q += " ORDER BY created_at DESC"
                return conn.execute(q, params).fetchall()
            except Exception:
                try:
                    return conn.execute("SELECT id, title, COALESCE(broker_house,'') as broker_house, COALESCE(category,'') as category, COALESCE(symbol,'') as symbol, COALESCE(call_type,'') as call_type, COALESCE(target_price,0) as target_price, COALESCE(current_price,0) as current_price, COALESCE(upside_pct,0) as upside_pct, COALESCE(analyst,'') as analyst, COALESCE(report_date,'') as report_date, COALESCE(sector,'') as sector, COALESCE(tags,'') as tags, COALESCE(notes,'') as notes, 'all' as visible_to, '' as pdf_filename, created_at, 0 as has_pdf FROM research_reports ORDER BY created_at DESC").fetchall()
                except Exception:
                    return []
        rows = _admin_fetch_reports(conn, broker_f, cat_f, call_f)
        conn.close()
        st.markdown(f"**{len(rows)} report(s)** found")
        for r in rows:
            pdf_badge = "📄 PDF" if r['has_pdf'] else "⚠️ No PDF"
            with st.expander(f"[{r['broker_house']}] {r['symbol'] or '—'} — {r['call_type']} | {r['title'][:55]} | {r['report_date']}  {pdf_badge}"):
                render_report_meta(dict(r))
                if r['has_pdf']:
                    if st.button("👁️ Preview PDF", key=f"prev_{r['id']}"):
                        st.session_state[f"show_pdf_{r['id']}"] = not st.session_state.get(f"show_pdf_{r['id']}", False)
                    if st.session_state.get(f"show_pdf_{r['id']}"):
                        conn2 = get_conn()
                        pdf_row = conn2.execute("SELECT pdf_data FROM research_reports WHERE id=?", (r['id'],)).fetchone()
                        conn2.close()
                        if pdf_row and pdf_row['pdf_data']:
                            render_pdf_viewer(bytes(pdf_row['pdf_data']), r['id'])
                else:
                    st.warning("No PDF uploaded for this report.")
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
                del_col1, del_col2 = st.columns([3, 1])
                del_col1.markdown('<div style="font-size:11px;color:#445566;padding-top:8px">⚠️ Deleting a report removes its PDF permanently.</div>', unsafe_allow_html=True)
                if del_col2.button("🗑️ Delete Report", key=f"dr_{r['id']}", use_container_width=True):
                    conn2 = get_conn()
                    conn2.execute("DELETE FROM research_reports WHERE id=?", (r['id'],))
                    conn2.commit(); conn2.close(); st.rerun()

    with tab3:
        st.markdown("##### 🏦 Broker Buy/Sell Calls (Structured)")
        bc1, bc2 = st.tabs(["➕ Add Call", "📋 All Calls"])
        with bc1:
            with st.form("broker_call_form"):
                r1, r2, r3 = st.columns(3)
                with r1:
                    bc_broker   = st.selectbox("Broker *", BROKER_HOUSES, key="bc_broker")
                    bc_symbol   = st.text_input("Symbol *", placeholder="INFY, NIFTY...")
                    bc_calltype = st.selectbox("Call Type *", ["BUY","SELL","HOLD"])
                    bc_analyst  = st.text_input("Analyst")
                with r2:
                    bc_entry  = st.number_input("Entry Price ₹", min_value=0.0, step=0.5)
                    bc_target = st.number_input("Target ₹", min_value=0.0, step=0.5)
                    bc_sl     = st.number_input("Stop Loss ₹", min_value=0.0, step=0.5)
                    bc_cmp    = st.number_input("CMP ₹", min_value=0.0, step=0.5)
                with r3:
                    bc_tf   = st.selectbox("Timeframe", ["Intraday","Short-term (1-4 weeks)","Medium-term (1-3 months)","Long-term (6-12 months)"])
                    bc_date = st.date_input("Call Date", value=date.today(), key="bc_date")
                    bc_up   = round(((bc_target - bc_cmp) / bc_cmp * 100), 2) if bc_cmp and bc_target else None
                    if bc_up is not None:
                        color = "#00ffb4" if bc_up >= 0 else "#ff6b6b"
                        st.markdown(f'<div style="margin-top:24px;background:#0a0715;border:1px solid #2d1f4e;border-radius:10px;padding:12px;text-align:center"><div style="font-size:10px;color:#445566;text-transform:uppercase">Upside</div><div style="font-size:24px;font-weight:800;color:{color}">{bc_up:+.1f}%</div></div>', unsafe_allow_html=True)
                bc_rationale = st.text_area("Rationale (optional)", height=70)
                if st.form_submit_button("Add Broker Call →", use_container_width=True):
                    if not bc_broker or not bc_symbol or not bc_calltype:
                        st.error("Broker, symbol, and call type required.")
                    else:
                        conn = get_conn()
                        conn.execute("""INSERT INTO broker_calls
                            (broker_house,symbol,call_type,target_price,stop_loss,entry_price,
                             current_price,upside_pct,timeframe,rationale,analyst,status,call_date)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (bc_broker, bc_symbol.upper().strip(), bc_calltype,
                             bc_target or None, bc_sl or None, bc_entry or None,
                             bc_cmp or None, bc_up, bc_tf, bc_rationale, bc_analyst,
                             "Active", str(bc_date)))
                        conn.commit(); conn.close()
                        st.success(f"✅ {bc_broker} → {bc_symbol.upper()} {bc_calltype} added.")

        with bc2:
            conn = get_conn()
            bf1, bf2 = st.columns(2)
            bc_broker_f = bf1.selectbox("Filter Broker", ["All"] + BROKER_HOUSES, key="bc_filter")
            bc_ct_f     = bf2.selectbox("Filter Call", ["All","BUY","SELL","HOLD"], key="bc_ct_filter")
            q2 = "SELECT * FROM broker_calls WHERE 1=1"
            p2 = []
            if bc_broker_f != "All": q2 += " AND broker_house=?"; p2.append(bc_broker_f)
            if bc_ct_f     != "All": q2 += " AND call_type=?";    p2.append(bc_ct_f)
            q2 += " ORDER BY created_at DESC"
            try:
                bc_rows = conn.execute(q2, p2).fetchall()
            except Exception:
                bc_rows = []
            conn.close()
            for r in bc_rows:
                render_broker_call_card(dict(r))
                bc1a, bc2a, bc2b = st.columns([4, 2, 1])
                new_st = bc1a.selectbox("Update Status", ["Active","Target Hit","Stop Hit","Closed"], key=f"bcs_{r['id']}")
                if bc2a.button("✅ Update Status", key=f"bcu_{r['id']}", use_container_width=True):
                    conn2 = get_conn()
                    conn2.execute("UPDATE broker_calls SET status=? WHERE id=?", (new_st, r['id']))
                    conn2.commit(); conn2.close(); st.rerun()
                if bc2b.button("🗑️", key=f"bcd_{r['id']}", help="Delete this broker call", use_container_width=True):
                    conn2 = get_conn()
                    conn2.execute("DELETE FROM broker_calls WHERE id=?", (r['id'],))
                    conn2.commit(); conn2.close(); st.rerun()
                st.markdown("<hr style='border-color:#1a1030;margin:4px 0 8px'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# ADMIN PAGES
# ══════════════════════════════════════════════════════════════════════

def admin_dashboard():
    st.markdown('<div class="section-header">🏠 Command Centre</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Live overview — all activity at a glance</div>', unsafe_allow_html=True)
    conn = get_conn()
    cols = st.columns(6)
    metrics = [
        (conn.execute("SELECT COUNT(*) FROM clients WHERE status='Active'").fetchone()[0], "Active Members","#00ddff"),
        (conn.execute("SELECT COUNT(*) FROM equity_calls WHERE status='Open'").fetchone()[0],  "Equity Open",  "#00ffb4"),
        (conn.execute("SELECT COUNT(*) FROM options_calls WHERE status='Open'").fetchone()[0], "Options Open", "#7b61ff"),
        (conn.execute("SELECT COUNT(*) FROM research_reports").fetchone()[0],                  "Reports",      "#ffd700"),
        (conn.execute("SELECT COUNT(*) FROM broker_calls WHERE status='Active'").fetchone()[0],"Broker Calls", "#c084fc"),
        (conn.execute("SELECT COUNT(*) FROM clients WHERE expiry_date<=? AND status='Active'",
                      (str(date.today() + timedelta(days=7)),)).fetchone()[0], "Expiring 7d","#ff6b6b"),
    ]
    for col, (val, label, color) in zip(cols, metrics):
        col.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{color}">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.divider()
    pc1, pc2 = st.columns(2)
    for col, table, label in [(pc1,"equity_calls","Equity"),(pc2,"options_calls","Options")]:
        with col:
            rows = conn.execute(f"SELECT pnl_pct FROM {table} WHERE status='Closed' AND pnl_pct IS NOT NULL").fetchall()
            if rows:
                pnls = [r[0] for r in rows]; wins = sum(1 for p in pnls if p > 0)
                col.markdown(f"""<div class="sub-card">
                  <div style="font-size:13px;color:#445566;letter-spacing:2px;text-transform:uppercase">{label} Track Record</div>
                  <div style="margin-top:12px;display:flex;gap:30px">
                    <div><div class="metric-value" style="font-size:32px;color:#00ffb4">{wins/len(pnls)*100:.0f}%</div><div class="metric-label">Win Rate</div></div>
                    <div><div class="metric-value" style="font-size:32px;color:{'#00ffb4' if sum(pnls)/len(pnls)>0 else '#ff6b6b'}">{sum(pnls)/len(pnls):+.1f}%</div><div class="metric-label">Avg P&L</div></div>
                    <div><div class="metric-value" style="font-size:32px">{len(pnls)}</div><div class="metric-label">Calls</div></div>
                  </div></div>""", unsafe_allow_html=True)
            else: col.info(f"No closed {label.lower()} calls yet.")
    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("#### Latest Equity")
        for r in conn.execute("SELECT * FROM equity_calls ORDER BY created_at DESC LIMIT 4").fetchall():
            pnl = f" | <span class='{'pnl-pos' if (r['pnl_pct'] or 0)>0 else 'pnl-neg'}'>{r['pnl_pct']:+.1f}%</span>" if r['pnl_pct'] else ""
            st.markdown(f'<div class="call-card {r["call_type"].lower()}"><b style="color:#fff">{r["symbol"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span class="badge badge-{r["status"].lower()}">{r["status"]}</span><span style="float:right;font-size:12px;color:#445566">{r["posted_date"] or ""}</span><br><span style="color:#99aabb;font-size:13px">Entry ₹{r["entry_price"]} | SL ₹{r["stop_loss"]}{pnl}</span></div>', unsafe_allow_html=True)
    with right:
        st.markdown("#### Latest Broker Calls")
        for r in conn.execute("SELECT * FROM broker_calls ORDER BY created_at DESC LIMIT 4").fetchall():
            render_broker_call_card(dict(r))
    conn.close()


def admin_equity():
    st.markdown('<div class="section-header">📊 Equity Calls</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Post, manage and close equity positions</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["➕ New Call","📋 Open Positions","📁 History","🔧 Manage All"])
    with tab1:
        with st.form("eq_form"):
            c1, c2 = st.columns(2)
            with c1:
                symbol      = st.text_input("Symbol *", placeholder="RELIANCE, TCS...")
                call_type   = st.selectbox("Type *", ["BUY","SELL"])
                entry_price = st.number_input("Entry ₹ *", min_value=0.0, step=0.5)
                stop_loss   = st.number_input("Stop Loss ₹ *", min_value=0.0, step=0.5)
            with c2:
                target1     = st.number_input("Target 1 ₹ *", min_value=0.0, step=0.5)
                target2     = st.number_input("Target 2 ₹", min_value=0.0, step=0.5)
                cmp         = st.number_input("CMP ₹", min_value=0.0, step=0.5)
                posted_date = st.date_input("Date", value=date.today())
            rationale = st.text_area("Rationale / Analysis", height=100)
            sc1, sc2  = st.columns(2)
            send_disc = sc1.checkbox("📤 Discord #equity", value=True)
            send_tg   = sc2.checkbox("✈️ Telegram channel", value=True)
            if st.form_submit_button("Post Call →", use_container_width=True):
                if not symbol or not entry_price or not target1 or not stop_loss:
                    st.error("Fill all required fields.")
                else:
                    call = dict(symbol=symbol.upper().strip(), call_type=call_type,
                                entry_price=entry_price, target1=target1,
                                target2=target2 or None, stop_loss=stop_loss,
                                cmp=cmp, rationale=rationale, posted_date=str(posted_date))
                    conn = get_conn()
                    conn.execute("INSERT INTO equity_calls (symbol,call_type,entry_price,target1,target2,stop_loss,cmp,rationale,posted_date,status) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (call["symbol"],call["call_type"],call["entry_price"],call["target1"],
                         call["target2"],call["stop_loss"],call["cmp"],call["rationale"],call["posted_date"],"Open"))
                    conn.commit(); conn.close()
                    msgs = []
                    if send_disc: ok,m = discord_equity(call); msgs.append(f"Discord:{'✅' if ok else '⚠️'}")
                    if send_tg:   ok,m = tg_equity(call);     msgs.append(f"Telegram:{'✅' if ok else '⚠️'}")
                    st.success(f"✅ {symbol.upper()} posted" + (" | "+" | ".join(msgs) if msgs else ""))
    with tab2:
        conn = get_conn()
        for r in conn.execute("SELECT * FROM equity_calls WHERE status='Open' ORDER BY created_at DESC").fetchall():
            with st.expander(f"{'🟢' if r['call_type']=='BUY' else '🔴'} {r['symbol']} — ₹{r['entry_price']} | {r['posted_date']}"):
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Entry",f"₹{r['entry_price']}"); c2.metric("Target 1",f"₹{r['target1']}")
                c3.metric("Stop Loss",f"₹{r['stop_loss']}"); c4.metric("CMP",f"₹{r['cmp']}" if r['cmp'] else "—")
                if r['rationale']: st.caption(r['rationale'])
                ec1,ec2,ec3,ec4 = st.columns(4)
                exit_p = ec1.number_input("Exit ₹", key=f"ep{r['id']}", min_value=0.0)
                result = ec2.selectbox("Result", ["Target Hit","Stop Hit","Partial","Manual"], key=f"res{r['id']}")
                if ec3.button("✅ Close", key=f"cl{r['id']}"):
                    pnl = round(((exit_p-r['entry_price'])/r['entry_price']*100)*(1 if r['call_type']=='BUY' else -1),2) if exit_p and r['entry_price'] else 0
                    conn.execute("UPDATE equity_calls SET status='Closed',exit_price=?,result=?,pnl_pct=?,exit_date=date('now') WHERE id=?",(exit_p,result,pnl,r['id']))
                    conn.commit(); st.success(f"Closed | P&L: {pnl:+.2f}%"); st.rerun()
                if ec4.button("🗑️ Delete", key=f"eq_del{r['id']}"):
                    conn.execute("DELETE FROM equity_calls WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
    with tab3:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM equity_calls WHERE status='Closed' ORDER BY exit_date DESC").fetchall()
        if not rows: st.info("No closed calls yet.")
        else:
            pnls = [r['pnl_pct'] for r in rows if r['pnl_pct'] is not None]
            if pnls:
                m1,m2,m3 = st.columns(3)
                wins = sum(1 for p in pnls if p>0)
                m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%"); m3.metric("Total",len(rows))
            for r in rows:
                pc = "#00ffb4" if (r['pnl_pct'] or 0)>0 else "#ff6b6b"
                pnl_str = f"{r['pnl_pct']:+.2f}%" if r['pnl_pct'] else "—"
                col_card, col_del = st.columns([10, 1])
                with col_card:
                    st.markdown(f'<div class="call-card closed"><b style="color:#fff">{r["symbol"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:700;float:right;font-size:18px">{pnl_str}</span><br><span style="color:#99aabb;font-size:13px">₹{r["entry_price"]} → ₹{r["exit_price"] or "—"} | {r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑️", key=f"eq_hdel{r['id']}", help="Delete this call"):
                        conn.execute("DELETE FROM equity_calls WHERE id=?", (r['id'],))
                        conn.commit(); st.rerun()
        conn.close()
    with tab4:
        st.markdown("##### 🔧 Manage All Equity Calls")
        st.caption("Search, edit status, reopen or permanently delete any call.")
        conn = get_conn()
        sym_search = st.text_input("Search symbol", placeholder="RELIANCE, TCS...", key="eq_mgmt_search")
        status_f   = st.selectbox("Filter by Status", ["All","Open","Closed"], key="eq_mgmt_status")
        q_mgmt = "SELECT * FROM equity_calls WHERE 1=1"
        p_mgmt = []
        if sym_search.strip(): q_mgmt += " AND symbol LIKE ?"; p_mgmt.append(f"%{sym_search.upper().strip()}%")
        if status_f != "All":  q_mgmt += " AND status=?";     p_mgmt.append(status_f)
        q_mgmt += " ORDER BY created_at DESC"
        all_eq = conn.execute(q_mgmt, p_mgmt).fetchall()
        conn.close()
        if not all_eq:
            st.info("No calls found.")
        else:
            st.markdown(f'<div style="font-size:12px;color:#445566;margin-bottom:10px">{len(all_eq)} call(s)</div>', unsafe_allow_html=True)
            for r in all_eq:
                pc = "#00ffb4" if r["call_type"]=="BUY" else "#ff6b6b"
                sc = "#00ffb4" if r["status"]=="Open" else "#445566"
                pnl_str = f"{r['pnl_pct']:+.2f}%" if r['pnl_pct'] else ""
                with st.expander(f"{'🟢' if r['call_type']=='BUY' else '🔴'} {r['symbol']} | {r['status']} | ₹{r['entry_price']} → {pnl_str} | {r['posted_date']}"):
                    m1,m2,m3,m4 = st.columns(4)
                    m1.metric("Entry",    f"₹{r['entry_price']}")
                    m2.metric("Target 1", f"₹{r['target1']}")
                    m3.metric("SL",       f"₹{r['stop_loss']}")
                    m4.metric("Exit",     f"₹{r['exit_price']}" if r['exit_price'] else "—")
                    if r['rationale']: st.caption(f"📝 {r['rationale']}")
                    act1, act2, act3 = st.columns(3)
                    # Reopen closed call
                    if r['status'] == 'Closed':
                        if act1.button("↩️ Reopen", key=f"eq_reopen{r['id']}", use_container_width=True):
                            conn2 = get_conn()
                            conn2.execute("UPDATE equity_calls SET status='Open',exit_price=NULL,result=NULL,pnl_pct=NULL,exit_date=NULL WHERE id=?", (r['id'],))
                            conn2.commit(); conn2.close(); st.success("Reopened!"); st.rerun()
                    else:
                        act1.markdown("")
                    # Edit P&L correction
                    new_pnl = act2.number_input("Correct P&L %", value=float(r['pnl_pct'] or 0), step=0.1, key=f"eq_pnl{r['id']}", format="%.2f")
                    if act2.button("💾 Save P&L", key=f"eq_savepnl{r['id']}", use_container_width=True):
                        conn2 = get_conn()
                        conn2.execute("UPDATE equity_calls SET pnl_pct=? WHERE id=?", (new_pnl, r['id']))
                        conn2.commit(); conn2.close(); st.success("P&L updated!"); st.rerun()
                    # Delete permanently
                    if act3.button("🗑️ Delete Permanently", key=f"eq_permadel{r['id']}", use_container_width=True):
                        conn2 = get_conn()
                        conn2.execute("DELETE FROM equity_calls WHERE id=?", (r['id'],))
                        conn2.commit(); conn2.close(); st.rerun()


def admin_options():
    st.markdown('<div class="section-header">⚡ Options & GEX</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Options calls with GEX-driven analysis</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Options Call","📊 GEX Weekly","📋 Open","📁 History","🔧 Manage All"])
    with tab1:
        with st.form("opt_form"):
            c1, c2 = st.columns(2)
            with c1:
                underlying     = st.selectbox("Underlying",["NIFTY","BANKNIFTY","FINNIFTY","SENSEX","MIDCPNIFTY"])
                option_type    = st.selectbox("CE / PE",["CE","PE"])
                strike         = st.number_input("Strike *",min_value=0.0,step=50.0)
                expiry         = st.text_input("Expiry *",placeholder="27-Mar-2025")
                call_type      = st.selectbox("BUY / SELL",["BUY","SELL"])
            with c2:
                entry_premium  = st.number_input("Entry Premium ₹ *",min_value=0.0,step=0.5)
                target_premium = st.number_input("Target Premium ₹ *",min_value=0.0,step=0.5)
                stop_premium   = st.number_input("Stop Loss Premium ₹ *",min_value=0.0,step=0.5)
                cmp_premium    = st.number_input("CMP Premium ₹",min_value=0.0,step=0.5)
                posted_date    = st.date_input("Date",value=date.today())
            rationale = st.text_area("Trade Rationale",height=80)
            gex_note  = st.text_area("GEX Context *",height=80,placeholder="e.g. +ve GEX above 22,400 → CE sell suits.")
            send_disc = st.checkbox("📤 Send to Discord #options",value=True)
            if st.form_submit_button("Post Options Call →",use_container_width=True):
                if not strike or not entry_premium or not expiry: st.error("Fill required fields.")
                else:
                    call = dict(underlying=underlying,option_type=option_type,strike=strike,
                                expiry=expiry,call_type=call_type,entry_premium=entry_premium,
                                target_premium=target_premium,stop_premium=stop_premium,
                                rationale=rationale,gex_note=gex_note,posted_date=str(posted_date))
                    conn = get_conn()
                    conn.execute("INSERT INTO options_calls (underlying,option_type,strike,expiry,call_type,entry_premium,target_premium,stop_premium,cmp_premium,rationale,gex_note,posted_date,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (underlying,option_type,strike,expiry,call_type,entry_premium,target_premium,stop_premium,cmp_premium,rationale,gex_note,str(posted_date),"Open"))
                    conn.commit(); conn.close()
                    msgs = []
                    if send_disc: ok,_ = discord_options(call); msgs.append(f"Discord:{'✅' if ok else '⚠️'}")
                    st.success("✅ Options call posted"+((" | "+" | ".join(msgs)) if msgs else ""))
    with tab2:
        with st.form("gex_form"):
            c1, c2 = st.columns(2)
            with c1:
                week_date=st.date_input("Week of",value=date.today()); gex_level=st.number_input("Net GEX (₹ Cr)",step=100.0)
                gex_bias=st.selectbox("Market Bias",["Positive GEX — Rangebound","Negative GEX — Volatile","Near Zero — Transition zone"])
            with c2:
                gamma_wall=st.number_input("Gamma Wall",step=50.0); put_support=st.number_input("Put Support",step=50.0); zero_line=st.number_input("Zero Gamma Line",step=50.0)
            outlook=st.text_area("Weekly GEX Outlook *",height=130); send_disc=st.checkbox("📤 Send to Discord",value=True)
            if st.form_submit_button("Post GEX Update →",use_container_width=True):
                content=f"**GEX:** ₹{gex_level:,.0f} Cr | **Bias:** {gex_bias}\n**Gamma Wall:** {gamma_wall} | **Put Support:** {put_support} | **Zero:** {zero_line}\n\n{outlook}"
                conn=get_conn(); conn.execute("INSERT INTO daily_updates (title,category,content,posted_date,tags) VALUES(?,?,?,?,?)",(f"GEX Weekly — {week_date}","GEX",content,str(week_date),"GEX,Options,Weekly")); conn.commit(); conn.close()
                if send_disc: ok,_=discord_embed("options",f"📊 GEX Weekly — {week_date}",content,0x7B61FF)
                st.success("✅ GEX update posted")
    with tab3:
        conn=get_conn()
        for r in conn.execute("SELECT * FROM options_calls WHERE status='Open' ORDER BY created_at DESC").fetchall():
            with st.expander(f"{'⚡' if r['call_type']=='BUY' else '🔻'} {r['underlying']} {r['strike']} {r['option_type']} | {r['expiry']}"):
                c1,c2,c3=st.columns(3); c1.metric("Entry",f"₹{r['entry_premium']}"); c2.metric("Target",f"₹{r['target_premium']}"); c3.metric("SL",f"₹{r['stop_premium']}")
                if r['gex_note']: st.info(f"📊 GEX: {r['gex_note']}")
                ec1,ec2,ec3,ec4=st.columns(4)
                exit_p=ec1.number_input("Exit Premium ₹",key=f"op_ep{r['id']}",min_value=0.0)
                result=ec2.selectbox("Result",["Target Hit","Stop Hit","Expiry","Manual"],key=f"op_res{r['id']}")
                if ec3.button("✅ Close",key=f"op_cl{r['id']}"):
                    pnl=round(((exit_p-r['entry_premium'])/r['entry_premium']*100)*(1 if r['call_type']=='BUY' else -1),2) if exit_p and r['entry_premium'] else 0
                    conn.execute("UPDATE options_calls SET status='Closed',exit_premium=?,result=?,pnl_pct=?,exit_date=date('now') WHERE id=?",(exit_p,result,pnl,r['id']))
                    conn.commit(); st.success(f"Closed | P&L: {pnl:+.2f}%"); st.rerun()
                if ec4.button("🗑️ Delete",key=f"op_del{r['id']}"):
                    conn.execute("DELETE FROM options_calls WHERE id=?", (r['id'],))
                    conn.commit(); st.rerun()
        conn.close()
    with tab4:
        conn=get_conn()
        rows=conn.execute("SELECT * FROM options_calls WHERE status='Closed' ORDER BY exit_date DESC").fetchall()
        if not rows: st.info("No closed calls yet.")
        else:
            pnls=[r['pnl_pct'] for r in rows if r['pnl_pct'] is not None]
            if pnls:
                wins=sum(1 for p in pnls if p>0); m1,m2,m3=st.columns(3)
                m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%"); m3.metric("Total",len(rows))
            for r in rows:
                pc="#00ffb4" if (r['pnl_pct'] or 0)>0 else "#ff6b6b"
                pnl_str=f"{r['pnl_pct']:+.2f}%" if r['pnl_pct'] else "—"
                col_card, col_del = st.columns([10, 1])
                with col_card:
                    st.markdown(f'<div class="call-card closed"><b style="color:#fff">{r["underlying"]} {r["strike"]} {r["option_type"]} | {r["expiry"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:700;float:right;font-size:18px">{pnl_str}</span><br><span style="color:#99aabb;font-size:13px">₹{r["entry_premium"]} → ₹{r["exit_premium"] or "—"} | {r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>',unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑️", key=f"op_hdel{r['id']}", help="Delete this call"):
                        conn.execute("DELETE FROM options_calls WHERE id=?", (r['id'],))
                        conn.commit(); st.rerun()
        conn.close()
    with tab5:
        st.markdown("##### 🔧 Manage All Options Calls")
        st.caption("Search, reopen or permanently delete any options call.")
        conn = get_conn()
        und_search = st.text_input("Search underlying", placeholder="NIFTY, BANKNIFTY...", key="op_mgmt_search")
        status_f2  = st.selectbox("Filter by Status", ["All","Open","Closed"], key="op_mgmt_status")
        q_mgmt2 = "SELECT * FROM options_calls WHERE 1=1"
        p_mgmt2 = []
        if und_search.strip(): q_mgmt2 += " AND underlying LIKE ?"; p_mgmt2.append(f"%{und_search.upper().strip()}%")
        if status_f2 != "All": q_mgmt2 += " AND status=?";          p_mgmt2.append(status_f2)
        q_mgmt2 += " ORDER BY created_at DESC"
        all_op = conn.execute(q_mgmt2, p_mgmt2).fetchall()
        conn.close()
        if not all_op:
            st.info("No calls found.")
        else:
            st.markdown(f'<div style="font-size:12px;color:#445566;margin-bottom:10px">{len(all_op)} call(s)</div>', unsafe_allow_html=True)
            for r in all_op:
                pnl_str = f"{r['pnl_pct']:+.2f}%" if r['pnl_pct'] else ""
                with st.expander(f"{'⚡' if r['call_type']=='BUY' else '🔻'} {r['underlying']} {r['strike']} {r['option_type']} | {r['expiry']} | {r['status']} | ₹{r['entry_premium']} {pnl_str}"):
                    m1,m2,m3,m4 = st.columns(4)
                    m1.metric("Entry",  f"₹{r['entry_premium']}")
                    m2.metric("Target", f"₹{r['target_premium']}")
                    m3.metric("SL",     f"₹{r['stop_premium']}")
                    m4.metric("Exit",   f"₹{r['exit_premium']}" if r['exit_premium'] else "—")
                    if r['gex_note']: st.info(f"📊 GEX: {r['gex_note']}")
                    act1, act2, act3 = st.columns(3)
                    if r['status'] == 'Closed':
                        if act1.button("↩️ Reopen", key=f"op_reopen{r['id']}", use_container_width=True):
                            conn2 = get_conn()
                            conn2.execute("UPDATE options_calls SET status='Open',exit_premium=NULL,result=NULL,pnl_pct=NULL,exit_date=NULL WHERE id=?", (r['id'],))
                            conn2.commit(); conn2.close(); st.success("Reopened!"); st.rerun()
                    else:
                        act1.markdown("")
                    new_pnl2 = act2.number_input("Correct P&L %", value=float(r['pnl_pct'] or 0), step=0.1, key=f"op_pnl{r['id']}", format="%.2f")
                    if act2.button("💾 Save P&L", key=f"op_savepnl{r['id']}", use_container_width=True):
                        conn2 = get_conn()
                        conn2.execute("UPDATE options_calls SET pnl_pct=? WHERE id=?", (new_pnl2, r['id']))
                        conn2.commit(); conn2.close(); st.success("P&L updated!"); st.rerun()
                    if act3.button("🗑️ Delete Permanently", key=f"op_permadel{r['id']}", use_container_width=True):
                        conn2 = get_conn()
                        conn2.execute("DELETE FROM options_calls WHERE id=?", (r['id'],))
                        conn2.commit(); conn2.close(); st.rerun()


def admin_updates():
    st.markdown('<div class="section-header">📢 Daily Updates</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Post market updates to Discord and members</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ New Update","📋 All Updates"])
    with tab1:
        with st.form("upd_form"):
            title=st.text_input("Title *",placeholder="Pre-market Analysis | GEX Update...")
            category=st.selectbox("Category",["Pre-Market","Intraday","Post-Market","GEX Update","Market View","News","Education","General"])
            content=st.text_area("Content *",height=180); tags=st.text_input("Tags",placeholder="Nifty, GEX, Options")
            vid_url=st.text_input("Video URL (optional)",placeholder="https://...")
            posted_date=st.date_input("Date",value=date.today()); send_disc=st.checkbox("📤 Send to Discord",value=True)
            if st.form_submit_button("Post Update →",use_container_width=True):
                if not title or not content: st.error("Title and content required.")
                else:
                    conn=get_conn(); conn.execute("INSERT INTO daily_updates (title,category,content,video_url,tags,posted_date) VALUES(?,?,?,?,?,?)",(title,category,content,vid_url or None,tags,str(posted_date))); conn.commit(); conn.close()
                    if send_disc: discord_embed("updates",f"📢 {title}",content,0x7B61FF)
                    st.success("✅ Update posted")
    with tab2:
        conn=get_conn()
        cat_f=st.selectbox("Filter",["All","Pre-Market","Intraday","Post-Market","GEX Update","Market View","Education"])
        q="SELECT * FROM daily_updates"+(f" WHERE category=?" if cat_f!="All" else "")+" ORDER BY created_at DESC"
        rows=conn.execute(q,(cat_f,) if cat_f!="All" else ()).fetchall(); conn.close()
        for r in rows:
            with st.expander(f"[{r['category']}] {r['title']} — {r['posted_date']}"):
                st.markdown(r['content'])
                c1,c2=st.columns(2)
                if c1.button("📤 Resend Discord",key=f"rs_{r['id']}"): discord_embed("updates",f"📢 {r['title']}",r['content'],0x7B61FF)
                if c2.button("🗑️ Delete",key=f"dd_{r['id']}"): conn2=get_conn(); conn2.execute("DELETE FROM daily_updates WHERE id=?",(r['id'],)); conn2.commit(); conn2.close(); st.rerun()


def admin_videos():
    st.markdown('<div class="section-header">🎬 Video Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Add videos using embed codes (iframe) — no URL needed</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Add Video","📚 Library"])
    with tab1:
        st.markdown("""
        <div style="background:#0a0715;border:1px solid #2d1f4e;border-radius:10px;padding:16px;margin-bottom:16px;font-size:13px;color:#9d8ab5;line-height:1.8">
        <b style="color:#c084fc">How to get embed codes:</b><br>
        • <b>YouTube:</b> Share → Embed → Copy the &lt;iframe&gt; code<br>
        • <b>Google Drive:</b> Share → Anyone with link → &lt;/&gt; Embed<br>
        • <b>Vimeo:</b> Share → Embed → Copy iframe<br>
        • <b>Loom:</b> Share → Embed → Copy embed snippet<br>
        Paste the full <code>&lt;iframe ...&gt;&lt;/iframe&gt;</code> code in the field below.
        </div>
        """, unsafe_allow_html=True)
        with st.form("vid_form"):
            c1, c2 = st.columns(2)
            with c1:
                title     = st.text_input("Title *")
                category  = st.selectbox("Category",["GEX Education","Options Strategy","Equity Analysis","Market Overview","ESG/Valuation","Live Session","Other"])
                duration  = st.text_input("Duration", placeholder="12:35")
                posted_date = st.date_input("Date", value=date.today())
            with c2:
                description = st.text_area("Description", height=100)
            embed_code = st.text_area("Embed Code * (paste full <iframe> code here)", height=120,
                placeholder='<iframe width="560" height="315" src="https://www.youtube.com/embed/..." frameborder="0" allowfullscreen></iframe>')
            if st.form_submit_button("Add to Library →", use_container_width=True):
                if not title or not embed_code:
                    st.error("Title and embed code are required.")
                elif "<iframe" not in embed_code.lower():
                    st.error("Embed code must contain a valid <iframe> tag.")
                else:
                    conn = get_conn()
                    conn.execute("INSERT INTO videos (title,category,description,embed_code,duration,posted_date) VALUES(?,?,?,?,?,?)",
                        (title, category, description, embed_code, duration, str(posted_date)))
                    conn.commit(); conn.close()
                    st.success(f"✅ '{title}' added.")

    with tab2:
        conn = get_conn()
        cat_f = st.selectbox("Filter",["All","GEX Education","Options Strategy","Equity Analysis","Market Overview","Live Session"])
        rows  = conn.execute("SELECT * FROM videos"+(f" WHERE category=?" if cat_f!="All" else "")+" ORDER BY created_at DESC",(cat_f,) if cat_f!="All" else ()).fetchall()
        conn.close()
        for r in rows:
            with st.expander(f"[{r['category']}] {r['title']} — {r['posted_date']}"):
                st.markdown(f"**Description:** {r['description'] or '—'}")
                st.markdown(f"**Duration:** {r['duration'] or '—'}")
                # Preview embed
                if r['embed_code']:
                    safe = r['embed_code'].replace('width="560"','width="100%"').replace("width='560'","width='100%'")
                    st.markdown(f'<div class="video-embed-wrap">{safe}</div>', unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"dv_{r['id']}"):
                    conn2 = get_conn(); conn2.execute("DELETE FROM videos WHERE id=?", (r['id'],)); conn2.commit(); conn2.close(); st.rerun()


def admin_clients():
    st.markdown('<div class="section-header">👥 Client Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Add members, manage subscriptions, Telegram reminders</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Member","👥 All Members","💰 Log Payment","⚠️ Expiring Soon"])
    with tab1:
        with st.form("add_member"):
            c1, c2 = st.columns(2)
            with c1:
                name=st.text_input("Full Name *"); username=st.text_input("Login Username *",placeholder="rahul_sharma")
                password=st.text_input("Initial Password *",type="password"); discord_id=st.text_input("Discord Username")
                telegram_id=st.text_input("Telegram Chat ID",placeholder="Get via @userinfobot")
            with c2:
                email=st.text_input("Email"); phone=st.text_input("Phone")
                plan=st.selectbox("Plan",list(PLAN_AMOUNTS.keys())); status=st.selectbox("Status",["Active","Trial","Inactive"])
                joined=st.date_input("Joined",value=date.today())
                days_map={"Equity Monthly":30,"Equity Quarterly":90,"Equity Annual":365,"Options Monthly":30,"Options Quarterly":90,"Options Annual":365,"Combo Monthly":30,"Combo Quarterly":90,"Combo Annual":365,"Trial":7}
                expiry=st.date_input("Expiry",value=joined+timedelta(days=days_map.get(plan,30)))
            notes=st.text_area("Notes"); send_tg=st.checkbox("📲 Send Telegram welcome",value=True)
            if st.form_submit_button("Add Member →",use_container_width=True):
                if not name or not username or not password: st.error("Name, username and password required.")
                else:
                    conn=get_conn()
                    try:
                        conn.execute("INSERT INTO clients (name,username,password_hash,discord_id,telegram_id,email,phone,plan,status,joined_date,expiry_date,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            (name,username.lower().strip(),hash_password(password),discord_id,telegram_id,email,phone,plan,status,str(joined),str(expiry),notes))
                        conn.commit()
                        # Show plan access
                        access = PLAN_ACCESS.get(plan, [])
                        access_str = " + ".join([a.capitalize() for a in access])
                        tg_msg = ""
                        if send_tg and telegram_id:
                            ok,_ = tg_welcome(telegram_id,name,username,password,plan); tg_msg=f" | TG:{'✅' if ok else '⚠️'}"
                        st.success(f"✅ {name} added | **{username}** | Access: **{access_str}**{tg_msg}")
                    except Exception as e: st.error(f"Username exists: {e}")
                    finally: conn.close()
    with tab2:
        conn=get_conn(); search=st.text_input("🔍 Search"); s=f"%{search}%"
        rows=conn.execute("SELECT * FROM clients WHERE name LIKE ? OR username LIKE ? ORDER BY created_at DESC",(s,s)).fetchall() if search else conn.execute("SELECT * FROM clients ORDER BY created_at DESC").fetchall(); conn.close()
        m1,m2,m3,m4=st.columns(4); m1.metric("Total",len(rows)); m2.metric("Active",sum(1 for r in rows if r['status']=='Active')); m3.metric("Trial",sum(1 for r in rows if r['status']=='Trial')); m4.metric("Inactive",sum(1 for r in rows if r['status']=='Inactive'))
        for r in rows:
            exp=date.fromisoformat(r['expiry_date']) if r['expiry_date'] else None; dl=(exp-date.today()).days if exp else None
            sc={"Active":"#00ffb4","Inactive":"#ff6b6b","Trial":"#ffd700"}.get(r['status'],"#aaa")
            warn=f" ⚠️{dl}d" if dl and dl<=7 else (f" {dl}d" if dl else "")
            access=PLAN_ACCESS.get(r['plan'],[]); access_badges=" ".join([f'<span style="background:{"#00ffb422" if a=="equity" else "#7b61ff22"};color:{"#00ffb4" if a=="equity" else "#9b7af7"};border:1px solid {"#00ffb444" if a=="equity" else "#7b61ff44"};border-radius:12px;padding:1px 8px;font-size:10px;font-weight:700">{a.upper()}</span>' for a in access])
            with st.expander(f"{'🟢' if r['status']=='Active' else '🔴'} {r['name']} (@{r['username']}) | {r['plan']}{warn}"):
                st.markdown(f'**Status:** <span style="color:{sc}">{r["status"]}</span> &nbsp; **Expires:** {r["expiry_date"] or "—"} &nbsp; **Days:** {f"{dl}d" if dl else "—"} &nbsp; **Access:** {access_badges}',unsafe_allow_html=True)
                if r['notes']: st.caption(f"📝 {r['notes']}")
                ac1,ac2=st.columns(2)
                if ac1.button("📲 Send Reminder",key=f"tgr_{r['id']}"):
                    if r['telegram_id']: ok,msg=tg_renewal_reminder(r['telegram_id'],r['name'],dl or 0,r['plan'],r['expiry_date'] or '—'); st.success(msg) if ok else st.error(msg)
                    else: st.warning("No Telegram ID.")
                with st.expander("🔑 Reset Password"):
                    np=st.text_input("New Password",type="password",key=f"pw_{r['id']}")
                    if st.button("Reset",key=f"rst_{r['id']}"): conn2=get_conn(); conn2.execute("UPDATE clients SET password_hash=? WHERE id=?",(hash_password(np),r['id'])); conn2.commit(); conn2.close(); st.success("Reset.")
                ec1,ec2,ec3,ec4=st.columns(4)
                new_st=ec1.selectbox("Status",["Active","Inactive","Trial"],index=["Active","Inactive","Trial"].index(r['status']),key=f"st_{r['id']}")
                ext_days=ec2.number_input("Extend (days)",0,365,key=f"ext_{r['id']}"); tg_new=ec3.text_input("Telegram ID",value=r['telegram_id'] or "",key=f"tgid_{r['id']}")
                if ec4.button("Update",key=f"upd_{r['id']}"):
                    new_exp=r['expiry_date']
                    if ext_days>0 and exp: new_exp=str(exp+timedelta(days=int(ext_days)))
                    conn2=get_conn(); conn2.execute("UPDATE clients SET status=?,expiry_date=?,telegram_id=? WHERE id=?",(new_st,new_exp,tg_new or None,r['id'])); conn2.commit(); conn2.close(); st.success("Updated!"); st.rerun()
                if st.button("🗑️ Remove",key=f"del_{r['id']}"): conn2=get_conn(); conn2.execute("DELETE FROM clients WHERE id=?",(r['id'],)); conn2.commit(); conn2.close(); st.rerun()
    with tab3:
        conn=get_conn(); ml=conn.execute("SELECT id,name,username FROM clients ORDER BY name").fetchall(); conn.close()
        if not ml: st.info("Add members first.")
        else:
            opts={f"{m['name']} (@{m['username']})":m['id'] for m in ml}
            with st.form("log_payment"):
                sel=st.selectbox("Member *",list(opts.keys())); amount=st.number_input("Amount ₹ *",min_value=0.0,step=1.0)
                plan=st.selectbox("Plan",list(PLAN_AMOUNTS.keys())); method=st.selectbox("Method",["UPI","Bank Transfer","Cash","Card","Other"])
                pd_=st.date_input("Payment Date",value=date.today()); pnotes=st.text_input("Notes / Ref ID"); extend=st.checkbox("Auto-extend subscription",value=True)
                if st.form_submit_button("Log Payment →",use_container_width=True):
                    if not amount: st.error("Amount required.")
                    else:
                        cid=opts[sel]; new_exp=None; conn2=get_conn()
                        conn2.execute("INSERT INTO payments (client_id,amount,plan,status,payment_method,notes,payment_date) VALUES(?,?,?,?,?,?,?)",(cid,amount,plan,'captured',method,pnotes,str(pd_)))
                        if extend:
                            days_map={"Equity Monthly":30,"Equity Quarterly":90,"Equity Annual":365,"Options Monthly":30,"Options Quarterly":90,"Options Annual":365,"Combo Monthly":30,"Combo Quarterly":90,"Combo Annual":365,"Trial":7}
                            row=conn2.execute("SELECT expiry_date FROM clients WHERE id=?",(cid,)).fetchone()
                            try:
                                base=date.fromisoformat(row['expiry_date']) if row['expiry_date'] else date.today()
                                if base<date.today(): base=date.today()
                                new_exp=str(base+timedelta(days=days_map.get(plan,30)))
                            except: new_exp=str(date.today()+timedelta(days=30))
                            conn2.execute("UPDATE clients SET status='Active',expiry_date=?,plan=? WHERE id=?",(new_exp,plan,cid))
                        conn2.commit(); conn2.close()
                        st.success(f"✅ ₹{amount:,.0f} logged."+(f" Extended to {new_exp}" if new_exp else ""))
            st.divider()
            st.markdown("#### 📋 Payment History")
            conn3=get_conn(); pays=conn3.execute("SELECT p.*,c.name,c.username FROM payments p LEFT JOIN clients c ON p.client_id=c.id ORDER BY p.created_at DESC").fetchall(); conn3.close()
            if pays:
                total=sum(p['amount'] for p in pays if p['amount'])
                st.markdown(f'<div class="metric-card" style="max-width:300px"><div class="metric-value" style="color:#00ffb4">₹{total:,.0f}</div><div class="metric-label">Total Revenue</div></div>',unsafe_allow_html=True)
                for p in pays:
                    st.markdown(f'<div class="call-card"><b style="color:#fff">{p["name"] or "Unknown"}</b> <span style="color:#445566">@{p["username"] or "—"}</span><span style="color:#00ffb4;float:right;font-weight:800;font-size:20px">₹{p["amount"]:,.0f}</span><br><span style="color:#99aabb;font-size:13px">{p["plan"]} | {p["payment_method"] or "—"} | {p["notes"] or "—"} | {p["payment_date"] or "—"}</span></div>',unsafe_allow_html=True)
    with tab4:
        conn=get_conn(); rows=conn.execute("SELECT * FROM clients WHERE status='Active' AND expiry_date IS NOT NULL AND expiry_date<=date('now','+7 days') ORDER BY expiry_date").fetchall(); conn.close()
        if not rows: st.success("✅ No renewals due in 7 days.")
        else:
            st.warning(f"⚠️ {len(rows)} member(s) expiring soon!")
            if st.button("📲 Send Bulk Reminders",type="primary"):
                sent=0
                for r in rows:
                    if r['telegram_id']:
                        dl=(date.fromisoformat(r['expiry_date'])-date.today()).days
                        ok,_=tg_renewal_reminder(r['telegram_id'],r['name'],dl,r['plan'],r['expiry_date'])
                        if ok: sent+=1
                st.success(f"✅ Sent {sent} reminder(s).")
            for r in rows:
                dl=(date.fromisoformat(r['expiry_date'])-date.today()).days
                st.markdown(f'<div class="call-card" style="border-left-color:#ffd700">{"🔴" if dl<=2 else "🟡"} <b style="color:#fff">{r["name"]}</b> @{r["username"]}<span style="color:#ffd700;float:right;font-weight:700">{dl}d left</span><br><span style="color:#99aabb;font-size:13px">{r["plan"]} | {r["expiry_date"]}</span></div>',unsafe_allow_html=True)


def admin_performance():
    st.markdown('<div class="section-header">📈 Performance Analytics</div>', unsafe_allow_html=True)
    conn=get_conn()
    eq_rows=conn.execute("SELECT symbol,call_type,entry_price,exit_price,pnl_pct,result,exit_date FROM equity_calls WHERE status='Closed' AND pnl_pct IS NOT NULL ORDER BY exit_date").fetchall()
    op_rows=conn.execute("SELECT underlying,option_type,strike,call_type,entry_premium,exit_premium,pnl_pct,result,exit_date FROM options_calls WHERE status='Closed' AND pnl_pct IS NOT NULL ORDER BY exit_date").fetchall()
    conn.close()
    tab1,tab2,tab3=st.tabs(["📊 Equity","⚡ Options","🔄 Combined"])
    with tab1:
        if not eq_rows: st.info("No closed equity calls yet.")
        else:
            pnls=[r['pnl_pct'] for r in eq_rows]; wins=sum(1 for p in pnls if p>0)
            m1,m2,m3,m4=st.columns(4); m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%"); m3.metric("Best",f"{max(pnls):+.2f}%"); m4.metric("Worst",f"{min(pnls):+.2f}%")
            cum=[]; r=0
            for p in pnls: r+=p; cum.append(round(r,2))
            render_line_chart("Cumulative Equity P&L (%)",[r['exit_date'] or f"#{i+1}" for i,r in enumerate(eq_rows)],cum,"#00ffb4")
            render_bar_chart("Individual Call P&L (%)",[r['symbol'] for r in eq_rows],pnls,["#00ffb4" if p>0 else "#ff6b6b" for p in pnls])
    with tab2:
        if not op_rows: st.info("No closed options calls yet.")
        else:
            pnls=[r['pnl_pct'] for r in op_rows]; wins=sum(1 for p in pnls if p>0)
            m1,m2,m3,m4=st.columns(4); m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%"); m3.metric("Best",f"{max(pnls):+.2f}%"); m4.metric("Worst",f"{min(pnls):+.2f}%")
            cum=[]; r=0
            for p in pnls: r+=p; cum.append(round(r,2))
            render_line_chart("Cumulative Options P&L (%)",[r['exit_date'] or f"#{i+1}" for i,r in enumerate(op_rows)],cum,"#7b61ff")
            render_bar_chart("Individual Options P&L (%)",[f"{r['underlying']} {r['strike']}{r['option_type']}" for r in op_rows],pnls,["#00ffb4" if p>0 else "#ff6b6b" for p in pnls])
    with tab3:
        all_pnls=[r['pnl_pct'] for r in eq_rows]+[r['pnl_pct'] for r in op_rows]
        if not all_pnls: st.info("No closed calls yet.")
        else:
            tw=sum(1 for p in all_pnls if p>0); avg=sum(all_pnls)/len(all_pnls)
            st.markdown(f"""<div class="sub-card" style="text-align:center;padding:40px">
              <div class="winrate-badge" style="font-size:36px;padding:12px 40px">{tw/len(all_pnls)*100:.0f}% Win Rate</div>
              <div style="display:flex;justify-content:center;gap:60px;margin-top:30px">
                <div><div class="metric-label">Total</div><div class="metric-value">{len(all_pnls)}</div></div>
                <div><div class="metric-label">Wins</div><div class="metric-value" style="color:#00ffb4">{tw}</div></div>
                <div><div class="metric-label">Avg P&L</div><div class="metric-value" style="color:{'#00ffb4' if avg>0 else '#ff6b6b'}">{avg:+.1f}%</div></div>
              </div></div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# MEMBER SHARED — Research Hub page (used by all portals)
# ══════════════════════════════════════════════════════════════════════

def member_research(member):
    st.markdown('<div class="section-header">📄 Research Hub</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Broker research reports & buy/sell calls — PDF viewer, no download</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📋 Research Reports", "🏦 Broker Calls"])

    with tab1:
        conn = get_conn()
        f1, f2, f3, f4 = st.columns(4)
        broker_f = f1.selectbox("Broker", ["All"] + BROKER_HOUSES, key="m_broker_f")
        cat_f    = f2.selectbox("Category", ["All"] + REPORT_CATEGORIES, key="m_cat_f")
        call_f   = f3.selectbox("Rating", ["All","BUY","SELL","HOLD","ACCUMULATE","NEUTRAL"], key="m_call_f")
        sym_f    = f4.text_input("Symbol", placeholder="RELIANCE...", key="m_sym_f")

        # Safe query — works on old and new DB schemas
        def _fetch_reports(conn, portal, broker_f, cat_f, call_f, sym_f):
            # Try full query with pdf_data check first
            try:
                q = """SELECT id, title, broker_house, category, symbol, call_type,
                              target_price, current_price, upside_pct, analyst,
                              report_date, sector, tags, notes,
                              COALESCE(visible_to, 'all') as visible_to,
                              COALESCE(pdf_filename, '') as pdf_filename,
                              CASE WHEN pdf_data IS NOT NULL THEN 1 ELSE 0 END AS has_pdf
                       FROM research_reports
                       WHERE (COALESCE(visible_to,'all')='all' OR COALESCE(visible_to,'all')=?)"""
                params = [portal]
                if broker_f != "All": q += " AND broker_house=?";  params.append(broker_f)
                if cat_f    != "All": q += " AND category=?";      params.append(cat_f)
                if call_f   != "All": q += " AND call_type=?";     params.append(call_f)
                if sym_f.strip():     q += " AND symbol LIKE ?";   params.append(f"%{sym_f.upper().strip()}%")
                q += " ORDER BY created_at DESC"
                return conn.execute(q, params).fetchall()
            except Exception:
                # Fallback for very old schemas — no pdf columns at all
                try:
                    q2 = "SELECT id, title, COALESCE(broker_house,'') as broker_house, COALESCE(category,'') as category, COALESCE(symbol,'') as symbol, COALESCE(call_type,'') as call_type, COALESCE(target_price,0) as target_price, COALESCE(current_price,0) as current_price, COALESCE(upside_pct,0) as upside_pct, COALESCE(analyst,'') as analyst, COALESCE(report_date,'') as report_date, COALESCE(sector,'') as sector, COALESCE(tags,'') as tags, COALESCE(notes,'') as notes, 'all' as visible_to, '' as pdf_filename, 0 as has_pdf FROM research_reports ORDER BY created_at DESC"
                    return conn.execute(q2).fetchall()
                except Exception:
                    return []

        rows = _fetch_reports(conn, st.session_state.get("active_portal", "equity"), broker_f, cat_f, call_f, sym_f)
        conn.close()

        if not rows:
            st.info("No research reports available yet.")
        else:
            st.markdown(f'<div style="font-size:12px;color:#445566;margin-bottom:16px">{len(rows)} report(s) found</div>', unsafe_allow_html=True)
            for r in rows:
                r = dict(r)
                ct_color = {"BUY":"#00ffb4","SELL":"#ff6b6b","HOLD":"#ffd700","ACCUMULATE":"#00ddff","NEUTRAL":"#9d8ab5"}.get((r.get('call_type') or "").upper(),"#9d8ab5")
                lbl = f"[{r['broker_house']}]  {r['symbol'] or '—'}  ·  {r['call_type']}  ·  {r['title'][:50]}  ·  {r['report_date']}"
                with st.expander(lbl):
                    render_report_meta(r)
                    if r['has_pdf']:
                        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                        view_key = f"view_pdf_{r['id']}"
                        if st.button("📖 Open PDF Viewer", key=f"opv_{r['id']}", use_container_width=False):
                            st.session_state[view_key] = not st.session_state.get(view_key, False)
                        if st.session_state.get(view_key, False):
                            st.markdown('<div style="margin-top:8px;font-size:11px;color:#3b2d55;letter-spacing:1px">🔒 PDF is displayed in secure viewer · Saving or downloading is not permitted</div>', unsafe_allow_html=True)
                            conn2 = get_conn()
                            pdf_row = conn2.execute("SELECT pdf_data FROM research_reports WHERE id=?", (r['id'],)).fetchone()
                            conn2.close()
                            if pdf_row and pdf_row['pdf_data']:
                                render_pdf_viewer(bytes(pdf_row['pdf_data']), r['id'])
                            else:
                                st.error("PDF not found in database.")
                    else:
                        st.info("PDF not yet uploaded for this report.")

    with tab2:
        conn = get_conn()
        bf1, bf2, bf3 = st.columns(3)
        bc_b = bf1.selectbox("Broker", ["All"] + BROKER_HOUSES, key="m_bc_broker")
        bc_c = bf2.selectbox("Call", ["All","BUY","SELL","HOLD"], key="m_bc_call")
        bc_s = bf3.selectbox("Status", ["All","Active","Target Hit","Stop Hit","Closed"], key="m_bc_status")
        q2 = "SELECT * FROM broker_calls WHERE 1=1"; p2 = []
        if bc_b != "All": q2 += " AND broker_house=?"; p2.append(bc_b)
        if bc_c != "All": q2 += " AND call_type=?";    p2.append(bc_c)
        if bc_s != "All": q2 += " AND status=?";       p2.append(bc_s)
        q2 += " ORDER BY created_at DESC"
        try:
            bc_rows = conn.execute(q2, p2).fetchall()
        except Exception:
            bc_rows = []
        conn.close()
        if not bc_rows:
            st.info("No broker calls available yet.")
        else:
            # Summary metrics
            active  = sum(1 for r in bc_rows if r['status'] == 'Active')
            t_hit   = sum(1 for r in bc_rows if r['status'] == 'Target Hit')
            s_hit   = sum(1 for r in bc_rows if r['status'] == 'Stop Hit')
            buys    = sum(1 for r in bc_rows if r['call_type'] == 'BUY')
            sells   = sum(1 for r in bc_rows if r['call_type'] == 'SELL')
            m1,m2,m3,m4,m5 = st.columns(5)
            m1.metric("Total",    len(bc_rows)); m2.metric("Active", active)
            m3.metric("Target ✅", t_hit);       m4.metric("Stop ❌", s_hit)
            m5.metric("BUY/SELL", f"{buys}/{sells}")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            for r in bc_rows:
                render_broker_call_card(dict(r))

# ══════════════════════════════════════════════════════════════════════
# EQUITY MEMBER PAGES
# ══════════════════════════════════════════════════════════════════════

def equity_home(member):
    st.markdown(f'<div class="section-header">Welcome, {member["name"].split()[0]} 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Equity Premium Dashboard</div>', unsafe_allow_html=True)
    conn = get_conn()
    c1,c2,c3,c4 = st.columns(4)
    open_eq = conn.execute("SELECT COUNT(*) FROM equity_calls WHERE status='Open'").fetchone()[0]
    eq_c    = conn.execute("SELECT pnl_pct FROM equity_calls WHERE status='Closed' AND pnl_pct IS NOT NULL").fetchall()
    eq_wr   = f"{sum(1 for r in eq_c if r[0]>0)/len(eq_c)*100:.0f}%" if eq_c else "—"
    avg_pnl = f"{sum(r[0] for r in eq_c)/len(eq_c):+.1f}%" if eq_c else "—"
    reps    = conn.execute("SELECT COUNT(*) FROM research_reports").fetchone()[0]
    for col,val,label,color in [(c1,open_eq,"Equity Open","#00ffb4"),(c2,eq_wr,"Win Rate","#00ddff"),(c3,avg_pnl,"Avg P&L","#ffd700"),(c4,reps,"Research Reports","#c084fc")]:
        col.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{color}">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("#### 📢 Today's Updates")
    updates = conn.execute("SELECT * FROM daily_updates WHERE posted_date=? ORDER BY created_at DESC",(str(date.today()),)).fetchall()
    if updates:
        for u in updates:
            st.markdown(f'<div class="update-card"><span class="tag">{u["category"]}</span><div style="font-weight:700;font-size:17px;margin:10px 0 8px;color:#fff">{u["title"]}</div><div style="color:#c0d0e0;line-height:1.6">{u["content"][:400]}{"..." if len(u["content"])>400 else ""}</div></div>', unsafe_allow_html=True)
    else: st.info("No updates today yet.")
    st.divider()
    st.markdown("#### 📊 Active Equity Calls")
    for r in conn.execute("SELECT * FROM equity_calls WHERE status='Open' ORDER BY created_at DESC LIMIT 5").fetchall():
        rr = round((r['target1']-r['entry_price'])/(r['entry_price']-r['stop_loss']),2) if r['entry_price'] and r['stop_loss'] and r['stop_loss']!=r['entry_price'] else None
        st.markdown(f"""<div class="call-card {r['call_type'].lower()}">
          <b style="color:#fff;font-size:18px">{r['symbol']}</b><span class="badge badge-{r['call_type'].lower()}">{r['call_type']}</span><span class="badge badge-open">OPEN</span>
          <div style="display:flex;gap:24px;margin-top:10px;flex-wrap:wrap">
            <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Entry</div><div style="font-size:20px;font-weight:700;color:#fff">₹{r['entry_price']}</div></div>
            <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Target 1</div><div style="font-size:20px;font-weight:700;color:#00ffb4">₹{r['target1']}</div></div>
            <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Stop Loss</div><div style="font-size:20px;font-weight:700;color:#ff6b6b">₹{r['stop_loss']}</div></div>
            {f"<div><div style='font-size:10px;color:#445566;text-transform:uppercase'>R:R</div><div style='font-size:20px;font-weight:700;color:#ffd700'>1:{rr}</div></div>" if rr else ""}
          </div>
          {f"<div style='margin-top:8px;font-size:13px;color:#99aabb'>{r['rationale']}</div>" if r['rationale'] else ""}
        </div>""", unsafe_allow_html=True)
    conn.close()


def equity_track_record(member):
    st.markdown('<div class="section-header">📈 Equity Track Record</div>', unsafe_allow_html=True)
    conn = get_conn()
    rows = conn.execute("SELECT * FROM equity_calls WHERE status='Closed' AND pnl_pct IS NOT NULL ORDER BY exit_date").fetchall()
    conn.close()
    if not rows: st.info("No closed equity calls yet."); return
    pnls = [r['pnl_pct'] for r in rows]; wins = sum(1 for p in pnls if p > 0)
    st.markdown(f"""<div class="sub-card" style="text-align:center;padding:36px">
      <div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:4px;margin-bottom:16px">Verified Equity Track Record</div>
      <div class="winrate-badge" style="font-size:32px;padding:10px 36px">{wins/len(pnls)*100:.0f}% Win Rate</div>
      <div style="display:flex;justify-content:center;gap:50px;margin-top:28px;flex-wrap:wrap">
        <div><div class="metric-label">Total</div><div class="metric-value">{len(pnls)}</div></div>
        <div><div class="metric-label">Winners</div><div class="metric-value" style="color:#00ffb4">{wins}</div></div>
        <div><div class="metric-label">Avg P&L</div><div class="metric-value" style="color:{'#00ffb4' if sum(pnls)/len(pnls)>0 else '#ff6b6b'}">{sum(pnls)/len(pnls):+.1f}%</div></div>
        <div><div class="metric-label">Best</div><div class="metric-value" style="color:#00ffb4">{max(pnls):+.0f}%</div></div>
      </div></div>""", unsafe_allow_html=True)
    cum = []; r = 0
    for p in pnls: r += p; cum.append(round(r, 2))
    render_line_chart("Cumulative Equity P&L (%)", [r['exit_date'] or f"#{i+1}" for i,r in enumerate(rows)], cum, "#00ffb4")
    render_bar_chart("Individual Call P&L (%)", [r['symbol'] for r in rows], pnls, ["#00ffb4" if p>0 else "#ff6b6b" for p in pnls])
    for r in rows[::-1]:
        pc = "#00ffb4" if r['pnl_pct'] > 0 else "#ff6b6b"
        st.markdown(f'<div class="call-card closed"><b style="color:#fff">{r["symbol"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:800;float:right">{r["pnl_pct"]:+.2f}%</span><br><span style="color:#99aabb;font-size:12px">{r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# OPTIONS MEMBER PAGES
# ══════════════════════════════════════════════════════════════════════

def options_home(member):
    st.markdown(f'<div class="section-header">Welcome, {member["name"].split()[0]} ⚡</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Options & GEX Premium Dashboard</div>', unsafe_allow_html=True)
    conn = get_conn()
    c1,c2,c3,c4 = st.columns(4)
    open_op = conn.execute("SELECT COUNT(*) FROM options_calls WHERE status='Open'").fetchone()[0]
    op_c    = conn.execute("SELECT pnl_pct FROM options_calls WHERE status='Closed' AND pnl_pct IS NOT NULL").fetchall()
    op_wr   = f"{sum(1 for r in op_c if r[0]>0)/len(op_c)*100:.0f}%" if op_c else "—"
    avg_pnl = f"{sum(r[0] for r in op_c)/len(op_c):+.1f}%" if op_c else "—"
    reps    = conn.execute("SELECT COUNT(*) FROM research_reports").fetchone()[0]
    for col,val,label,color in [(c1,open_op,"Options Open","#7b61ff"),(c2,op_wr,"Win Rate","#00ddff"),(c3,avg_pnl,"Avg P&L","#ffd700"),(c4,reps,"Research Reports","#c084fc")]:
        col.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{color}">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("#### 📢 Today's Updates")
    updates = conn.execute("SELECT * FROM daily_updates WHERE posted_date=? ORDER BY created_at DESC",(str(date.today()),)).fetchall()
    if updates:
        for u in updates:
            st.markdown(f'<div class="update-card"><span class="tag">{u["category"]}</span><div style="font-weight:700;font-size:17px;margin:10px 0 8px;color:#fff">{u["title"]}</div><div style="color:#c0d0e0;line-height:1.6">{u["content"][:400]}{"..." if len(u["content"])>400 else ""}</div></div>', unsafe_allow_html=True)
    else: st.info("No updates today yet.")
    st.divider()
    st.markdown("#### ⚡ Active Options Calls")
    for r in conn.execute("SELECT * FROM options_calls WHERE status='Open' ORDER BY created_at DESC LIMIT 5").fetchall():
        st.markdown(f"""<div class="call-card {r['call_type'].lower()}">
          <b style="color:#fff;font-size:18px">{r['underlying']} {r['strike']} {r['option_type']}</b><span class="badge badge-{r['call_type'].lower()}">{r['call_type']}</span>
          <span style="font-size:12px;color:#445566;float:right">Exp: {r['expiry']}</span>
          <div style="display:flex;gap:24px;margin-top:10px;flex-wrap:wrap">
            <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Entry</div><div style="font-size:20px;font-weight:700;color:#fff">₹{r['entry_premium']}</div></div>
            <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Target</div><div style="font-size:20px;font-weight:700;color:#00ffb4">₹{r['target_premium']}</div></div>
            <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Stop Loss</div><div style="font-size:20px;font-weight:700;color:#ff6b6b">₹{r['stop_premium']}</div></div>
          </div>
          {f"<div style='margin-top:8px;background:#020e20;border-radius:6px;padding:8px;font-size:13px;color:#c0d0e0'><b style='color:#7b61ff'>GEX:</b> {r['gex_note']}</div>" if r['gex_note'] else ""}
        </div>""", unsafe_allow_html=True)
    conn.close()


def options_gex_analysis(member):
    st.markdown('<div class="section-header">📊 GEX Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Weekly Gamma Exposure maps and analysis</div>', unsafe_allow_html=True)
    conn = get_conn()
    rows = conn.execute("SELECT * FROM daily_updates WHERE category='GEX' ORDER BY created_at DESC LIMIT 12").fetchall()
    conn.close()
    if not rows: st.info("No GEX analysis posted yet.")
    for r in rows:
        with st.expander(f"📊 {r['title']} — {r['posted_date']}"):
            st.markdown(r['content'])


def options_track_record(member):
    st.markdown('<div class="section-header">📈 Options Track Record</div>', unsafe_allow_html=True)
    conn = get_conn()
    rows = conn.execute("SELECT * FROM options_calls WHERE status='Closed' AND pnl_pct IS NOT NULL ORDER BY exit_date").fetchall()
    conn.close()
    if not rows: st.info("No closed options calls yet."); return
    pnls = [r['pnl_pct'] for r in rows]; wins = sum(1 for p in pnls if p > 0)
    st.markdown(f"""<div class="sub-card" style="text-align:center;padding:36px">
      <div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:4px;margin-bottom:16px">Verified Options Track Record</div>
      <div class="winrate-badge" style="font-size:32px;padding:10px 36px">{wins/len(pnls)*100:.0f}% Win Rate</div>
      <div style="display:flex;justify-content:center;gap:50px;margin-top:28px;flex-wrap:wrap">
        <div><div class="metric-label">Total</div><div class="metric-value">{len(pnls)}</div></div>
        <div><div class="metric-label">Winners</div><div class="metric-value" style="color:#00ffb4">{wins}</div></div>
        <div><div class="metric-label">Avg P&L</div><div class="metric-value" style="color:{'#00ffb4' if sum(pnls)/len(pnls)>0 else '#ff6b6b'}">{sum(pnls)/len(pnls):+.1f}%</div></div>
        <div><div class="metric-label">Best</div><div class="metric-value" style="color:#00ffb4">{max(pnls):+.0f}%</div></div>
      </div></div>""", unsafe_allow_html=True)
    cum = []; r = 0
    for p in pnls: r += p; cum.append(round(r, 2))
    render_line_chart("Cumulative Options P&L (%)", [r['exit_date'] or f"#{i+1}" for i,r in enumerate(rows)], cum, "#7b61ff")
    for r in rows[::-1]:
        pc = "#00ffb4" if r['pnl_pct'] > 0 else "#ff6b6b"
        st.markdown(f'<div class="call-card closed"><b style="color:#fff">{r["underlying"]} {r["strike"]} {r["option_type"]} | {r["expiry"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:800;float:right">{r["pnl_pct"]:+.2f}%</span><br><span style="color:#99aabb;font-size:12px">{r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SHARED MEMBER PAGES (used by both portals)
# ══════════════════════════════════════════════════════════════════════

def member_updates(member):
    st.markdown('<div class="section-header">📢 Updates Feed</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Daily market analysis, GEX maps, insights from Dr. Niyas</div>', unsafe_allow_html=True)
    conn = get_conn()
    f1, f2 = st.columns([2, 1])
    cat_f  = f1.selectbox("Category",["All","Pre-Market","Intraday","Post-Market","GEX Update","Market View","Education","General"])
    date_f = f2.date_input("Date", value=None)
    q = "SELECT * FROM daily_updates"; params = []; conds = []
    if cat_f != "All": conds.append("category=?"); params.append(cat_f)
    if date_f:         conds.append("posted_date=?"); params.append(str(date_f))
    if conds: q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY created_at DESC"
    rows = conn.execute(q, params).fetchall(); conn.close()
    if not rows: st.info("No updates in this category.")
    for r in rows:
        cc = {"Pre-Market":"#00ddff","GEX Update":"#7b61ff","Intraday":"#ffd700","Post-Market":"#00ffb4","Market View":"#ff6b6b","Education":"#00ffb4"}.get(r['category'],"#445566")
        tags = " ".join([f'<span class="tag">{t.strip()}</span>' for t in r['tags'].split(',')]) if r['tags'] else ""
        st.markdown(f"""<div class="update-card">
          <div style="display:flex;justify-content:space-between;margin-bottom:12px">
            <span style="background:{cc}22;color:{cc};border:1px solid {cc}44;border-radius:20px;font-size:11px;padding:2px 12px;font-weight:700;text-transform:uppercase">{r['category']}</span>
            <div style="font-size:12px;color:#445566">{r['posted_date'] or ''}</div>
          </div>
          <div style="font-size:20px;font-weight:700;color:#fff;margin-bottom:12px">{r['title']}</div>
          <div style="color:#c0d0e0;line-height:1.7;font-size:15px">{r['content']}</div>
          {('<div style="margin-top:12px">'+tags+'</div>') if tags else ""}
        </div>""", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#0a2040;margin:4px 0 20px'>", unsafe_allow_html=True)


def member_videos(member):
    st.markdown('<div class="section-header">🎬 Video Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Premium educational videos — embedded, view-only</div>', unsafe_allow_html=True)
    conn = get_conn()
    cat_f = st.selectbox("Browse by Category",["All","GEX Education","Options Strategy","Equity Analysis","Market Overview","ESG/Valuation","Live Session","Other"])
    rows  = conn.execute("SELECT * FROM videos"+(f" WHERE category=?" if cat_f!="All" else "")+" ORDER BY created_at DESC",(cat_f,) if cat_f!="All" else ()).fetchall()
    conn.close()
    if not rows: st.info("No videos in this category yet."); return

    if cat_f == "All":
        from collections import defaultdict
        grouped = defaultdict(list)
        for r in rows: grouped[r['category']].append(r)
        icons = {"GEX Education":"📊","Options Strategy":"⚡","Equity Analysis":"📈","Market Overview":"🌐","ESG/Valuation":"🏷️","Live Session":"🔴","Other":"🎬"}
        for cat, vids in grouped.items():
            st.markdown(f"#### {icons.get(cat,'🎬')} {cat}")
            _video_embed_grid(vids); st.divider()
    else:
        _video_embed_grid(rows)


def _video_embed_grid(rows):
    for r in rows:
        with st.expander(f"🎬 {r['title']} — {r['posted_date'] or ''}  |  {r['duration'] or ''}"):
            if r['description']:
                st.markdown(f'<div style="font-size:13px;color:#9d8ab5;margin-bottom:12px">{r["description"]}</div>', unsafe_allow_html=True)
            if r['embed_code']:
                # Make embed responsive and full width
                safe = r['embed_code'].replace('width="560"','width="100%"').replace("width='560'","width='100%'")
                safe = safe.replace('height="315"','height="400"').replace("height='315'","height='400'")
                st.markdown(f'<div class="video-embed-wrap">{safe}</div>', unsafe_allow_html=True)
                st.markdown('<div style="font-size:10px;color:#3b2d55;margin-top:6px;letter-spacing:1px">🔒 View only — download disabled</div>', unsafe_allow_html=True)
            else:
                st.warning("No embed code available for this video.")


def member_profile(member, portal_type):
    exp      = date.fromisoformat(member['expiry_date']) if member.get('expiry_date') else None
    dl       = (exp - date.today()).days if exp else None
    dl_col   = "#ff6b6b" if dl is not None and dl <= 7 else "#00ffb4"
    sc       = {"Active": "#a855f7","Trial": "#ffd700","Inactive": "#ff6b6b"}.get(member['status'],"#aaa")
    plan_icon = {"Equity Monthly":"📈","Equity Quarterly":"📈","Equity Annual":"📈",
                 "Options Monthly":"⚡","Options Quarterly":"⚡","Options Annual":"⚡",
                 "Combo Monthly":"💎","Combo Quarterly":"💎","Combo Annual":"💎","Trial":"🔬"}.get(member.get('plan',''), "📋")
    access    = PLAN_ACCESS.get(member.get('plan',''), [])
    acc_html  = " + ".join([f'<span style="font-weight:700;color:{"#00ffb4" if a=="equity" else "#9b7af7"}">{a.upper()}</span>' for a in access])

    st.markdown('<div class="section-header">👤 My Profile</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:3px;background:linear-gradient(90deg,transparent,#a855f7,#c084fc,transparent);border-radius:4px;margin-bottom:20px;"></div>', unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#120d20,#0f0a1e);border:1px solid #3d1f6b;border-radius:16px;padding:24px;">
          <div style="font-size:28px;font-weight:800;color:#fff;">{member['name']}</div>
          <div style="font-size:13px;color:#6b5a8a;margin-top:6px;">@{member['username']}</div>
          {f'<div style="font-size:13px;color:#5a4870;margin-top:6px;">📧 {member["email"]}</div>' if member.get("email") else ""}
          <div style="margin-top:12px;font-size:12px;color:#5a4870">Access: {acc_html}</div>
        </div>""", unsafe_allow_html=True)
    with col_right:
        st.markdown(f"""
        <div style="background:#a855f718;border:1px solid #a855f744;border-radius:16px;padding:24px;text-align:center;">
          <div style="font-size:10px;color:#5a4870;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">Current Plan</div>
          <div style="font-size:18px;font-weight:800;color:#c084fc;">{plan_icon} {member.get('plan','—')}</div>
          <div style="margin-top:14px;font-size:10px;color:#5a4870;text-transform:uppercase;letter-spacing:2px;">Status</div>
          <div style="font-size:16px;font-weight:700;color:{sc};margin-top:6px;">{member['status']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div style="background:#0a0715;border:1px solid #2d1f4e;border-radius:12px;padding:16px;text-align:center;"><div style="font-size:10px;color:#5a4870;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">Member Since</div><div style="font-size:15px;font-weight:700;color:#fff;">{member.get("joined_date","—")}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div style="background:#0a0715;border:1px solid #2d1f4e;border-radius:12px;padding:16px;text-align:center;"><div style="font-size:10px;color:#5a4870;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">Expires On</div><div style="font-size:15px;font-weight:700;color:#fff;">{member.get("expiry_date","—")}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div style="background:#0a0715;border:1px solid {"#ff6b6b44" if dl is not None and dl<=7 else "#2d1f4e"};border-radius:12px;padding:16px;text-align:center;"><div style="font-size:10px;color:#5a4870;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;">Days Left</div><div style="font-size:15px;font-weight:700;color:{dl_col};">{"⚠️ " if dl is not None and dl<=7 else ""}{f"{dl} days" if dl is not None else "—"}</div></div>', unsafe_allow_html=True)

    if dl is not None and dl <= 7:
        st.markdown(f'<div style="margin-top:16px;background:#ff6b6b11;border:1px solid #ff6b6b33;border-radius:12px;padding:14px 18px;color:#ff9999;font-size:13px;">⚠️ Subscription expires in <b>{dl} days</b>. Contact Dr. Niyas N to renew.</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown('<div style="background:#0f0a1e;border:1px solid #2d1f4e;border-radius:16px;padding:24px;"><div style="font-size:16px;font-weight:700;color:#c084fc;margin-bottom:12px;">📞 Need Help or Renewal?</div><div style="font-size:14px;color:#6b5a8a;line-height:1.9;">Contact Dr. Niyas N directly:<br><a href="https://linkedin.com/in/drniyas" target="_blank" style="color:#a855f7;text-decoration:none;font-weight:600;">🔗 linkedin.com/in/drniyas</a></div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR HELPER
# ══════════════════════════════════════════════════════════════════════

def sidebar_member_info(member, accent="#a855f7"):
    exp = date.fromisoformat(member['expiry_date']) if member.get('expiry_date') else None
    dl  = (exp - date.today()).days if exp else None
    dl_color = "#ff6b6b" if dl and dl <= 7 else "#00ffb4"
    st.sidebar.markdown(f'<div style="background:#041428;border:1px solid #0a2040;border-radius:10px;padding:12px 16px;margin-bottom:16px"><div style="font-weight:700;color:#fff;font-size:15px">{member["name"]}</div><div style="font-size:11px;color:#445566">{member["plan"]}</div><div style="font-size:12px;color:{dl_color};margin-top:6px;font-weight:600">{"⚠️ " if dl and dl<=7 else "✅ "}{f"{dl} days left" if dl else "Active"}</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════════

def main():
    # Load persisted session from disk (no-op if already loaded this run)
    _load_session()

    if "portal" not in st.session_state:
        st.session_state.portal = None

    portal = st.session_state.get("portal")

    # ── No portal selected ────────────────────────────────────────────
    if not portal:
        select_portal()
        return

    # ── ADMIN PORTAL ──────────────────────────────────────────────────
    if portal == "admin":
        if not st.session_state.get("admin_logged_in"):
            admin_login(); return

        with st.sidebar:
            st.markdown('''<div style="text-align:center;padding:20px 12px 4px;">
              <div style="font-family:Outfit,sans-serif;font-size:20px;font-weight:900;color:#c084fc;">NYZTrade</div>
              <div style="font-size:9px;color:#4b3a6b;letter-spacing:3px;text-transform:uppercase;margin-top:3px;">Command Centre</div>
            </div>''', unsafe_allow_html=True)
            st.divider()
            page = st.radio("", [
                "🏠 Dashboard","📊 Equity Calls","⚡ Options & GEX",
                "📄 Research & Broker","📢 Daily Updates","🎬 Video Library",
                "👥 Client Management","📈 Performance",
            ], label_visibility="collapsed")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                _clear_session()
                st.session_state.clear()
                st.rerun()
            st.markdown('<div style="font-size:11px;color:#445566;text-align:center">Dr. Niyas N | Admin</div>', unsafe_allow_html=True)

        _save_session()
        pages = {
            "🏠 Dashboard":           admin_dashboard,
            "📊 Equity Calls":        admin_equity,
            "⚡ Options & GEX":       admin_options,
            "📄 Research & Broker":   admin_research,
            "📢 Daily Updates":       admin_updates,
            "🎬 Video Library":       admin_videos,
            "👥 Client Management":   admin_clients,
            "📈 Performance":         admin_performance,
        }
        pages[page]()
        return

    # ── EQUITY PORTAL ─────────────────────────────────────────────────
    if portal == "equity":
        member = st.session_state.get("member")
        if not member or st.session_state.get("active_portal") != "equity":
            st.session_state.pop("member", None)
            portal_login("equity"); return

        with st.sidebar:
            st.markdown('''<div style="text-align:center;padding:20px 12px 4px;">
              <div style="font-family:Outfit,sans-serif;font-size:20px;font-weight:900;color:#00ffb4;">NYZTrade</div>
              <div style="font-size:9px;color:#4b3a6b;letter-spacing:3px;text-transform:uppercase;margin-top:3px;">Equity Portal</div>
            </div>''', unsafe_allow_html=True)
            st.divider()
            sidebar_member_info(member, "#00ffb4")
            page = st.radio("", [
                "🏠 Home","📊 Active Calls","📈 Track Record",
                "📄 Research Hub","📢 Updates Feed","🎬 Video Library","👤 My Profile",
            ], label_visibility="collapsed")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                _clear_session()
                st.session_state.clear()
                st.rerun()

        _save_session()
        eq_pages = {
            "🏠 Home":          equity_home,
            "📊 Active Calls":  equity_home,
            "📈 Track Record":  equity_track_record,
            "📄 Research Hub":  member_research,
            "📢 Updates Feed":  member_updates,
            "🎬 Video Library": member_videos,
            "👤 My Profile":    lambda m: member_profile(m, "equity"),
        }
        if page == "📊 Active Calls":
            st.markdown('<div class="section-header">📊 Active Equity Calls</div>', unsafe_allow_html=True)
            conn = get_conn()
            rows = conn.execute("SELECT * FROM equity_calls WHERE status='Open' ORDER BY created_at DESC").fetchall()
            conn.close()
            if not rows: st.info("No active calls right now.")
            for r in rows:
                rr = round((r['target1']-r['entry_price'])/(r['entry_price']-r['stop_loss']),2) if r['entry_price'] and r['stop_loss'] and r['stop_loss']!=r['entry_price'] else None
                st.markdown(f"""<div class="call-card {r['call_type'].lower()}">
                  <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px">
                    <div><span style="font-size:18px;font-weight:800;color:#fff">{r['symbol']}</span><span class="badge badge-{r['call_type'].lower()}">{r['call_type']}</span><span class="badge badge-open">OPEN</span></div>
                    <div style="font-size:12px;color:#445566">{r['posted_date'] or ''}</div>
                  </div>
                  <div style="display:flex;gap:16px;margin-top:12px;flex-wrap:wrap">
                    <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Entry</div><div style="font-size:18px;font-weight:700;color:#fff">₹{r['entry_price']}</div></div>
                    <div><div style="font-size:10px;color:#445566;text-transform:uppercase">T1</div><div style="font-size:18px;font-weight:700;color:#00ffb4">₹{r['target1']}</div></div>
                    {"<div><div style='font-size:10px;color:#445566;text-transform:uppercase'>T2</div><div style='font-size:18px;font-weight:700;color:#00ffb4'>₹"+str(r['target2'])+"</div></div>" if r['target2'] else ""}
                    <div><div style="font-size:10px;color:#445566;text-transform:uppercase">SL</div><div style="font-size:18px;font-weight:700;color:#ff6b6b">₹{r['stop_loss']}</div></div>
                    {"<div><div style='font-size:10px;color:#445566;text-transform:uppercase'>R:R</div><div style='font-size:18px;font-weight:700;color:#ffd700'>1:"+str(rr)+"</div></div>" if rr else ""}
                  </div>
                  {"<div style='margin-top:10px;background:#020e20;border-radius:6px;padding:8px;font-size:13px;color:#c0d0e0'><b style='color:#00ddff'>Analysis:</b> "+r['rationale']+"</div>" if r['rationale'] else ""}
                </div>""", unsafe_allow_html=True)
        else:
            eq_pages[page](member)
        return

    # ── OPTIONS PORTAL ────────────────────────────────────────────────
    if portal == "options":
        member = st.session_state.get("member")
        if not member or st.session_state.get("active_portal") != "options":
            st.session_state.pop("member", None)
            portal_login("options"); return

        with st.sidebar:
            st.markdown('''<div style="text-align:center;padding:20px 12px 4px;">
              <div style="font-family:Outfit,sans-serif;font-size:20px;font-weight:900;color:#9b7af7;">NYZTrade</div>
              <div style="font-size:9px;color:#4b3a6b;letter-spacing:3px;text-transform:uppercase;margin-top:3px;">Options Portal</div>
            </div>''', unsafe_allow_html=True)
            st.divider()
            sidebar_member_info(member, "#7b61ff")
            page = st.radio("", [
                "🏠 Home","⚡ Active Calls","📊 GEX Analysis","📈 Track Record",
                "📄 Research Hub","📢 Updates Feed","🎬 Video Library","👤 My Profile",
            ], label_visibility="collapsed")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                _clear_session()
                st.session_state.clear()
                st.rerun()

        _save_session()
        op_pages = {
            "🏠 Home":          options_home,
            "📊 GEX Analysis":  options_gex_analysis,
            "📈 Track Record":  options_track_record,
            "📄 Research Hub":  member_research,
            "📢 Updates Feed":  member_updates,
            "🎬 Video Library": member_videos,
            "👤 My Profile":    lambda m: member_profile(m, "options"),
        }
        if page == "⚡ Active Calls":
            st.markdown('<div class="section-header">⚡ Active Options Calls</div>', unsafe_allow_html=True)
            conn = get_conn()
            rows = conn.execute("SELECT * FROM options_calls WHERE status='Open' ORDER BY created_at DESC").fetchall()
            conn.close()
            if not rows: st.info("No active options calls right now.")
            for r in rows:
                st.markdown(f"""<div class="call-card {r['call_type'].lower()}">
                  <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px">
                    <div><span style="font-size:18px;font-weight:800;color:#fff">{r['underlying']} {r['strike']} {r['option_type']}</span><span class="badge badge-{r['call_type'].lower()}">{r['call_type']}</span></div>
                    <div style="font-size:12px;color:#445566">Exp: {r['expiry']}</div>
                  </div>
                  <div style="display:flex;gap:16px;margin-top:12px;flex-wrap:wrap">
                    <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Entry</div><div style="font-size:18px;font-weight:700;color:#fff">₹{r['entry_premium']}</div></div>
                    <div><div style="font-size:10px;color:#445566;text-transform:uppercase">Target</div><div style="font-size:18px;font-weight:700;color:#00ffb4">₹{r['target_premium']}</div></div>
                    <div><div style="font-size:10px;color:#445566;text-transform:uppercase">SL</div><div style="font-size:18px;font-weight:700;color:#ff6b6b">₹{r['stop_premium']}</div></div>
                  </div>
                  {"<div style='margin-top:10px;background:#020e20;border-radius:6px;padding:8px;font-size:13px;color:#c0d0e0'><b style='color:#7b61ff'>GEX:</b> "+r['gex_note']+"</div>" if r['gex_note'] else ""}
                  {"<div style='margin-top:6px;background:#020e20;border-radius:6px;padding:8px;font-size:13px;color:#c0d0e0'><b style='color:#00ddff'>Analysis:</b> "+r['rationale']+"</div>" if r['rationale'] else ""}
                </div>""", unsafe_allow_html=True)
        else:
            op_pages[page](member)
        return

    # ── RESEARCH PORTAL ───────────────────────────────────────────────
    if portal == "research":
        member = st.session_state.get("member")
        if not member or st.session_state.get("active_portal") != "research":
            st.session_state.pop("member", None)
            portal_login("research"); return

        with st.sidebar:
            st.markdown('''<div style="text-align:center;padding:20px 12px 4px;">
              <div style="font-family:Outfit,sans-serif;font-size:20px;font-weight:900;color:#ffd700;">NYZTrade</div>
              <div style="font-size:9px;color:#4b3a6b;letter-spacing:3px;text-transform:uppercase;margin-top:3px;">Research Hub</div>
            </div>''', unsafe_allow_html=True)
            st.divider()
            sidebar_member_info(member, "#ffd700")
            page = st.radio("", [
                "📄 Research Reports","🏦 Broker Calls","📢 Updates Feed","👤 My Profile",
            ], label_visibility="collapsed")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                _clear_session()
                st.session_state.clear()
                st.rerun()

        _save_session()
        res_pages = {
            "📄 Research Reports": member_research,
            "🏦 Broker Calls":     member_research,
            "📢 Updates Feed":     member_updates,
            "👤 My Profile":       lambda m: member_profile(m, "research"),
        }
        res_pages[page](member)
        return


main()
