import sqlite3
import hashlib
import secrets
import base64
import json
from datetime import datetime
from cryptography.fernet import Fernet
from models.user import User
from models.session import Session, ChatData, QuizData, TeachbackData
from utils.config import set_api_key, set_model

class Database:
    def __init__(self, db_path='sessions.db'):
        self.db_path = db_path
        self.db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def db(self) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                encrypted_api_key TEXT,
                created_at TEXT,
                last_login TEXT
                )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TEXT,
                session_name TEXT UNIQUE NOT NULL,
                is_current INT CHECK(is_current IN(0, 1)) DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_data (
                chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TEXT,
                chat_name TEXT UNIQUE NOT NULL,
                filename TEXT,
                document_text TEXT,
                chats TEXT,
                FOREIGN KEY (session_id) REFERENCES session(session_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_data (
                quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TEXT,
                quiz_name TEXT UNIQUE NOT NULL,
                quiz_score INTEGER,
                quiz TEXT,
                quiz_result TEXT,
                feedbacks TEXT,
                FOREIGN KEY (session_id) REFERENCES session(session_id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachback_data (
                teachback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TEXT,
                teachback_name TEXT UNIQUE NOT NULL,
                topic TEXT,
                explanation TEXT,
                teachback TEXT,
                FOREIGN KEY (session_id) REFERENCES session(session_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    def save_chat_session(self, user_id, timestamp, chat_obj: ChatData) -> Session:
        conn = self.get_connection()
        cursor = conn.cursor()

        session_name = f'session_{timestamp.strftime('%Y-%m-%d_%H%M%S')}'
        cursor.execute("""
            INSERT INTO session
            (user_id, timestamp, session_name)
            VALUES (?, ?, ?)
        """, (user_id, 
              timestamp.isoformat(),
              session_name
              )
        )
        new_session_id = cursor.lastrowid

        chat_name = f'chat_{chat_obj.filename}-{timestamp.strftime('%Y-%m-%d_%H%M%S')}'
        cursor.execute("""
            INSERT INTO chat_data
            (session_id, timestamp, chat_name, filename, document_text, chats)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (new_session_id,
              timestamp.isoformat(),
              chat_name,
              chat_obj.filename,
              chat_obj.document_text,
              json.dumps(chat_obj.chats))
        )
        new_chat_id = cursor.lastrowid

        conn.commit()
        conn.close()

        chat_obj.chat_id = new_chat_id
        chat_obj.session_id = new_session_id
        chat_obj.chat_name = chat_name
        
        return Session(session_id=new_session_id, user_id=user_id, 
                       timestamp=timestamp, session_name=session_name,
                       chat_data=chat_obj)

    def update_chat_session(self, timestamp, session_obj: Session, chat_obj: ChatData) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE chat_data
                SET timestamp = ?, chats = ?
                WHERE session_id = ? AND chat_id = ?
            """, (timestamp.isoformat(),
                  json.dumps(chat_obj.chats),
                  session_obj.session_id,
                  chat_obj.chat_id)
            )
            cursor.execute("""
                UPDATE session
                SET timestamp = ?
                WHERE session_id = ?
            """, (timestamp.isoformat(),
                  session_obj.session_id)
            )

            conn.commit()
            chat_obj.timestamp = timestamp
            session_obj.timestamp = timestamp
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def save_quiz_session(self, timestamp, session_obj: Session, quiz_obj: QuizData) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        new_quiz_name = f'quiz_{timestamp.strftime('%Y-%m-%d_%H%M%S')}'
        cursor.execute("""
            INSERT INTO quiz_data
            (session_id, timestamp, quiz_name, quiz_score,
             quiz, quiz_result, feedbacks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_obj.session_id,
              timestamp.isoformat(),
              new_quiz_name,
              quiz_obj.quiz_score,
              json.dumps(quiz_obj.quiz),
              json.dumps(quiz_obj.quiz_result),
              json.dumps(quiz_obj.feedbacks)))
        new_quiz_id = cursor.lastrowid

        conn.commit()
        conn.close()

        quiz_obj.quiz_id = new_quiz_id
        quiz_obj.session_id = session_obj.session_id
        quiz_obj.quiz_name = new_quiz_name

        session_obj.quiz_datas.append(quiz_obj)

    def update_quiz_session(self, timestamp, session_obj: Session, quiz_obj: QuizData) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE quiz_data
                SET timestamp = ?, quiz_score = ?, quiz = ?,
                    quiz_result = ?, feedbacks = ?
                WHERE session_id = ? and quiz_id = ?
            """, (timestamp.isoformat(), 
                  json.dumps(quiz_obj.quiz_score),
                  json.dumps(quiz_obj.quiz),
                  json.dumps(quiz_obj.quiz_result),
                  json.dumps(quiz_obj.feedbacks),
                  session_obj.session_id,
                  quiz_obj.quiz_id)
            )
            cursor.execute("UPDATE session SET timestamp = ? WHERE user_id = ?",
                           (timestamp, session_obj.session_id))

            conn.commit()
            quiz_obj.timestamp = timestamp
            session_obj.timestamp = timestamp
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def save_teachback_session(self, timestamp, session_obj: Session, teachback_obj: TeachbackData) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        new_teachback_name = f'teachback_{timestamp.strftime('%Y-%m-%d_%H%M%S')}'
        cursor.execute("""
            INSERT INTO teachback_data
            (session_id, timestamp, teachback_name, 
             topic, explanation, teachback)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_obj.session_id,
              timestamp.isoformat(),
              new_teachback_name,
              teachback_obj.topic,
              teachback_obj.explanation,
              json.dumps(teachback_obj.teachback)))
        new_teachback_id = cursor.lastrowid

        conn.commit()
        conn.close()

        teachback_obj.quiz_id = new_teachback_id
        teachback_obj.session_id = session_obj.session_id
        teachback_obj.quiz_name = new_teachback_name

        session_obj.quiz_datas.append(teachback_obj)

    def update_teachback_session(self, timestamp, session_obj: Session, teachback_obj: TeachbackData) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE teachback_data
                SET timestamp = ?, topic = ?,
                    explanation = ?, teachback = ?
                WHERE session_id = ? and teachback_id = ?
            """, (timestamp.isoformat(), 
                  json.dumps(teachback_obj.topic),
                  json.dumps(teachback_obj.explanation),
                  json.dumps(teachback_obj.teachback),
                  session_obj.session_id,
                  teachback_obj.teachback_id)
            )
            cursor.execute("UPDATE session SET timestamp = ? WHERE user_id = ?",
                           (timestamp, session_obj.session_id))
            
            conn.commit()
            teachback_obj.timestamp = timestamp
            session_obj.timestamp = timestamp
            
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def set_current_session(self, session: Session) -> None:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("UPDATE session SET is_current = ? WHERE user_id = ? AND is_current = ?",
                       (0, session.user_id, 1))
        cursor.execute("UPDATE session SET is_current = ? WHERE user_id = ? AND session_id = ?",
                       (1, session.user_id, session.session_id))

        conn.commit()
        conn.close()

    def get_all_sessions(self, user_id) -> list[Session]:
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.session_id, s.user_id, s.timestamp, s.session_name, s.is_current,
                c.chat_id, c.chat_name, c.filename, c.document_text, c.chats
                FROM session AS s
                JOIN chat_data AS c ON s.session_id = c.session_id
                WHERE s.user_id = ?
                ORDER BY s.timestamp DESC
        """, (user_id,))

        sessions = []
        rows = cursor.fetchall()
        for row in rows:
            s_id, u_id, t_stamp, s_name, is_curr, c_id, c_name, f_name, d_text, msgs = row

            chat_data = ChatData(chat_id=c_id, session_id=s_id, 
                                 timestamp=t_stamp, chat_name=c_name, 
                                 filename=f_name, document_text=d_text,
                                 chats=json.loads(msgs))
            session_obj = Session(session_id=s_id, user_id=u_id,
                              timestamp=t_stamp, session_name=s_name, 
                              chat_data=chat_data, is_current=bool(is_curr))

            cursor.execute("""
                SELECT quiz_id, timestamp, quiz_name, 
                        quiz_score, quiz, quiz_result, feedbacks
                FROM quiz_data
                WHERE session_id = ?
            """, (s_id,))
            for q_row in cursor.fetchall():
                session_obj.quiz_datas.append(QuizData(quiz_id=q_row[0],
                                                       session_id=s_id,
                                                       timestamp=q_row[1],
                                                       quiz_name=q_row[2],
                                                       quiz_score=q_row[3],
                                                       quiz=json.loads(q_row[4]),
                                                       quiz_result=json.loads(q_row[5]),
                                                       feedbacks=json.loads(q_row[6])
                                                       ))

            cursor.execute("""
                SELECT teachback_id, timestamp, teachback_name,
                        topic, explanation, teachback
                FROM teachback_data
                WHERE session_id = ?
            """, (s_id,))
            for t_row in cursor.fetchall():
                session_obj.teachback_datas.append(TeachbackData(teachback_id=t_row[0],
                                                                 session_id=s_id,
                                                                 timestamp=t_row[1],
                                                                 teachback_name=t_row[2],
                                                                 topic=t_row[3],
                                                                 explanation=t_row[4],
                                                                 teachback=json.loads(t_row[5])
                                                                 ))

            sessions.append(session_obj)

        conn.commit()
        conn.close()
        return sessions

    def change_username(self, new_username, user: User) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("UPDATE user SET username = ? WHERE user_id = ?",
                           (new_username, user.user_id))

            conn.commit()
            user.username = new_username

            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def change_password(self, new_password, user_obj: User) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            new_password_hash, new_salt = self._hash_password(new_password)
            cursor.execute("UPDATE user SET password_hash = ?, salt = ? WHERE user_id = ?",
                           (new_password_hash, new_salt, user_obj.user_id))

            conn.commit()
            user_obj.password_hash = new_password_hash
            user_obj.salt = new_salt
            
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def change_api_key(self, new_api_key, user_obj: User) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            new_encrypted_key = self._encrypt_api_key(new_api_key, user_obj.password_hash, user_obj.salt)
            cursor.execute("UPDATE user SET encrypted_api_key = ? WHERE user_id = ?",
                           (new_encrypted_key, user_obj.user_id))

            conn.commit()
            user_obj.encrypted_api_key = new_encrypted_key
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def rename_session(self, new_name, session_obj: Session) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE session
                SET session_name = ?
                WHERE user_id = ? AND session_id = ?
            """, (new_name, session_obj.user_id, session_obj.session_id))

            conn.commit()
            session_obj.session_name = new_name

            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def rename_chat_data(self, new_name, chat_obj: ChatData) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE chat_data
                SET chat_name = ?
                WHERE session_id = ?
            """, (new_name, chat_obj.session_id))

            conn.commit()
            chat_obj.chat_name = new_name

            return True, '' 
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def rename_quiz_data(self, new_name, quiz_obj: QuizData) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE quiz_data
                SET quiz_name = ?
                WHERE session_id = ?
            """, (new_name, quiz_obj.session_id))

            conn.commit()
            quiz_obj.quiz_name = new_name

            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()
        

    def rename_teachback_data(self, new_name, teachback_obj: TeachbackData) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE teachback_data
                SET teachback_name = ?
                WHERE session_id = ?
            """, (new_name, teachback_obj.session_id))

            conn.commit()
            teachback_obj.teachback_name = new_name

            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()
        

    def delete_account(self, user_obj: User) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM user WHERE user_id = ?",
                       (user_obj.user_id,))

            conn.commit()
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def delete_session(self, session_obj: Session) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM session
                WHERE user_id = ? AND session_id = ?
            """, (session_obj.user_id, session_obj.session_id))

            conn.commit()
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def delete_chat_data(self, chat_obj: ChatData) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM chat_data
                WHERE session_id = ?
            """, (chat_obj.session_id,))

            conn.commit()
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def delete_quiz_data(self, quiz_obj: QuizData) -> tuple[bool, str]:
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM quiz_data
                WHERE session_id = ?
            """, (quiz_obj.session_id,))

            conn.commit()
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def delete_teachback_data(self, teachback_obj: TeachbackData):
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM teachback_data
                WHERE session_id = ?
            """, (teachback_obj.session_id,))

            conn.commit()
            return True, ''
        except sqlite3.Error as e:
            return False, str(e)
        finally:
            conn.close()

    def _hash_password(self, password, salt=None) -> tuple[str, str]:
        if not salt:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password+salt).encode()).hexdigest()
        return hashed, salt

    def _verify_password(self, input_password, stored_hash, stored_salt) -> bool:
        entered_hash, _ = self._hash_password(input_password, stored_salt)
        return secrets.compare_digest(entered_hash, stored_hash)

    def _derive_fernet_key(self, password_hash, salt) -> bytes:
        key_material = hashlib.sha256((password_hash+salt).encode()).digest()
        return base64.urlsafe_b64encode(key_material)

    def _encrypt_api_key(self, api_key, password_hash, salt) -> str:
        key = self._derive_fernet_key(password_hash, salt)
        return Fernet(key).encrypt(api_key.encode()).decode()

    def _decrypt_api_key(self, encrypted, password_hash, salt) -> str | None:
        try:
            key = self._derive_fernet_key(password_hash, salt)
            return Fernet(key).decrypt(encrypted.encode()).decode()
        except Exception:
            return None

    def register_user(self, username, password, api_key):
        password_hash, salt = self._hash_password(password)
        encrypted_key = self._encrypt_api_key(api_key, password_hash, salt)

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO user
                    (username, password_hash, salt, encrypted_api_key, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, password_hash, salt, encrypted_key, datetime.now().isoformat()))

                conn.commit()
            
            return True, 'Account created successfully!'
        except sqlite3.IntegrityError:
            return False, 'Username already exists.'
        except Exception as e:
            return False, f'Error: {str(e)}'

    def authenticate_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, password_hash, salt, encrypted_api_key
            FROM user
            WHERE username = ?
        """, (username,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, 'User not found.'

        user_id, stored_hash, salt, encrypted_key = row

        if not self._verify_password(password, stored_hash, salt):
            conn.close()
            return False, 'Incorrect password.'

        cursor.execute("""
            UPDATE user
            SET last_login = ?
            WHERE user_id = ?
        """, (datetime.now().isoformat(), user_id))

        conn.commit()
        conn.close()

        api_key = self._decrypt_api_key(encrypted_key, stored_hash, salt)
        if not api_key:
            return False, 'Could not decrypt API key.'

        set_api_key(api_key)
        set_model('gemini-3.8-flash')
        return True, User(user_id=user_id, username=username,
                          password_hash=stored_hash, salt=salt,
                          encrypted_api_key=encrypted_key)