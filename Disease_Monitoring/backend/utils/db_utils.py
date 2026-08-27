import json
import sqlite3

DB_PATH = "leaf_monitoring.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fruit_sessions (
            session_id TEXT,
            day INTEGER,
            severity_anthracnose REAL,
            severity_ber REAL,
            severity_swv REAL,
            weather_data TEXT,
            combined_risk_score REAL,
            combined_risk_level TEXT,
            treatment_advice TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, day)
        )
        """
    )
    conn.commit()
    conn.close()


def save_fruit_data(session_id, day, sev_anth, sev_ber, sev_swv, weather, risk_score, risk_level, advice):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO fruit_sessions
        (session_id, day, severity_anthracnose, severity_ber, severity_swv,
         weather_data, combined_risk_score, combined_risk_level, treatment_advice)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            day,
            sev_anth,
            sev_ber,
            sev_swv,
            json.dumps(weather),
            risk_score,
            risk_level,
            json.dumps(advice),
        ),
    )
    conn.commit()
    conn.close()


def get_fruit_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM fruit_sessions WHERE session_id = ? ORDER BY day ASC",
        (session_id,),
    )
    rows = cursor.fetchall()

    history = {}
    for row in rows:
        history[f"day{row['day']}"] = {
            "sev_anth": row["severity_anthracnose"],
            "sev_ber": row["severity_ber"],
            "sev_swv": row["severity_swv"],
            "weather": json.loads(row["weather_data"]),
            "risk_score": row["combined_risk_score"],
            "risk_level": row["combined_risk_level"],
        }
    conn.close()
    return history


def get_all_uploaded_days(session_id, is_fruit=False):
    table = "fruit_sessions" if is_fruit else "fruit_sessions"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT day FROM {table} WHERE session_id = ?", (session_id,))
    days = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sorted(days)


init_db()
