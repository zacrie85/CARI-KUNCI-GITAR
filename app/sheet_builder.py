# -*- coding: utf-8 -*-
"""ChordKu - penyusun sheet lirik+chord dari hasil deteksi + lirik otomatis.

Cara kerja:
  - Lirik TERSINKRON (LRC, ada stempel waktu per baris) -> setiap baris
    lirik dipasangkan dengan chord yang berbunyi pada jendela waktunya;
    chord sebelum lirik pertama menjadi bagian "Intro :".
  - Lirik POLOS (tanpa waktu) -> chord dibagi rata mengikuti urutan baris.
  - Chord yang berulang berurutan diringkas jadi satu.

Hasilnya format sheet klasik: baris chord di atas baris liriknya,
langsung bisa ditranspos di tab Transposisi.
"""
from .lyrics import parse_lrc


def _dedupe_consecutive(seq):
    out = []
    for c in seq:
        if not out or c != out[-1]:
            out.append(c)
    return out


def _chunks(seq, size):
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def _place_chords(chords, lyric=''):
    """Susun nama chord di satu baris, tersebar kira-kira sepanjang lirik."""
    if not chords:
        return ''
    n = len(chords)
    if n == 1:
        return chords[0]
    widest = max(len(c) for c in chords)
    span = max(len(lyric or ''), (n - 1) * (widest + 2))
    cols = []
    for i, ch in enumerate(chords):
        col = int(round(i * span / float(n - 1)))
        if cols:
            col = max(col, cols[-1] + len(chords[i - 1]) + 1)
        cols.append(col)
    buf = [' '] * (cols[-1] + len(chords[-1]))
    for ch, col in zip(chords, cols):
        for j, cch in enumerate(ch):
            buf[col + j] = cch
    return ''.join(buf).rstrip()


def _header(title, key_root, lyrics_meta, notes):
    lines = ['%s (LIRIK OTOMATIS)' % (title or 'LAGU HASIL DETEKSI').upper()]
    if key_root:
        lines.append('Kunci Asli: %s' % key_root)
    if lyrics_meta:
        lines.append('Lirik: %s%s (lrclib.net)'
                     % (lyrics_meta.get('artist') or '(artis tak diketahui)',
                        (' - %s' % lyrics_meta['track'])
                        if lyrics_meta.get('track') else ''))
    for n in notes:
        lines.append(n)
    lines.append('')
    return lines


def _intro_lines(chords, label='Intro :'):
    """Chord pembuka menjadi 1+ baris, 8 chord per baris."""
    out = []
    for i, g in enumerate(_chunks(chords, 8)):
        out.append('%s %s' % (label, ' '.join(g)) if i == 0
                   else ' '.join(g))
    return out


def build_from_synced(title, key_root, segments, duration, lrc_lines,
                      lyrics_meta=None):
    """Align per baris lirik memakai stempel waktu LRC."""
    body = []
    first_t = lrc_lines[0][0]
    intro_chords = _dedupe_consecutive(
        [s[2] for s in segments if s[0] < first_t])
    body.extend(_intro_lines(intro_chords))
    if intro_chords:
        body.append('')

    for k, (t, txt) in enumerate(lrc_lines):
        t_next = lrc_lines[k + 1][0] if k + 1 < len(lrc_lines) \
            else (duration or 0) + 1.0
        chords = _dedupe_consecutive(
            [s[2] for s in segments if t <= s[0] < t_next])
        chord_line = _place_chords(chords, txt)
        body.append(chord_line)
        body.append(txt)

    return '\n'.join(_header(title, key_root, lyrics_meta,
                             ['(penempatan chord mengikuti waktu deteksi - '
                              'boleh digeser manual)'])
                     + body)


def build_from_plain(title, key_root, segments, plain_text,
                     lyrics_meta=None):
    """Lirik polos: chord dibagi rata mengikuti jumlah baris lirik."""
    lines = []
    for ln in (plain_text or '').splitlines():
        ln = ln.strip()
        if ln and not ln.startswith('['):
            lines.append(ln)
    if not lines:
        return None
    n_seg = len(segments)
    per_line = max(1, -(-n_seg // len(lines))) if n_seg else 0

    body = []
    for k, txt in enumerate(lines):
        segs = segments[k * per_line:(k + 1) * per_line] if per_line else []
        chords = _dedupe_consecutive([s[2] for s in segs])
        body.append(_place_chords(chords, txt))
        body.append(txt)

    return '\n'.join(_header(title, key_root, lyrics_meta,
                             ['(pembagian chord perkiraan - geser manual '
                              'bila perlu)'])
                     + body)


def build_sheet(title, key_root, segments, duration, lyrics):
    """Gabungkan hasil deteksi + lirik -> sheet siap transposisi.

    lyrics: dict {'plain', 'synced', 'track', 'artist'} atau None.
    Return str sheet, atau None bila lirik tidak ada.
    """
    if not lyrics:
        return None
    title = title or ''
    key_root = key_root or ''
    meta = lyrics if isinstance(lyrics, dict) else None
    segments = list(segments or [])

    synced = (meta or {}).get('synced')
    if synced:
        lrc = parse_lrc(synced)
        if lrc:
            sheet = build_from_synced(title, key_root, segments,
                                      duration, lrc, meta)
            if sheet:
                return sheet
    plain = (meta or {}).get('plain')
    if plain:
        return build_from_plain(title, key_root, segments, plain, meta)
    return None
