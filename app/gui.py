# -*- coding: utf-8 -*-
"""ChordKu - jendela utama (tema futuristik merah-putih-emas) + utilitas."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .database import SongDB, load_config, save_config

APP_TITLE = 'CARI KUNCI GITAR (ChordKu) v1.0.5'

# ------------------------------------------------------------ palet tema
BG = '#120A0E'          # latar sangat gelap bernuansa maroon
BG_ALT = '#1A0F14'
PANEL = '#1D1218'       # panel gelap
PANEL_LIGHT = '#261820'
BORDER = '#3D2430'
TEXT = '#F4EDE4'        # putih hangat
MUTED = '#B49BA3'
GOLD = '#F5C542'        # emas
GOLD_LIGHT = '#FFE08A'
GOLD_DARK = '#8A6A1C'
RED = '#E5093C'         # merah menyala
RED_DARK = '#8E0B29'
RED_SOFT = '#FF3355'
HEADER_A = '#1C0710'
HEADER_B = '#B00A33'
HEADER_C = '#F5C542'
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
    """Isi tab Transposisi dari tab lain, lalu pindah ke sana.

    Return False (tanpa mengubah apa pun) bila tab belum siap atau
    teks yang dikirim kosong — pencegah dialog "Belum ada sheet"."""
    w = ctx.refs.get('transpose_input')
    if w is None or not (text or '').strip():
        return False
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
    return True


def _match_key(key):
    from .transposer import KEY_DISPLAY
    k = (key or '').strip()
    for disp in KEY_DISPLAY:
        for part in disp.split('/'):
            if k.upper() == part.upper():
                return disp
    return KEY_DISPLAY[0]


def diagram_colors():
    """Palet untuk widget ilustrasi chord (app/chord_canvas.py)."""
    return {'panel': PANEL, 'gold': GOLD, 'red': RED, 'dot': RED,
            'dot_soft': RED_SOFT, 'dot_text': '#FFFFFF', 'muted': MUTED,
            'wood': '#5C3A21', 'wood_dark': '#4A2E19'}


# ------------------------------------------------------------------ tema
def _gradient(canvas, w, h, stops):
    """Gambar gradien horizontal multi-titik (stops: [(pos, '#hex')])."""
    def hex2rgb(hx):
        hx = hx.lstrip('#')
        return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))
    pts = [(p, hex2rgb(c)) for p, c in stops]
    for x in range(w):
        t = x / max(w - 1, 1)
        for k in range(len(pts) - 1):
            p0, c0 = pts[k]
            p1, c1 = pts[k + 1]
            if p0 <= t <= p1:
                f = (t - p0) / (p1 - p0 or 1)
                col = tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(3))
                canvas.create_line(x, 0, x, h, fill='#%02x%02x%02x' % col)
                break


def make_header(parent):
    """Header gradien merah-emas dengan judul menyala. Return canvas."""
    c = tk.Canvas(parent, height=72, highlightthickness=0, bg=BG)
    c.pack(fill='x')

    def redraw(_e=None):
        c.delete('all')
        w = max(c.winfo_width(), 10)
        h = 72
        _gradient(c, w, h, [(0.0, HEADER_A), (0.55, HEADER_B),
                            (0.9, '#D88A2B'), (1.0, HEADER_C)])
        # kilau judul: bayangan gelap lalu teks utama
        cx = w / 2
        c.create_text(cx + 2, 25, text=APP_TITLE, fill='#3D0410',
                      font=('Segoe UI', 17, 'bold'))
        c.create_text(cx, 23, text=APP_TITLE, fill='#FFFFFF',
                      font=('Segoe UI', 17, 'bold'))
        c.create_text(cx, 51, text='DETEKSI CHORD  •  TRANSPOSISI  •  '
                                   'YOUTUBE  •  ILUSTRASI CHORD',
                      fill=GOLD, font=('Segoe UI', 8, 'bold'))
        c.create_line(0, h - 1, w, h - 1, fill=GOLD, width=2)

    c.bind('<Configure>', redraw)
    return c


def _apply_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except Exception:
        pass
    root.configure(bg=BG)
    style.configure('.', background=BG, foreground=TEXT,
                    font=('Segoe UI', 10))
    # notebook & tab
    style.configure('TNotebook', background=BG, borderwidth=0, tabmargins=(6, 4, 6, 0))
    style.configure('TNotebook.Tab', padding=(18, 9),
                    font=('Segoe UI', 10, 'bold'),
                    background=BG_ALT, foreground=GOLD, borderwidth=0)
    style.map('TNotebook.Tab',
              background=[('selected', RED), ('!selected', BG_ALT)],
              foreground=[('selected', '#FFFFFF'), ('!selected', GOLD)],
              focuscolor=[('selected', RED)])
    # frame & label
    style.configure('TFrame', background=BG)
    style.configure('P.TFrame', background=PANEL)
    style.configure('TLabel', background=BG, foreground=TEXT)
    style.configure('P.TLabel', background=PANEL, foreground=TEXT)
    style.configure('Title.TLabel', background=PANEL, foreground=GOLD,
                    font=('Segoe UI', 13, 'bold'))
    style.configure('Muted.TLabel', background=BG, foreground=MUTED)
    style.configure('PMuted.TLabel', background=PANEL, foreground=MUTED)
    style.configure('Gold.TLabel', background=BG, foreground=GOLD,
                    font=('Segoe UI', 10, 'bold'))
    # tombol: emas (utama), merah (aksen), gelap (biasa) + efek hover
    style.configure('TButton', padding=(12, 7), borderwidth=1,
                    background=PANEL_LIGHT, foreground=TEXT,
                    font=('Segoe UI', 9), bordercolor=BORDER,
                    focuscolor=PANEL_LIGHT)
    style.map('TButton', background=[('active', BORDER), ('disabled', '#241820')],
              foreground=[('disabled', '#776070'), ('active', GOLD_LIGHT)],
              bordercolor=[('active', GOLD_DARK)])
    style.configure('Accent.TButton', padding=(14, 8), borderwidth=0,
                    background=GOLD, foreground='#1A0A0F',
                    font=('Segoe UI', 10, 'bold'), focuscolor=GOLD)
    style.map('Accent.TButton',
              background=[('disabled', '#6E5A24'), ('active', GOLD_LIGHT)],
              foreground=[('disabled', '#A89A78'), ('active', '#000000')])
    style.configure('Red.TButton', padding=(14, 8), borderwidth=0,
                    background=RED, foreground='#FFFFFF',
                    font=('Segoe UI', 10, 'bold'), focuscolor=RED)
    style.map('Red.TButton',
              background=[('disabled', RED_DARK), ('active', RED_SOFT)],
              foreground=[('disabled', '#D9A9B5')])
    # labelframe: kotak panel bergaris emas tipis
    style.configure('TLabelframe', background=PANEL, borderwidth=1,
                    bordercolor=BORDER, relief='solid')
    style.configure('TLabelframe.Label', background=PANEL, foreground=GOLD,
                    font=('Segoe UI', 9, 'bold'))
    # entry & combobox gelap
    style.configure('TEntry', fieldbackground=PANEL_LIGHT, foreground=TEXT,
                    insertcolor=TEXT, bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, padding=4)
    style.map('TEntry', bordercolor=[('focus', RED)],
              lightcolor=[('focus', RED)], darkcolor=[('focus', RED)])
    style.configure('TCombobox', fieldbackground=PANEL_LIGHT,
                    background=PANEL_LIGHT, foreground=TEXT, arrowcolor=GOLD,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    padding=4)
    style.map('TCombobox', fieldbackground=[('readonly', PANEL_LIGHT)],
              bordercolor=[('focus', RED)])
    # treeview gelap + seleksi merah
    style.configure('Treeview', background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, rowheight=26, bordercolor=BORDER)
    style.map('Treeview', background=[('selected', RED_DARK)],
              foreground=[('selected', '#FFFFFF')])
    style.configure('Treeview.Heading', background=BG_ALT, foreground=GOLD,
                    font=('Segoe UI', 9, 'bold'), borderwidth=0)
    style.map('Treeview.Heading', background=[('active', BORDER)])
    # progressbar merah menyala
    style.configure('TProgressbar', troughcolor=BG_ALT, background=RED,
                    thickness=14, borderwidth=0)
    # scrollbar gelap
    style.configure('Vertical.TScrollbar', background=PANEL_LIGHT,
                    troughcolor=BG_ALT, bordercolor=BG_ALT,
                    arrowcolor=GOLD)
    style.configure('Horizontal.TScrollbar', background=PANEL_LIGHT,
                    troughcolor=BG_ALT, bordercolor=BG_ALT,
                    arrowcolor=GOLD)


def launch():
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry('1100x820')
    root.minsize(940, 700)
    _apply_style(root)
    ctx = Ctx(root)
    make_header(root)

    nb = ttk.Notebook(root)
    nb.pack(fill='both', expand=True, padx=10, pady=(6, 10))
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
