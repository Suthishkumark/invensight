"""
InvenSight Authentication Module
─────────────────────────────────
Handles: user registration, login, session tracking,
         activity logging, and admin user management.
Database: SQLite (auth/users.db) — auto-created on first run.
"""
import sqlite3
import bcrypt
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, List

# ─── DB Path ─────────────────────────────────────────────────────────────────
_AUTH_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(_AUTH_DIR, "users.db")

# ─── Default Admin Credentials ────────────────────────────────────────────────
ADMIN_EMAIL    = "suthishkumark18@gmail.com"
ADMIN_PASSWORD = "Suthishk@18"
ADMIN_NAME     = "Suthish Kumar"


# ─── DB Initialisation ───────────────────────────────────────────────────────
def init_db() -> None:
    """Create tables and seed admin account if they don't exist."""
    con = _conn()
    cur = con.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'user',
            created_at    TEXT    NOT NULL,
            last_login    TEXT,
            is_active     INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL REFERENCES users(id),
            page       TEXT    NOT NULL,
            action     TEXT,
            session_id TEXT,
            timestamp  TEXT    NOT NULL
        );
    """)
    con.commit()

    # Seed admin if not present
    row = cur.execute("SELECT id FROM users WHERE email = ?", (ADMIN_EMAIL,)).fetchone()
    if row is None:
        _insert_user(cur, ADMIN_NAME, ADMIN_EMAIL, ADMIN_PASSWORD, role="admin")
        con.commit()

    con.close()


# ─── Internal Helpers ─────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def _insert_user(cur, name: str, email: str, password: str, role: str = "user") -> None:
    cur.execute(
        "INSERT INTO users (name, email, password_hash, role, created_at) VALUES (?,?,?,?,?)",
        (name.strip(), email.strip().lower(), _hash(password), role,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── Public API ───────────────────────────────────────────────────────────────

def register_user(name: str, email: str, password: str) -> Dict:
    """
    Register a new user.
    Returns: {"ok": True, "user": {...}} or {"ok": False, "error": "..."}
    """
    if not name.strip():
        return {"ok": False, "error": "Name cannot be empty."}
    if not email.strip() or "@" not in email:
        return {"ok": False, "error": "Enter a valid email address."}
    if len(password) < 6:
        return {"ok": False, "error": "Password must be at least 6 characters."}

    con = _conn()
    cur = con.cursor()
    try:
        existing = cur.execute("SELECT id FROM users WHERE email = ?",
                               (email.strip().lower(),)).fetchone()
        if existing:
            return {"ok": False, "error": "This email is already registered. Please login."}
        _insert_user(cur, name, email, password)
        con.commit()
        user = cur.execute("SELECT * FROM users WHERE email = ?",
                           (email.strip().lower(),)).fetchone()
        return {"ok": True, "user": dict(user)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        con.close()


def login_user(email: str, password: str) -> Dict:
    """
    Authenticate a user.
    Returns: {"ok": True, "user": {...}} or {"ok": False, "error": "..."}
    """
    con = _conn()
    cur = con.cursor()
    try:
        user = cur.execute("SELECT * FROM users WHERE email = ?",
                           (email.strip().lower(),)).fetchone()
        if user is None:
            return {"ok": False, "error": "No account found with this email. Please register."}
        if not user["is_active"]:
            return {"ok": False, "error": "Your account has been disabled. Contact admin."}
        if not _verify(password, user["password_hash"]):
            return {"ok": False, "error": "Incorrect password. Please try again."}

        # Update last_login
        cur.execute("UPDATE users SET last_login = ? WHERE id = ?",
                    (_now(), user["id"]))
        con.commit()
        return {"ok": True, "user": dict(user)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        con.close()


def log_activity(user_id: int, page: str, action: str = "", session_id: str = "") -> None:
    """Log a user's page visit or action."""
    try:
        con = _conn()
        con.execute(
            "INSERT INTO activity_log (user_id, page, action, session_id, timestamp) VALUES (?,?,?,?,?)",
            (user_id, page, action, session_id, _now())
        )
        con.commit()
        con.close()
    except Exception:
        pass  # Never crash the main app on logging failure


# ─── Admin APIs ───────────────────────────────────────────────────────────────

def get_all_users() -> List[Dict]:
    """Return all users (excluding password hash)."""
    con = _conn()
    rows = con.execute(
        "SELECT id, name, email, role, created_at, last_login, is_active FROM users ORDER BY created_at DESC"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_activity_log(limit: int = 500) -> List[Dict]:
    """Return recent activity log joined with user names."""
    con = _conn()
    rows = con.execute("""
        SELECT a.id, u.name, u.email, a.page, a.action, a.session_id, a.timestamp
        FROM activity_log a
        JOIN users u ON u.id = a.user_id
        ORDER BY a.timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_user_activity(user_id: int) -> List[Dict]:
    """Return activity log for a specific user."""
    con = _conn()
    rows = con.execute(
        "SELECT page, action, timestamp FROM activity_log WHERE user_id = ? ORDER BY timestamp DESC",
        (user_id,)
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def toggle_user_active(user_id: int) -> None:
    """Enable / disable a user account (admin action)."""
    con = _conn()
    con.execute(
        "UPDATE users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id = ?",
        (user_id,)
    )
    con.commit()
    con.close()


def get_usage_summary() -> Dict:
    """Return summary stats for admin dashboard."""
    con = _conn()
    total_users    = con.execute("SELECT COUNT(*) FROM users WHERE role='user'").fetchone()[0]
    active_users   = con.execute("SELECT COUNT(*) FROM users WHERE role='user' AND is_active=1").fetchone()[0]
    total_sessions = con.execute("SELECT COUNT(DISTINCT session_id) FROM activity_log").fetchone()[0]
    total_actions  = con.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
    page_stats     = con.execute(
        "SELECT page, COUNT(*) as visits FROM activity_log GROUP BY page ORDER BY visits DESC"
    ).fetchall()
    con.close()
    return {
        "total_users":    total_users,
        "active_users":   active_users,
        "total_sessions": total_sessions,
        "total_actions":  total_actions,
        "page_stats":     [dict(r) for r in page_stats],
    }


def change_password(user_id: int, old_password: str, new_password: str) -> Dict:
    """Change a user's password."""
    if len(new_password) < 6:
        return {"ok": False, "error": "New password must be at least 6 characters."}
    con = _conn()
    cur = con.cursor()
    try:
        user = cur.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or not _verify(old_password, user["password_hash"]):
            return {"ok": False, "error": "Current password is incorrect."}
        cur.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                    (_hash(new_password), user_id))
        con.commit()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        con.close()


def new_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())


