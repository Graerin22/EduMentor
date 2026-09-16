import sqlite3
import json
from datetime import datetime

class Datetime:
    def __init__(self, db_path='sessions.db'):
        self.db_path = db_path
        self.db()

    def db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                filename TEXT,
                document_text TEXT,
                messages TEXT,
                quiz_data TEXT,
                teachback_data TEXT,
                session_type TEXT DEFAULT 'manual')
        """)

        conn.commit()
        conn.close()

    def save_sessions(self, filename, document_text, messages, quiz_data=None, teachback_data=None, session_type='manual'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions
            (timestamp, filename, document_text, messages, quiz_data, teachback_data, session_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), 
              filename, 
              document_text, 
              json.dumps(messages), 
              json.dumps(quiz_data) if quiz_data else {}, 
              json.dumps(teachback_data) if teachback_data else {}, 
              session_type))

        conn.commit()
        conn.close()

    def get_all_sessions(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, timestamp, filename, session_type
            FROM sessions
            ORDER BY timestamp DESC
        """)

        rows = cursor.fetchall()
        conn.close()
        return rows

    def load_full_sessions(self, session_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT filename, document_text, messages, quiz_data, teachback_data
            FROM sessions WHERE id = ?
        """, (session_id,))

        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'filename': row[0],
                'document_text': row[1],
                'messages': json.loads(row[2]),
                'quiz_data': json.laod(row[3]),
                'teachback_data': json.loads(row[4]) 
            }
        return None

    def get_latest_auto_session(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT filename, document_text, messages
            FROM sessions
            WHERE session_type = 'auto'
            ORDER BY timestamp DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'filename': row[0],
                'document_text': row[1],
                'messages': json.loads(row[2])
            }
        return None