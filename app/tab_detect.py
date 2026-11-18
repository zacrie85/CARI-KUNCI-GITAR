# -*- coding: utf-8 -*-
"""ChordKu - tab Deteksi Chord dari file audio."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from . import detector as det
from .chord_canvas import ChordGrid
from .gui import PANEL, TEXT, MUTED, MONO, run_bg, diagram_colors, \
    load_into_transposer

FILETYPES = [('Audio', '*.mp3 *.m4a *.wav *.flac *.ogg *.opus *.aac '
                        '*.mp4 *.webm'),
             ('Semua file', '*.*')]


def build(parent, ctx):
    ttk.Label(parent, text='Tebak chord sebuah file audio (MP3/WAV/MP4...) — '
                           'hasilnya perkiraan, periksa dengan telinga',
              style='Muted.TLabel').pack(anchor='w', padx=12, pady=(10, 6))

    top = ttk.LabelFrame(parent, text='  Sumber audio  ')
    top.pack(fill='x', padx=12, pady=4)

    path_var = ctx.refs['detect_path'] = tk.StringVar(value='')
    ttk.Label(top, text='File:').grid(row=0, column=0, sticky='w', padx=8,
                                     pady=8)
    ttk.Entry(top, textvariable=path_var).grid(row=0, column=1, sticky='ew',
                                               padx=4)
    top.columnconfigure(1, weight=1)
    ttk.Button(top, text='Pilih File Audio...',
               command=lambda: _choose_file(path_var)).grid(
        row=0, column=2, padx=(4, 8))

    prog_row = ttk.Frame(top)
    prog_row.grid(row=1, column=0, columnspan=3, sticky='ew', padx=8,
                  pady=(0, 4))
    bar = ttk.Progressbar(prog_row, maximum=1.0, value=0.0)
    bar.pack(side='left', fill='x', expand=True)
    status_var = tk.StringVar(value='Siap.')
    ttk.Label(prog_row, textvariable=status_var, style='PMuted.TLabel',
              width=44).pack(side='left', padx=(10, 0))

    action_row = ttk.Frame(top)
    action_row.grid(row=2, column=0, columnspan=3, sticky='ew', padx=8,
                    pady=(0, 10))
    detect_btn = ttk.Button(action_row, text='Deteksi Chord',
                            style='Accent.TButton',
                            command=lambda: _detect(ctx, path_var, bar,
                                                    status_var, detect_btn))
    detect_btn.pack(side='left')

    ffmpeg = det.find_ffmpeg()
    note = ('ffmpeg ditemukan: bisa memproses MP3/MP4/M4A/FLAC.' if ffmpeg
            else 'ffmpeg TIDAK ditemukan — hanya file .wav yang bisa '
                 'diproses. Pasang ffmpeg (lihat tab Panduan).')
    ttk.Label(top, text=note, style='PMuted.TLabel',
              foreground='#FF6B81' if not ffmpeg else MUTED).grid(
        row=3, column=0, columnspan=3, sticky='w', padx=8, pady=(0, 8))

    # hasil
    res = ttk.LabelFrame(parent,
                         text='  Hasil deteksi (urutan chord berwaktu)  ')
    res.pack(fill='both', expand=True, padx=12, pady=6)
    res.rowconfigure(0, weight=1)
    res.columnconfigure(0, weight=1)
    out = tk.Text(res, font=MONO, wrap='word', bg=PANEL, fg=TEXT,
                  relief='flat', padx=10, pady=10, state='disabled')
    out.grid(row=0, column=0, sticky='nsew')
    sb = ttk.Scrollbar(res, orient='vertical', command=out.yview)
    sb.grid(row=0, column=1, sticky='ns')
    out.configure(yscrollcommand=sb.set)
    ctx.refs['detect_result_text'] = out

    # ilustrasi chord hasil deteksi (diagram fretboard)
    ilus = ttk.LabelFrame(parent, text='  Ilustrasi chord yang terdeteksi '
                                       '(senar vertikal, jari di dalam '
                                       'titik)  ')
    ilus.pack(fill='x', padx=12, pady=(2, 2))
    grid = ChordGrid(ilus, colors=diagram_colors())
    grid.pack(fill='x', padx=6, pady=(0, 6))
    ctx.refs['detect_chords'] = grid

    btn_row = ttk.Frame(parent)
    btn_row.pack(fill='x', padx=12, pady=(2, 12))
    ttk.Button(btn_row, text='Kirim ke Transposisi',
               style='Accent.TButton',
               command=lambda: _send(ctx)).pack(side='left')
    ttk.Button(btn_row, text='Simpan ke Database',
               command=lambda: _save(ctx)).pack(side='left', padx=6)


def _choose_file(path_var):
    p = filedialog.askopenfilename(title='Pilih file audio',
                                   filetypes=FILETYPES)
    if p:
        path_var.set(p)


def _detect(ctx, path_var, bar, status_var, button):
    path = path_var.get().strip()
    if not path or not os.path.isfile(path):
        messagebox.showwarning('File belum dipilih',
                               'Pilih dulu file audionya.')
        return

    def work(prog):
        return det.detect_file(path, prog)

    def on_prog(pct, msg):
        bar['value'] = pct
        status_var.set(msg)

    def on_done(result):
        bar['value'] = 1.0
        status_var.set('Selesai.')
        button['state'] = 'normal'
        ctx.refs['detect_result'] = result
        text = (
            'Kunci terdeteksi   : %s (keyakinan %s, r=%.2f)\n'
            'Durasi             : %d menit %02d detik\n'
            'Jumlah segmen chord: %d\n'
            '-----------------------------------------------\n\n'
            '%s\n\n-----------------------------------------------\n'
            'Baris chord (untuk tab Transposisi):\n%s'
            % (result['key'], result['confidence_label'],
               result['confidence'], int(result['duration']) // 60,
               int(result['duration']) % 60, len(result['segments']),
               result['timeline'], result['chord_line']))
        out = ctx.refs.get('detect_result_text')
        if out:
            out.configure(state='normal')
            out.delete('1.0', 'end')
            out.insert('1.0', text)
            out.configure(state='disabled')
        grid = ctx.refs.get('detect_chords')
        if grid is not None:
            seen, seq = set(), []
            for seg in result.get('segments') or []:
                ch = seg[2] if len(seg) > 2 else str(seg)
                if ch not in seen:
                    seen.add(ch)
                    seq.append(ch)
                    if len(seq) >= 14:
                        break
            grid.set_chords(seq, limit=14)

    def on_err(msg):
        bar['value'] = 0.0
        status_var.set('Gagal.')
        button['state'] = 'normal'
        messagebox.showerror('Deteksi gagal', msg)

    button['state'] = 'disabled'
    status_var.set('Memulai...')
    run_bg(ctx, work, on_done=on_done, on_progress=on_prog, on_error=on_err)


def _send(ctx):
    res = ctx.refs.get('detect_result')
    if not res:
        messagebox.showinfo('Belum ada hasil', 'Jalankan deteksi dulu.')
        return
    load_into_transposer(ctx, res['chord_line'], res['key_root'])
    messagebox.showinfo('Terkirim',
                        'Chord hasil deteksi dikirim ke tab Transposisi. '
                        'Pilih kunci tujuan lalu klik "Transpose".')


def _save(ctx):
    res = ctx.refs.get('detect_result')
    if not res:
        messagebox.showinfo('Belum ada hasil', 'Jalankan deteksi dulu.')
        return
    title = simpledialog.askstring('Simpan Lagu', 'Judul lagu:',
                                   parent=ctx.root)
    if not title:
        return
    artist = simpledialog.askstring('Simpan Lagu', 'Nama artis (boleh kosong):',
                                    parent=ctx.root) or ''
    ctx.db.add_song(title, artist, res['key_root'],
                    res['key_root'], res['chord_line'], source='deteksi')
    messagebox.showinfo('Tersimpan', '"%s" tersimpan ke database.' % title)
