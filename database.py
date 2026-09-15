import sqlite3
import datetime

DB_NAME = "grid_agent.db"

def init_db():
    """Creates the table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            run_type TEXT,
            node_id TEXT,
            intended_action TEXT,
            is_false_trip BOOLEAN,
            groundedness TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_trace(run_type: str, node_id: str, intended_action: str, is_false_trip: bool, groundedness: str):
    """Saves a single AI decision to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO agent_actions (timestamp, run_type, node_id, intended_action, is_false_trip, groundedness)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime.datetime.now().isoformat(), run_type, node_id, intended_action, is_false_trip, groundedness))
    conn.commit()
    conn.close()

def fetch_runs(run_type: str) -> list:
    """Retrieves all runs of a specific type for the scorecard."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT is_false_trip, groundedness FROM agent_actions WHERE run_type = ?', (run_type,))
    rows = cursor.fetchall()
    conn.close()
    
    # Format into dictionaries so your existing calculate_metrics logic still works
    return [{"is_false_trip": bool(row[0]), "groundedness": row[1]} for row in rows]