import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH", "./skillbridge.db")

def get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','industry','academician','institution')),
            department TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 1,
            evidence TEXT DEFAULT '',
            evidence_type TEXT DEFAULT 'Self-reported',
            verified INTEGER DEFAULT 0,
            UNIQUE(user_id, name)
        );
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            kind TEXT NOT NULL,
            description TEXT DEFAULT '',
            required_skills TEXT NOT NULL,
            location TEXT DEFAULT 'Remote',
            eligibility TEXT DEFAULT 'Open to students',
            posted_by INTEGER REFERENCES users(id),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            opportunity_id INTEGER NOT NULL REFERENCES opportunities(id),
            status TEXT DEFAULT 'Applied',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, opportunity_id)
        );
        CREATE TABLE IF NOT EXISTS learning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            skill TEXT NOT NULL,
            provider TEXT DEFAULT 'SkillBridge Learning',
            url TEXT DEFAULT '#'
        );
        """)
        db.commit()
