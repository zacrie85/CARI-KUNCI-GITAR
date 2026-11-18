# -*- coding: utf-8 -*-
"""
ChordKu - Pengunduh audio dari YouTube.

Dua jalur:
  1. Bawaan: yt-dlp (pustaka Python) -> unduh audio + konversi MP3 via ffmpeg.
  2. Tool eksternal: mis. "Zac Downloader" yang terpasang di PC pengguna.
     Aplikasi menyimpan path tool-nya di konfigurasi, membukanya langsung,
     lalu pengguna memuat file hasil unduhan ke tab Deteksi secara manual.

Catatan: hak cipta musik di YouTube tetap milik pemiliknya. Gunakan
pengunduhan ini hanya untuk penggunaan pribadi (belajar chord).
"""
import os
import shutil
import subprocess

AUDIO_EXTS = ('.mp3', '.m4a', '.wav', '.flac', '.ogg', '.opus', '.webm',
              '.mp4', '.aac')


def find_ytdlp():
    """Return (mode, modul/path) atau (None, pesan) bila belum terpasang."""
    try:
        import yt_dlp
        return 'lib', yt_dlp
    except ImportError:
        pass
    exe = shutil.which('yt-dlp')
    if exe:
        return 'cli', exe
    return None, 'yt-dlp belum terpasang. Install: pip install yt-dlp'


def find_ffmpeg():
    from .detector import find_ffmpeg as _f
    return _f()


def get_title(url):
    """Ambil judul video tanpa mengunduh. None bila gagal."""
    mode, ydl = find_ytdlp()
    if mode == 'lib':
        try:
            with ydl.YoutubeDL({'quiet': True, 'no_warnings': True,
                                'noplaylist': True,
                                'skip_download': True}) as y:
                info = y.extract_info(url, download=False)
                return info.get('title') if info else None
        except Exception:
            return None
    return None


def _progress_hook(cb):
    def hook(d):
        if not cb:
            return
        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            done = d.get('downloaded_bytes', 0)
            pct = done / total if total else 0
            cb(pct * 0.95, 'Mengunduh: %s' % d.get('filename', ''))
        elif status == 'finished':
            cb(0.96, 'Mengonversi ke MP3 (ffmpeg)...')
    return hook


def download_audio(url, out_dir, progress_cb=None):
    """
    Unduh audio dari URL YouTube -> file MP3 di out_dir.
    Return (path_file, judul). Melempar Exception dengan pesan Indonesia.
    """
    mode, ydl = find_ytdlp()
    if mode is None:
        raise RuntimeError(ydl)
    os.makedirs(out_dir, exist_ok=True)
    ffmpeg = find_ffmpeg()

    outtmpl = os.path.join(out_dir, '%(title)s.%(ext)s')
    if mode == 'lib':
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [_progress_hook(progress_cb)],
        }
        if ffmpeg:
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        try:
            with ydl.YoutubeDL(opts) as y:
                info = y.extract_info(url, download=True)
                title = info.get('title') if info else None
        except Exception as e:
            raise RuntimeError('Gagal mengunduh: %s' % str(e)[:300])
    else:
        cmd = [ydl, '-x' if ffmpeg else '-f', 'bestaudio/best', '-o', outtmpl,
               '--no-playlist', url]
        if ffmpeg:
            cmd = [ydl, '-x', '--audio-format', 'mp3', '-o', outtmpl,
                   '--no-playlist', url]
        res = subprocess.run(cmd, capture_output=True, timeout=3600)
        if res.returncode != 0:
            raise RuntimeError('yt-dlp gagal: %s' %
                               res.stderr.decode(errors='ignore')[:300])
        title = None

    path = newest_audio_file(out_dir, after=None)
    if not path:
        raise RuntimeError('Unduhan selesai tapi file audio tidak ditemukan.')
    if progress_cb:
        progress_cb(1.0, 'Selesai: %s' % os.path.basename(path))
    return path, title


def newest_audio_file(folder, after=None):
    """File audio terbaru di folder (opsional: setelah timestamp)."""
    best, best_mtime = None, -1
    try:
        for name in os.listdir(folder):
            p = os.path.join(folder, name)
            if os.path.isfile(p) and name.lower().endswith(AUDIO_EXTS):
                m = os.path.getmtime(p)
                if m > best_mtime and (after is None or m > after):
                    best, best_mtime = p, m
    except OSError:
        pass
    return best


def open_external_tool(tool_path):
    """Buka tool eksternal (mis. Zac Downloader.exe) sebagai proses baru."""
    if not tool_path or not os.path.isfile(tool_path):
        raise RuntimeError('Path tool eksternal tidak valid: %r' % tool_path)
    return subprocess.Popen([tool_path], cwd=os.path.dirname(tool_path))


def open_folder(path):
    """Buka folder di file explorer (Windows/Linux)."""
    os.makedirs(path, exist_ok=True)
    try:
        if os.name == 'nt':
            os.startfile(path)          # noqa (khusus Windows)
        elif shutil.which('xdg-open'):
            subprocess.Popen(['xdg-open', path])
        elif shutil.which('open'):
            subprocess.Popen(['open', path])
    except Exception:
        pass
