"""
Speed Radar Hub - Database Module
SQLite database for storing radar configurations and readings
"""

import os
import sqlite3
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DATABASE_PATH = os.environ.get("DATABASE_PATH", "/config/speed_radar_hub.db")


def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_cursor():
    """Context manager for database operations."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()


def init_database():
    """Initialize the database schema."""
    with db_cursor() as cursor:
        # Radars table - stores registered radar devices
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS radars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                config TEXT DEFAULT '{}',
                notes TEXT
            )
        """)

        # Readings table - stores speed readings from radars
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                radar_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                speed REAL NOT NULL,
                direction TEXT,
                is_speeder BOOLEAN DEFAULT 0,
                FOREIGN KEY (radar_id) REFERENCES radars (id)
            )
        """)

        # Stats table - stores periodic statistics snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                radar_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                vehicle_count INTEGER DEFAULT 0,
                approaching_count INTEGER DEFAULT 0,
                leaving_count INTEGER DEFAULT 0,
                average_speed REAL DEFAULT 0,
                max_speed REAL DEFAULT 0,
                speeder_count INTEGER DEFAULT 0,
                violation_percentage REAL DEFAULT 0,
                percentile_85 REAL DEFAULT 0,
                peak_hour INTEGER DEFAULT 0,
                peak_hour_count INTEGER DEFAULT 0,
                FOREIGN KEY (radar_id) REFERENCES radars (id)
            )
        """)

        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_radar_time ON readings (radar_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stats_radar_time ON stats (radar_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_radars_api_key ON radars (api_key)")


def generate_api_key() -> str:
    """Generate a secure API key for a radar."""
    return secrets.token_urlsafe(24)  # 32 characters


# ============================================================
# Radar Management
# ============================================================

def create_radar(name: str, location: str = "", notes: str = "") -> Dict[str, Any]:
    """Create a new radar and return its details including API key."""
    api_key = generate_api_key()

    with db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO radars (api_key, name, location, notes, config)
            VALUES (?, ?, ?, ?, ?)
        """, (api_key, name, location, notes, json.dumps({
            "speed_limit": 50,
            "min_threshold": 15,
            "direction_filter": "both"
        })))

        radar_id = cursor.lastrowid

    return {
        "id": radar_id,
        "api_key": api_key,
        "name": name,
        "location": location,
        "notes": notes
    }


def get_radar_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Get radar details by API key."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM radars WHERE api_key = ? AND is_active = 1", (api_key,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_radar_by_id(radar_id: int) -> Optional[Dict[str, Any]]:
    """Get radar details by ID."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM radars WHERE id = ?", (radar_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_all_radars() -> List[Dict[str, Any]]:
    """Get all registered radars."""
    with db_cursor() as cursor:
        cursor.execute("SELECT * FROM radars WHERE is_active = 1 ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def update_radar(radar_id: int, **kwargs) -> bool:
    """Update radar properties."""
    allowed_fields = ["name", "location", "notes", "config", "is_active"]
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not updates:
        return False

    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [radar_id]

    with db_cursor() as cursor:
        cursor.execute(f"UPDATE radars SET {set_clause} WHERE id = ?", values)
        return cursor.rowcount > 0


def update_radar_last_seen(radar_id: int):
    """Update the last_seen timestamp for a radar."""
    with db_cursor() as cursor:
        cursor.execute("UPDATE radars SET last_seen = CURRENT_TIMESTAMP WHERE id = ?", (radar_id,))


def delete_radar(radar_id: int) -> bool:
    """Soft delete a radar (mark as inactive)."""
    return update_radar(radar_id, is_active=False)


def regenerate_api_key(radar_id: int) -> Optional[str]:
    """Generate a new API key for a radar."""
    new_key = generate_api_key()
    with db_cursor() as cursor:
        cursor.execute("UPDATE radars SET api_key = ? WHERE id = ?", (new_key, radar_id))
        if cursor.rowcount > 0:
            return new_key
    return None


def get_radar_config(radar_id: int) -> Dict[str, Any]:
    """Get configuration for a radar."""
    radar = get_radar_by_id(radar_id)
    if radar and radar.get("config"):
        return json.loads(radar["config"])
    return {
        "speed_limit": 50,
        "min_threshold": 15,
        "direction_filter": "both"
    }


def set_radar_config(radar_id: int, config: Dict[str, Any]) -> bool:
    """Set configuration for a radar."""
    return update_radar(radar_id, config=json.dumps(config))


# ============================================================
# Readings and Statistics
# ============================================================

def record_reading(radar_id: int, speed: float, direction: str, is_speeder: bool = False):
    """Record a single speed reading."""
    with db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO readings (radar_id, speed, direction, is_speeder)
            VALUES (?, ?, ?, ?)
        """, (radar_id, speed, direction, is_speeder))


def record_stats(radar_id: int, stats: Dict[str, Any]):
    """Record a statistics snapshot."""
    with db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO stats (
                radar_id, vehicle_count, approaching_count, leaving_count,
                average_speed, max_speed, speeder_count, violation_percentage,
                percentile_85, peak_hour, peak_hour_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            radar_id,
            stats.get("vehicle_count", 0),
            stats.get("approaching_count", 0),
            stats.get("leaving_count", 0),
            stats.get("average_speed", 0),
            stats.get("max_speed", 0),
            stats.get("speeder_count", 0),
            stats.get("violation_percentage", 0),
            stats.get("percentile_85", 0),
            stats.get("peak_hour", 0),
            stats.get("peak_hour_count", 0)
        ))


def get_recent_readings(radar_id: int, hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent readings for a radar."""
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM readings
            WHERE radar_id = ? AND timestamp > datetime('now', ?)
            ORDER BY timestamp DESC
        """, (radar_id, f"-{hours} hours"))
        return [dict(row) for row in cursor.fetchall()]


def get_latest_stats(radar_id: int) -> Optional[Dict[str, Any]]:
    """Get the most recent stats for a radar."""
    with db_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM stats
            WHERE radar_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (radar_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_daily_summary(radar_id: int, date: str = None) -> Dict[str, Any]:
    """Get daily summary for a radar."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    with db_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_readings,
                AVG(speed) as avg_speed,
                MAX(speed) as max_speed,
                SUM(CASE WHEN is_speeder THEN 1 ELSE 0 END) as speeder_count,
                SUM(CASE WHEN direction = 'Approaching' THEN 1 ELSE 0 END) as approaching,
                SUM(CASE WHEN direction = 'Leaving' THEN 1 ELSE 0 END) as leaving
            FROM readings
            WHERE radar_id = ? AND DATE(timestamp) = ?
        """, (radar_id, date))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return {}


def cleanup_old_data(retention_days: int = 30):
    """Delete data older than retention period."""
    with db_cursor() as cursor:
        cursor.execute("""
            DELETE FROM readings
            WHERE timestamp < datetime('now', ?)
        """, (f"-{retention_days} days",))

        cursor.execute("""
            DELETE FROM stats
            WHERE timestamp < datetime('now', ?)
        """, (f"-{retention_days} days",))


# Initialize database on module load
init_database()
