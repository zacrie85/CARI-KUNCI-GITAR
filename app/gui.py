# -*- coding: utf-8 -*-
"""ChordKu - jendela utama (tema terang minimalis) + utilitas bersama."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .database import SongDB, load_config, save_config

APP_TITLE = 'CARI KUNCI GITAR (ChordKu) v1.0'
ACCENT = '#2563EB'
ACCENT_DARK = '#1D4ED8'
BG = '#F5F7FB'
PANEL = '#FFFFFF'
TEXT = '#1E293B'
MUTED = '#64748B'
MONO = ('Consolas', 10)


class Ctx(object):
    """Konteks aplikasi yang dipakai bersama oleh semua tab."""

    def __init__(self, root):
        self.root = root
        self.db = SongDB()
        self.config = load_config()
        self.refs = {}          # widget/state lintas tab

    def save_cfg(self):
        save_config(self.config)


def run_bg(ctx, fn, on_done=None, on_progress=None, on_error=None):
    """
    Jalankan fn(progress_cb) di thread belakang.
    Callback dipanggil aman di thread utama Tk.
    """
    q = queue.Queue()

    def worker():
        try:
            def prog(pct, msg):
                q.put(('p', pct, msg))
            result = fn(prog)
            q.put(('done', result))
        except Exception as e:  # noqa
            q.put(('err', str(e)))

    threading.Thread(target=worker, daemon=True).start()

    def poll():
        finished = False
        try:
            while True:
                kind, *rest = q.get_nowait()
                if kind == 'p' and on_progress:
                    on_progress(rest[0], rest[1])
                elif kind == 'done':
                    finished = True
                    if on_done:
                        try:
                            on_done(rest[0])
                        except Exception as e:  # noqa
                            messagebox.showerror('Kesalahan', str(e))
                elif kind == 'err':
                    finished = True
                    if on_error:
                        on_error(rest[0])
                    else:
                        messagebox.showerror('Kesalahan', rest[0])
        except queue.Empty:
            pass
        if not finished:
            ctx.root.after(150, poll)

    poll()


def load_into_transposer(ctx, text, from_key=None):
    """Isi tab Transposisi dari tab lain, lalu pindah ke sana."""
    w = ctx.refs.get('transpose_input')
    if w is None:
        return
    w.delete('1.0', 'end')
    w.insert('1.0', text)
    if from_key:
        var = ctx.refs.get('transpose_from')
        if var is not None:
            var.set(_match_key(from_key))
    nb = ctx.refs.get('notebook')
    idx = ctx.refs.get('tab_index', {}).get('transpose', 0)
    if nb is not None:
        nb.select(idx)


def _match_key(key):
    from .transposer import KEY_DISPLAY
    k = (key or '').strip()
    for disp in KEY_DISPLAY:
        for part in disp.split('/'):
            if k.upper() == part.upper():
                return disp
    return KEY_DISPLAY[0]


def _apply_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        pass
    root.configure(bg=BG)
    style.configure('.', background=BG, foreground=TEXT,
                    font=('Segoe UI', 10))
    style.configure('TNotebook', background=BG, borderwidth=0)
    style.configure('TNotebook.Tab', padding=(16, 9),
                    font=('Segoe UI', 10, 'bold'))
    style.map('TNotebook.Tab',
              background=[('selected', ACCENT), ('!selected', '#E2E8F0')],
              foreground=[('selected', 'white'), ('!selected', TEXT)])
    style.configure('TFrame', background=BG)
    style.configure('P.TFrame', background=PANEL)
    style.configure('TLabel', background=BG, foreground=TEXT)
    style.configure('P.TLabel', background=PANEL)
    style.configure('Title.TLabel', background=PANEL, foreground=ACCENT,
                    font=('Segoe UI', 13, 'bold'))
    style.configure('Muted.TLabel', background=BG, foreground=MUTED)
    style.configure('PMuted.TLabel', background=PANEL, foreground=MUTED)
    style.configure('TButton', padding=(10, 6))
    style.configure('Accent.TButton', foreground='white', background=ACCENT,
                    font=('Segoe UI', 10, 'bold'), padding=(12, 7))
    style.map('Accent.TButton',
              background=[('active', ACCENT_DARK), ('disabled', '#93C5FD')],
              foreground=[('disabled', '#E2E8F0')])
    style.configure('TLabelframe', background=PANEL, borderwidth=0)
    style.configure('TLabelframe.Label', background=PANEL, foreground=ACCENT,
                    font=('Segoe UI', 10, 'bold'))
    style.configure('TEntry', padding=4)
    style.configure('TCombobox', padding=4)
    style.configure('Treeview', background=PANEL, fieldbackground=PANEL,
                    rowheight=24)
    style.configure('Treeview.Heading', background='#EFF6FF',
                    foreground=ACCENT, font=('Segoe UI', 9, 'bold'))
    style.configure('TProgressbar', troughcolor='#DBEAFE',
                    background=ACCENT, thickness=14)
    style.configure('Vertical.TScrollbar', background='#CBD5E1')


def launch():
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry('1040x700')
    root.minsize(880, 580)
    _apply_style(root)
    ctx = Ctx(root)

    nb = ttk.Notebook(root)
    nb.pack(fill='both', expand=True, padx=8, pady=8)
    ctx.refs['notebook'] = nb
    ctx.refs['tab_index'] = {}

    from .tab_transpose import build as t_transpose
    from .tab_detect import build as t_detect
    from .tab_youtube import build as t_youtube
    from .tab_library import build as t_library
    from .tab_guide import build as t_guide

    specs = [
        ('Transposisi', t_transpose, 'transpose'),
        ('Deteksi Chord', t_detect, 'detect'),
        ('YouTube', t_youtube, 'youtube'),
        ('Lagu Tersimpan', t_library, 'library'),
        ('Panduan', t_guide, 'guide'),
    ]
    for text, builder, key in specs:
        frame = ttk.Frame(nb)
        builder(frame, ctx)
        ctx.refs['tab_index'][key] = len(nb.tabs())
        nb.add(frame, text=' ' + text + ' ')

    def on_close():
        try:
            ctx.db.close()
        except Exception:
            pass
        root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)
    root.mainloop()
    return 0
