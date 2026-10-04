import sqlite3
from datetime import datetime
from config import DATABASE_PATH


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                manager_name TEXT NOT NULL DEFAULT '',
                manager_phone TEXT NOT NULL DEFAULT '',
                salary_manager_name TEXT NOT NULL DEFAULT '',
                salary_manager_phone TEXT NOT NULL DEFAULT '',
                setup_complete INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                inn TEXT NOT NULL,
                company_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def ensure_user(telegram_id: int):
    now = datetime.now().isoformat(timespec="seconds")
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (telegram_id, updated_at)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO NOTHING
            """,
            (telegram_id, now),
        )
        conn.commit()


def get_user(telegram_id: int):
    ensure_user(telegram_id)
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
    return dict(row) if row else None


def update_user(telegram_id: int, **fields):
    if not fields:
        return
    allowed = {
        "manager_name",
        "manager_phone",
        "salary_manager_name",
        "salary_manager_phone",
        "setup_complete",
    }
    payload = {k: v for k, v in fields.items() if k in allowed}
    if not payload:
        return
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
    set_sql = ", ".join(f"{k} = ?" for k in payload)
    values = list(payload.values()) + [telegram_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE users SET {set_sql} WHERE telegram_id = ?", values)
        conn.commit()


def add_organization(telegram_id: int, inn: str, company_name: str):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO organizations (telegram_id, inn, company_name, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                telegram_id,
                inn.strip(),
                company_name.strip(),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
