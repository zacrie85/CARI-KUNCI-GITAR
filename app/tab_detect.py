# -*- coding: utf-8 -*-
"""ChordKu - tab Deteksi Chord dari file audio."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from . import detector as det
from . import lyrics as lyr
from . import sheet_builder as sheetb
from .database import save_config
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
               command=lambda: _choose_file(path_var, judul_var)).grid(
        row=0, column=2, padx=(4, 8))

    judul_var = ctx.refs['detect_judul'] = tk.StringVar(value='')
    ttk.Label(top, text='Judul lagu (untuk ambil lirik):').grid(
        row=1, column=0, sticky='w', padx=8)
    ttk.Entry(top, textvariable=judul_var).grid(row=1, column=1, sticky='ew',
                                                padx=4)
    ttk.Label(top, text='Terisi otomatis dari nama file / judul YouTube '
                        '— boleh dikoreksi manual.',
              style='PMuted.TLabel').grid(row=1, column=2, sticky='w',
                                          padx=(4, 8))

    prog_row = ttk.Frame(top)
    prog_row.grid(row=2, column=0, columnspan=3, sticky='ew', padx=8,
                  pady=(0, 4))
    bar = ttk.Progressbar(prog_row, maximum=1.0, value=0.0)
    bar.pack(side='left', fill='x', expand=True)
    status_var = tk.StringVar(value='Siap.')
    ttk.Label(prog_row, textvariable=status_var, style='PMuted.TLabel',
              width=44).pack(side='left', padx=(10, 0))

    action_row = ttk.Frame(top)
    action_row.grid(row=3, column=0, columnspan=3, sticky='ew', padx=8,
                    pady=(0, 10))
    detect_btn = ttk.Button(action_row, text='Deteksi Chord',
                            style='Accent.TButton',
                            command=lambda: _detect(ctx, path_var, bar,
                                                    status_var, detect_btn))
    detect_btn.pack(side='left')
    ttk.Label(action_row, text='Kehalusan deteksi:',
              style='PMuted.TLabel').pack(side='left', padx=(16, 4))
    sens_var = ctx.refs['detect_sens'] = tk.StringVar(value='Normal')
    ttk.Combobox(action_row, textvariable=sens_var,
                 values=('Kasar', 'Normal', 'Halus'),
                 state='readonly', width=8).pack(side='left')
    ttk.Label(action_row, text='Halus = lebih banyak perubahan chord '
                               'tertangkap sampai akhir lagu.',
              style='PMuted.TLabel').pack(side='left', padx=(8, 0))
    # v1.0.7: jalur Zac Downloader — simpan referensi widget agar pesan
    # jembatan bisa mengisi file & menjalankan deteksi otomatis
    ctx.refs['detect_bar'] = bar
    ctx.refs['detect_status'] = status_var
    ctx.refs['detect_btn'] = detect_btn
    ctx.refs['zac_auto_detect'] = tk.BooleanVar(
        value=bool(ctx.config.get('zac_auto_detect', True)))
    ttk.Checkbutton(action_row, text='🎸 Auto-deteksi file dari Zac',
                    variable=ctx.refs['zac_auto_detect'],
                    command=lambda: _save_zac_auto(ctx)).pack(
        side='left', padx=(10, 0))

    ffmpeg = det.find_ffmpeg()
    note = ('ffmpeg ditemukan: bisa memproses MP3/MP4/M4A/FLAC.' if ffmpeg
            else 'ffmpeg TIDAK ditemukan — hanya file .wav yang bisa '
                 'diproses. Pasang ffmpeg (lihat tab Panduan).')
    ttk.Label(top, text=note, style='PMuted.TLabel',
              foreground='#FF6B81' if not ffmpeg else MUTED).grid(
        row=4, column=0, columnspan=3, sticky='w', padx=8, pady=(0, 8))

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
    ttk.Button(btn_row, text='Kirim ke Transposisi + Lirik',
               style='Accent.TButton',
               command=lambda: _send_with_lyrics(ctx, bar, status_var)
               ).pack(side='left')
    ttk.Button(btn_row, text='Kirim ke Transposisi (chord saja)',
               command=lambda: _send(ctx)).pack(side='left', padx=6)
    ttk.Button(btn_row, text='Simpan ke Database',
               command=lambda: _save(ctx)).pack(side='left')


def _choose_file(path_var, judul_var):
    p = filedialog.askopenfilename(title='Pilih file audio',
                                   filetypes=FILETYPES)
    if p:
        path_var.set(p)
        if not judul_var.get().strip():
            judul_var.set(lyr.parse_title_from_filename(p))


def _save_zac_auto(ctx):
    """v1.0.7: simpan pilihan auto-deteksi file dari Zac Downloader."""
    var = ctx.refs.get('zac_auto_detect')
    if var is None:
        return
    ctx.config['zac_auto_detect'] = bool(var.get())
    save_config(ctx.config)


def _detect(ctx, path_var, bar, status_var, button):
    path = path_var.get().strip()
    if not path or not os.path.isfile(path):
        messagebox.showwarning('File belum dipilih',
                               'Pilih dulu file audionya.')
        return

    def work(prog):
        return det.detect_file(path, prog, sensitivity=sens_val)

    def on_prog(pct, msg):
        bar['value'] = pct
        status_var.set(msg)

    def on_done(result):
        bar['value'] = 1.0
        status_var.set('Selesai.')
        button['state'] = 'normal'
        ctx.refs['detect_result'] = result
        judul = ctx.refs.get('detect_judul')
        if judul is not None and not judul.get().strip():
            judul.set(lyr.parse_title_from_filename(path_var.get()))
        text = (
            'Kunci terdeteksi   : %s (keyakinan %s, r=%.2f)\n'
            'Kehalusan          : %s\n'
            'Durasi             : %d menit %02d detik\n'
            'Jumlah segmen chord: %d\n'
            '-----------------------------------------------\n\n'
            '%s\n\n-----------------------------------------------\n'
            'Baris chord (untuk tab Transposisi, LENGKAP sampai akhir '
            'lagu):\n%s'
            % (result['key'], result['confidence_label'],
               result['confidence'], sens_val,
               int(result['duration']) // 60,
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
    # baca pilihan kehalusan di thread utama (StringVar tidak boleh
    # disentuh dari thread latar belakang)
    sens = ctx.refs.get('detect_sens')
    sens_val = sens.get().strip().lower() if sens else 'normal'
    run_bg(ctx, work, on_done=on_done, on_progress=on_prog, on_error=on_err)


def _send(ctx, quiet=False):
    """Kirim chord saja (tanpa lirik) ke tab Transposisi."""
    res = ctx.refs.get('detect_result')
    if not res:
        messagebox.showinfo('Belum ada hasil', 'Jalankan deteksi dulu.')
        return
    if not (res.get('chord_line') or '').strip():
        messagebox.showwarning(
            'Tidak ada chord',
            'Deteksi tidak menghasilkan chord. Coba audio yang lebih jelas '
            'atau pilih lagu dengan musik dominan.')
        return
    ok = load_into_transposer(ctx, res['chord_line'], res['key_root'])
    if not quiet:
        messagebox.showinfo('Terkirim',
                            'Chord hasil deteksi dikirim ke tab Transposisi. '
                            'Pilih kunci tujuan lalu klik "Transpose".'
                            if ok else
                            'Tab Transposisi tidak siap.')


def _send_with_lyrics(ctx, bar, status_var):
    """Ambil lirik otomatis (lrclib.net), gabung dengan chord deteksi,
    lalu muat sheet LIRIK+CHORD ke tab Transposisi."""
    res = ctx.refs.get('detect_result')
    if not res:
        messagebox.showinfo('Belum ada hasil',
                            'Jalankan deteksi chord dulu di atas.')
        return
    if not (res.get('chord_line') or '').strip():
        messagebox.showwarning(
            'Tidak ada chord',
            'Deteksi tidak menghasilkan chord, jadi tidak ada yang bisa '
            'digabung dengan lirik. Coba audio yang lebih jelas.')
        return
    judul_var = ctx.refs.get('detect_judul')
    title = judul_var.get().strip() if judul_var else ''
    if not title:
        title = lyr.parse_title_from_filename(
            ctx.refs.get('detect_path', tk.StringVar()).get())
    if not title:
        title = simpledialog.askstring(
            'Judul lagu', 'Ketik judul lagu untuk mencari liriknya:',
            parent=ctx.root) or ''
        if judul_var is not None and title:
            judul_var.set(title)
    if not title.strip():
        messagebox.showinfo('Judul kosong',
                            'Isi dulu kolom "Judul lagu" supaya lirik bisa '
                            'dicari. Atau pakai tombol chord saja.')
        return

    def work(prog):
        meta = lyr.search_lyrics(title)
        if meta is None:
            return None, None
        sheet = sheetb.build_sheet(title, res.get('key_root'),
                                   res.get('segments'),
                                   res.get('duration'), meta)
        return sheet, meta

    def on_prog(pct, msg):
        if bar is not None:
            bar['value'] = pct
        if status_var is not None:
            status_var.set(msg)

    def on_done(pair):
        sheet, meta = pair
        if status_var is not None:
            status_var.set('Lirik: %s' % ('ditemukan' if sheet
                                          else 'tidak ditemukan'))
        if sheet:
            load_into_transposer(ctx, sheet, res.get('key_root'))
            messagebox.showinfo(
                'Sheet siap!',
                'Lirik ditemukan: %s%s\n\nSheet LIRIK + CHORD sudah dimuat '
                'ke tab Transposisi.\nKunci asal otomatis: %s\n\nLangkah '
                'selanjutnya: pilih "Kunci tujuan" lalu klik "Transpose ke '
                'Kunci Ini".' % (meta.get('artist') or '(?)',
                                 ' - %s' % meta.get('track')
                                 if meta.get('track') else '',
                                 res.get('key_root') or '?'))
        else:
            if messagebox.askyesno(
                    'Lirik tidak ditemukan',
                    'Lirik tidak ditemukan di layanan lrclib.net\n'
                    '(judul salah / lagu belum ada / internet bermasalah).\n\n'
                    'Kirim CHORD SAJA ke tab Transposisi?'):
                _send(ctx, quiet=True)

    def on_err(msg):
        if status_var is not None:
            status_var.set('Gagal ambil lirik.')
        if messagebox.askyesno(
                'Gagal mengambil lirik',
                'Koneksi ke lrclib.net gagal:\n%s\n\n'
                'Kirim CHORD SAJA ke tab Transposisi?' % msg):
            _send(ctx, quiet=True)

    if bar is not None:
        bar['value'] = 0.0
    if status_var is not None:
        status_var.set('Mencari lirik "%s"...' % title[:40])
    run_bg(ctx, work, on_done=on_done, on_progress=on_prog, on_error=on_err)


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
