# -*- coding: utf-8 -*-
"""ChordKu - pengambil lirik otomatis dari lrclib.net (API publik gratis).

Lirik diambil saat aplikasi berjalan (on the fly) untuk penggunaan
pribadi; aplikasi TIDAK membawa file lirik apa pun di dalam paketnya.
Sumber: https://lrclib.net/api - tanpa kunci API, format JSON.
"""
import json
import os
import re
import urllib.parse
import urllib.request

UA = 'ChordKu/1.0 (pemutar chord pribadi; penggunaan pribadi)'
_TIMEOUT = 25

# kata/susunan yang biasanya bukan judul lagu dalam nama file
_NOISE_RE = re.compile(
    r'\((?:official\s+(?:video|music\s*video|audio|visualizer|lyric'
    r'(?:\s*video)?)|lyric(?:\s*video)?s?|lirik|mv|hd|4k|hq|audio|video|'
    r'live|full\s*album|visualizer)\)'
    r'|\[[^\]]*\]'
    r'|\b(?:official\s*video|official\s*audio|lyrics?\s*video|lyrics?|'
    r'lirik|yt5s?|youtu(?:\.?be)?|www\.|full\s*album|hq|hd|4k|mp3|mp4|'
    r'download|\d{3,4}p)\b',
    re.IGNORECASE)


def parse_title_from_filename(path):
    """'Lagu - Artis (Official Video).mp3' -> 'Lagu - Artis'."""
    name = os.path.basename(str(path))
    name = os.path.splitext(name)[0]
    name = _NOISE_RE.sub(' ', name)
    name = re.sub(r'[-_\u2013\u2014]{2,}', '-', name)
    name = re.sub(r'[_]+', ' ', name)
    name = re.sub(r'\s{2,}', ' ', name).strip(' -_\u2013\u2014.')
    return name


def split_artist_title(name):
    """'Artis - Judul' -> ('Artis', 'Judul'); tanpa pemisah -> ('', name)."""
    for sep in (' - ', ' \u2013 ', ' \u2014 '):
        if sep in name:
            a, t = name.split(sep, 1)
            if a.strip() and t.strip():
                return a.strip(), t.strip()
    return '', name.strip()


def _fetch_json(url, timeout=_TIMEOUT):
    """GET JSON; kembalikan None bila gagal (jaringan/HTTP)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8', 'replace'))
    except Exception:  # noqa (URLError, HTTPError, timeout, JSON)
        return None


def _score(hit, title, artist):
    t = (hit.get('trackName') or '').lower().strip()
    a = (hit.get('artistName') or '').lower().strip()
    tl = (title or '').lower().strip()
    al = (artist or '').lower().strip()
    s = 0
    if tl and tl == t:
        s += 4
    elif tl and (tl in t or t in tl):
        s += 2
    if al and (al in a or a in al):
        s += 2
    if hit.get('syncedLyrics'):
        s += 2
    if hit.get('plainLyrics'):
        s += 1
    if hit.get('instrumental'):
        s -= 3
    for bad in ('karaoke', 'instrumental', 'cover version', 'akustik remix'):
        if bad in t or bad in a:
            s -= 2
    return s


def search_lyrics(title, artist='', timeout=_TIMEOUT):
    """Cari lirik di lrclib.net.

    Return {'track', 'artist', 'plain', 'synced'} untuk hasil terbaik,
    atau None bila tidak ada/tidak terhubung. `artist` boleh kosong.
    """
    if not title or not title.strip():
        return None
    title = title.strip()
    artist = (artist or '').strip()
    queries = []
    base = 'https://lrclib.net/api/search?'
    if artist:
        queries.append(base + urllib.parse.urlencode(
            {'track_name': title, 'artist_name': artist}))
    queries.append(base + urllib.parse.urlencode({'track_name': title}))
    queries.append(base + urllib.parse.urlencode({'q': title}))

    best, best_score = None, 0
    seen_ids = set()
    for url in queries:
        try:
            hits = _fetch_json(url, timeout=timeout)
        except Exception:  # noqa - kegagalan jaringan = tidak ada hasil
            hits = None
        if not isinstance(hits, list):
            continue
        for hit in hits:
            if not isinstance(hit, dict) or hit.get('id') in seen_ids:
                continue
            seen_ids.add(hit.get('id'))
            if not (hit.get('plainLyrics') or hit.get('syncedLyrics')):
                continue
            sc = _score(hit, title, artist)
            if sc > best_score:
                best, best_score = hit, sc
        if best and best_score >= 6:
            break  # hasil bagus, tak perlu query lanjutan
    if best is None or best_score < 2:
        return None
    return {'track': best.get('trackName') or title,
            'artist': best.get('artistName') or '',
            'plain': (best.get('plainLyrics') or '').strip() or None,
            'synced': (best.get('syncedLyrics') or '').strip() or None}


_LRC_RE = re.compile(r'^\[(\d+):(\d+(?:[.,]\d+)?)\](.*)$')


def parse_lrc(lrc_text):
    """LRC (Lirik tersinkron) -> [(detik, baris lirik)] terurut."""
    out = []
    for ln in (lrc_text or '').splitlines():
        m = _LRC_RE.match(ln.strip())
        if not m:
            continue
        t = int(m.group(1)) * 60.0 + float(m.group(2).replace(',', '.'))
        txt = m.group(3).strip()
        if txt:
            out.append((t, txt))
    out.sort(key=lambda x: x[0])
    return out
