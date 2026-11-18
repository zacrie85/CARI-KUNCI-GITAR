# -*- coding: utf-8 -*-
"""ChordKu - tab YouTube: browser tersemat, pencarian, unduh, tool opsional."""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from . import downloader as dl
from . import yt_browser as ytb
from . import lyrics as lyr
from .gui import PANEL, MUTED, GOLD, run_bg


def build(parent, ctx):
    ttk.Label(parent, text='Jelajahi YouTube langsung dari aplikasi (browser '
                           'tersemat), cari musik, atau tempel URL — unduh '
                           'jadi MP3 hanya untuk belajar musik.',
              style='Muted.TLabel').pack(anchor='w', padx=12, pady=(10, 6))

    # url_var dibuat lebih awal agar bisa dipakai browser & pencarian
    url_var = tk.StringVar(value=ctx.config.get('last_youtube_url', ''))
    ctx.refs['yt_url_var'] = url_var  # v1.0.7: jalur Zac Downloader

    # ------------------------------------------ 1) browser tersemat
    br = ttk.LabelFrame(parent, text='  Browser YouTube — Zac Downloader '
                                     'tersemat (mesin WebView2/Edge)  ')
    br.pack(fill='x', padx=12, pady=(0, 4))
    br.columnconfigure(0, weight=1)

    row_b = ttk.Frame(br)
    row_b.grid(row=0, column=0, columnspan=2, sticky='ew', padx=8,
               pady=(8, 4))
    ttk.Button(row_b, text='Buka Browser YouTube', style='Accent.TButton',
               command=lambda: _open_browser(ctx, auto_var, br_status,
                                             url_var)).pack(side='left')
    ttk.Button(row_b, text='Buka YouTube di Browser Sistem',
               command=lambda: ytb.open_in_system_browser()).pack(
        side='left', padx=6)
    auto_var = tk.BooleanVar(value=True)
    ctx.refs['yt_auto_var'] = auto_var  # v1.0.7: jalur Zac Downloader
    ttk.Checkbutton(row_b, text='URL video otomatis masuk Unduhan Bawaan',
                    variable=auto_var).pack(side='left', padx=(12, 0))

    ok, note = ytb.webview_available()
    br_status = tk.StringVar(value=note)
    ctx.refs['yt_br_status'] = br_status  # v1.0.7: jalur Zac Downloader
    ttk.Label(br, textvariable=br_status, style='PMuted.TLabel',
              justify='left').grid(row=1, column=0, columnspan=2, sticky='w',
                                   padx=8)
    ttk.Label(br, text='Cara pakai: klik "Buka Browser YouTube", cari lagu '
                       'yang diinginkan, dan begitu halaman video terbuka '
                       'URL-nya otomatis terisi di kolom "URL YouTube" di '
                       'bawah — tinggal klik "Download Audio (MP3)".',
              style='PMuted.TLabel', justify='left').grid(
        row=2, column=0, columnspan=2, sticky='w', padx=8, pady=(0, 8))

    # ------------------------------------------ 2) pencarian terintegrasi
    search = ttk.LabelFrame(
        parent, text='  Cari musik di YouTube (pencarian terintegrasi)  ')
    search.pack(fill='both', expand=True, padx=12, pady=4)
    search.columnconfigure(0, weight=1)
    search.rowconfigure(1, weight=1)

    qrow = ttk.Frame(search)
    qrow.grid(row=0, column=0, sticky='ew', padx=8, pady=(8, 4))
    qrow.columnconfigure(0, weight=1)
    q_var = tk.StringVar()
    ent = ttk.Entry(qrow, textvariable=q_var)
    ent.grid(row=0, column=0, sticky='ew')
    ttk.Button(qrow, text='Cari', style='Accent.TButton',
               command=lambda: _search(ctx, q_var, tree, search_status,
                                       btn_use, btn_dl)).grid(
        row=0, column=1, padx=(6, 0))
    ent.bind('<Return>', lambda e: _search(ctx, q_var, tree, search_status,
                                           btn_use, btn_dl))

    cols = ('judul', 'channel', 'durasi')
    tree = ttk.Treeview(search, columns=cols, show='headings', height=5)
    tree.grid(row=1, column=0, sticky='nsew', padx=8)
    sb = ttk.Scrollbar(search, orient='vertical', command=tree.yview)
    sb.grid(row=1, column=1, sticky='ns', padx=(0, 8))
    tree.configure(yscrollcommand=sb.set)
    tree.heading('judul', text='Judul')
    tree.heading('channel', text='Channel')
    tree.heading('durasi', text='Durasi')
    tree.column('judul', width=330, anchor='w')
    tree.column('channel', width=150, anchor='w')
    tree.column('durasi', width=64, anchor='center')
    tree.tag_configure('odd', background=PANEL)
    tree.tag_configure('even', background='#22141C')

    search_status = tk.StringVar(value='Alternatif tanpa browser: ketik '
                                      'judul lagu / artis lalu klik "Cari". '
                                      'Klik-dua-kali hasil = langsung jadi '
                                      'URL unduhan.')
    ttk.Label(search, textvariable=search_status, style='PMuted.TLabel',
              justify='left').grid(row=2, column=0, sticky='w', padx=8,
                                   pady=(2, 0))

    brow = ttk.Frame(search)
    brow.grid(row=3, column=0, columnspan=2, sticky='ew', padx=8,
              pady=(4, 8))
    btn_use = ttk.Button(brow, text='Pakai URL Ini -> Unduhan Bawaan',
                         style='Red.TButton', state='disabled',
                         command=lambda: _use_selected(ctx, tree, url_var,
                                                       search_status))
    btn_use.pack(side='left')
    btn_dl = ttk.Button(brow, text='Download Langsung (MP3)',
                        style='Accent.TButton', state='disabled',
                        command=lambda: _dl_selected(ctx, tree, url_var,
                                                     search_status, bar,
                                                     status_var, dl_btn))
    btn_dl.pack(side='left', padx=6)
    tree.bind('<Double-1>', lambda e: _use_selected(ctx, tree, url_var,
                                                    search_status))
    ctx.refs['yt_search_tree'] = tree

    # ------------------------------------------ 3) unduhan bawaan
    top = ttk.LabelFrame(parent, text='  Unduhan bawaan (yt-dlp)  ')
    top.pack(fill='x', padx=12, pady=(8, 4))
    top.columnconfigure(1, weight=1)

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
    ff_txt = ('ffmpeg: OK (bundel di dalam aplikasi, hasil otomatis MP3)'
              if ffmpeg
              else 'ffmpeg tidak ada — file tersimpan dalam format asli; '
                   'deteksi memerlukan ffmpeg')
    ttk.Label(top, text=ydl_txt + '    |    ' + ff_txt,
              style='PMuted.TLabel',
              foreground='#FF6B81' if not mode else MUTED).grid(
        row=3, column=0, columnspan=3, sticky='w', padx=8, pady=(0, 8))

    # v1.0.7: status jalur Zac Downloader (URL/file masuk otomatis)
    ctx.refs['yt_zac_status'] = tk.StringVar(
        value='Jalur Zac Downloader: aktif — link & file dari Zac '
              'Downloader otomatis masuk ke sini.')
    ttk.Label(top, textvariable=ctx.refs['yt_zac_status'],
              style='PMuted.TLabel', foreground=GOLD).grid(
        row=4, column=0, columnspan=3, sticky='w', padx=8, pady=(0, 8))

    # ------------------------------------------ 4) tool eksternal
    ext = ttk.LabelFrame(parent,
                         text='  Tool eksternal (opsional, mis. Zac '
                              'Downloader)  ')
    ext.pack(fill='x', padx=12, pady=(4, 10))
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
    ttk.Label(ext, text='Kini browser + pencarian sudah ada di dalam '
                        'aplikasi (di atas), jadi tool eksternal hanya '
                        'cadangan.',
              style='PMuted.TLabel').grid(row=2, column=0, columnspan=3,
                                          sticky='w', padx=8, pady=(0, 8))

    if not mode:
        ent.configure(state='disabled')
        search_status.set('yt-dlp belum terpasang — pencarian nonaktif. '
                          'Jalankan setup.bat atau "pip install yt-dlp".')


# --------------------------------------------------------------- browser
def _apply_captured_url(ctx, url_var, status_var, auto_var, url):
    """URL dari browser tersemat -> kolom Unduhan Bawaan (thread Tk)."""
    url = (url or '').strip()
    if not url:
        return
    if auto_var.get():
        url_var.set(url)
        status_var.set('URL video masuk Unduhan Bawaan: %s' % url)
    else:
        status_var.set('Video terbuka (auto-isi mati): %s' % url)


def _open_browser(ctx, auto_var, status_var, url_var, start_url=None):
    def on_url(url):
        def apply():
            _apply_captured_url(ctx, url_var, status_var, auto_var, url)
        try:
            ctx.root.after(0, apply)
        except RuntimeError:
            pass  # jendela aplikasi sudah ditutup

    def on_status(text):
        try:
            ctx.root.after(0, lambda: status_var.set(text))
        except RuntimeError:
            pass

    try:
        ytb.open_browser(start_url=start_url, on_url=on_url,
                         on_status=on_status)
    except Exception as e:
        status_var.set('Gagal membuka browser: %s' % e)
        messagebox.showwarning(
            'Browser YouTube',
            str(e) + '\n\nAlternatif: klik "Buka YouTube di Browser '
                     'Sistem", lalu salin-tempel URL-nya ke Unduhan '
                     'Bawaan.')


# ------------------------------------------------------------- pencarian
def _search(ctx, q_var, tree, status_var, btn_use, btn_dl):
    query = q_var.get().strip()
    if not query:
        messagebox.showwarning('Kata kunci kosong',
                               'Ketik dulu judul lagu atau nama artisnya.')
        return

    def work(prog):
        prog(0.4, 'Mencari di YouTube...')
        return dl.search_youtube(query, limit=10)

    def on_done(results):
        for iid in tree.get_children():
            tree.delete(iid)
        for i, r in enumerate(results):
            tree.insert('', 'end', iid=str(i), values=(
                r['title'], r['uploader'], r['duration']),
                tags=('odd', 'even')[i % 2])
        _store_results(tree, results)
        status_var.set('%d hasil untuk "%s" — klik-dua-kali hasil untuk '
                       'mengisi URL Unduhan Bawaan.' % (len(results), query))
        btn_use['state'] = 'normal'
        btn_dl['state'] = 'normal'

    def on_err(msg):
        status_var.set('Pencarian gagal.')
        messagebox.showerror('Pencarian gagal', msg)

    status_var.set('Mencari "%s"...' % query)
    run_bg(ctx, work, on_done=on_done, on_error=on_err)


def ctx_results(tree):
    # hasil pencarian disimpan di atribut widget agar aman dibawa bersama
    return getattr(tree, '_yt_results', [])


def _store_results(tree, results):
    tree._yt_results = results


def _selected_url(tree):
    results = ctx_results(tree)
    sel = tree.selection()
    if not sel or not results:
        return None
    idx = int(sel[0])
    return results[idx]['url'] if idx < len(results) else None


def _use_selected(ctx, tree, url_var, status_var):
    url = _selected_url(tree)
    if not url:
        messagebox.showinfo('Pilih hasil', 'Pilih dulu salah satu hasil '
                            'pencarian di daftar.')
        return
    url_var.set(url)
    status_var.set('URL dimuat ke kolom "URL YouTube" di bagian Unduhan '
                   'Bawaan — klik "Download Audio (MP3)" bila ingin langsung '
                   'mengunduh.')


def _dl_selected(ctx, tree, url_var, status_var, bar, dl_status, dl_btn):
    url = _selected_url(tree)
    if not url:
        messagebox.showinfo('Pilih hasil', 'Pilih dulu salah satu hasil '
                            'pencarian di daftar.')
        return
    url_var.set(url)
    _download(ctx, url_var, bar, dl_status, dl_btn)


# --------------------------------------------------------------- unduhan
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
            judul = ctx.refs.get('detect_judul')
            if judul is not None:
                judul.set(lyr.parse_title_from_filename(
                    res[1] or res[0]))
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


# ------------------------------------------------------------- eksternal
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
    judul = ctx.refs.get('detect_judul')
    if judul is not None:
        judul.set(lyr.parse_title_from_filename(path))
    ctx.refs['notebook'].select(ctx.refs['tab_index']['detect'])
    messagebox.showinfo('Siap dideteksi',
                        'File dimuat ke tab Deteksi Chord:\n%s'
                        % os.path.basename(path))
