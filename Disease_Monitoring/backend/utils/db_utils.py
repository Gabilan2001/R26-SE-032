import sqlite3
import json
import os

DB_PATH = "leaf_monitoring.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Table to store daily upload results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaf_sessions (
            session_id TEXT,
            day INTEGER,
            severity_a REAL,
            severity_b REAL,
            weather_data TEXT,
            combined_risk_score REAL,
            combined_risk_level TEXT,
            treatment_advice TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (session_id, day)
        )
    ''')
    conn.commit()
    conn.close()

def save_daily_data(session_id, day, sev_a, sev_b, weather, risk_score, risk_level, advice):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO leaf_sessions 
        (session_id, day, severity_a, severity_b, weather_data, combined_risk_score, combined_risk_level, treatment_advice)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, day, sev_a, sev_b, json.dumps(weather), risk_score, risk_level, json.dumps(advice)))
    conn.commit()
    conn.close()

def get_session_history(session_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM leaf_sessions WHERE session_id = ? ORDER BY day ASC', (session_id,))
    rows = cursor.fetchall()
    
    history = {}
    for row in rows:
        history[f"day{row['day']}"] = {
            "sev_a": row['severity_a'],
            "sev_b": row['severity_b'],
            "weather": json.loads(row['weather_data']),
            "risk_score": row['combined_risk_score'],
            "risk_level": row['combined_risk_level']
        }
    conn.close()
    return history

def get_all_uploaded_days(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT day FROM leaf_sessions WHERE session_id = ?', (session_id,))
    days = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sorted(days)

# Initialize on import
init_db()
