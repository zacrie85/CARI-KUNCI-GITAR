# -*- coding: utf-8 -*-
"""ChordKu - tab YouTube: unduh audio (yt-dlp) + slot tool eksternal."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from . import downloader as dl
from .gui import PANEL, TEXT, MUTED, MONO, run_bg


def build(parent, ctx):
    ttk.Label(parent, text='Ambil audio lagu dari YouTube untuk dideteksi '
                           'chord-nya. Unduhan hanya untuk belajar musik '
                           '(penggunaan pribadi).',
              style='Muted.TLabel').pack(anchor='w', padx=12, pady=(10, 6))

    # ---------------------------------------------- unduhan bawaan
    top = ttk.LabelFrame(parent, text='  Unduhan bawaan (yt-dlp)  ')
    top.pack(fill='x', padx=12, pady=4)
    top.columnconfigure(1, weight=1)

    url_var = tk.StringVar(value=ctx.config.get('last_youtube_url', ''))
    ttk.Label(top, text='URL YouTube:').grid(row=0, column=0, sticky='w',
                                             padx=8, pady=8)
    ttk.Entry(top, textvariable=url_var).grid(row=0, column=1, sticky='ew',
                                              padx=4)
    ttk.Button(top, text='Cek Judul',
               command=lambda: _check_title(ctx, url_var)).grid(
        row=0, column=2, padx=4)

    prog_row = ttk.Frame(top)
    prog_row.grid(row=1, column=0, columnspan=3, sticky='ew', padx=8,
                  pady=(0, 4))
    bar = ttk.Progressbar(prog_row, maximum=1.0, value=0.0)
    bar.pack(side='left', fill='x', expand=True)
    status_var = tk.StringVar(value='')
    ttk.Label(prog_row, textvariable=status_var,
              style='PMuted.TLabel', width=48).pack(side='left', padx=(10, 0))

    act = ttk.Frame(top)
    act.grid(row=2, column=0, columnspan=3, sticky='ew', padx=8,
             pady=(0, 4))
    dl_btn = ttk.Button(act, text='Download Audio (MP3)',
                        style='Accent.TButton',
                        command=lambda: _download(ctx, url_var, bar,
                                                  status_var, dl_btn))
    dl_btn.pack(side='left')
    ttk.Button(act, text='Buka Folder Download',
               command=lambda: dl.open_folder(
                   ctx.config['download_dir'])).pack(side='left', padx=6)

    mode, _ = dl.find_ytdlp()
    ffmpeg = dl.find_ffmpeg()
    ydl_txt = ('yt-dlp: OK (siap dipakai)' if mode
               else 'yt-dlp BELUM TERPASANG — jalankan setup.bat atau '
                    '"pip install yt-dlp"')
    ff_txt = ('ffmpeg: OK (hasil otomatis MP3)' if ffmpeg
              else 'ffmpeg tidak ada — file tersimpan dalam format asli '
                   '(m4a/webm); deteksi memerlukan ffmpeg')
    ttk.Label(top, text=ydl_txt + '    |    ' + ff_txt,
              style='PMuted.TLabel',
              foreground='#B91C1C' if not mode else MUTED).grid(
        row=3, column=0, columnspan=3, sticky='w', padx=8, pady=(0, 8))

    # ---------------------------------------------- tool eksternal
    ext = ttk.LabelFrame(parent, text='  Tool eksternal (mis. Zac Downloader)  ')
    ext.pack(fill='x', padx=12, pady=8)
    ext.columnconfigure(1, weight=1)

    tool_var = tk.StringVar(value=ctx.config.get('external_tool_path', ''))
    ttk.Label(ext, text='Path tool:').grid(row=0, column=0, sticky='w',
                                           padx=8, pady=8)
    ttk.Entry(ext, textvariable=tool_var).grid(row=0, column=1, sticky='ew',
                                               padx=4)
    ttk.Button(ext, text='Pilih...',
               command=lambda: _choose_tool(ctx, tool_var)).grid(
        row=0, column=2, padx=4)
    row2 = ttk.Frame(ext)
    row2.grid(row=1, column=0, columnspan=3, sticky='w', padx=8, pady=(0, 8))
    ttk.Button(row2, text='Buka Tool Eksternal',
               command=lambda: _open_tool(ctx, tool_var)).pack(side='left')
    ttk.Button(row2, text='Muat File Terakhir ke Deteksi',
               command=lambda: _load_last(ctx)).pack(side='left', padx=6)

    hint = ('Zac Downloader adalah aplikasi tampilan terpisah, jadi alurnya '
            'begini:\n'
            '1. Klik "Pilih..." lalu arahkan ke Zac Downloader.exe di PC-mu.\n'
            '2. Klik "Buka Tool Eksternal" dan unduh video musik lewat tool '
            'itu.\n'
            '3. Kembali ke sini, klik "Muat File Terakhir ke Deteksi" — file '
            'hasil unduhan langsung masuk ke tab Deteksi Chord.')
    ttk.Label(ext, text=hint, style='PMuted.TLabel', justify='left').grid(
        row=2, column=0, columnspan=3, sticky='w', padx=8, pady=(0, 8))


def _check_title(ctx, url_var):
    url = url_var.get().strip()
    if not url:
        messagebox.showwarning('URL kosong', 'Tempel dulu tautan YouTube-nya.')
        return

    def work(prog):
        prog(0.5, 'Mengambil judul...')
        return dl.get_title(url)

    def on_done(title):
        if title:
            messagebox.showinfo('Judul video', title)
        else:
            messagebox.showwarning('Gagal',
                                   'Judul tidak bisa diambil. Periksa '
                                   'koneksi / tautan, atau perbarui '
                                   'yt-dlp: pip install -U yt-dlp')

    run_bg(ctx, work, on_done=on_done)


def _download(ctx, url_var, bar, status_var, button):
    url = url_var.get().strip()
    if not url.startswith('http'):
        messagebox.showwarning('URL tidak valid',
                               'Tempel tautan YouTube, mis:\n'
                               'https://www.youtube.com/watch?v=...')
        return

    def work(prog):
        path, title = dl.download_audio(url, ctx.config['download_dir'], prog)
        return path, title

    def on_prog(pct, msg):
        bar['value'] = pct
        status_var.set(msg)

    def on_done(res):
        bar['value'] = 1.0
        status_var.set('Selesai: %s' % os.path.basename(res[0]))
        button['state'] = 'normal'
        ctx.config['last_youtube_url'] = url_var.get().strip()
        ctx.save_cfg()
        if messagebox.askyesno('Unduhan selesai',
                               'File: %s\n\nMuat file ini ke tab Deteksi '
                               'Chord sekarang?' % os.path.basename(res[0])):
            ctx.refs['detect_path'].set(res[0])
            ctx.refs['notebook'].select(ctx.refs['tab_index']['detect'])

    def on_err(msg):
        bar['value'] = 0.0
        status_var.set('Gagal.')
        button['state'] = 'normal'
        messagebox.showerror('Unduhan gagal', msg)

    button['state'] = 'disabled'
    bar['value'] = 0.0
    status_var.set('Memulai unduhan...')
    run_bg(ctx, work, on_done=on_done, on_progress=on_prog, on_error=on_err)


def _choose_tool(ctx, tool_var):
    p = filedialog.askopenfilename(
        title='Pilih tool eksternal (mis. Zac Downloader.exe)',
        filetypes=[('Program', '*.exe'), ('Semua file', '*.*')])
    if p:
        tool_var.set(p)
        ctx.config['external_tool_path'] = p
        ctx.save_cfg()


def _open_tool(ctx, tool_var):
    try:
        dl.open_external_tool(tool_var.get().strip())
    except RuntimeError as e:
        messagebox.showerror('Tool eksternal', str(e))


def _load_last(ctx):
    path = dl.newest_audio_file(ctx.config['download_dir'])
    if not path:
        messagebox.showinfo('Tidak ada file',
                            'Belum ada file audio di folder download:\n%s'
                            % ctx.config['download_dir'])
        return
    ctx.refs['detect_path'].set(path)
    ctx.refs['notebook'].select(ctx.refs['tab_index']['detect'])
    messagebox.showinfo('Siap dideteksi',
                        'File dimuat ke tab Deteksi Chord:\n%s'
                        % os.path.basename(path))
