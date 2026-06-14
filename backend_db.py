"""SQLite-backed database logic for the Skill Swap Streamlit app."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from survey_data import DB_PATH, initialize_database


def _ensure_database_ready() -> None:
    initialize_database()


def _rows(cursor: sqlite3.Cursor) -> list[dict]:
    return [dict(row) for row in cursor.fetchall()]


def get_connection() -> sqlite3.Connection:
    _ensure_database_ready()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def add_user(name: str, usn: str, email: str, dept: str, year: int) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, usn, email, dept, year) VALUES (?, ?, ?, ?, ?)",
        (name, usn, email, dept, year),
    )
    conn.commit()
    user_id = int(cur.lastrowid)
    cur.close()
    conn.close()
    return user_id


def get_user_by_usn(usn: str) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE usn = ?", (usn,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def get_all_users() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY name")
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def update_user(user_id: int, name: str, email: str, dept: str, year: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET name = ?, email = ?, dept = ?, year = ? WHERE user_id = ?",
        (name, email, dept, year, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_all_skills() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM skills ORDER BY skill_name")
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def add_skill(skill_name: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO skills (skill_name) VALUES (?)", (skill_name,))
    conn.commit()
    cur.execute("SELECT skill_id FROM skills WHERE skill_name = ?", (skill_name,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return int(row[0]) if row else 0


def assign_skill_to_user(user_id: int, skill_id: int, proficiency: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO user_skills (user_id, skill_id, proficiency_level)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id, skill_id) DO UPDATE SET
               proficiency_level = excluded.proficiency_level""",
        (user_id, skill_id, proficiency),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_skills_by_user(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT s.skill_id, s.skill_name, us.proficiency_level
           FROM user_skills us JOIN skills s ON us.skill_id = s.skill_id
           WHERE us.user_id = ? ORDER BY s.skill_name""",
        (user_id,),
    )
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def search_teachers_by_skill(skill_name: str) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT u.name, u.usn, u.dept, u.year,
                  s.skill_name, us.proficiency_level
           FROM users u
           JOIN user_skills us ON u.user_id = us.user_id
           JOIN skills s ON us.skill_id = s.skill_id
           WHERE lower(s.skill_name) LIKE lower(?)
           ORDER BY CASE us.proficiency_level
                    WHEN 'Expert' THEN 3
                    WHEN 'Intermediate' THEN 2
                    ELSE 1 END DESC,
                    u.name""",
        (f"%{skill_name}%",),
    )
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def add_want_to_learn(user_id: int, skill_id: int, reason: str = ""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO want_to_learn (user_id, skill_id, reason)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id, skill_id) DO UPDATE SET
               reason = excluded.reason""",
        (user_id, skill_id, reason),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_wants_by_user(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT s.skill_id, s.skill_name, w.reason
           FROM want_to_learn w JOIN skills s ON w.skill_id = s.skill_id
           WHERE w.user_id = ? ORDER BY s.skill_name""",
        (user_id,),
    )
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def send_request(sender_id: int, receiver_id: int, skill_id: int) -> int:
    if sender_id == receiver_id:
        raise ValueError("You cannot send a request to yourself.")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO exchange_requests (sender_id, receiver_id, skill_id) VALUES (?, ?, ?)",
        (sender_id, receiver_id, skill_id),
    )
    conn.commit()
    request_id = int(cur.lastrowid)
    cur.close()
    conn.close()
    return request_id


def get_total_request_count() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM exchange_requests")
    count = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return count


def update_request_status(request_id: int, status: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE exchange_requests SET status = ? WHERE request_id = ?",
        (status, request_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_requests_for_user(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT er.request_id, s.name AS sender_name, s.usn AS sender_usn,
                  sk.skill_name, er.status, er.created_at
           FROM exchange_requests er
           JOIN users s ON er.sender_id = s.user_id
           JOIN skills sk ON er.skill_id = sk.skill_id
           WHERE er.receiver_id = ?
           ORDER BY er.created_at DESC""",
        (user_id,),
    )
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def get_requests_sent_by_user(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT er.request_id, r.name AS receiver_name, r.usn AS receiver_usn,
                  sk.skill_name, er.status, er.created_at
           FROM exchange_requests er
           JOIN users r ON er.receiver_id = r.user_id
           JOIN skills sk ON er.skill_id = sk.skill_id
           WHERE er.sender_id = ?
           ORDER BY er.created_at DESC""",
        (user_id,),
    )
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def find_swap_matches(user_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT DISTINCT
               u.user_id,
               u.name AS partner_name,
               u.usn AS partner_usn,
               u.dept AS partner_dept,
               s_teach.skill_name AS they_teach,
               s_learn.skill_name AS you_teach
           FROM users u
           JOIN user_skills us_t ON u.user_id = us_t.user_id
           JOIN want_to_learn wtl ON wtl.user_id = ? AND wtl.skill_id = us_t.skill_id
           JOIN skills s_teach ON s_teach.skill_id = us_t.skill_id
           JOIN want_to_learn wtl2 ON wtl2.user_id = u.user_id
           JOIN user_skills us_l ON us_l.user_id = ? AND us_l.skill_id = wtl2.skill_id
           JOIN skills s_learn ON s_learn.skill_id = us_l.skill_id
                     WHERE u.user_id <> ?
                         AND s_teach.skill_name <> s_learn.skill_name""",
        (user_id, user_id, user_id),
    )
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def skill_demand_stats() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT s.skill_name, COUNT(*) AS demand_count
           FROM want_to_learn w JOIN skills s ON w.skill_id = s.skill_id
           GROUP BY s.skill_name ORDER BY demand_count DESC"""
    )
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def skill_supply_stats() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT s.skill_name, COUNT(*) AS supply_count
           FROM user_skills us JOIN skills s ON us.skill_id = s.skill_id
           GROUP BY s.skill_name ORDER BY supply_count DESC"""
    )
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def dept_distribution() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT dept, COUNT(*) AS count FROM users GROUP BY dept ORDER BY count DESC")
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows


def request_status_stats() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) AS count FROM exchange_requests GROUP BY status")
    rows = _rows(cur)
    cur.close()
    conn.close()
    return rows
