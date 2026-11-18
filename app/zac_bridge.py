# -*- coding: utf-8 -*-
"""
ChordKu - Jembatan Zac Downloader (v1.0.7).

Komunikasi ChordKu <-> Zac Downloader lewat folder bridge berbasis
file JSON (tanpa port/socket, aman offline & bebas dialog firewall):

  inbox.json   : Zac Downloader -> ChordKu
                 {"ts": ..., "mode": "url"|"browser"|"file"|"both",
                  "url": "...", "path": "...", "title": "...",
                  "source": "browser"|"download"|"hub"}
  status.json  : ChordKu -> Zac Downloader (detak jantung)
                 {"pid": ..., "version": "1.0.7", "ts": ...}

Lokasi folder (urutan):
  1. env CHORDKU_BRIDGE_DIR (untuk tes / pengaturan manual)
  2. Windows: %APPDATA%\\ZacChordKuBridge
  3. selain Windows: <folder aplikasi>/bridge
"""
import json
import os
import sys
import tempfile
import time

BRIDGE_DIRNAME = 'ZacChordKuBridge'
INBOX_NAME = 'inbox.json'
STATUS_NAME = 'status.json'


def bridge_dir():
    """Folder jembatan bersama (dibuat otomatis bila belum ada)."""
    env = os.environ.get('CHORDKU_BRIDGE_DIR')
    if env:
        d = env
    elif sys.platform.startswith('win'):
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        d = os.path.join(base, BRIDGE_DIRNAME)
    else:
        try:
            from .database import app_dir
            d = os.path.join(app_dir(), 'bridge')
        except Exception:
            d = os.path.join(os.path.expanduser('~'), '.zac-chordku-bridge')
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def inbox_path():
    return os.path.join(bridge_dir(), INBOX_NAME)


def status_path():
    return os.path.join(bridge_dir(), STATUS_NAME)


def _write_atomic(path, data):
    """Tulis JSON atomik (tmp + rename) supaya pembaca tidak setengah file."""
    try:
        fd, tmp = tempfile.mkstemp(prefix='.bridge-', suffix='.tmp',
                                   dir=os.path.dirname(path) or '.')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        try:
            os.replace(tmp, path)
        except OSError:
            os.unlink(tmp)
            return False
        return True
    except Exception:
        return False


def _read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def send_message(mode, url='', path='', title='', source='hub', ts=None):
    """Tulis pesan masuk untuk ChordKu (dipakai Zac Downloader / tes)."""
    mode = str(mode or 'url').strip().lower()
    if mode not in ('url', 'browser', 'file', 'both'):
        mode = 'url'
    msg = {
        'ts': float(ts if ts is not None else time.time()),
        'mode': mode,
        'url': str(url or '').strip(),
        'path': str(path or '').strip(),
        'title': str(title or '').strip(),
        'source': str(source or 'hub'),
    }
    if msg['mode'] == 'file' and not msg['path']:
        return None
    if msg['mode'] in ('url', 'browser', 'both') and not msg['url']:
        return None
    return msg if _write_atomic(inbox_path(), msg) else None


def read_message():
    """Baca pesan inbox (atau None). Pemanggil yang urus dedup ts."""
    return _read_json(inbox_path())


def write_status(version='1.0.7'):
    """Detak jantung ChordKu -> Zac Downloader."""
    return _write_atomic(status_path(), {
        'pid': os.getpid(),
        'version': str(version),
        'ts': time.time(),
    })


def read_status(max_age=15.0):
    """Status ChordKu + flag hidup (heartbeat < max_age detik)."""
    st = _read_json(status_path())
    if not st:
        return {'running': False, 'version': '', 'age': None}
    try:
        age = max(0.0, time.time() - float(st.get('ts', 0)))
    except (TypeError, ValueError):
        age = None
    st = dict(st)
    st['age'] = age
    st['running'] = age is not None and age <= max_age
    return st


def is_message_new(msg, last_ts):
    """True bila pesan lebih baru dari posisi terakhir yang diproses."""
    if not msg:
        return False
    try:
        return float(msg.get('ts', 0)) > float(last_ts or 0.0)
    except (TypeError, ValueError):
        return False
