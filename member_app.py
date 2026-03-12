import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
st.set_page_config(page_title="Nyztrade Premium", page_icon="📈",
                   layout="wide", initial_sidebar_state="expanded")

from shared.db import init_db, verify_member
from shared.styles import DARK_CSS

init_db()
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ── Member auth ───────────────────────────────
def check_member():
    if st.session_state.get("member"):
        return True

    st.markdown("""
    <div style="max-width:440px;margin:60px auto;">
      <div style="text-align:center;margin-bottom:30px;">
        <div style="font-family:'Syne',sans-serif;font-size:40px;font-weight:800;color:#00ddff">📈 NYZTRADE</div>
        <div style="font-size:11px;color:#445566;letter-spacing:4px;text-transform:uppercase;margin-top:4px">Premium Member Portal</div>
      </div>
    </div>""", unsafe_allow_html=True)

    with st.form("member_login"):
        username = st.text_input("Username", placeholder="Your username")
        password = st.text_input("Password", type="password", placeholder="Your password")
        submitted = st.form_submit_button("Access Premium →", use_container_width=True)

        if submitted:
            member = verify_member(username, password)
            if member:
                st.session_state.member = dict(member)
                st.rerun()
            else:
                st.error("Invalid credentials or subscription inactive. Contact admin.")

    st.markdown("""
    <div style="text-align:center;margin-top:20px;font-size:13px;color:#445566">
      Need access? Join Nyztrade Premium Discord community.<br>
      <a href="https://linkedin.com/in/drniyas" target="_blank" style="color:#00ddff">linkedin.com/in/drniyas</a>
    </div>""", unsafe_allow_html=True)
    return False

if not check_member():
    st.stop()

member = st.session_state.member

# ── Import member pages ───────────────────────
from member.pages import (home, equity, options, updates, videos, profile, performance)

# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.markdown('<div class="portal-logo">📈 NYZTRADE</div>', unsafe_allow_html=True)
    st.markdown('<div class="portal-sub">Premium Member</div>', unsafe_allow_html=True)
    st.divider()

    # Member info pill
    from datetime import date
    exp = date.fromisoformat(member['expiry_date']) if member.get('expiry_date') else None
    dl  = (exp - date.today()).days if exp else None
    dl_color = "#ff6b6b" if dl and dl <= 7 else "#00ffb4"
    st.markdown(f"""
    <div style="background:#041428;border:1px solid #0a2040;border-radius:10px;
                padding:12px 16px;margin-bottom:16px;">
      <div style="font-weight:700;color:#fff;font-size:15px">{member['name']}</div>
      <div style="font-size:11px;color:#445566;margin-top:2px">{member['plan']}</div>
      <div style="font-size:12px;color:{dl_color};margin-top:6px;font-weight:600">
        {'⚠️ ' if dl and dl<=7 else '✅ '}{f'{dl} days left' if dl else 'Active'}
      </div>
    </div>""", unsafe_allow_html=True)

    page = st.radio("", [
        "🏠 Home",
        "📊 Equity Calls",
        "⚡ Options & GEX",
        "📢 Updates Feed",
        "🎬 Video Library",
        "📈 Track Record",
        "👤 My Profile",
    ], label_visibility="collapsed")

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        del st.session_state.member
        st.rerun()

# ── Routing ───────────────────────────────────
routes = {
    "🏠 Home":           home.show,
    "📊 Equity Calls":   equity.show,
    "⚡ Options & GEX":  options.show,
    "📢 Updates Feed":   updates.show,
    "🎬 Video Library":  videos.show,
    "📈 Track Record":   performance.show,
    "👤 My Profile":     profile.show,
}
routes[page](member)
