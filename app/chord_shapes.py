# -*- coding: utf-8 -*-
"""
ChordKu - database bentuk chord + perhitungan bentuk barre otomatis.

Format bentuk: string 6 karakter, urutan senar 6 (E rendah) -> 1 (e tinggi).
  '0' = senar dibuka (open), 'x' = senar tidak dipetik, digit = nomor fret.
Contoh: C = 'x32010'.
"""
import re

# --------------------------------------------------------------- database
OPEN_SHAPES = {
    # mayor
    'C': 'x32010', 'D': 'xx0232', 'E': '022100', 'F': '133211',
    'G': '320003', 'A': 'x02220', 'B': 'x24442',
    # minor
    'Am': 'x02210', 'Bm': 'x24432', 'Cm': 'x35543', 'Dm': 'xx0231',
    'Em': '022000', 'Fm': '133111', 'Gm': '355333',
    # dominant 7
    'C7': 'x32310', 'D7': 'xx0212', 'E7': '020100', 'F7': '131211',
    'G7': '320001', 'A7': 'x02020', 'B7': 'x21202',
    # minor 7
    'Dm7': 'xx0211', 'Em7': '020000', 'Fm7': '131111', 'Gm7': '353333',
    'Am7': 'x02010', 'Bm7': 'x24232',
    # mayor 7
    'Cmaj7': 'x32000', 'Dmaj7': 'xx0222', 'Emaj7': '021100',
    'Fmaj7': 'xx3210', 'Gmaj7': '320002', 'Amaj7': 'x02120',
    # sus2 / sus4
    'Asus2': 'x02200', 'Dsus2': 'xx0230',
    'Asus4': 'x02230', 'Dsus4': 'xx0233', 'Esus4': '022200',
    'Gsus4': '3x0013',
    # 6
    'C6': 'x32210', 'D6': 'xx0202', 'A6': 'x02222', 'Em6': '022020',
}

# penomoran jari (1 telunjuk .. 4 kelingking), urutan senar 6 -> 1,
# 0 = tidak ditekan. Hanya untuk bentuk yang penomorannya baku.
FINGERINGS = {
    'C': [0, 3, 2, 0, 1, 0],
    'D': [0, 0, 0, 1, 3, 2],
    'E': [0, 2, 3, 1, 0, 0],
    'G': [2, 1, 0, 0, 0, 3],
    'A': [0, 0, 2, 1, 3, 0],
    'Am': [0, 0, 2, 3, 1, 0],
    'Dm': [0, 0, 0, 2, 3, 1],
    'Em': [0, 2, 3, 0, 0, 0],
    'A7': [0, 0, 2, 0, 3, 0],
    'D7': [0, 0, 0, 2, 1, 3],
    'E7': [0, 2, 0, 1, 0, 0],
    'C7': [0, 3, 2, 4, 1, 0],
    'B7': [0, 2, 1, 3, 0, 4],
    'Am7': [0, 0, 2, 0, 1, 0],
    'Em7': [0, 2, 0, 0, 0, 0],
    'Cmaj7': [0, 3, 2, 0, 0, 0],
    'Fmaj7': [0, 0, 3, 2, 1, 0],
    'Gmaj7': [2, 1, 0, 0, 0, 3],
}

# ---------------------------------------------------------- templat barre
# offset fret relatif terhadap posisi barre (templet E & A yang bisa
# digeser ke nada root mana pun). None = senar tidak dipetik.
#   'E' = akar di senar 6 (bentuk E), 'A' = akar di senar 5 (bentuk A).
QUALITY_BARRE = {
    '': {'E': (0, 2, 2, 1, 0, 0), 'A': (None, 0, 2, 2, 2, 0)},
    'm': {'E': (0, 2, 2, 0, 0, 0), 'A': (None, 0, 2, 2, 1, 0)},
    '7': {'E': (0, 2, 0, 1, 0, 0), 'A': (None, 0, 2, 0, 2, 0)},
    'm7': {'E': (0, 2, 0, 0, 0, 0), 'A': (None, 0, 2, 0, 1, 0)},
    'maj7': {'E': (0, 2, 1, 1, 0, 0), 'A': (None, 0, 2, 1, 2, 0)},
    'sus4': {'E': (0, 2, 2, 2, 0, 0), 'A': (None, 0, 2, 2, 3, 0)},
    'sus2': {'A': (None, 0, 2, 2, 0, 0)},
    '6': {'E': (0, 2, 2, 1, 2, 0), 'A': (None, 0, 2, 2, 2, 2)},
    '5': {'E': (0, 2, 2, None, None, None),
          'A': (None, 0, 2, 2, None, None)},
}

NOTE_ORDER = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_TO_SHARP = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
SUFFIX_ALIAS = {'min': 'm', 'min7': 'm7', 'M7': 'maj7', 'maj': '',
                'sus': 'sus4', 'dom7': '7'}

_PARSE = re.compile(r'^([A-Ga-g][#b]?)([0-9A-Za-z]*(?:\+.*)?)$')


def _normalize_suffix(sfx):
    sfx = (sfx or '').strip()
    if sfx.startswith('add'):
        return None                       # bentuk tidak disediakan
    return SUFFIX_ALIAS.get(sfx, sfx)


def parse_chord_name(name):
    """
    'C#m7/G#' -> ('C#', 'm7'). Return None jika tidak bisa diparse.
    Slash chord: bagian sebelum '/' yang dipakai (bentuk dasar).
    """
    base = (name or '').strip().strip('(){}[],."\'!?')
    if '/' in base:
        base = base.split('/')[0]
    m = _PARSE.match(base)
    if not m:
        return None
    root = m.group(1)
    root = root[0].upper() + root[1:]
    root = FLAT_TO_SHARP.get(root, root)
    if root not in NOTE_ORDER:
        return None
    sfx = _normalize_suffix(m.group(2))
    if sfx is None or sfx not in QUALITY_BARRE:
        return None                      # dim/aug/9/add9/b5 dll: tanpa bentuk
    return root, sfx


def _shape_from_string(s):
    """'x32010' -> [-1, 3, 2, 0, 1, 0]."""
    out = []
    for ch in s:
        if ch == 'x':
            out.append(-1)
        elif ch == '0':
            out.append(0)
        else:
            out.append(int(ch))
    return out


def _barre_fingering(frets, barre_fret, span):
    """Jari: barre = 1, sisanya 2,3,4 berurutan dari senar 6."""
    fingers = [0] * 6
    lo, hi = span
    for i in range(lo - 1, hi):
        if frets[i] == barre_fret:
            fingers[i] = 1
    nxt = 2
    for i in range(6):
        if frets[i] > barre_fret and nxt <= 4:
            fingers[i] = nxt
            nxt += 1
    return fingers


def get_shape(name):
    """
    Cari bentuk chord. Return dict:
      name, frets (6 nilai: -1 mute, 0 open, n fret),
      base (fret paling atas yang ditampilkan),
      fingers (list 6 int, boleh None), barre ((fret, senar_awal, senar_akhir)
      atau None) -- atau None jika bentuk tidak tersedia.
    """
    parsed = parse_chord_name(name)
    if not parsed:
        return None
    root, sfx = parsed
    key = root + sfx

    if key in OPEN_SHAPES:
        frets = _shape_from_string(OPEN_SHAPES[key])
        played = [f for f in frets if f > 0]
        base = 1 if (not played or min(played) <= 2) else min(played)
        return {'name': name, 'frets': frets, 'base': base,
                'fingers': FINGERINGS.get(key), 'barre': None}

    # bentuk terbuka alternatif: key tanpa alias, mis. 'Cmin' -> 'Cm'
    alt = root + SUFFIX_ALIAS.get(sfx, sfx)
    if alt in OPEN_SHAPES:
        frets = _shape_from_string(OPEN_SHAPES[alt])
        played = [f for f in frets if f > 0]
        base = 1 if (not played or min(played) <= 2) else min(played)
        return {'name': name, 'frets': frets, 'base': base,
                'fingers': FINGERINGS.get(alt), 'barre': None}

    tmpl = QUALITY_BARRE.get(sfx)
    if not tmpl:
        return None
    ri = NOTE_ORDER.index(root)
    options = []
    if 'E' in tmpl:
        f = (ri - NOTE_ORDER.index('E')) % 12
        if f > 0:
            options.append((f, 'E', tmpl['E']))
    if 'A' in tmpl:
        f = (ri - NOTE_ORDER.index('A')) % 12
        if f > 0:
            options.append((f, 'A', tmpl['A']))
    if not options:
        return None
    # pilih posisi barre terendah (lebih mudah dimainkan)
    options.sort(key=lambda o: o[0])
    f, shape_kind, offsets = options[0]
    frets = []
    for off in offsets:
        if off is None:
            frets.append(-1)
        else:
            frets.append(f + off)
    zero_idx = [i + 1 for i, off in enumerate(offsets) if off == 0]
    span = (min(zero_idx), max(zero_idx)) if zero_idx else (1, 6)
    if shape_kind == 'E':
        span = (min(span[0], 1), max(span[1], 1))
    return {'name': name, 'frets': frets, 'base': f,
            'fingers': _barre_fingering(frets, f, span),
            'barre': (f, span[0], span[1])}
