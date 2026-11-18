# -*- coding: utf-8 -*-
"""ChordKu - tab Transposisi: geser kunci lagu (mis. C -> D)."""
import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from . import transposer as tr
from . import chords_data as cd
from .gui import PANEL, TEXT, MUTED, MONO


def _parse_key(var_value):
    """'C#/Db' -> 'C#'; 'Otomatis' -> None."""
    v = (var_value or '').strip()
    if not v or v.lower().startswith('otomatis'):
        return None
    return v.split('/')[0]


def build(parent, ctx):
    ttk.Label(parent, text='Geser seluruh chord lagu ke kunci lain — '
                           'contoh: Pujaan Hati dari kunci C ke kunci D',
              style='Muted.TLabel').pack(anchor='w', padx=12, pady=(10, 6))

    main = ttk.Frame(parent)
    main.pack(fill='both', expand=True)
    for c, w in ((0, 1), (1, 1)):
        main.columnconfigure(c, weight=w)
    main.rowconfigure(0, weight=1)

    # ------------------------------------------------ kiri: sheet asli
    left = ttk.LabelFrame(main, text='  Sheet chord asli (tempel teksnya di sini)  ')
    left.grid(row=0, column=0, sticky='nsew', padx=(12, 6), pady=4)
    left.rowconfigure(0, weight=1)
    left.columnconfigure(0, weight=1)

    input_txt = tk.Text(left, font=MONO, wrap='word', bg=PANEL, fg=TEXT,
                        relief='flat', padx=10, pady=10, undo=True,
                        insertbackground=TEXT)
    input_txt.grid(row=0, column=0, sticky='nsew')
    sb = ttk.Scrollbar(left, orient='vertical', command=input_txt.yview)
    sb.grid(row=0, column=1, sticky='ns')
    input_txt.configure(yscrollcommand=sb.set)
    ctx.refs['transpose_input'] = input_txt

    btns = ttk.Frame(left)
    btns.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=8)
    ttk.Button(btns, text='Muat Contoh: Pujaan Hati (C)',
               command=lambda: _load_sample(ctx, input_txt)).pack(side='left')
    ttk.Button(btns, text='Buka File .txt',
               command=lambda: _open_file(input_txt)).pack(side='left', padx=6)
    ttk.Button(btns, text='Bersihkan',
               command=lambda: input_txt.delete('1.0', 'end')).pack(side='left')

    # ------------------------------------------------ kanan: hasil
    right = ttk.LabelFrame(main, text='  Hasil transposisi (+ kamus jari)  ')
    right.grid(row=0, column=1, sticky='nsew', padx=(6, 12), pady=4)
    right.rowconfigure(0, weight=1)
    right.columnconfigure(0, weight=1)

    output_txt = tk.Text(right, font=MONO, wrap='word', bg=PANEL, fg=TEXT,
                         relief='flat', padx=10, pady=10, state='disabled')
    output_txt.grid(row=0, column=0, sticky='nsew')
    sb2 = ttk.Scrollbar(right, orient='vertical', command=output_txt.yview)
    sb2.grid(row=0, column=1, sticky='ns')
    output_txt.configure(yscrollcommand=sb2.set)
    ctx.refs['transpose_output'] = output_txt

    capo_var = tk.StringVar(value='Saran capo akan muncul di sini setelah '
                                 'transposisi.')
    ttk.Label(right, textvariable=capo_var, style='PMuted.TLabel',
              wraplength=420, justify='left').grid(
        row=1, column=0, sticky='ew', padx=10, pady=(0, 8))

    # ------------------------------------------------ bawah: kontrol
    ctrl = ttk.Frame(parent)
    ctrl.pack(fill='x', padx=12, pady=(2, 12))
    keys = ['Otomatis'] + tr.KEY_DISPLAY

    ttk.Label(ctrl, text='Kunci asal:').pack(side='left')
    from_var = tk.StringVar(value='Otomatis')
    cb_from = ttk.Combobox(ctrl, textvariable=from_var, values=keys,
                           width=10, state='readonly')
    cb_from.pack(side='left', padx=(4, 2))
    ctx.refs['transpose_from'] = from_var

    ttk.Label(ctrl, text='  ->  Kunci tujuan:').pack(side='left')
    to_var = tk.StringVar(value='D')
    cb_to = ttk.Combobox(ctrl, textvariable=to_var, values=tr.KEY_DISPLAY,
                         width=8, state='readonly')
    cb_to.pack(side='left', padx=(4, 8))
    ctx.refs['transpose_to'] = to_var

    shift_var = tk.StringVar(value='')
    ttk.Label(ctrl, textvariable=shift_var, style='Muted.TLabel').pack(
        side='left', padx=(0, 10), fill='x', expand=True)

    ttk.Button(ctrl, text='Transpose ke Kunci Ini', style='Accent.TButton',
               command=lambda: _do_transpose(ctx, input_txt, output_txt,
                                             from_var, to_var, shift_var,
                                             capo_var)).pack(side='left')
    ttk.Button(ctrl, text='Tampilkan 12 Kunci Alternatif',
               command=lambda: _show_all_keys(ctx, input_txt, from_var)
               ).pack(side='left', padx=6)
    ttk.Button(ctrl, text='Salin Hasil',
               command=lambda: _copy_output(ctx)).pack(side='left')
    ttk.Button(ctrl, text='Simpan ke Database',
               command=lambda: _save_song(ctx, from_var, to_var)
               ).pack(side='left', padx=6)


def _load_sample(ctx, input_txt):
    input_txt.delete('1.0', 'end')
    input_txt.insert('1.0', cd.SAMPLE_PUJAAN_HATI)
    ctx.refs['transpose_from'].set('C')


def _open_file(input_txt):
    p = filedialog.askopenfilename(title='Pilih sheet chord (.txt)',
                                   filetypes=[('Teks', '*.txt'),
                                              ('Semua file', '*.*')])
    if p:
        try:
            with open(p, 'r', encoding='utf-8', errors='replace') as f:
                input_txt.delete('1.0', 'end')
                input_txt.insert('1.0', f.read())
        except OSError as e:
            messagebox.showerror('Kesalahan', 'Tidak bisa membuka file: %s' % e)


def _unique_chords(text, limit=24):
    seen, out = set(), []
    for tok in re.split(r'\s+', text):
        core = tok.strip('(){}[],."\'!?')
        parsed = tr.parse_chord(core)
        if parsed and core not in seen:
            seen.add(core)
            out.append(core)
            if len(out) >= limit:
                break
    return out


def _do_transpose(ctx, input_txt, output_txt, from_var, to_var, shift_var,
                  capo_var):
    text = input_txt.get('1.0', 'end').strip()
    if not text:
        messagebox.showwarning('Belum ada sheet',
                               'Tempel dulu sheet chord lagunya (atau klik '
                               '"Muat Contoh").')
        return
    from_key = _parse_key(from_var.get())
    if from_key is None:
        from_key = tr.guess_sheet_key(text)
        if not from_key:
            messagebox.showwarning('Kunci asal tidak diketahui',
                                   'Pilih "Kunci asal" secara manual — sheet '
                                   'tidak berisi chord untuk ditebak.')
            return
    to_key = _parse_key(to_var.get())
    if not to_key:
        messagebox.showwarning('Kunci tujuan kosong', 'Pilih kunci tujuan.')
        return
    try:
        new_text, semis, flats = tr.transpose_sheet_by_key(text, from_key,
                                                           to_key)
    except ValueError as e:
        messagebox.showerror('Kesalahan', str(e))
        return

    shift_var.set(tr.describe_shift(from_key, to_key))

    # saran capo
    sugs = tr.capo_suggestions(to_key)
    if sugs:
        capo_var.set('Saran capo: ' + ' | '.join(
            'fret %d (bentuk %s)' % (c, k) for c, k, s in sugs))
    else:
        capo_var.set('Tidak ada posisi capo yang lebih mudah untuk kunci ini '
                     '— mainkan langsung bentuk kuncinya.')

    # kamus jari chord unik
    chords = _unique_chords(new_text)
    f_lines = [cd.fingering_text(c) for c in chords]
    body = (new_text + '\n\n--- Kamus jari chord yang dipakai ---\n'
            + '\n'.join(f_lines))
    output_txt.configure(state='normal')
    output_txt.delete('1.0', 'end')
    output_txt.insert('1.0', body)
    output_txt.configure(state='disabled')
    ctx.refs['last_transposed'] = new_text
    ctx.refs['last_keys'] = (from_key, to_key)


def _show_all_keys(ctx, input_txt, from_var):
    text = input_txt.get('1.0', 'end').strip()
    if not text:
        messagebox.showwarning('Belum ada sheet', 'Tempel dulu sheet chordnya.')
        return
    from_key = _parse_key(from_var.get()) or tr.guess_sheet_key(text)
    if not from_key:
        messagebox.showwarning('Kunci asal tidak diketahui',
                               'Pilih "Kunci asal" secara manual.')
        return
    versions = tr.all_key_versions(text, from_key)
    blocks = ['SEMUA KUNCI ALTERNATIF (asal: %s)' % from_key]
    for label, step, txt in versions:
        arah = 'asli' if step == 0 else ('naik +%d' % step)
        blocks.append('\n=== Kunci %s (%s) ===\n%s' % (label, arah, txt))
    content = '\n'.join(blocks)

    win = tk.Toplevel(ctx.root)
    win.title('12 Kunci Alternatif')
    win.geometry('760x560')
    txt = tk.Text(win, font=MONO, wrap='word', bg=PANEL, padx=10, pady=10)
    txt.pack(fill='both', expand=True, side='left')
    sb = ttk.Scrollbar(win, orient='vertical', command=txt.yview)
    sb.pack(fill='y', side='right')
    txt.configure(yscrollcommand=sb.set)
    txt.insert('1.0', content)
    txt.configure(state='disabled')

    def copy_all():
        ctx.root.clipboard_clear()
        ctx.root.clipboard_append(content)
        messagebox.showinfo('Tersalin', 'Semua versi kunci tersalin ke '
                                        'clipboard.', parent=win)

    ttk.Button(win, text='Salin Semua', command=copy_all).pack(
        pady=6, side='bottom')


def _copy_output(ctx):
    out = ctx.refs.get('transpose_output')
    if out is None:
        return
    content = out.get('1.0', 'end').strip()
    if not content:
        messagebox.showinfo('Kosong', 'Belum ada hasil untuk disalin.')
        return
    ctx.root.clipboard_clear()
    ctx.root.clipboard_append(content)
    messagebox.showinfo('Tersalin', 'Hasil transposisi tersalin ke clipboard.')


def _save_song(ctx, from_var, to_var):
    body = ctx.refs.get('last_transposed')
    if not body:
        messagebox.showinfo('Kosong', 'Transpose dulu, lalu simpan di sini.')
        return
    title = simpledialog.askstring('Simpan Lagu', 'Judul lagu:',
                                   parent=ctx.root)
    if not title:
        return
    artist = simpledialog.askstring('Simpan Lagu', 'Nama artis (boleh kosong):',
                                    parent=ctx.root) or ''
    from_key, to_key = ctx.refs.get('last_keys', ('', ''))
    from_key = _parse_key(from_var.get()) or from_key or ''
    to_key = _parse_key(to_var.get()) or to_key or ''
    ctx.db.add_song(title, artist, from_key, to_key, body,
                    source='transposisi')
    messagebox.showinfo('Tersimpan',
                        '"%s" tersimpan ke database (%d lagu).'
                        % (title, ctx.db.count()))
