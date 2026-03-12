import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
st.set_page_config(page_title="Nyztrade Admin", page_icon="⚙️",
                   layout="wide", initial_sidebar_state="expanded")

from shared.db import init_db
from shared.styles import DARK_CSS
import hashlib

init_db()

# ── Admin auth ────────────────────────────────
ADMIN_USER = "drniyas"
ADMIN_HASH = hashlib.sha256("nyztrade2024".encode()).hexdigest()

st.markdown(DARK_CSS, unsafe_allow_html=True)

def check_admin():
    if st.session_state.get("admin_logged_in"):
        return True
    st.markdown("""
    <div style="max-width:420px;margin:80px auto;background:#041428;
                border:1px solid #0a2040;border-radius:16px;padding:40px;">
      <div style="text-align:center;font-family:'Syne',sans-serif;font-size:30px;
                  font-weight:800;color:#00ddff;">⚙️ ADMIN PORTAL</div>
      <div style="text-align:center;font-size:11px;color:#445566;
                  letter-spacing:4px;margin-bottom:28px;">NYZTRADE COMMAND CENTRE</div>
    </div>""", unsafe_allow_html=True)
    with st.form("admin_login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login →", use_container_width=True):
            if u == ADMIN_USER and hashlib.sha256(p.encode()).hexdigest() == ADMIN_HASH:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")
    return False

if not check_admin():
    st.stop()

# ── Import pages ──────────────────────────────
from admin.pages import (dashboard, equity, options,
                          daily_updates, videos, clients, performance)

# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.markdown('<div class="portal-logo">⚙️ ADMIN</div>', unsafe_allow_html=True)
    st.markdown('<div class="portal-sub">Nyztrade Command Centre</div>', unsafe_allow_html=True)
    st.divider()

    page = st.radio("", [
        "🏠 Dashboard",
        "📊 Equity Calls",
        "⚡ Options & GEX",
        "📢 Daily Updates",
        "🎬 Video Library",
        "👥 Client Management",
        "📈 Performance",
    ], label_visibility="collapsed")

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.admin_logged_in = False
        st.rerun()
    st.markdown('<div style="font-size:11px;color:#445566;text-align:center;margin-top:8px;">Dr. Niyas N | Admin</div>',
                unsafe_allow_html=True)

# ── Routing ───────────────────────────────────
routes = {
    "🏠 Dashboard":        dashboard.show,
    "📊 Equity Calls":     equity.show,
    "⚡ Options & GEX":    options.show,
    "📢 Daily Updates":    daily_updates.show,
    "🎬 Video Library":    videos.show,
    "👥 Client Management":clients.show,
    "📈 Performance":       performance.show,
}
routes[page]()
