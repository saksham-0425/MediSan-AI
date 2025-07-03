import sqlite3
from datetime import datetime
import streamlit as st
import os

def init_db():
    os.makedirs("logs", exist_ok=True)
    conn = sqlite3.connect("logs/prediction_history.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_name TEXT,
        age INTEGER,
        gender TEXT,
        image_name TEXT,
        prediction TEXT,
        confidence REAL,
        timestamp TEXT,
        email TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_prediction(patient_name, age, gender, image_name, prediction, confidence):
    conn = sqlite3.connect("logs/prediction_history.db")
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email = st.session_state.user["email"] if "user" in st.session_state else "unknown"
    cursor.execute("""
        INSERT INTO history (patient_name, age, gender, image_name, prediction, confidence, timestamp, email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (patient_name, age, gender, image_name, prediction, confidence, timestamp, email))
    conn.commit()
    conn.close()

def get_all_history():
    conn = sqlite3.connect("logs/prediction_history.db")
    cursor = conn.cursor()

    if "role" in st.session_state and st.session_state.role == "patient":
        email = st.session_state.user["email"]
        cursor.execute("""
            SELECT patient_name, age, gender, image_name, prediction, confidence, timestamp
            FROM history
            WHERE email = ?
            ORDER BY id DESC
        """, (email,))
    else:
        cursor.execute("""
            SELECT patient_name, age, gender, image_name, prediction, confidence, timestamp
            FROM history
            ORDER BY id DESC
        """)

    data = cursor.fetchall()
    conn.close()
    return data
