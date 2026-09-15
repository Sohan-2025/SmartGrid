import streamlit as st
import sqlite3
import pandas as pd

# Page config
st.set_page_config(page_title="SmartGrid Agent Logs", layout="wide")
st.title("SmartGrid: Agent Action Logs")

# Connect to SQLite DB
DB_NAME = "grid_agent.db"

def load_data():
    try:
        conn = sqlite3.connect(DB_NAME)
        # Fetch all records, newest first
        df = pd.read_sql_query("SELECT * FROM agent_actions ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Could not load database: {e}")
        return pd.DataFrame()

# Refresh button
if st.button("🔄 Refresh Data"):
    st.rerun()

# Load and display data
df = load_data()

if df.empty:
    st.info("No agent actions recorded yet. Run the simulation to generate data.")
else:
    # Highlight false trips in red for the demo
    def highlight_false_trips(row):
        if row['is_false_trip']:
            return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        df.style.apply(highlight_false_trips, axis=1),
        use_container_width=True,
        hide_index=True
    )