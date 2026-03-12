"""
Nyztrade Premium — Single File App
====================================
Two portals in one file. No external modules needed.
Deploy directly to Streamlit Cloud with just this file + requirements.txt

CONFIGURE BEFORE DEPLOY:
  1. ADMIN_PASSWORD  — change "nyztrade2024" below
  2. DISCORD WEBHOOKS — find "YOUR_EQUITY_WEBHOOK" and replace
  3. TELEGRAM         — find "YOUR_BOT_TOKEN" and replace
  4. RAZORPAY         — find "rzp_live_YOUR_KEY_ID" and replace
"""

import sys, os, sqlite3, hashlib, hmac, json, requests
from datetime import date, timedelta, datetime

import streamlit as st

# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION — Edit these before deploying
# ══════════════════════════════════════════════════════════════════════

ADMIN_USERNAME  = "drniyas"
ADMIN_PASSWORD  = "nyztrade2024"        # ← change this

# Discord Webhooks
DISCORD_WEBHOOKS = {
    "equity":  "https://discord.com/api/webhooks/YOUR_EQUITY_WEBHOOK",
    "options": "https://discord.com/api/webhooks/YOUR_OPTIONS_WEBHOOK",
    "updates": "https://discord.com/api/webhooks/YOUR_UPDATES_WEBHOOK",
}

# Telegram Bot
TG_BOT_TOKEN   = "YOUR_BOT_TOKEN"       # from @BotFather
TG_CHANNEL_ID  = "@nyztrade_premium"    # your channel username
TG_ADMIN_ID    = "YOUR_TELEGRAM_CHAT_ID"  # your personal Telegram ID

# Razorpay
RZP_KEY_ID     = "rzp_live_YOUR_KEY_ID"
RZP_KEY_SECRET = "YOUR_KEY_SECRET"

PLAN_AMOUNTS = {
    "Premium Monthly":   999,
    "Premium Quarterly": 2499,
    "Premium Annual":    7999,
    "Trial":             0,
}

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
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;800&family=Inter:wght@400;500;600&family=Space+Mono&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #010912; color: #e0eaf5; }

[data-testid="stSidebar"] {
    background: #020e20 !important;
    border-right: 1px solid #0a2040;
}

.portal-logo {
    text-align: center; padding: 24px 0 6px;
    font-family: 'Syne', sans-serif; font-size: 28px;
    font-weight: 800; color: #00ddff; letter-spacing: 1px;
}
.portal-sub {
    text-align: center; font-size: 11px; color: #445566;
    margin-bottom: 20px; letter-spacing: 4px; text-transform: uppercase;
}

.metric-card {
    background: #041428; border: 1px solid #0a2040;
    border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 10px;
}
.metric-value { font-family: 'Syne', sans-serif; font-size: 38px; font-weight: 800; color: #00ddff; }
.metric-label { font-size: 11px; color: #445566; text-transform: uppercase; letter-spacing: 2px; margin-top: 4px; }

.call-card {
    background: #041428; border-left: 4px solid #00ddff;
    border-radius: 8px; padding: 16px 20px; margin-bottom: 12px;
}
.call-card.buy    { border-left-color: #00ffb4; }
.call-card.sell   { border-left-color: #ff6b6b; }
.call-card.hold   { border-left-color: #ffd700; }
.call-card.closed { border-left-color: #445566; opacity: 0.7; }

.badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; margin-left: 6px; letter-spacing: 1px;
}
.badge-buy    { background: #00ffb422; color: #00ffb4; border: 1px solid #00ffb4; }
.badge-sell   { background: #ff6b6b22; color: #ff6b6b; border: 1px solid #ff6b6b; }
.badge-hold   { background: #ffd70022; color: #ffd700; border: 1px solid #ffd700; }
.badge-open   { background: #00ddff22; color: #00ddff; border: 1px solid #00ddff; }
.badge-closed { background: #44556622; color: #99aabb; border: 1px solid #445566; }
.badge-ce     { background: #00ffb422; color: #00ffb4; border: 1px solid #00ffb4; }
.badge-pe     { background: #ff6b6b22; color: #ff6b6b; border: 1px solid #ff6b6b; }

.section-header {
    font-family: 'Syne', sans-serif; font-size: 30px;
    font-weight: 800; color: #ffffff; margin-bottom: 4px;
}
.section-sub { font-size: 13px; color: #445566; margin-bottom: 24px; letter-spacing: 1px; }

.tag {
    display: inline-block; background: #00ddff22; color: #00ddff;
    border: 1px solid #00ddff44; border-radius: 20px; font-size: 11px;
    padding: 2px 10px; margin-right: 6px; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase;
}

.update-card {
    background: #041428; border: 1px solid #0a2040;
    border-radius: 12px; padding: 20px; margin-bottom: 16px;
    transition: border-color 0.2s;
}
.update-card:hover { border-color: #00ddff44; }

.sub-card {
    background: linear-gradient(135deg, #041428, #041e38);
    border: 1px solid #00ddff33; border-radius: 16px;
    padding: 28px; margin-bottom: 20px;
}

.pnl-pos { color: #00ffb4; font-weight: 700; }
.pnl-neg { color: #ff6b6b; font-weight: 700; }

.stButton > button {
    background: #00ddff !important; color: #010912 !important;
    font-weight: 700 !important; border: none !important;
    border-radius: 8px !important; transition: all 0.2s;
}
.stButton > button:hover { background: #00ffb4 !important; transform: translateY(-1px); }

div[data-testid="stForm"] {
    background: #041428; border: 1px solid #0a2040; border-radius: 12px; padding: 20px;
}

.stTextInput > div > div, .stSelectbox > div,
.stTextArea > div > div, .stNumberInput > div > div {
    background: #020e20 !important; border-color: #0a2040 !important; color: #e0eaf5 !important;
}

.winrate-badge {
    background: linear-gradient(135deg, #00ffb422, #00ddff22);
    border: 1px solid #00ffb444; border-radius: 50px; padding: 6px 20px;
    font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 800;
    color: #00ffb4; display: inline-block;
}
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nyztrade.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
        discord_id TEXT, telegram_id TEXT, email TEXT, phone TEXT,
        plan TEXT DEFAULT 'Premium Monthly', status TEXT DEFAULT 'Active',
        joined_date TEXT, expiry_date TEXT, notes TEXT,
        reminder_sent INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, client_id INTEGER,
        razorpay_id TEXT, amount REAL, currency TEXT DEFAULT 'INR',
        plan TEXT, status TEXT DEFAULT 'captured', payment_method TEXT,
        notes TEXT, payment_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(client_id) REFERENCES clients(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS equity_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
        call_type TEXT NOT NULL, entry_price REAL, target1 REAL,
        target2 REAL, stop_loss REAL, cmp REAL, status TEXT DEFAULT 'Open',
        rationale TEXT, result TEXT, exit_price REAL, pnl_pct REAL,
        posted_date TEXT, exit_date TEXT, sent_discord INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS options_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT, underlying TEXT NOT NULL,
        option_type TEXT, strike REAL, expiry TEXT, call_type TEXT,
        entry_premium REAL, target_premium REAL, stop_premium REAL,
        cmp_premium REAL, status TEXT DEFAULT 'Open', rationale TEXT,
        gex_note TEXT, exit_premium REAL, pnl_pct REAL, result TEXT,
        posted_date TEXT, exit_date TEXT, sent_discord INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS daily_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        category TEXT, content TEXT, image_path TEXT, video_url TEXT,
        tags TEXT, sent_discord INTEGER DEFAULT 0, posted_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
        category TEXT, description TEXT, video_url TEXT, thumbnail TEXT,
        duration TEXT, posted_date TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); conn.close()

def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()

def verify_member(username, password):
    conn = get_conn()
    row  = conn.execute(
        "SELECT * FROM clients WHERE username=? AND password_hash=? AND status='Active'",
        (username, hash_password(password))
    ).fetchone()
    conn.close()
    return row

init_db()


# ══════════════════════════════════════════════════════════════════════
# DISCORD
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
        return (True, "✅ Discord") if r.status_code in (200,204) else (False, f"HTTP {r.status_code}")
    except Exception as e: return False, str(e)

def discord_equity(call):
    color  = 0x00FFB4 if call["call_type"]=="BUY" else 0xFF6B6B
    fields = [
        {"name":"Entry",    "value":f"₹{call['entry_price']}", "inline":True},
        {"name":"Target 1", "value":f"₹{call['target1']}",     "inline":True},
        {"name":"Stop Loss","value":f"₹{call['stop_loss']}",   "inline":True},
    ]
    if call.get("target2"): fields.append({"name":"Target 2","value":f"₹{call['target2']}","inline":True})
    if call.get("rationale"): fields.append({"name":"📝 Analysis","value":call["rationale"],"inline":False})
    icon = "🟢" if call["call_type"]=="BUY" else "🔴"
    return discord_embed("equity", f"{icon} EQUITY — {call['symbol']}", f"**{call['call_type']}**", color, fields)

def discord_options(call):
    color  = 0x00DDFF if call["call_type"]=="BUY" else 0xFF6B6B
    fields = [
        {"name":"Contract",       "value":f"{call['underlying']} {call['strike']} {call['option_type']} {call['expiry']}","inline":False},
        {"name":"Entry Premium",  "value":f"₹{call['entry_premium']}",  "inline":True},
        {"name":"Target Premium", "value":f"₹{call['target_premium']}", "inline":True},
        {"name":"Stop Loss",      "value":f"₹{call['stop_premium']}",   "inline":True},
    ]
    if call.get("gex_note"): fields.append({"name":"📊 GEX","value":call["gex_note"],"inline":False})
    icon = "⚡" if call["call_type"]=="BUY" else "🔻"
    return discord_embed("options", f"{icon} OPTIONS — {call['underlying']}", f"**{call['call_type']}** {call['option_type']}", color, fields)


# ══════════════════════════════════════════════════════════════════════
# TELEGRAM
# ══════════════════════════════════════════════════════════════════════

def _tg_send(chat_id, text):
    if "YOUR_" in TG_BOT_TOKEN: return False, "Bot token not configured"
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={"chat_id":chat_id,"text":text,"parse_mode":"HTML",
                  "disable_web_page_preview":True}, timeout=10)
        data = r.json()
        return (True,"✅ Telegram") if data.get("ok") else (False, data.get("description","TG error"))
    except Exception as e: return False, str(e)

def tg_equity(call):
    t2  = f"\n📍 <b>Target 2:</b> ₹{call['target2']}" if call.get("target2") else ""
    rat = f"\n\n📝 <i>{call['rationale']}</i>" if call.get("rationale") else ""
    icon = "🟢" if call["call_type"]=="BUY" else "🔴"
    return _tg_send(TG_CHANNEL_ID,
        f"{icon} <b>EQUITY — {call['symbol']}</b>\n━━━━━━━━━━━━━━━━━\n"
        f"📌 <b>{call['call_type']}</b>\n💰 Entry: ₹{call['entry_price']}\n"
        f"🎯 T1: ₹{call['target1']}{t2}\n🛡 SL: ₹{call['stop_loss']}\n"
        f"━━━━━━━━━━━━━━━━━{rat}\n\n<i>Nyztrade Premium | @drniyas</i>")

def tg_options(call):
    gex = f"\n\n📊 <b>GEX:</b>\n<i>{call['gex_note']}</i>" if call.get("gex_note") else ""
    icon = "⚡" if call["call_type"]=="BUY" else "🔻"
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
        f"Renew: 👉 https://linkedin.com/in/drniyas\n\n<i>Nyztrade Premium</i>")

def tg_welcome(telegram_id, name, username, password, plan):
    return _tg_send(telegram_id,
        f"🎉 <b>Welcome to Nyztrade Premium!</b>\n\nHi <b>{name}</b>,\n\n"
        f"━━━━━━━━━━━━━━━━━\n🔐 Username: <code>{username}</code>\n"
        f"Password: <code>{password}</code>\n━━━━━━━━━━━━━━━━━\n\n"
        f"Plan: <b>{plan}</b>\n\n<i>— Dr. Niyas N | Nyztrade Premium</i>")

def tg_admin(msg):
    if "YOUR_" in str(TG_ADMIN_ID): return False, "Admin ID not configured"
    return _tg_send(TG_ADMIN_ID, f"🔔 <b>Nyztrade Alert</b>\n\n{msg}")


# ══════════════════════════════════════════════════════════════════════
# RAZORPAY
# ══════════════════════════════════════════════════════════════════════

def get_payment_link(plan, name, email, phone):
    if "YOUR_" in RZP_KEY_ID: return {"success":False,"error":"Razorpay not configured"}
    try:
        import razorpay
        client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))
        link = client.payment_link.create({
            "amount": PLAN_AMOUNTS.get(plan,999)*100, "currency":"INR",
            "accept_partial": False,
            "description": f"Nyztrade Premium — {plan}",
            "customer": {"name":name,"email":email,"contact":phone},
            "notify": {"sms":True,"email":True}, "reminder_enable":True,
            "notes": {"plan":plan},
        })
        return {"success":True,"url":link["short_url"]}
    except ImportError: return {"success":False,"error":"pip install razorpay"}
    except Exception as e: return {"success":False,"error":str(e)}


# ══════════════════════════════════════════════════════════════════════
# CHART HELPERS
# ══════════════════════════════════════════════════════════════════════

def render_line_chart(title, labels, values, color="#00ffb4"):
    chart_id    = f"c{abs(hash(title))}"
    zero_colors = json.dumps(["#00ffb4" if v>=0 else "#ff6b6b" for v in values])
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
# PORTAL SELECTOR — shown on first load
# ══════════════════════════════════════════════════════════════════════

def select_portal():
    st.markdown("""
    <div style="max-width:500px;margin:80px auto;text-align:center">
      <div style="font-family:'Syne',sans-serif;font-size:42px;font-weight:800;color:#00ddff">📈 NYZTRADE</div>
      <div style="font-size:11px;color:#445566;letter-spacing:5px;text-transform:uppercase;margin-top:4px;margin-bottom:48px">
        Select Portal
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("""
        <div style="display:flex;gap:16px">
          <div style="flex:1;background:#041428;border:1px solid #0a2040;border-radius:12px;
                      padding:30px 20px;text-align:center;cursor:pointer">
            <div style="font-size:32px">⚙️</div>
            <div style="font-family:'Syne',sans-serif;font-size:16px;font-weight:700;
                        color:#fff;margin-top:8px">Admin</div>
            <div style="font-size:12px;color:#445566;margin-top:4px">Command Centre</div>
          </div>
          <div style="flex:1;background:#041428;border:1px solid #0a2040;border-radius:12px;
                      padding:30px 20px;text-align:center;cursor:pointer">
            <div style="font-size:32px">📊</div>
            <div style="font-family:'Syne',sans-serif;font-size:16px;font-weight:700;
                        color:#fff;margin-top:8px">Member</div>
            <div style="font-size:12px;color:#445566;margin-top:4px">Premium Portal</div>
          </div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        if pc1.button("⚙️ Admin Portal", use_container_width=True):
            st.session_state.portal = "admin"
            st.rerun()
        if pc2.button("📈 Member Portal", use_container_width=True):
            st.session_state.portal = "member"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
# ADMIN AUTH
# ══════════════════════════════════════════════════════════════════════

def admin_login():
    ADMIN_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
    st.markdown("""
    <div style="max-width:420px;margin:80px auto;background:#041428;
                border:1px solid #0a2040;border-radius:16px;padding:40px;">
      <div style="text-align:center;font-family:'Syne',sans-serif;font-size:30px;
                  font-weight:800;color:#00ddff">⚙️ ADMIN PORTAL</div>
      <div style="text-align:center;font-size:11px;color:#445566;
                  letter-spacing:4px;margin-bottom:28px">NYZTRADE COMMAND CENTRE</div>
    </div>""", unsafe_allow_html=True)
    with st.form("admin_login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login →", use_container_width=True):
            if u == ADMIN_USERNAME and hashlib.sha256(p.encode()).hexdigest() == ADMIN_HASH:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")
    if st.button("← Back to portal select"):
        st.session_state.portal = None
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# ADMIN PAGES
# ══════════════════════════════════════════════════════════════════════

def admin_dashboard():
    st.markdown('<div class="section-header">🏠 Command Centre</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Live overview — all activity at a glance</div>', unsafe_allow_html=True)
    conn = get_conn()
    cols = st.columns(5)
    metrics = [
        (conn.execute("SELECT COUNT(*) FROM clients WHERE status='Active'").fetchone()[0], "Active Members","#00ddff"),
        (conn.execute("SELECT COUNT(*) FROM equity_calls WHERE status='Open'").fetchone()[0],  "Equity Open",   "#00ffb4"),
        (conn.execute("SELECT COUNT(*) FROM options_calls WHERE status='Open'").fetchone()[0], "Options Open",  "#7b61ff"),
        (conn.execute("SELECT COUNT(*) FROM daily_updates WHERE posted_date=?", (str(date.today()),)).fetchone()[0], "Updates Today","#ffd700"),
        (conn.execute("SELECT COUNT(*) FROM clients WHERE expiry_date<=? AND status='Active'",
                      (str(date.today()+timedelta(days=7)),)).fetchone()[0], "Expiring 7d","#ff6b6b"),
    ]
    for col,(val,label,color) in zip(cols,metrics):
        col.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{color}">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("#### 📈 Performance Summary")
    pc1, pc2 = st.columns(2)
    for col, table, label in [(pc1,"equity_calls","Equity"), (pc2,"options_calls","Options")]:
        with col:
            rows = conn.execute(f"SELECT pnl_pct FROM {table} WHERE status='Closed' AND pnl_pct IS NOT NULL").fetchall()
            if rows:
                pnls = [r[0] for r in rows]; wins = sum(1 for p in pnls if p>0); avg = sum(pnls)/len(pnls)
                col.markdown(f"""<div class="sub-card">
                  <div style="font-size:13px;color:#445566;letter-spacing:2px;text-transform:uppercase">{label} Track Record</div>
                  <div style="margin-top:12px;display:flex;gap:30px">
                    <div><div class="metric-value" style="font-size:32px;color:#00ffb4">{wins/len(pnls)*100:.0f}%</div><div class="metric-label">Win Rate</div></div>
                    <div><div class="metric-value" style="font-size:32px;color:{'#00ffb4' if avg>0 else '#ff6b6b'}">{avg:+.1f}%</div><div class="metric-label">Avg P&L</div></div>
                    <div><div class="metric-value" style="font-size:32px">{len(pnls)}</div><div class="metric-label">Calls</div></div>
                  </div></div>""", unsafe_allow_html=True)
            else: col.info(f"No closed {label.lower()} calls yet.")
    st.divider()
    left, right = st.columns(2)
    with left:
        st.markdown("#### Latest Equity")
        for r in conn.execute("SELECT * FROM equity_calls ORDER BY created_at DESC LIMIT 5").fetchall():
            pnl = f" | <span class='{'pnl-pos' if (r['pnl_pct'] or 0)>0 else 'pnl-neg'}'>{r['pnl_pct']:+.1f}%</span>" if r['pnl_pct'] else ""
            st.markdown(f'<div class="call-card {r["call_type"].lower()}"><b style="color:#fff">{r["symbol"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span class="badge badge-{r["status"].lower()}">{r["status"]}</span><span style="float:right;font-size:13px;color:#445566">{r["posted_date"] or ""}</span><br><span style="color:#99aabb;font-size:14px">Entry ₹{r["entry_price"]} | SL ₹{r["stop_loss"]}{pnl}</span></div>', unsafe_allow_html=True)
    with right:
        st.markdown("#### Latest Options")
        for r in conn.execute("SELECT * FROM options_calls ORDER BY created_at DESC LIMIT 5").fetchall():
            pnl = f" | <span class='{'pnl-pos' if (r['pnl_pct'] or 0)>0 else 'pnl-neg'}'>{r['pnl_pct']:+.1f}%</span>" if r['pnl_pct'] else ""
            st.markdown(f'<div class="call-card {r["call_type"].lower()}"><b style="color:#fff">{r["underlying"]} {r["strike"]} {r["option_type"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span class="badge badge-{r["status"].lower()}">{r["status"]}</span><br><span style="color:#99aabb;font-size:14px">Exp {r["expiry"]} | ₹{r["entry_premium"]}{pnl}</span></div>', unsafe_allow_html=True)
    conn.close()


def admin_equity():
    st.markdown('<div class="section-header">📊 Equity Calls</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Post, manage and close equity positions</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["➕ New Call", "📋 Open Positions", "📁 History"])

    with tab1:
        with st.form("eq_form"):
            c1,c2 = st.columns(2)
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
            sc1,sc2   = st.columns(2)
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
                        (call["symbol"],call["call_type"],call["entry_price"],call["target1"],call["target2"],call["stop_loss"],call["cmp"],call["rationale"],call["posted_date"],"Open"))
                    conn.commit(); conn.close()
                    msgs = []
                    if send_disc: ok,m = discord_equity(call); msgs.append(f"Discord:{'✅' if ok else '⚠️'}")
                    if send_tg:   ok,m = tg_equity(call);     msgs.append(f"Telegram:{'✅' if ok else '⚠️'}")
                    st.success(f"✅ {symbol.upper()} posted" + (" | "+" | ".join(msgs) if msgs else ""))

    with tab2:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM equity_calls WHERE status='Open' ORDER BY created_at DESC").fetchall()
        if not rows: st.info("No open calls.")
        for r in rows:
            with st.expander(f"{'🟢' if r['call_type']=='BUY' else '🔴'} {r['symbol']} — ₹{r['entry_price']} | {r['posted_date']}"):
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("Entry",    f"₹{r['entry_price']}")
                c2.metric("Target 1", f"₹{r['target1']}")
                c3.metric("Stop Loss",f"₹{r['stop_loss']}")
                c4.metric("CMP",      f"₹{r['cmp']}" if r['cmp'] else "—")
                if r['rationale']: st.caption(r['rationale'])
                ec1,ec2,ec3 = st.columns(3)
                exit_p = ec1.number_input("Exit ₹", key=f"ep{r['id']}", min_value=0.0)
                result = ec2.selectbox("Result", ["Target Hit","Stop Hit","Partial","Manual"], key=f"res{r['id']}")
                if ec3.button("Close", key=f"cl{r['id']}"):
                    pnl = round(((exit_p-r['entry_price'])/r['entry_price']*100)*(1 if r['call_type']=='BUY' else -1),2) if exit_p and r['entry_price'] else 0
                    conn.execute("UPDATE equity_calls SET status='Closed',exit_price=?,result=?,pnl_pct=?,exit_date=date('now') WHERE id=?", (exit_p,result,pnl,r['id']))
                    conn.commit(); st.success(f"Closed | P&L: {pnl:+.2f}%"); st.rerun()
        conn.close()

    with tab3:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM equity_calls WHERE status='Closed' ORDER BY exit_date DESC").fetchall()
        if not rows: st.info("No closed calls yet.")
        else:
            pnls = [r['pnl_pct'] for r in rows if r['pnl_pct'] is not None]
            if pnls:
                wins = sum(1 for p in pnls if p>0)
                m1,m2,m3 = st.columns(3)
                m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%"); m3.metric("Total",len(rows))
            for r in rows:
                pc = "#00ffb4" if (r['pnl_pct'] or 0)>0 else "#ff6b6b"
                pnl_str = f"{r['pnl_pct']:+.2f}%" if r['pnl_pct'] else "—"
                st.markdown(f'<div class="call-card closed"><b style="color:#fff">{r["symbol"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:700;float:right;font-size:18px">{pnl_str}</span><br><span style="color:#99aabb;font-size:13px">₹{r["entry_price"]} → ₹{r["exit_price"] or "—"} | {r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)
        conn.close()


def admin_options():
    st.markdown('<div class="section-header">⚡ Options & GEX</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Options calls with GEX-driven analysis</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Options Call","📊 GEX Weekly","📋 Open","📁 History"])

    with tab1:
        with st.form("opt_form"):
            c1,c2 = st.columns(2)
            with c1:
                underlying    = st.selectbox("Underlying",["NIFTY","BANKNIFTY","FINNIFTY","SENSEX","MIDCPNIFTY"])
                option_type   = st.selectbox("CE / PE",["CE","PE"])
                strike        = st.number_input("Strike *", min_value=0.0, step=50.0)
                expiry        = st.text_input("Expiry *", placeholder="27-Mar-2025")
                call_type     = st.selectbox("BUY / SELL",["BUY","SELL"])
            with c2:
                entry_premium = st.number_input("Entry Premium ₹ *", min_value=0.0, step=0.5)
                target_premium= st.number_input("Target Premium ₹ *", min_value=0.0, step=0.5)
                stop_premium  = st.number_input("Stop Loss Premium ₹ *", min_value=0.0, step=0.5)
                cmp_premium   = st.number_input("CMP Premium ₹", min_value=0.0, step=0.5)
                posted_date   = st.date_input("Date", value=date.today())
            rationale = st.text_area("Trade Rationale", height=80)
            gex_note  = st.text_area("GEX Context *", height=80, placeholder="e.g. +ve GEX above 22,400 → CE sell suits.")
            send_disc = st.checkbox("📤 Send to Discord #options", value=True)
            if st.form_submit_button("Post Options Call →", use_container_width=True):
                if not strike or not entry_premium or not expiry:
                    st.error("Fill required fields.")
                else:
                    call = dict(underlying=underlying, option_type=option_type, strike=strike,
                                expiry=expiry, call_type=call_type, entry_premium=entry_premium,
                                target_premium=target_premium, stop_premium=stop_premium,
                                rationale=rationale, gex_note=gex_note, posted_date=str(posted_date))
                    conn = get_conn()
                    conn.execute("INSERT INTO options_calls (underlying,option_type,strike,expiry,call_type,entry_premium,target_premium,stop_premium,cmp_premium,rationale,gex_note,posted_date,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (underlying,option_type,strike,expiry,call_type,entry_premium,target_premium,stop_premium,cmp_premium,rationale,gex_note,str(posted_date),"Open"))
                    conn.commit(); conn.close()
                    msgs = []
                    if send_disc: ok,_ = discord_options(call); msgs.append(f"Discord:{'✅' if ok else '⚠️'}")
                    st.success("✅ Options call posted" + (" | "+" | ".join(msgs) if msgs else ""))

    with tab2:
        st.markdown("#### 📊 Weekly GEX Analysis Post")
        with st.form("gex_form"):
            c1,c2 = st.columns(2)
            with c1:
                week_date   = st.date_input("Week of", value=date.today())
                gex_level   = st.number_input("Net GEX (₹ Cr)", step=100.0)
                gex_bias    = st.selectbox("Market Bias",["Positive GEX — Rangebound","Negative GEX — Volatile","Near Zero — Transition zone"])
            with c2:
                gamma_wall  = st.number_input("Gamma Wall", step=50.0)
                put_support = st.number_input("Put Support", step=50.0)
                zero_line   = st.number_input("Zero Gamma Line", step=50.0)
            outlook   = st.text_area("Weekly GEX Outlook *", height=130)
            send_disc = st.checkbox("📤 Send to Discord", value=True)
            if st.form_submit_button("Post GEX Update →", use_container_width=True):
                content = f"**GEX:** ₹{gex_level:,.0f} Cr | **Bias:** {gex_bias}\n**Gamma Wall:** {gamma_wall} | **Put Support:** {put_support} | **Zero:** {zero_line}\n\n{outlook}"
                conn = get_conn()
                conn.execute("INSERT INTO daily_updates (title,category,content,posted_date,tags) VALUES(?,?,?,?,?)",
                    (f"GEX Weekly — {week_date}","GEX",content,str(week_date),"GEX,Options,Weekly"))
                conn.commit(); conn.close()
                disc_msg = ""
                if send_disc:
                    ok,_ = discord_embed("options", f"📊 GEX Weekly — {week_date}", content, 0x7B61FF)
                    disc_msg = f" | Discord:{'✅' if ok else '⚠️'}"
                st.success(f"✅ GEX update posted{disc_msg}")

    with tab3:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM options_calls WHERE status='Open' ORDER BY created_at DESC").fetchall()
        if not rows: st.info("No open options calls.")
        for r in rows:
            with st.expander(f"{'⚡' if r['call_type']=='BUY' else '🔻'} {r['underlying']} {r['strike']} {r['option_type']} | {r['expiry']}"):
                c1,c2,c3 = st.columns(3)
                c1.metric("Entry",  f"₹{r['entry_premium']}")
                c2.metric("Target", f"₹{r['target_premium']}")
                c3.metric("SL",     f"₹{r['stop_premium']}")
                if r['gex_note']: st.info(f"📊 GEX: {r['gex_note']}")
                ec1,ec2,ec3 = st.columns(3)
                exit_p = ec1.number_input("Exit Premium ₹", key=f"op_ep{r['id']}", min_value=0.0)
                result = ec2.selectbox("Result",["Target Hit","Stop Hit","Expiry","Manual"], key=f"op_res{r['id']}")
                if ec3.button("Close", key=f"op_cl{r['id']}"):
                    pnl = round(((exit_p-r['entry_premium'])/r['entry_premium']*100)*(1 if r['call_type']=='BUY' else -1),2) if exit_p and r['entry_premium'] else 0
                    conn.execute("UPDATE options_calls SET status='Closed',exit_premium=?,result=?,pnl_pct=?,exit_date=date('now') WHERE id=?", (exit_p,result,pnl,r['id']))
                    conn.commit(); st.success(f"Closed | P&L: {pnl:+.2f}%"); st.rerun()
        conn.close()

    with tab4:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM options_calls WHERE status='Closed' ORDER BY exit_date DESC").fetchall()
        if not rows: st.info("No closed options calls yet.")
        else:
            pnls = [r['pnl_pct'] for r in rows if r['pnl_pct'] is not None]
            if pnls:
                wins = sum(1 for p in pnls if p>0)
                m1,m2,m3 = st.columns(3)
                m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%"); m3.metric("Total",len(rows))
            for r in rows:
                pc = "#00ffb4" if (r['pnl_pct'] or 0)>0 else "#ff6b6b"
                pnl_str = f"{r['pnl_pct']:+.2f}%" if r['pnl_pct'] else "—"
                st.markdown(f'<div class="call-card closed"><b style="color:#fff">{r["underlying"]} {r["strike"]} {r["option_type"]} | {r["expiry"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:700;float:right;font-size:18px">{pnl_str}</span><br><span style="color:#99aabb;font-size:13px">₹{r["entry_premium"]} → ₹{r["exit_premium"] or "—"} | {r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)
        conn.close()


def admin_updates():
    st.markdown('<div class="section-header">📢 Daily Updates</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Post market updates to Discord and members</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ New Update","📋 All Updates"])

    with tab1:
        with st.form("upd_form"):
            title    = st.text_input("Title *", placeholder="Pre-market Analysis | GEX Update...")
            category = st.selectbox("Category",["Pre-Market","Intraday","Post-Market","GEX Update","Market View","News","Education","General"])
            content  = st.text_area("Content *", height=180)
            tags     = st.text_input("Tags", placeholder="Nifty, GEX, Options")
            vid_url  = st.text_input("Video URL", placeholder="https://...")
            posted_date = st.date_input("Date", value=date.today())
            send_disc   = st.checkbox("📤 Send to Discord #updates", value=True)
            if st.form_submit_button("Post Update →", use_container_width=True):
                if not title or not content: st.error("Title and content required.")
                else:
                    conn = get_conn()
                    conn.execute("INSERT INTO daily_updates (title,category,content,video_url,tags,posted_date) VALUES(?,?,?,?,?,?)",
                        (title,category,content,vid_url or None,tags,str(posted_date)))
                    conn.commit(); conn.close()
                    disc_msg = ""
                    if send_disc:
                        ok,_ = discord_embed("updates",f"📢 {title}",content,0x7B61FF)
                        disc_msg = f" | Discord:{'✅' if ok else '⚠️'}"
                    st.success(f"✅ Update posted{disc_msg}")

    with tab2:
        conn = get_conn()
        cat_f = st.selectbox("Filter",["All","Pre-Market","Intraday","Post-Market","GEX Update","Market View","Education"])
        q = "SELECT * FROM daily_updates" + (" WHERE category=?" if cat_f!="All" else "") + " ORDER BY created_at DESC"
        rows = conn.execute(q,(cat_f,) if cat_f!="All" else ()).fetchall(); conn.close()
        for r in rows:
            with st.expander(f"[{r['category']}] {r['title']} — {r['posted_date']}"):
                st.markdown(r['content'])
                if r['video_url']: st.markdown(f"🎬 [Watch Video]({r['video_url']})")
                c1,c2 = st.columns(2)
                if c1.button("📤 Resend Discord", key=f"rs_{r['id']}"):
                    ok,msg = discord_embed("updates",f"📢 {r['title']}",r['content'],0x7B61FF)
                    st.success(msg) if ok else st.error(msg)
                if c2.button("🗑️ Delete", key=f"dd_{r['id']}"):
                    conn2 = get_conn(); conn2.execute("DELETE FROM daily_updates WHERE id=?",(r['id'],)); conn2.commit(); conn2.close(); st.rerun()


def admin_videos():
    st.markdown('<div class="section-header">🎬 Video Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Manage educational content for members</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["➕ Add Video","📚 Library"])

    with tab1:
        with st.form("vid_form"):
            c1,c2 = st.columns(2)
            with c1:
                title     = st.text_input("Title *")
                category  = st.selectbox("Category",["GEX Education","Options Strategy","Equity Analysis","Market Overview","ESG/Valuation","Live Session","Other"])
                video_url = st.text_input("Video URL *", placeholder="YouTube / Drive link")
                duration  = st.text_input("Duration", placeholder="12:35")
            with c2:
                description = st.text_area("Description", height=100)
                thumbnail   = st.text_input("Thumbnail URL")
                posted_date = st.date_input("Date", value=date.today())
            if st.form_submit_button("Add to Library →", use_container_width=True):
                if not title or not video_url: st.error("Title and URL required.")
                else:
                    conn = get_conn()
                    conn.execute("INSERT INTO videos (title,category,description,video_url,thumbnail,duration,posted_date) VALUES(?,?,?,?,?,?,?)",
                        (title,category,description,video_url,thumbnail or None,duration,str(posted_date)))
                    conn.commit(); conn.close(); st.success(f"✅ '{title}' added.")

    with tab2:
        conn = get_conn()
        cat_f = st.selectbox("Filter",["All","GEX Education","Options Strategy","Equity Analysis","Market Overview","Live Session"])
        rows  = conn.execute("SELECT * FROM videos"+(f" WHERE category=?" if cat_f!="All" else "")+" ORDER BY created_at DESC",
            (cat_f,) if cat_f!="All" else ()).fetchall(); conn.close()
        for i in range(0,len(rows),2):
            cols = st.columns(2)
            for j,col in enumerate(cols):
                if i+j>=len(rows): break
                r = rows[i+j]
                with col:
                    st.markdown(f'<div class="update-card"><span class="tag">{r["category"]}</span><div style="font-weight:700;font-size:16px;margin:10px 0 4px;color:#fff">{r["title"]}</div><div style="font-size:13px;color:#99aabb">{r["description"] or ""}</div><div style="font-size:11px;color:#445566;margin-top:8px">{r["posted_date"]}</div></div>', unsafe_allow_html=True)
                    ca,cb = col.columns(2)
                    ca.link_button("▶️ Watch", r['video_url'], use_container_width=True)
                    if cb.button("🗑️", key=f"dv_{r['id']}"):
                        conn2 = get_conn(); conn2.execute("DELETE FROM videos WHERE id=?",(r['id'],)); conn2.commit(); conn2.close(); st.rerun()


def admin_clients():
    st.markdown('<div class="section-header">👥 Client Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Members, payments, Telegram reminders</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Member","👥 All Members","💳 Payments","⚠️ Expiring Soon"])

    with tab1:
        with st.form("add_member"):
            c1,c2 = st.columns(2)
            with c1:
                name        = st.text_input("Full Name *")
                username    = st.text_input("Login Username *", placeholder="rahul_sharma")
                password    = st.text_input("Initial Password *", type="password")
                discord_id  = st.text_input("Discord Username")
                telegram_id = st.text_input("Telegram Chat ID", placeholder="Get via @userinfobot")
            with c2:
                email    = st.text_input("Email")
                phone    = st.text_input("Phone")
                plan     = st.selectbox("Plan", list(PLAN_AMOUNTS.keys()))
                status   = st.selectbox("Status",["Active","Trial","Inactive"])
                joined   = st.date_input("Joined", value=date.today())
                days_map = {"Premium Monthly":30,"Premium Quarterly":90,"Premium Annual":365,"Trial":7}
                expiry   = st.date_input("Expiry", value=joined+timedelta(days=days_map.get(plan,30)))
            notes           = st.text_area("Notes")
            send_tg_welcome = st.checkbox("📲 Send Telegram welcome", value=True)
            if st.form_submit_button("Add Member →", use_container_width=True):
                if not name or not username or not password: st.error("Name, username, password required.")
                else:
                    conn = get_conn()
                    try:
                        conn.execute("INSERT INTO clients (name,username,password_hash,discord_id,telegram_id,email,phone,plan,status,joined_date,expiry_date,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                            (name,username.lower().strip(),hash_password(password),discord_id,telegram_id,email,phone,plan,status,str(joined),str(expiry),notes))
                        conn.commit()
                        tg_msg = ""
                        if send_tg_welcome and telegram_id:
                            ok,msg = tg_welcome(telegram_id,name,username,password,plan)
                            tg_msg = f" | Telegram:{'✅' if ok else '⚠️'}"
                        st.success(f"✅ {name} added | **{username}** / **{password}**{tg_msg}")
                    except Exception as e: st.error(f"Username exists: {e}")
                    finally: conn.close()

    with tab2:
        conn = get_conn()
        search = st.text_input("🔍 Search")
        s = f"%{search}%"
        rows = conn.execute("SELECT * FROM clients WHERE name LIKE ? OR username LIKE ? ORDER BY created_at DESC",(s,s)).fetchall() if search \
              else conn.execute("SELECT * FROM clients ORDER BY created_at DESC").fetchall()
        conn.close()
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Total",len(rows)); m2.metric("Active",sum(1 for r in rows if r['status']=='Active'))
        m3.metric("Trial",sum(1 for r in rows if r['status']=='Trial')); m4.metric("Inactive",sum(1 for r in rows if r['status']=='Inactive'))
        for r in rows:
            exp = date.fromisoformat(r['expiry_date']) if r['expiry_date'] else None
            dl  = (exp-date.today()).days if exp else None
            sc  = {"Active":"#00ffb4","Inactive":"#ff6b6b","Trial":"#ffd700"}.get(r['status'],"#aaa")
            warn= f" ⚠️{dl}d" if dl and dl<=7 else (f" {dl}d" if dl else "")
            with st.expander(f"{'🟢' if r['status']=='Active' else '🔴'} {r['name']} (@{r['username']}) | {r['plan']}{warn}"):
                c1,c2,c3,c4 = st.columns(4)
                c1.markdown(f"**Status:** <span style='color:{sc}'>{r['status']}</span>", unsafe_allow_html=True)
                c2.markdown(f"**Expires:** {r['expiry_date'] or '—'}")
                c3.markdown(f"**Days left:** {f'{dl}d' if dl else '—'}")
                c4.markdown(f"**Plan:** {r['plan']}")
                ic = st.columns(4)
                if r['email']:       ic[0].caption(f"📧 {r['email']}")
                if r['phone']:       ic[1].caption(f"📱 {r['phone']}")
                if r['discord_id']:  ic[2].caption(f"💬 {r['discord_id']}")
                if r['telegram_id']: ic[3].caption("✈️ Telegram linked")
                ac1,ac2 = st.columns(2)
                if ac1.button("📲 Send Reminder", key=f"tgr_{r['id']}"):
                    if r['telegram_id']:
                        ok,msg = tg_renewal_reminder(r['telegram_id'],r['name'],dl or 0,r['plan'],r['expiry_date'] or '—')
                        st.success(msg) if ok else st.error(msg)
                    else: st.warning("No Telegram ID.")
                if ac2.button("💳 Payment Link", key=f"pl_{r['id']}"):
                    res = get_payment_link(r['plan'],r['name'],r['email'] or "",r['phone'] or "")
                    st.code(res['url']) if res.get('success') else st.error(res.get('error'))
                with st.expander("🔑 Reset Password"):
                    np = st.text_input("New Password", type="password", key=f"pw_{r['id']}")
                    if st.button("Reset", key=f"rst_{r['id']}"):
                        conn2 = get_conn(); conn2.execute("UPDATE clients SET password_hash=? WHERE id=?",(hash_password(np),r['id'])); conn2.commit(); conn2.close(); st.success("Reset.")
                ec1,ec2,ec3,ec4 = st.columns(4)
                new_st   = ec1.selectbox("Status",["Active","Inactive","Trial"],index=["Active","Inactive","Trial"].index(r['status']),key=f"st_{r['id']}")
                ext_days = ec2.number_input("Extend (days)",0,365,key=f"ext_{r['id']}")
                tg_new   = ec3.text_input("Telegram ID",value=r['telegram_id'] or "",key=f"tgid_{r['id']}")
                if ec4.button("Update",key=f"upd_{r['id']}"):
                    new_exp = r['expiry_date']
                    if ext_days>0 and exp: new_exp = str(exp+timedelta(days=int(ext_days)))
                    conn2 = get_conn(); conn2.execute("UPDATE clients SET status=?,expiry_date=?,telegram_id=? WHERE id=?",(new_st,new_exp,tg_new or None,r['id'])); conn2.commit(); conn2.close(); st.success("Updated!"); st.rerun()
                if st.button("🗑️ Remove", key=f"del_{r['id']}"):
                    conn2 = get_conn(); conn2.execute("DELETE FROM clients WHERE id=?",(r['id'],)); conn2.commit(); conn2.close(); st.rerun()

    with tab3:
        ptab1,ptab2 = st.tabs(["📋 All Payments","➕ Log Payment"])
        with ptab1:
            conn = get_conn()
            pays = conn.execute("SELECT p.*,c.name,c.username FROM payments p LEFT JOIN clients c ON p.client_id=c.id ORDER BY p.created_at DESC").fetchall(); conn.close()
            if not pays: st.info("No payments logged yet.")
            else:
                total = sum(p['amount'] for p in pays if p['amount'])
                st.markdown(f'<div class="metric-card" style="max-width:300px"><div class="metric-value" style="color:#00ffb4">₹{total:,.0f}</div><div class="metric-label">Total Revenue</div></div>', unsafe_allow_html=True)
                for p in pays:
                    st.markdown(f'<div class="call-card"><b style="color:#fff">{p["name"] or "Unknown"}</b> <span style="color:#445566">@{p["username"] or "—"}</span><span style="color:#00ffb4;float:right;font-weight:800;font-size:20px">₹{p["amount"]:,.0f}</span><br><span style="color:#99aabb;font-size:13px">{p["plan"]} | {p["payment_method"] or "—"} | {p["razorpay_id"] or "Manual"} | {p["payment_date"] or "—"}</span></div>', unsafe_allow_html=True)
        with ptab2:
            conn = get_conn()
            ml = conn.execute("SELECT id,name,username FROM clients ORDER BY name").fetchall(); conn.close()
            if not ml: st.info("Add members first.")
            else:
                opts = {f"{m['name']} (@{m['username']})":m['id'] for m in ml}
                with st.form("log_payment"):
                    sel    = st.selectbox("Member *", list(opts.keys()))
                    rz_id  = st.text_input("Razorpay ID", placeholder="pay_XXXXXXXXXX")
                    amount = st.number_input("Amount ₹ *", min_value=0.0, step=1.0)
                    plan   = st.selectbox("Plan", list(PLAN_AMOUNTS.keys()))
                    method = st.selectbox("Method",["UPI","Card","Net Banking","Cash","Bank Transfer","Other"])
                    pd_    = st.date_input("Payment Date", value=date.today())
                    pnotes = st.text_input("Notes")
                    extend = st.checkbox("Auto-extend subscription", value=True)
                    if st.form_submit_button("Log Payment →", use_container_width=True):
                        if not amount: st.error("Amount required.")
                        else:
                            cid = opts[sel]; new_exp = None
                            conn2 = get_conn()
                            conn2.execute("INSERT INTO payments (client_id,razorpay_id,amount,plan,status,payment_method,notes,payment_date) VALUES(?,?,?,?,?,?,?,?)",
                                (cid,rz_id or None,amount,plan,'captured',method,pnotes,str(pd_)))
                            if extend:
                                days_map = {"Premium Monthly":30,"Premium Quarterly":90,"Premium Annual":365,"Trial":7}
                                row = conn2.execute("SELECT expiry_date FROM clients WHERE id=?",(cid,)).fetchone()
                                try:
                                    base = date.fromisoformat(row['expiry_date']) if row['expiry_date'] else date.today()
                                    if base<date.today(): base = date.today()
                                    new_exp = str(base+timedelta(days=days_map.get(plan,30)))
                                except: new_exp = str(date.today()+timedelta(days=30))
                                conn2.execute("UPDATE clients SET status='Active',expiry_date=?,plan=? WHERE id=?",(new_exp,plan,cid))
                            conn2.commit(); conn2.close()
                            st.success(f"✅ ₹{amount:,.0f} logged."+(f" Extended to {new_exp}" if new_exp else ""))

    with tab4:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM clients WHERE status='Active' AND expiry_date IS NOT NULL AND expiry_date<=date('now','+7 days') ORDER BY expiry_date").fetchall(); conn.close()
        if not rows: st.success("✅ No renewals due in 7 days.")
        else:
            st.warning(f"⚠️ {len(rows)} member(s) expiring soon!")
            if st.button("📲 Send Bulk Telegram Reminders", type="primary"):
                sent = 0
                for r in rows:
                    if r['telegram_id']:
                        dl = (date.fromisoformat(r['expiry_date'])-date.today()).days
                        ok,_ = tg_renewal_reminder(r['telegram_id'],r['name'],dl,r['plan'],r['expiry_date'])
                        if ok: sent += 1
                st.success(f"✅ Sent {sent} reminder(s).")
            for r in rows:
                dl = (date.fromisoformat(r['expiry_date'])-date.today()).days
                st.markdown(f'<div class="call-card" style="border-left-color:#ffd700">{"🔴" if dl<=2 else "🟡"} <b style="color:#fff">{r["name"]}</b> <span style="color:#445566">@{r["username"]}</span><span style="color:#ffd700;float:right;font-weight:700">{dl}d left</span><br><span style="color:#99aabb;font-size:13px">{r["plan"]} | Exp {r["expiry_date"]}{" | 📱 "+r["phone"] if r["phone"] else ""}{" | ✈️ Telegram" if r["telegram_id"] else " | ❌ No Telegram"}</span></div>', unsafe_allow_html=True)


def admin_performance():
    st.markdown('<div class="section-header">📈 Performance Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">P&L charts, win rates, track record</div>', unsafe_allow_html=True)
    conn = get_conn()
    eq_rows = conn.execute("SELECT symbol,call_type,entry_price,exit_price,pnl_pct,result,exit_date FROM equity_calls WHERE status='Closed' AND pnl_pct IS NOT NULL ORDER BY exit_date").fetchall()
    op_rows = conn.execute("SELECT underlying,option_type,strike,call_type,entry_premium,exit_premium,pnl_pct,result,exit_date FROM options_calls WHERE status='Closed' AND pnl_pct IS NOT NULL ORDER BY exit_date").fetchall()
    conn.close()

    tab1,tab2,tab3 = st.tabs(["📊 Equity","⚡ Options","🔄 Combined"])

    with tab1:
        if not eq_rows: st.info("Close some equity calls first.")
        else:
            pnls = [r['pnl_pct'] for r in eq_rows]; wins = sum(1 for p in pnls if p>0)
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%")
            m3.metric("Best",f"{max(pnls):+.2f}%"); m4.metric("Worst",f"{min(pnls):+.2f}%")
            cum=[]; r=0
            for p in pnls: r+=p; cum.append(round(r,2))
            render_line_chart("Cumulative Equity P&L (%)",[r['exit_date'] or f"#{i+1}" for i,r in enumerate(eq_rows)],cum,"#00ffb4")
            render_bar_chart("Individual Call P&L (%)",[r['symbol'] for r in eq_rows],pnls,["#00ffb4" if p>0 else "#ff6b6b" for p in pnls])

    with tab2:
        if not op_rows: st.info("Close some options calls first.")
        else:
            pnls = [r['pnl_pct'] for r in op_rows]; wins = sum(1 for p in pnls if p>0)
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%")
            m3.metric("Best",f"{max(pnls):+.2f}%"); m4.metric("Worst",f"{min(pnls):+.2f}%")
            cum=[]; r=0
            for p in pnls: r+=p; cum.append(round(r,2))
            render_line_chart("Cumulative Options P&L (%)",[r['exit_date'] or f"#{i+1}" for i,r in enumerate(op_rows)],cum,"#7b61ff")
            render_bar_chart("Individual Options P&L (%)",[f"{r['underlying']} {r['strike']}{r['option_type']}" for r in op_rows],pnls,["#00ffb4" if p>0 else "#ff6b6b" for p in pnls])

    with tab3:
        all_pnls = [r['pnl_pct'] for r in eq_rows]+[r['pnl_pct'] for r in op_rows]
        if not all_pnls: st.info("No closed calls yet.")
        else:
            tw = sum(1 for p in all_pnls if p>0); avg = sum(all_pnls)/len(all_pnls)
            st.markdown(f"""<div class="sub-card" style="text-align:center;padding:40px">
              <div style="font-size:13px;color:#445566;text-transform:uppercase;letter-spacing:3px;margin-bottom:16px">Overall Track Record</div>
              <div class="winrate-badge" style="font-size:36px;padding:12px 40px">{tw/len(all_pnls)*100:.0f}% Win Rate</div>
              <div style="display:flex;justify-content:center;gap:60px;margin-top:30px">
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:2px">Total</div><div style="font-family:'Syne',sans-serif;font-size:40px;font-weight:800;color:#fff">{len(all_pnls)}</div></div>
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:2px">Wins</div><div style="font-family:'Syne',sans-serif;font-size:40px;font-weight:800;color:#00ffb4">{tw}</div></div>
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:2px">Losses</div><div style="font-family:'Syne',sans-serif;font-size:40px;font-weight:800;color:#ff6b6b">{len(all_pnls)-tw}</div></div>
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:2px">Avg P&L</div><div style="font-family:'Syne',sans-serif;font-size:40px;font-weight:800;color:{'#00ffb4' if avg>0 else '#ff6b6b'}">{avg:+.1f}%</div></div>
              </div></div>""", unsafe_allow_html=True)
            conn = get_conn()
            pays = conn.execute("SELECT amount FROM payments WHERE status='captured'").fetchall(); conn.close()
            if pays:
                rev = sum(p['amount'] for p in pays if p['amount'])
                st.markdown(f'<div class="metric-card" style="max-width:300px;margin:0 auto"><div class="metric-value" style="color:#00ffb4">₹{rev:,.0f}</div><div class="metric-label">Total Revenue</div></div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# MEMBER AUTH
# ══════════════════════════════════════════════════════════════════════

def member_login():
    st.markdown("""
    <div style="max-width:440px;margin:60px auto;text-align:center">
      <div style="font-family:'Syne',sans-serif;font-size:40px;font-weight:800;color:#00ddff">📈 NYZTRADE</div>
      <div style="font-size:11px;color:#445566;letter-spacing:4px;text-transform:uppercase;margin:4px 0 30px">Premium Member Portal</div>
    </div>""", unsafe_allow_html=True)
    with st.form("member_login"):
        username  = st.text_input("Username")
        password  = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Access Premium →", use_container_width=True)
        if submitted:
            member = verify_member(username, password)
            if member:
                st.session_state.member = dict(member)
                st.rerun()
            else:
                st.error("Invalid credentials or subscription inactive.")
    st.markdown('<div style="text-align:center;margin-top:16px;font-size:13px;color:#445566">Need access? <a href="https://linkedin.com/in/drniyas" target="_blank" style="color:#00ddff">linkedin.com/in/drniyas</a></div>', unsafe_allow_html=True)
    if st.button("← Back"):
        st.session_state.portal = None
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# MEMBER PAGES
# ══════════════════════════════════════════════════════════════════════

def member_home(member):
    st.markdown(f'<div class="section-header">Welcome back, {member["name"].split()[0]} 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Your daily trading dashboard</div>', unsafe_allow_html=True)
    conn = get_conn()
    c1,c2,c3,c4 = st.columns(4)
    open_eq  = conn.execute("SELECT COUNT(*) FROM equity_calls WHERE status='Open'").fetchone()[0]
    open_op  = conn.execute("SELECT COUNT(*) FROM options_calls WHERE status='Open'").fetchone()[0]
    eq_c = conn.execute("SELECT pnl_pct FROM equity_calls WHERE status='Closed' AND pnl_pct IS NOT NULL").fetchall()
    op_c = conn.execute("SELECT pnl_pct FROM options_calls WHERE status='Closed' AND pnl_pct IS NOT NULL").fetchall()
    eq_wr = f"{sum(1 for r in eq_c if r[0]>0)/len(eq_c)*100:.0f}%" if eq_c else "—"
    op_wr = f"{sum(1 for r in op_c if r[0]>0)/len(op_c)*100:.0f}%" if op_c else "—"
    for col,val,label,color in [(c1,open_eq,"Equity Open","#00ddff"),(c2,open_op,"Options Open","#7b61ff"),(c3,eq_wr,"Equity Win Rate","#00ffb4"),(c4,op_wr,"Options Win Rate","#ffd700")]:
        col.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{color}">{val}</div><div class="metric-label">{label}</div></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("#### 📢 Today's Updates")
    updates = conn.execute("SELECT * FROM daily_updates WHERE posted_date=? ORDER BY created_at DESC",(str(date.today()),)).fetchall()
    if updates:
        for u in updates:
            st.markdown(f'<div class="update-card"><span class="tag">{u["category"]}</span><div style="font-weight:700;font-size:17px;margin:10px 0 8px;color:#fff">{u["title"]}</div><div style="color:#c0d0e0;line-height:1.6">{u["content"][:400]}{"..." if len(u["content"])>400 else ""}</div></div>', unsafe_allow_html=True)
    else: st.info("No updates today yet.")
    st.divider()
    left,right = st.columns(2)
    with left:
        st.markdown("#### 📊 Active Equity")
        for r in conn.execute("SELECT * FROM equity_calls WHERE status='Open' ORDER BY created_at DESC LIMIT 4").fetchall():
            st.markdown(f'<div class="call-card {r["call_type"].lower()}"><b style="color:#fff;font-size:16px">{r["symbol"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><br><span style="color:#99aabb;font-size:13px">Entry ₹{r["entry_price"]} | T1 ₹{r["target1"]} | SL ₹{r["stop_loss"]}</span></div>', unsafe_allow_html=True)
    with right:
        st.markdown("#### ⚡ Active Options")
        for r in conn.execute("SELECT * FROM options_calls WHERE status='Open' ORDER BY created_at DESC LIMIT 4").fetchall():
            st.markdown(f'<div class="call-card {r["call_type"].lower()}"><b style="color:#fff;font-size:16px">{r["underlying"]} {r["strike"]} {r["option_type"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><br><span style="color:#99aabb;font-size:13px">Exp {r["expiry"]} | ₹{r["entry_premium"]} | T ₹{r["target_premium"]} | SL ₹{r["stop_premium"]}</span></div>', unsafe_allow_html=True)
    conn.close()


def member_equity(member):
    st.markdown('<div class="section-header">📊 Equity Calls</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">All equity trading calls — live and historical</div>', unsafe_allow_html=True)
    tab1,tab2 = st.tabs(["📋 Open Calls","📁 Track Record"])
    conn = get_conn()
    with tab1:
        rows = conn.execute("SELECT * FROM equity_calls WHERE status='Open' ORDER BY created_at DESC").fetchall()
        if not rows: st.info("No active equity calls right now.")
        for r in rows:
            rr = round((r['target1']-r['entry_price'])/(r['entry_price']-r['stop_loss']),2) if r['entry_price'] and r['stop_loss'] and r['stop_loss']!=r['entry_price'] else None
            st.markdown(f"""<div class="call-card {r['call_type'].lower()}">
              <div style="display:flex;justify-content:space-between">
                <div><span style="font-size:20px;font-weight:800;color:#fff">{r['symbol']}</span><span class="badge badge-{r['call_type'].lower()}">{r['call_type']}</span><span class="badge badge-open">OPEN</span></div>
                <div style="font-size:13px;color:#445566">{r['posted_date'] or ''}</div>
              </div>
              <div style="display:flex;gap:30px;margin-top:14px;flex-wrap:wrap">
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Entry</div><div style="font-size:22px;font-weight:700;color:#fff">₹{r['entry_price']}</div></div>
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Target 1</div><div style="font-size:22px;font-weight:700;color:#00ffb4">₹{r['target1']}</div></div>
                {"<div><div style='font-size:11px;color:#445566;text-transform:uppercase'>Target 2</div><div style='font-size:22px;font-weight:700;color:#00ffb4'>₹"+str(r['target2'])+"</div></div>" if r['target2'] else ""}
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Stop Loss</div><div style="font-size:22px;font-weight:700;color:#ff6b6b">₹{r['stop_loss']}</div></div>
                {"<div><div style='font-size:11px;color:#445566;text-transform:uppercase'>R:R</div><div style='font-size:22px;font-weight:700;color:#ffd700'>1:"+str(rr)+"</div></div>" if rr else ""}
              </div>
              {"<div style='margin-top:12px;background:#020e20;border-radius:6px;padding:10px;font-size:14px;color:#c0d0e0'><b style='color:#00ddff'>Analysis:</b> "+r['rationale']+"</div>" if r['rationale'] else ""}
            </div>""", unsafe_allow_html=True)
    with tab2:
        rows = conn.execute("SELECT * FROM equity_calls WHERE status='Closed' ORDER BY exit_date DESC").fetchall()
        if not rows: st.info("No closed calls yet.")
        else:
            pnls = [r['pnl_pct'] for r in rows if r['pnl_pct'] is not None]
            if pnls:
                wins = sum(1 for p in pnls if p>0)
                st.markdown(f'<div class="sub-card" style="display:flex;gap:40px;align-items:center"><div class="winrate-badge">{wins/len(pnls)*100:.0f}% Win</div><div><span style="color:#99aabb;font-size:13px">Avg P&L</span><div style="font-size:24px;font-weight:800;color:{"#00ffb4" if sum(pnls)/len(pnls)>0 else "#ff6b6b"}">{sum(pnls)/len(pnls):+.1f}%</div></div><div><span style="color:#99aabb;font-size:13px">Total</span><div style="font-size:24px;font-weight:800;color:#fff">{len(rows)}</div></div></div>', unsafe_allow_html=True)
            for r in rows:
                pc = "#00ffb4" if (r['pnl_pct'] or 0)>0 else "#ff6b6b"
                pnl_str = f"{r['pnl_pct']:+.2f}%" if r['pnl_pct'] else "—"
                st.markdown(f'<div class="call-card closed"><b style="color:#fff">{r["symbol"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:800;float:right;font-size:20px">{pnl_str}</span><br><span style="color:#99aabb;font-size:13px">₹{r["entry_price"]} → ₹{r["exit_price"] or "—"} | {r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)
    conn.close()


def member_options(member):
    st.markdown('<div class="section-header">⚡ Options & GEX</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Options calls with gamma exposure analysis</div>', unsafe_allow_html=True)
    tab1,tab2,tab3 = st.tabs(["⚡ Open Calls","📊 GEX Analysis","📁 Track Record"])
    conn = get_conn()
    with tab1:
        rows = conn.execute("SELECT * FROM options_calls WHERE status='Open' ORDER BY created_at DESC").fetchall()
        if not rows: st.info("No active options calls.")
        for r in rows:
            st.markdown(f"""<div class="call-card {r['call_type'].lower()}">
              <div style="display:flex;justify-content:space-between">
                <div><span style="font-size:20px;font-weight:800;color:#fff">{r['underlying']} {r['strike']} {r['option_type']}</span><span class="badge badge-{r['call_type'].lower()}">{r['call_type']}</span><span class="badge badge-{r['option_type'].lower()}">{r['option_type']}</span></div>
                <div style="font-size:13px;color:#445566">Exp: {r['expiry']}</div>
              </div>
              <div style="display:flex;gap:30px;margin-top:14px">
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Entry Premium</div><div style="font-size:22px;font-weight:700;color:#fff">₹{r['entry_premium']}</div></div>
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Target</div><div style="font-size:22px;font-weight:700;color:#00ffb4">₹{r['target_premium']}</div></div>
                <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Stop Loss</div><div style="font-size:22px;font-weight:700;color:#ff6b6b">₹{r['stop_premium']}</div></div>
              </div>
              {"<div style='margin-top:12px;background:#020e20;border-radius:6px;padding:10px;font-size:14px;color:#c0d0e0'><b style='color:#7b61ff'>📊 GEX:</b> "+r['gex_note']+"</div>" if r['gex_note'] else ""}
              {"<div style='margin-top:8px;background:#020e20;border-radius:6px;padding:10px;font-size:14px;color:#c0d0e0'><b style='color:#00ddff'>Analysis:</b> "+r['rationale']+"</div>" if r['rationale'] else ""}
            </div>""", unsafe_allow_html=True)
    with tab2:
        rows = conn.execute("SELECT * FROM daily_updates WHERE category='GEX' ORDER BY created_at DESC LIMIT 8").fetchall()
        if not rows: st.info("No GEX analysis posted yet.")
        for r in rows:
            with st.expander(f"📊 {r['title']} — {r['posted_date']}"):
                st.markdown(r['content'])
    with tab3:
        rows = conn.execute("SELECT * FROM options_calls WHERE status='Closed' ORDER BY exit_date DESC").fetchall()
        if not rows: st.info("No closed options calls yet.")
        else:
            pnls = [r['pnl_pct'] for r in rows if r['pnl_pct'] is not None]
            if pnls:
                wins = sum(1 for p in pnls if p>0)
                st.markdown(f'<div class="sub-card" style="display:flex;gap:40px;align-items:center"><div class="winrate-badge">{wins/len(pnls)*100:.0f}% Win</div><div><span style="color:#99aabb;font-size:13px">Avg P&L</span><div style="font-size:24px;font-weight:800;color:{"#00ffb4" if sum(pnls)/len(pnls)>0 else "#ff6b6b"}">{sum(pnls)/len(pnls):+.1f}%</div></div><div><span style="color:#99aabb;font-size:13px">Total</span><div style="font-size:24px;font-weight:800;color:#fff">{len(pnls)}</div></div></div>', unsafe_allow_html=True)
            for r in rows:
                pc = "#00ffb4" if (r['pnl_pct'] or 0)>0 else "#ff6b6b"
                pnl_str = f"{r['pnl_pct']:+.2f}%" if r['pnl_pct'] else "—"
                st.markdown(f'<div class="call-card closed"><b style="color:#fff">{r["underlying"]} {r["strike"]} {r["option_type"]} | {r["expiry"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:700;float:right;font-size:18px">{pnl_str}</span><br><span style="color:#99aabb;font-size:13px">₹{r["entry_premium"]} → ₹{r["exit_premium"] or "—"} | {r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)
    conn.close()


def member_updates(member):
    st.markdown('<div class="section-header">📢 Updates Feed</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Daily market analysis, GEX maps, insights from Dr. Niyas</div>', unsafe_allow_html=True)
    conn = get_conn()
    f1,f2 = st.columns([2,1])
    cat_f  = f1.selectbox("Category",["All","Pre-Market","Intraday","Post-Market","GEX Update","Market View","Education","General"])
    date_f = f2.date_input("Date", value=None)
    q = "SELECT * FROM daily_updates"; params=[]; conds=[]
    if cat_f!="All": conds.append("category=?"); params.append(cat_f)
    if date_f:       conds.append("posted_date=?"); params.append(str(date_f))
    if conds: q+=" WHERE "+" AND ".join(conds)
    q+=" ORDER BY created_at DESC"
    rows = conn.execute(q,params).fetchall(); conn.close()
    if not rows: st.info("No updates in this category.")
    for r in rows:
        cc = {"Pre-Market":"#00ddff","GEX Update":"#7b61ff","Intraday":"#ffd700","Post-Market":"#00ffb4","Market View":"#ff6b6b","Education":"#00ffb4"}.get(r['category'],"#445566")
        tags = " ".join([f'<span class="tag">{t.strip()}</span>' for t in r['tags'].split(',')]) if r['tags'] else ""
        st.markdown(f"""<div class="update-card">
          <div style="display:flex;justify-content:space-between;margin-bottom:12px">
            <span style="background:{cc}22;color:{cc};border:1px solid {cc}44;border-radius:20px;font-size:11px;padding:2px 12px;font-weight:700;text-transform:uppercase">{r['category']}</span>
            <div style="font-size:12px;color:#445566">{r['posted_date'] or ''}</div>
          </div>
          <div style="font-family:'Syne',sans-serif;font-size:20px;font-weight:700;color:#fff;margin-bottom:12px">{r['title']}</div>
          <div style="color:#c0d0e0;line-height:1.7;font-size:15px">{r['content']}</div>
          {('<div style="margin-top:12px">'+tags+'</div>') if tags else ""}
        </div>""", unsafe_allow_html=True)
        if r['video_url']:
            st.markdown(f'<div style="margin:-8px 0 16px;background:#041428;border:1px solid #0a2040;border-radius:8px;padding:12px 16px">🎬 <a href="{r["video_url"]}" target="_blank" style="color:#00ddff;text-decoration:none;font-weight:600">Watch Video →</a></div>', unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#0a2040;margin:4px 0 20px'>", unsafe_allow_html=True)


def member_videos(member):
    st.markdown('<div class="section-header">🎬 Video Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Premium educational content — GEX, options strategy, equity analysis</div>', unsafe_allow_html=True)
    conn = get_conn()
    cat_f = st.selectbox("Browse by Category",["All","GEX Education","Options Strategy","Equity Analysis","Market Overview","ESG/Valuation","Live Session","Other"])
    rows  = conn.execute("SELECT * FROM videos"+(f" WHERE category=?" if cat_f!="All" else "")+" ORDER BY created_at DESC",(cat_f,) if cat_f!="All" else ()).fetchall(); conn.close()
    if not rows: st.info("No videos here yet."); return
    if cat_f=="All":
        from collections import defaultdict
        grouped = defaultdict(list)
        for r in rows: grouped[r['category']].append(r)
        icons = {"GEX Education":"📊","Options Strategy":"⚡","Equity Analysis":"📈","Market Overview":"🌐","ESG/Valuation":"🏷️","Live Session":"🔴","Other":"🎬"}
        for cat,vids in grouped.items():
            st.markdown(f"#### {icons.get(cat,'🎬')} {cat}")
            _video_grid(vids); st.divider()
    else: _video_grid(rows)

def _video_grid(rows):
    for i in range(0,len(rows),3):
        cols = st.columns(3)
        for j,col in enumerate(cols):
            if i+j>=len(rows): break
            r = rows[i+j]
            with col:
                if r['thumbnail']: st.image(r['thumbnail'], use_column_width=True)
                else: st.markdown('<div style="background:#041428;border:1px solid #0a2040;border-radius:8px;height:120px;display:flex;align-items:center;justify-content:center;font-size:40px;margin-bottom:8px">🎬</div>', unsafe_allow_html=True)
                desc_html = f'<div style="font-size:12px;color:#99aabb;margin-bottom:6px">{r["description"][:80]}{"..." if r["description"] and len(r["description"])>80 else ""}</div>' if r["description"] else ""
                st.markdown(f'<div style="padding:4px 0 12px"><div style="font-weight:700;font-size:15px;color:#fff;margin-bottom:4px;line-height:1.4">{r["title"]}</div>{desc_html}<div style="font-size:11px;color:#445566">{r["posted_date"] or ""}</div></div>', unsafe_allow_html=True)
                st.link_button("▶️ Watch Now", r['video_url'], use_container_width=True)


def member_performance(member):
    st.markdown('<div class="section-header">📈 Track Record</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Verified performance — all closed calls</div>', unsafe_allow_html=True)
    conn = get_conn()
    eq_rows = conn.execute("SELECT symbol,call_type,entry_price,exit_price,pnl_pct,result,exit_date FROM equity_calls WHERE status='Closed' AND pnl_pct IS NOT NULL ORDER BY exit_date").fetchall()
    op_rows = conn.execute("SELECT underlying,option_type,strike,call_type,entry_premium,exit_premium,pnl_pct,result,exit_date FROM options_calls WHERE status='Closed' AND pnl_pct IS NOT NULL ORDER BY exit_date").fetchall()
    conn.close()
    all_pnls = [r['pnl_pct'] for r in eq_rows]+[r['pnl_pct'] for r in op_rows]
    if not all_pnls: st.info("Track record will appear here as calls are closed."); return
    tw = sum(1 for p in all_pnls if p>0); avg = sum(all_pnls)/len(all_pnls)
    st.markdown(f"""<div class="sub-card" style="text-align:center;padding:36px">
      <div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:4px;margin-bottom:16px">Verified Track Record — Dr. Niyas N</div>
      <div class="winrate-badge" style="font-size:32px;padding:10px 36px">{tw/len(all_pnls)*100:.0f}% Win Rate</div>
      <div style="display:flex;justify-content:center;gap:50px;margin-top:28px;flex-wrap:wrap">
        <div><div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:2px">Total Calls</div><div style="font-family:'Syne',sans-serif;font-size:38px;font-weight:800;color:#fff">{len(all_pnls)}</div></div>
        <div><div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:2px">Winners</div><div style="font-family:'Syne',sans-serif;font-size:38px;font-weight:800;color:#00ffb4">{tw}</div></div>
        <div><div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:2px">Avg P&L</div><div style="font-family:'Syne',sans-serif;font-size:38px;font-weight:800;color:{'#00ffb4' if avg>0 else '#ff6b6b'}">{avg:+.1f}%</div></div>
        <div><div style="font-size:11px;color:#445566;text-transform:uppercase;letter-spacing:2px">Best</div><div style="font-family:'Syne',sans-serif;font-size:38px;font-weight:800;color:#00ffb4">{max(all_pnls):+.0f}%</div></div>
      </div></div>""", unsafe_allow_html=True)
    st.divider()
    tab1,tab2 = st.tabs(["📊 Equity","⚡ Options"])
    with tab1:
        if not eq_rows: st.info("No closed equity calls yet.")
        else:
            pnls=[r['pnl_pct'] for r in eq_rows]; wins=sum(1 for p in pnls if p>0)
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%"); m3.metric("Best",f"{max(pnls):+.2f}%"); m4.metric("Total",len(pnls))
            cum=[]; r=0
            for p in pnls: r+=p; cum.append(round(r,2))
            render_line_chart("Cumulative Equity P&L (%)",[r['exit_date'] or f"#{i+1}" for i,r in enumerate(eq_rows)],cum,"#00ffb4")
            for r in eq_rows[::-1]:
                pc = "#00ffb4" if r['pnl_pct']>0 else "#ff6b6b"
                st.markdown(f'<div class="call-card closed" style="padding:10px 16px"><b style="color:#fff">{r["symbol"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:800;float:right">{r["pnl_pct"]:+.2f}%</span><br><span style="color:#99aabb;font-size:12px">{r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)
    with tab2:
        if not op_rows: st.info("No closed options calls yet.")
        else:
            pnls=[r['pnl_pct'] for r in op_rows]; wins=sum(1 for p in pnls if p>0)
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("Win Rate",f"{wins/len(pnls)*100:.0f}%"); m2.metric("Avg P&L",f"{sum(pnls)/len(pnls):+.2f}%"); m3.metric("Best",f"{max(pnls):+.2f}%"); m4.metric("Total",len(pnls))
            cum=[]; r=0
            for p in pnls: r+=p; cum.append(round(r,2))
            render_line_chart("Cumulative Options P&L (%)",[r['exit_date'] or f"#{i+1}" for i,r in enumerate(op_rows)],cum,"#7b61ff")
            for r in op_rows[::-1]:
                pc = "#00ffb4" if r['pnl_pct']>0 else "#ff6b6b"
                st.markdown(f'<div class="call-card closed" style="padding:10px 16px"><b style="color:#fff">{r["underlying"]} {r["strike"]} {r["option_type"]}</b><span class="badge badge-{r["call_type"].lower()}">{r["call_type"]}</span><span style="color:{pc};font-weight:800;float:right">{r["pnl_pct"]:+.2f}%</span><br><span style="color:#99aabb;font-size:12px">{r["result"] or "—"} | {r["exit_date"] or "—"}</span></div>', unsafe_allow_html=True)


def member_profile(member):
    st.markdown('<div class="section-header">👤 My Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Your subscription details and account settings</div>', unsafe_allow_html=True)
    exp = date.fromisoformat(member['expiry_date']) if member.get('expiry_date') else None
    dl  = (exp-date.today()).days if exp else None
    dl_col = "#ff6b6b" if dl and dl<=7 else "#00ffb4"
    sc = {"Active":"#00ffb4","Trial":"#ffd700","Inactive":"#ff6b6b"}.get(member['status'],"#aaa")
    st.markdown(f"""<div class="sub-card">
      <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:16px">
        <div>
          <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:#fff">{member['name']}</div>
          <div style="font-size:13px;color:#445566">@{member['username']}</div>
          {f'<div style="font-size:13px;color:#445566">💬 {member["discord_id"]}</div>' if member.get('discord_id') else ""}
          {f'<div style="font-size:13px;color:#445566">📧 {member["email"]}</div>' if member.get('email') else ""}
        </div>
        <div style="text-align:right">
          <div style="font-size:11px;color:#445566;text-transform:uppercase">Plan</div>
          <div style="font-size:20px;font-weight:700;color:#00ddff">{member['plan']}</div>
          <div style="font-size:11px;color:#445566;text-transform:uppercase;margin-top:8px">Status</div>
          <div style="font-size:18px;font-weight:700;color:{sc}">{member['status']}</div>
        </div>
      </div>
      <div style="display:flex;gap:30px;margin-top:24px;padding-top:20px;border-top:1px solid #0a2040;flex-wrap:wrap">
        <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Member Since</div><div style="font-size:18px;font-weight:700;color:#fff">{member.get('joined_date','—')}</div></div>
        <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Expires</div><div style="font-size:18px;font-weight:700;color:#fff">{member.get('expiry_date','—')}</div></div>
        <div><div style="font-size:11px;color:#445566;text-transform:uppercase">Days Left</div><div style="font-size:18px;font-weight:700;color:{dl_col}">{f'{dl} days' if dl is not None else '—'}{'  ⚠️' if dl and dl<=7 else ''}</div></div>
      </div>
      {f'<div style="margin-top:16px;background:#ff6b6b11;border:1px solid #ff6b6b33;border-radius:8px;padding:12px;color:#ff6b6b;font-size:14px">⚠️ Expiring in {dl} days — contact admin to renew.</div>' if dl and dl<=7 else ""}
    </div>""", unsafe_allow_html=True)
    st.divider()
    st.markdown("#### 🔑 Change Password")
    with st.form("change_pw"):
        cur_pw  = st.text_input("Current Password", type="password")
        new_pw  = st.text_input("New Password", type="password", placeholder="Min 8 characters")
        conf_pw = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password →", use_container_width=True):
            if not cur_pw or not new_pw or not conf_pw: st.error("All fields required.")
            elif new_pw != conf_pw: st.error("New passwords don't match.")
            elif len(new_pw) < 8: st.error("Min 8 characters.")
            else:
                conn = get_conn()
                row = conn.execute("SELECT id FROM clients WHERE id=? AND password_hash=?",(member['id'],hash_password(cur_pw))).fetchone()
                if not row: st.error("Current password incorrect.")
                else:
                    conn.execute("UPDATE clients SET password_hash=? WHERE id=?",(hash_password(new_pw),member['id']))
                    conn.commit(); st.session_state.member['password_hash']=hash_password(new_pw)
                    st.success("✅ Password updated.")
                conn.close()


# ══════════════════════════════════════════════════════════════════════
# MAIN APP ROUTER
# ══════════════════════════════════════════════════════════════════════

def main():
    if "portal" not in st.session_state:
        st.session_state.portal = None

    portal = st.session_state.get("portal")

    # ── No portal selected ────────────────────
    if not portal:
        select_portal()
        return

    # ── ADMIN PORTAL ──────────────────────────
    if portal == "admin":
        if not st.session_state.get("admin_logged_in"):
            admin_login()
            return

        with st.sidebar:
            st.markdown('<div class="portal-logo">⚙️ ADMIN</div>', unsafe_allow_html=True)
            st.markdown('<div class="portal-sub">Nyztrade Command Centre</div>', unsafe_allow_html=True)
            st.divider()
            page = st.radio("", [
                "🏠 Dashboard", "📊 Equity Calls", "⚡ Options & GEX",
                "📢 Daily Updates", "🎬 Video Library",
                "👥 Client Management", "📈 Performance",
            ], label_visibility="collapsed")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()
            st.markdown('<div style="font-size:11px;color:#445566;text-align:center">Dr. Niyas N | Admin</div>', unsafe_allow_html=True)

        pages = {
            "🏠 Dashboard":         admin_dashboard,
            "📊 Equity Calls":      admin_equity,
            "⚡ Options & GEX":     admin_options,
            "📢 Daily Updates":     admin_updates,
            "🎬 Video Library":     admin_videos,
            "👥 Client Management": admin_clients,
            "📈 Performance":       admin_performance,
        }
        pages[page]()

    # ── MEMBER PORTAL ─────────────────────────
    elif portal == "member":
        if not st.session_state.get("member"):
            member_login()
            return

        member = st.session_state.member

        with st.sidebar:
            st.markdown('<div class="portal-logo">📈 NYZTRADE</div>', unsafe_allow_html=True)
            st.markdown('<div class="portal-sub">Premium Member</div>', unsafe_allow_html=True)
            st.divider()
            exp = date.fromisoformat(member['expiry_date']) if member.get('expiry_date') else None
            dl  = (exp-date.today()).days if exp else None
            dl_color = "#ff6b6b" if dl and dl<=7 else "#00ffb4"
            st.markdown(f'<div style="background:#041428;border:1px solid #0a2040;border-radius:10px;padding:12px 16px;margin-bottom:16px"><div style="font-weight:700;color:#fff;font-size:15px">{member["name"]}</div><div style="font-size:11px;color:#445566">{member["plan"]}</div><div style="font-size:12px;color:{dl_color};margin-top:6px;font-weight:600">{"⚠️ " if dl and dl<=7 else "✅ "}{f"{dl} days left" if dl else "Active"}</div></div>', unsafe_allow_html=True)
            page = st.radio("", [
                "🏠 Home", "📊 Equity Calls", "⚡ Options & GEX",
                "📢 Updates Feed", "🎬 Video Library",
                "📈 Track Record", "👤 My Profile",
            ], label_visibility="collapsed")
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                del st.session_state.member
                st.rerun()

        pages = {
            "🏠 Home":           member_home,
            "📊 Equity Calls":   member_equity,
            "⚡ Options & GEX":  member_options,
            "📢 Updates Feed":   member_updates,
            "🎬 Video Library":  member_videos,
            "📈 Track Record":   member_performance,
            "👤 My Profile":     member_profile,
        }
        pages[page](member)


main()
