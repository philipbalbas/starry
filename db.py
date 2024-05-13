from typing import Tuple, Optional
import sqlite3

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('bot_data.db')  # This creates the database file
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def setup_database(conn):
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                guild_id TEXT,
                channel_id TEXT,
                user_id TEXT,
                session_id TEXT,
                PRIMARY KEY (guild_id, channel_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(e)

conn = create_connection()
cursor = conn.cursor()


def get_agent_id() -> Optional[str]:
    try:
        cursor.execute("SELECT agent_id FROM agents LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Database error in `get_agent_id`: {e}")
        return None

def set_agent_id(agent_id: str):
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO agents (agent_id) VALUES (?)",
            (agent_id,),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error in `set_agent_id`: {e}")

def get_session_ids(guild_id: str) -> Tuple[Optional[str], Optional[str]]:
    print("guild_id", guild_id)
    try:
        cursor.execute(
        "SELECT user_id, session_id FROM sessions WHERE guild_id=?",
        (guild_id,)
    )

        result = cursor.fetchone()
        print("result", result)
        if result is not None:
            return result
        return None, None
    except sqlite3.Error as e:
        print(f"Database error in `get_session_ids`: {e}")
        return None, None




def set_session(guild_id: str, channel_id: str, user_id: str, session_id: str):
    try:
        cursor.execute(
            "INSERT INTO sessions (guild_id, channel_id, user_id, session_id) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (guild_id, channel_id) DO UPDATE SET user_id = excluded.user_id, session_id = excluded.session_id",
            (guild_id, channel_id, user_id, session_id),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error in `set_session`: {e}")

def session_exists(guild_id: str, channel_id: str) -> bool:
    try:
        cursor.execute(
            "SELECT 1 FROM sessions WHERE guild_id=? AND channel_id=?",
            (guild_id, channel_id),
        )
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        print(f"Database error in `session_exists`: {e}")
        return False

def get_session_id(channel_id: str) -> Optional[str]:
    try:
        cursor.execute("SELECT session_id FROM sessions WHERE channel_id=?", (channel_id,))
        row = cursor.fetchone()
        print("row", row)
        return row[0] if row else None
    except sqlite3.Error as e:
        print(f"Database error in `get_session_id`: {e}")
        return None


def delete_all_sessions():
    cursor.execute("DELETE FROM sessions")
    conn.commit()
