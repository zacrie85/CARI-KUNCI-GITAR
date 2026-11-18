# -*- coding: utf-8 -*-
"""ChordKu - tab Lagu Tersimpan (database SQLite)."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .gui import PANEL, TEXT, MONO, load_into_transposer

COLUMNS = ('judul', 'artis', 'asal', 'kini', 'sumber', 'tanggal')
HEADINGS = ('Judul', 'Artis', 'Kunci Asal', 'Kunci Sekarang', 'Sumber',
            'Dibuat')


def build(parent, ctx):
    ttk.Label(parent, text='Sheet chord yang pernah kamu simpan — tersimpan '
                           'di chordku.db di sebelah aplikasi',
              style='Muted.TLabel').pack(anchor='w', padx=12, pady=(10, 6))

    wrap = ttk.Frame(parent)
    wrap.pack(fill='both', expand=True, padx=12, pady=4)
    wrap.rowconfigure(0, weight=3)
    wrap.rowconfigure(1, weight=2)
    wrap.columnconfigure(0, weight=1)

    tree = ttk.Treeview(wrap, columns=COLUMNS, show='headings', height=8)
    tree.grid(row=0, column=0, sticky='nsew')
    sb = ttk.Scrollbar(wrap, orient='vertical', command=tree.yview)
    sb.grid(row=0, column=1, sticky='ns')
    tree.configure(yscrollcommand=sb.set)
    for col, head in zip(COLUMNS, HEADINGS):
        tree.heading(col, text=head)
        tree.column(col, anchor='w')
    tree.column('judul', width=180)
    tree.column('artis', width=120)
    tree.column('asal', width=70, anchor='center')
    tree.column('kini', width=90, anchor='center')
    tree.column('sumber', width=90, anchor='center')
    tree.column('tanggal', width=110, anchor='center')

    preview = tk.Text(wrap, font=MONO, wrap='word', bg=PANEL, fg=TEXT,
                      relief='flat', padx=10, pady=8, height=8)
    preview.grid(row=1, column=0, sticky='nsew', pady=(8, 0))
    sb2 = ttk.Scrollbar(wrap, orient='vertical', command=preview.yview)
    sb2.grid(row=1, column=1, sticky='ns', pady=(8, 0))
    preview.configure(yscrollcommand=sb2.set, state='disabled')

    btn = ttk.Frame(parent)
    btn.pack(fill='x', padx=12, pady=(4, 12))
    ttk.Button(btn, text='Muat ke Transposisi', style='Accent.TButton',
               command=lambda: _load(ctx, tree, preview)).pack(side='left')
    ttk.Button(btn, text='Ekspor ke .txt',
               command=lambda: _export(ctx, tree)).pack(side='left', padx=6)
    ttk.Button(btn, text='Hapus',
               command=lambda: _delete(ctx, tree, preview)).pack(side='left')
    ttk.Button(btn, text='Segarkan',
               command=lambda: _refresh(ctx, tree, preview)).pack(side='left',
                                                                  padx=6)

    tree.bind('<Double-1>', lambda e: _load(ctx, tree, preview))
    tree.bind('<<TreeviewSelect>>',
              lambda e: _preview(ctx, tree, preview))
    _refresh(ctx, tree, preview)


def _refresh(ctx, tree, preview):
    for iid in tree.get_children():
        tree.delete(iid)
    for row in ctx.db.list_songs():
        tree.insert('', 'end', iid=str(row['id']), values=(
            row['title'], row['artist'], row['original_key'],
            row['current_key'], row['source'], row['created_at']))
    _set_preview(preview, 'Total %d lagu tersimpan. Pilih baris untuk '
                          'melihat pratinjau chord.' % ctx.db.count())


def _selected_id(tree):
    sel = tree.selection()
    return int(sel[0]) if sel else None


def _set_preview(preview, text):
    preview.configure(state='normal')
    preview.delete('1.0', 'end')
    preview.insert('1.0', text)
    preview.configure(state='disabled')


def _preview(ctx, tree, preview):
    sid = _selected_id(tree)
    if sid is None:
        return
    row = ctx.db.get_song(sid)
    if row:
        _set_preview(preview, row['chord_text'])


def _load(ctx, tree, preview):
    sid = _selected_id(tree)
    if sid is None:
        messagebox.showinfo('Pilih lagu', 'Pilih dulu lagu di daftar.')
        return
    row = ctx.db.get_song(sid)
    if not row:
        return
    load_into_transposer(ctx, row['chord_text'], row['original_key'])
    messagebox.showinfo('Dimuat',
                        '"%s" dimuat ke tab Transposisi.' % row['title'])


def _export(ctx, tree):
    sid = _selected_id(tree)
    if sid is None:
        messagebox.showinfo('Pilih lagu', 'Pilih dulu lagu di daftar.')
        return
    row = ctx.db.get_song(sid)
    if not row:
        return
    fname = '%s - %s.txt' % (row['artist'] or 'unknown',
                             row['title']).replace('/', '-')
    p = filedialog.asksaveasfilename(title='Simpan sheet chord',
                                     initialfile=fname,
                                     defaultextension='.txt',
                                     filetypes=[('Teks', '*.txt')])
    if not p:
        return
    try:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(row['chord_text'])
        messagebox.showinfo('Terekspor', 'Sheet tersimpan ke:\n%s' % p)
    except OSError as e:
        messagebox.showerror('Gagal', str(e))


def _delete(ctx, tree, preview):
    sid = _selected_id(tree)
    if sid is None:
        messagebox.showinfo('Pilih lagu', 'Pilih dulu lagu di daftar.')
        return
    row = ctx.db.get_song(sid)
    if row and messagebox.askyesno('Hapus',
                                   'Hapus "%s" dari database?' % row['title']):
        ctx.db.delete_song(sid)
        _refresh(ctx, tree, preview)
