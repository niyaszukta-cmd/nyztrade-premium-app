"""
Auto-Expiry & Renewal Reminder Scheduler
─────────────────────────────────────────
Run this as a background job — daily at 9 AM IST recommended.

Option 1 (simple): Run manually each day
  python scheduler.py

Option 2 (automated): Add to crontab
  0 9 * * * cd /path/to/nyztrade_v2 && python scheduler.py >> logs/scheduler.log 2>&1

Option 3 (Railway/Render): Add as a separate worker service
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from shared.db import get_conn
from shared.telegram_bot import send_renewal_reminder, send_admin_alert
from datetime import date, datetime

LOG_FILE = "logs/scheduler.log"

def log(msg: str):
    ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run_daily_jobs():
    log("=" * 50)
    log("Running daily Nyztrade scheduler...")
    conn = get_conn()
    today = date.today()

    # ── 1. Auto-expire members ────────────────
    expired = conn.execute("""
        SELECT id, name, username FROM clients
        WHERE status='Active' AND expiry_date < ? AND expiry_date IS NOT NULL
    """, (str(today),)).fetchall()

    for m in expired:
        conn.execute("UPDATE clients SET status='Inactive' WHERE id=?", (m['id'],))
        log(f"EXPIRED: {m['name']} (@{m['username']})")
        send_admin_alert(f"Member expired: <b>{m['name']}</b> (@{m['username']})")

    if expired:
        conn.commit()
        log(f"Auto-expired {len(expired)} member(s).")

    # ── 2. Send renewal reminders ─────────────
    reminder_days = [7, 3, 1]  # send reminders at these day thresholds

    for days in reminder_days:
        target_date = str(today + __import__('datetime').timedelta(days=days))
        members = conn.execute("""
            SELECT * FROM clients
            WHERE status='Active'
            AND expiry_date=?
            AND telegram_id IS NOT NULL
            AND telegram_id != ''
        """, (target_date,)).fetchall()

        for m in members:
            ok, msg = send_renewal_reminder(
                telegram_id=m['telegram_id'],
                name=m['name'],
                days_left=days,
                plan=m['plan'],
                expiry_date=m['expiry_date']
            )
            status = "✅" if ok else f"❌ {msg}"
            log(f"Reminder ({days}d) → {m['name']}: {status}")

    # ── 3. Daily admin summary ────────────────
    active_count  = conn.execute("SELECT COUNT(*) FROM clients WHERE status='Active'").fetchone()[0]
    expiring_7    = conn.execute("""
        SELECT COUNT(*) FROM clients WHERE status='Active'
        AND expiry_date BETWEEN ? AND ?
    """, (str(today), str(today + __import__('datetime').timedelta(days=7)))).fetchone()[0]
    open_eq  = conn.execute("SELECT COUNT(*) FROM equity_calls WHERE status='Open'").fetchone()[0]
    open_op  = conn.execute("SELECT COUNT(*) FROM options_calls WHERE status='Open'").fetchone()[0]

    summary = (
        f"📊 <b>Daily Summary — {today}</b>\n\n"
        f"👥 Active members: <b>{active_count}</b>\n"
        f"⚠️ Expiring in 7 days: <b>{expiring_7}</b>\n"
        f"📊 Open equity calls: <b>{open_eq}</b>\n"
        f"⚡ Open options calls: <b>{open_op}</b>\n"
        f"🔴 Auto-expired today: <b>{len(expired)}</b>"
    )
    send_admin_alert(summary)
    log("Daily summary sent to admin.")
    conn.close()
    log("Scheduler complete.")
    log("=" * 50)

if __name__ == "__main__":
    run_daily_jobs()
