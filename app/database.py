# An sqlite db for storing any expenses I made.

import sqlite3
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# database file will live in this location within docker container
# DB_PATH = Path("/data/expenses.db")
DB_PATH = Path(os.environ.get("DB_PATH","./expenses.db"))

def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        transcript TEXT NOT NULL,
        amount REAL NOT NULL,
        store TEXT,
        category TEXT,
        notes TEXT,
        raw_response TEXT )
        """
    )
    conn.commit()
    return conn

def get_all_expenses(limit: int=50, offset: int=0) -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM expenses ORDER BY created_at DESC LIMIT ? OFFSET ?",
                        (limit, offset)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_expense(expense_id: int ) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?",(expense_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_summary(days: int=30) -> dict:
    conn = get_db()
    cutoff = datetime.now(timezone.utc).isoformat()[:10]
    rows = conn.execute(
        """SELECT category, SUM(amount) as total_spent, COUNT(*) as count
        FROM expenses
        WHERE created_at >= date(?, '-' || ? || ' days') 
        GROUP BY category
        ORDER BY total_spent DESC
""",(cutoff, days)
    ).fetchall()
    conn.close()
    return {
        "by category": [dict(row) for row in rows],
        "total": sum(row["total_spent"] for row in rows)

    }
    
def save_expense(transcript: str,amount: float,
        store: str | None = None, category: str | None = None,
        notes: str | None = None, raw_response: str | None = None ) -> int:
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO expenses (created_at, transcript, amount, store, category, notes, raw_response)
        VALUES(?,?,?,?,?,?,?)""",
        (datetime.now(timezone.utc).isoformat(), transcript, amount, store,
        category, notes, raw_response,
        )
    )
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id

def delete_expense(expense_id: int) -> bool:
    conn = get_db()
    cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


    