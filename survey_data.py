"""Survey response import helpers for the Skill Swap app.

The original project expected a separate MySQL import step. This version keeps
the survey importer self-contained and uses the local workspace Excel response
file to seed a SQLite database automatically when the app starts.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "skillswap.db"

SKILL_MAP = {
    "python": "Python",
    "java": "Java",
    "sql": "SQL",
    "ui/ux": "UI/UX",
    "design": "Design",
    "web development": "Web Development (HTML, CSS, JavaScript)",
    "web development ( html": "Web Development (HTML, CSS, JavaScript)",
    "data structures": "Data Structures",
    "backend development": "Backend Development",
    "ml": "ML",
    "ai": "AI",
    "data science": "Data Science",
    "mern stack": "MERN Stack",
    "public speaking": "Public Speaking",
    "photography": "Photography",
    "instrumental music": "Instrumental Music (Guitar, Violin, Piano)",
    "video editing": "Video Editing",
    "language": "Language",
}

SKILL_CATALOG = [
    "AI",
    "Backend Development",
    "Data Science",
    "Data Structures",
    "Design",
    "Instrumental Music (Guitar, Violin, Piano)",
    "Java",
    "Language",
    "MERN Stack",
    "ML",
    "Photography",
    "Public Speaking",
    "Python",
    "SQL",
    "UI/UX",
    "Video Editing",
    "Web Development (HTML, CSS, JavaScript)",
]

TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    usn TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    email TEXT,
    dept TEXT,
    year INTEGER
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_skills (
    user_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    proficiency_level TEXT NOT NULL,
    UNIQUE(user_id, skill_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS want_to_learn (
    user_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    reason TEXT,
    UNIQUE(user_id, skill_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS exchange_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    skill_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(receiver_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def normalise_skill(raw: str) -> str | None:
    cleaned = raw.strip().lower()
    for key, canonical in SKILL_MAP.items():
        if key in cleaned:
            return canonical
    return None


def parse_skills(cell_value) -> list[str]:
    if pd.isna(cell_value):
        return []
    parts = str(cell_value).split(",")
    result: list[str] = []
    for part in parts:
        skill = normalise_skill(part)
        if skill and skill not in result:
            result.append(skill)
    return result


def parse_proficiency(cell_value) -> str:
    val = str(cell_value).strip().lower()
    if "expert" in val:
        return "Expert"
    if "intermediate" in val:
        return "Intermediate"
    return "Beginner"


def generate_email(name: str, _usn: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", name.lower().replace(" ", ""))
    return f"{slug}@bit.edu.in"


def discover_excel_path() -> Path | None:
    candidates = [
        BASE_DIR / "Survey Form (Responses).xlsx",
        BASE_DIR / "Survey_Form__Responses_.xlsx",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    matches = sorted(BASE_DIR.glob("*.xlsx"))
    for match in matches:
        if "response" in match.name.lower() or "survey" in match.name.lower():
            return match
    return None


def _read_responses(excel_path: Path) -> pd.DataFrame:
    df = pd.read_excel(excel_path)
    df.columns = [str(column).strip() for column in df.columns]
    return df


def _find_column(columns: list[str], candidates: list[str]) -> str | None:
    lower_columns = {column.lower(): column for column in columns}
    for candidate in candidates:
        candidate_lower = candidate.lower()
        for lower_name, original_name in lower_columns.items():
            if candidate_lower == lower_name or candidate_lower in lower_name:
                return original_name
    return None


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(TABLES_SQL)
    for skill_name in SKILL_CATALOG:
        conn.execute("INSERT OR IGNORE INTO skills (skill_name) VALUES (?)", (skill_name,))
    conn.commit()


def _import_excel_to_db(conn: sqlite3.Connection, excel_path: Path, *, force_reload: bool = False) -> tuple[int, int]:
    df = _read_responses(excel_path)
    if df.empty:
        return 0, 0

    columns = list(df.columns)
    name_col = _find_column(columns, ["full name", "name"])
    usn_col = _find_column(columns, ["university seat number", "usn"])
    dept_col = _find_column(columns, ["department", "branch"])
    year_col = _find_column(columns, ["current year of study", "year"])
    proficiency_col = _find_column(columns, ["proficiency level in your strongest skill", "proficiency"])
    teach_col = _find_column(columns, ["skills you possess and can teach others", "can teach others"])
    learn_col = _find_column(columns, ["skills you want to learn from a peer", "want to learn"])
    reason_col = _find_column(columns, ["why do you want to learn this skill", "reason"])

    if not name_col or not usn_col:
        raise ValueError(f"Could not detect required survey columns in {excel_path.name}")

    skill_rows = conn.execute("SELECT skill_name, skill_id FROM skills").fetchall()
    skill_cache = {row["skill_name"]: row["skill_id"] for row in skill_rows}

    inserted_users = 0
    skipped_users = 0

    for _, row in df.iterrows():
        name = str(row.get(name_col, "")).strip()
        usn = str(row.get(usn_col, "")).strip()
        dept = str(row.get(dept_col, "")).strip() if dept_col else "Other"
        year_value = row.get(year_col, 1) if year_col else 1
        email = generate_email(name, usn)

        if not name or not usn or usn.lower() == "nan":
            skipped_users += 1
            continue

        try:
            year = int(float(year_value))
        except (TypeError, ValueError):
            year = 1
        year = max(1, min(4, year))

        conn.execute(
            """INSERT INTO users (usn, name, email, dept, year)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(usn) DO UPDATE SET
                   name = excluded.name,
                   email = excluded.email,
                   dept = excluded.dept,
                   year = excluded.year""",
            (usn, name, email, dept, year),
        )

        user_row = conn.execute("SELECT user_id FROM users WHERE usn = ?", (usn,)).fetchone()
        if user_row is None:
            skipped_users += 1
            continue

        user_id = int(user_row["user_id"])
        proficiency = parse_proficiency(row.get(proficiency_col, "")) if proficiency_col else "Beginner"

        teach_skills = parse_skills(row.get(teach_col, "")) if teach_col else []
        learn_skills = parse_skills(row.get(learn_col, "")) if learn_col else []
        reason = str(row.get(reason_col, "")).strip() if reason_col else ""

        if force_reload:
            conn.execute("DELETE FROM user_skills WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM want_to_learn WHERE user_id = ?", (user_id,))

        for skill_name in teach_skills:
            skill_id = skill_cache.get(skill_name)
            if skill_id is not None:
                conn.execute(
                    """INSERT INTO user_skills (user_id, skill_id, proficiency_level)
                       VALUES (?, ?, ?)
                       ON CONFLICT(user_id, skill_id) DO UPDATE SET
                           proficiency_level = excluded.proficiency_level""",
                    (user_id, skill_id, proficiency),
                )

        for skill_name in learn_skills:
            skill_id = skill_cache.get(skill_name)
            if skill_id is not None:
                conn.execute(
                    """INSERT INTO want_to_learn (user_id, skill_id, reason)
                       VALUES (?, ?, ?)
                       ON CONFLICT(user_id, skill_id) DO UPDATE SET
                           reason = excluded.reason""",
                    (user_id, skill_id, reason),
                )

        inserted_users += 1

    conn.commit()
    return inserted_users, skipped_users


def initialize_database(force_reload: bool = False) -> dict[str, object]:
    excel_path = discover_excel_path()
    with get_connection() as conn:
        _seed_schema(conn)

        user_count = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        should_import = force_reload or user_count == 0

        imported_users = 0
        skipped_users = 0
        source_file = None

        if should_import and excel_path is not None:
            imported_users, skipped_users = _import_excel_to_db(
                conn,
                excel_path,
                force_reload=force_reload,
            )
            source_file = excel_path.name

        return {
            "database_path": str(DB_PATH),
            "excel_path": source_file,
            "imported_users": imported_users,
            "skipped_users": skipped_users,
            "user_count": conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"],
            "skill_count": conn.execute("SELECT COUNT(*) AS count FROM skills").fetchone()["count"],
        }


def main():
    info = initialize_database(force_reload=True)
    print("Import complete")
    print(info)


if __name__ == "__main__":
    main()
