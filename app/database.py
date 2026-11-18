# -*- coding: utf-8 -*-
"""ChordKu - Database SQLite (lagu tersimpan) + konfigurasi aplikasi."""
import json
import os
import sqlite3
import sys
from datetime import datetime


def app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _db_path():
    return os.path.join(app_dir(), 'chordku.db')


def _config_path():
    return os.path.join(app_dir(), 'config.json')


class SongDB:
    """Penyimpanan lagu/chord berbasis SQLite (chordku.db)."""

    def __init__(self, path=None):
        self.path = path or _db_path()
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._create()

    def _create(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT DEFAULT '',
                original_key TEXT DEFAULT '',
                current_key TEXT DEFAULT '',
                chord_text TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                created_at TEXT NOT NULL
            )""")
        self.conn.commit()

    def add_song(self, title, artist='', original_key='', current_key='',
                 chord_text='', source='manual'):
        cur = self.conn.execute(
            "INSERT INTO songs (title, artist, original_key, current_key,"
            " chord_text, source, created_at) VALUES (?,?,?,?,?,?,?)",
            (title, artist, original_key, current_key, chord_text, source,
             datetime.now().strftime('%Y-%m-%d %H:%M')))
        self.conn.commit()
        return cur.lastrowid

    def list_songs(self):
        return self.conn.execute(
            "SELECT id, title, artist, original_key, current_key, created_at,"
            " source FROM songs ORDER BY id DESC").fetchall()

    def get_song(self, song_id):
        return self.conn.execute(
            "SELECT * FROM songs WHERE id=?", (song_id,)).fetchone()

    def delete_song(self, song_id):
        self.conn.execute("DELETE FROM songs WHERE id=?", (song_id,))
        self.conn.commit()
        return self.conn.total_changes > 0

    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]

    def close(self):
        self.conn.close()


DEFAULT_CONFIG = {
    'download_dir': os.path.join(app_dir(), 'downloads'),
    'external_tool_path': '',
    'last_youtube_url': '',
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_config_path(), 'r', encoding='utf-8') as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(_config_path(), 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
