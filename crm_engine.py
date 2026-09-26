import sqlite3
import os
import config
from contextlib import closing
from datetime import datetime

DB_FILE = os.path.join(config.DATA_DIR, "crm_database.db")


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_crm_db():
    """Initializes relational tables for the CRM engine."""
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        
        # Contacts / Leads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                primary_contact TEXT,
                email TEXT,
                phone TEXT,
                status TEXT DEFAULT 'New',
                lead_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Last confirmed CRM form location defaults
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS location_preferences (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                country TEXT,
                state TEXT,
                district TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sales Pipeline / Deals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                deal_name TEXT NOT NULL,
                deal_value REAL DEFAULT 0.0,
                stage TEXT DEFAULT 'Prospect',
                probability INTEGER DEFAULT 20,
                close_date DATE,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
            )
        """)

        # Interaction Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                type TEXT NOT NULL, -- Call, Email, Meeting, Note
                summary TEXT NOT NULL,
                logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
            )
        """)

        # Tasks / Reminders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                title TEXT NOT NULL,
                due_date DATETIME NOT NULL,
                is_completed INTEGER DEFAULT 0,
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE SET NULL
            )
        """)

        # Sales & Marketing library.  Each row is one marketing asset, so a
        # product sector can have any number of YouTube links, Reels, photos,
        # videos, brochures, and other corporate collateral.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promotional_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_sector TEXT NOT NULL,
                title TEXT NOT NULL,
                material_type TEXT NOT NULL,
                campaign_name TEXT,
                platform TEXT,
                url TEXT,
                attachment_path TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def get_location_preferences():
    """Return the last confirmed Country/State/District selection."""
    try:
        with closing(get_db()) as conn:
            row = conn.execute(
                """
                SELECT country, state, district
                FROM location_preferences
                WHERE id = 1
                """
            ).fetchone()
    except sqlite3.OperationalError:
        return {"country": "", "state": "", "district": ""}
    if row is None:
        return {"country": "", "state": "", "district": ""}
    return {
        "country": row["country"] or "",
        "state": row["state"] or "",
        "district": row["district"] or "",
    }


def save_location_preferences(country="", state="", district=""):
    """Persist one last-confirmed location preference row."""
    values = (
        str(country or "").strip(),
        str(state or "").strip(),
        str(district or "").strip(),
    )
    with closing(get_db()) as conn:
        conn.execute(
            """
            INSERT INTO location_preferences
                (id, country, state, district, updated_at)
            VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                country = excluded.country,
                state = excluded.state,
                district = excluded.district,
                updated_at = CURRENT_TIMESTAMP
            """,
            values,
        )
        conn.commit()


# Operations API
def add_contact(company, contact_person, email, phone, status="New"):
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (company_name, primary_contact, email, phone, status) VALUES (?, ?, ?, ?, ?)",
            (company, contact_person, email, phone, status)
        )
        conn.commit()
        return cursor.lastrowid


def log_interaction(contact_id, interaction_type, summary):
    with closing(get_db()) as conn:
        conn.execute(
            "INSERT INTO interactions (contact_id, type, summary) VALUES (?, ?, ?)",
            (contact_id, interaction_type, summary)
        )
        conn.commit()


def fetch_all_contacts():
    with closing(get_db()) as conn:
        return conn.execute("SELECT * FROM contacts ORDER BY created_at DESC").fetchall()


def fetch_pipeline_metrics():
    """Returns aggregated metrics for dashboard views."""
    with closing(get_db()) as conn:
        total_value = conn.execute("SELECT SUM(deal_value) FROM deals").fetchone()[0] or 0.0
        active_leads = conn.execute("SELECT COUNT(*) FROM contacts WHERE status != 'Lost'").fetchone()[0]
        pending_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE is_completed = 0").fetchone()[0]
        return {
            "total_pipeline_value": total_value,
            "active_leads": active_leads,
            "pending_tasks": pending_tasks
        }


def add_promotional_material(product_sector, title, material_type, campaign_name="",
                             platform="", url="", attachment_path="", notes=""):
    """Save one marketing asset in the corporate promotion-material library."""
    with closing(get_db()) as conn:
        cursor = conn.execute(
            """INSERT INTO promotional_materials
               (product_sector, title, material_type, campaign_name, platform, url,
                attachment_path, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (product_sector, title, material_type, campaign_name, platform, url,
             attachment_path, notes),
        )
        conn.commit()
        return cursor.lastrowid


def fetch_promotional_materials(product_sector=None):
    """Return saved marketing assets, optionally limited to a product sector."""
    with closing(get_db()) as conn:
        if product_sector:
            return conn.execute(
                "SELECT * FROM promotional_materials WHERE product_sector = ? "
                "ORDER BY created_at DESC, id DESC", (product_sector,)
            ).fetchall()
        return conn.execute(
            "SELECT * FROM promotional_materials ORDER BY created_at DESC, id DESC"
        ).fetchall()


def delete_promotional_material(material_id):
    with closing(get_db()) as conn:
        conn.execute("DELETE FROM promotional_materials WHERE id = ?", (material_id,))
        conn.commit()
