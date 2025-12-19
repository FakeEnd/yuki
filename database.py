import sqlite3
import time
import os

DB_NAME = "processed_videos.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            uploader_id TEXT,
            platform TEXT,
            publish_date INTEGER,
            processed_date INTEGER,
            summary_path TEXT,
            audio_downloaded INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def is_video_processed(video_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def add_processed_video(video_id, title, uploader_id, platform, publish_date, summary_path, audio_downloaded=False):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO videos 
            (video_id, title, uploader_id, platform, publish_date, processed_date, summary_path, audio_downloaded)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (video_id, title, uploader_id, platform, publish_date, int(time.time()), summary_path, 1 if audio_downloaded else 0))
        conn.commit()
        print(f"Recorded video {video_id} in database.")
    except Exception as e:
        print(f"Error adding video to DB: {e}")
    finally:
        conn.close()

# Initialize on import
init_db()
