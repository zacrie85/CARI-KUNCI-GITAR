# -*- coding: utf-8 -*-
"""
ChordKu - browser YouTube tersemat (ala Zac Downloader).

Membuka jendela browser sungguhan (mesin WebView2/Edge bawaan
Windows 10-11) di dalam lingkungan ChordKu lewat pywebview. Setiap
kali pengguna membuka sebuah video di browser itu, URL-nya dikirim
kembali ke aplikasi sehingga kolom "URL YouTube" di Unduhan Bawaan
terisi otomatis.

Dua jalur pengiriman URL (saling melengkapi):
  1. Event navigasi selesai (window.events.loaded) -> get_current_url.
  2. Hook JavaScript pada history.pushState/popstate -> pywebview.api.
Pola URL yang dianggap video: 'watch?v=' dan 'youtu.be/'.
"""
import threading

WATCH_PATTERNS = ('watch?v=', 'youtu.be/')
DEFAULT_START = 'https://www.youtube.com'


def webview_available():
    """Cek pywebview. Return (bool, pesan_penjelasan)."""
    try:
        import webview  # noqa
        return True, 'WebView2/pywebview tersedia.'
    except ImportError:
        return False, ('pywebview belum terpasang. Di exe resmi ChordKu '
                       'sudah ter-bundle; dari kode sumber jalankan: '
                       'pip install pywebview')


def is_watch_url(url):
    """True bila URL tampaknya halaman video (watch?v= / youtu.be/)."""
    u = (url or '').lower()
    return any(p in u for p in WATCH_PATTERNS)


class YouTubeBrowser(object):
    """
    Kelola satu jendela browser YouTube.

    on_url(url)      -> dipanggil dari thread webview saat video dibuka.
    on_status(text)  -> info status (juga dari thread webview).
    Callback wajib memarshal sendiri ke thread Tk (root.after).
    """

    def __init__(self):
        self.window = None
        self._lock = threading.Lock()
        self.on_url = None
        self.on_status = None

    def _notify(self, text):
        if self.on_status:
            try:
                self.on_status(text)
            except Exception:
                pass

    def _report(self, url):
        """Terima URL hasil navigasi/hook JS; saring lalu teruskan."""
        if not url or not is_watch_url(url):
            return
        self._notify('Video terbuka di browser: %s' % url)
        if self.on_url:
            try:
                self.on_url(url)
            except Exception:
                pass

    # ---------------- jembatan JavaScript (pywebview js_api) --------------
    class _Api(object):
        """Objek yang diekspos ke JS sebagai pywebview.api."""

        def __init__(self, owner):
            self._owner = owner

        def note_url(self, url=None):
            self._owner._report(url)
            return 'ok'

        def ping(self):
            return 'chordku'

    # ------------------------------------------------------------------
    _HOOK_JS = (
        "(function(){"
        " if (window.__chordku_hook) {"
        "   try { pywebview.api.note_url(location.href); } catch (e) {}"
        "   return 'hooked';"
        " }"
        " function report(u){"
        "   if (!u) return;"
        "   try { pywebview.api.note_url(u); } catch (e) {}"
        " }"
        " var ps = history.pushState;"
        " history.pushState = function(s, t, u){"
        "   ps.apply(history, arguments);"
        "   report(u ? location.origin + u : location.href);"
        " };"
        " window.addEventListener('popstate', function(){"
        "   report(location.href); });"
        " window.__chordku_hook = true;"
        " report(location.href);"
        " return 'hooked';"
        "})()"
    )

    def _on_loaded(self):
        """Event navigasi selesai: saring URL & pasang hook JS."""
        try:
            url = self.window.get_current_url()
        except Exception:
            url = None
        if url:
            self._report(url)
        try:
            self.window.evaluate_js(self._HOOK_JS)
        except Exception:
            pass  # halaman tanpa history API / js belum siap

    def open(self, start_url=DEFAULT_START, on_url=None, on_status=None):
        """
        Buka browser YouTube. Aman dipanggil berkali-kali: event loop
        webview hanya dijalankan sekali; jendela baru ditambahkan ke
        loop yang sudah berjalan.
        """
        ok, note = webview_available()
        if not ok:
            raise RuntimeError(note)
        import webview
        global _LOOP_STARTED

        with self._lock:
            self.on_url = on_url
            self.on_status = on_status
            if self.window is not None:
                # v1.0.7: pakai ulang jendela yang sudah terbuka —
                # navigasi ke URL baru (jembatan Zac Downloader) alih-
                # alih menumpuk jendela baru.
                try:
                    self.window.load_url(start_url or DEFAULT_START)
                    self._notify('Browser YouTube pindah ke: %s'
                                 % (start_url or DEFAULT_START))
                except Exception:
                    pass
                return self.window
            api = YouTubeBrowser._Api(self)
            self.window = webview.create_window(
                'Browser YouTube - ChordKu (Zac Downloader tersemat)',
                start_url or DEFAULT_START,
                js_api=api, width=1080, height=720,
                min_size=(720, 480))
            self.window.events.loaded += self._on_loaded

            if not _LOOP_STARTED:
                _LOOP_STARTED = True
                threading.Thread(
                    target=webview.start,
                    kwargs={'block': True, 'private_mode': False,
                            'gui': None},
                    daemon=True).start()
        self._notify('Browser YouTube dibuka. Buka video musiknya — '
                     'URL otomatis dikirim ke ChordKu.')
        return self.window


_BROWSER = None
_LOOP_STARTED = False


def open_browser(start_url=DEFAULT_START, on_url=None, on_status=None):
    """Singleton: satu browser untuk seluruh aplikasi."""
    global _BROWSER
    if _BROWSER is None:
        _BROWSER = YouTubeBrowser()
    return _BROWSER.open(start_url=start_url, on_url=on_url,
                         on_status=on_status)


def open_in_system_browser(url=DEFAULT_START):
    """Fallback: buka YouTube di browser bawaan Windows (Edge/Chrome)."""
    import webbrowser
    webbrowser.open(url or DEFAULT_START)
