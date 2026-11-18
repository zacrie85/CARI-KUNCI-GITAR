# -*- coding: utf-8 -*-
"""ChordKu - tab Panduan (menampilkan GUIDE_TEXT)."""
import tkinter as tk
from tkinter import ttk

from .guide_text import GUIDE_TEXT
from .gui import PANEL, TEXT, MONO


def build(parent, ctx):
    ttk.Label(parent, text='Cara memasang & memakai aplikasi, kunci '
                           'algoritma, dan pemecahan masalah',
              style='Muted.TLabel').pack(anchor='w', padx=12, pady=(10, 6))

    frame = ttk.Frame(parent)
    frame.pack(fill='both', expand=True, padx=12, pady=(0, 12))
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    txt = tk.Text(frame, font=MONO, wrap='word', bg=PANEL, fg=TEXT,
                  relief='flat', padx=14, pady=12, state='disabled')
    txt.grid(row=0, column=0, sticky='nsew')
    sb = ttk.Scrollbar(frame, orient='vertical', command=txt.yview)
    sb.grid(row=0, column=1, sticky='ns')
    txt.configure(yscrollcommand=sb.set)
    txt.configure(state='normal')
    txt.insert('1.0', GUIDE_TEXT)
    txt.configure(state='disabled')
