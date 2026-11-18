# -*- coding: utf-8 -*-
"""ChordKu - data contoh lagu & kamus jari chord dasar."""

# Contoh lagu untuk demo transposisi.
# Chord diambil dari chordtela.com (cuplikan, kunci asli C).
SAMPLE_PUJAAN_HATI = """PUJAAN HATI - KANGEN BAND
Kunci Asli: C
(Sumber chord: chordtela.com - cuplikan untuk demo transposisi)

Intro : C G Am Em F C Dm G C G

C        G
hei pujaan hati.. apa kabarmu
Am         Em
ku harap.. kau baik-baik saja
F        C
pujaan hati.. andai kau tahu
Dm        G
ku sangat.. mencintai dirimu

Musik : C G Am Em F C D G

C        G
hei pujaan hati.. setiap malam
Am         Em
aku berdoa kepada sang Tuhan
F        C
berharap cintaku jadi kenyataan
Dm        G
agar ku tenang meniti kehidupan..

Reff:
C      G
hei pujaan hati.. apa kabarmu
Am         Em
ku harap.. kau baik-baik saja
F        C
pujaan hati.. andai kau tahu
Dm        G
ku sangat.. mencintai dirimu

C     G
pujaan hati.. setiap malam
Am       Em
aku berdoa kepada sang Tuhan
F        C
berharap cintaku jadi kenyataan
Dm          G          C
agar ku tenang meniti kehidupan..
"""

SAMPLE_SONGS = {
    'Pujaan Hati - Kangen Band (Kunci C)': SAMPLE_PUJAAN_HATI,
}

# ------------------------------------------------------------- kamus jari
# Format: string 6 digit, urutan senar low-E A D G B e.
# 'x' = senar tidak dibunyikan, angka = posisi fret.
FINGERINGS = {
    # Mayor
    'C': 'x32010', 'D': 'xx0232', 'E': '022100', 'F': '133211',
    'G': '320003', 'A': 'x02220', 'B': 'x24442',
    'Db': 'x46664', 'Eb': 'xx1343', 'Gb': '244322', 'Ab': '466544', 'Bb': 'x13331',
    # Minor
    'Am': 'x02210', 'Bm': 'x24432', 'Cm': 'x35543', 'Dm': 'xx0231',
    'Em': '022000', 'Fm': '133111', 'Gm': '355333',
    'C#m': 'x46654', 'F#m': '244222', 'Bbm': 'x13321', 'G#m': '466444',
    # Dominan 7
    'A7': 'x02020', 'B7': 'x21202', 'C7': 'x32310', 'D7': 'xx0212',
    'E7': '020100', 'G7': '320001',
    # Minor 7 & major 7 umum
    'Am7': 'x02010', 'Bm7': 'x20202', 'Dm7': 'xx0211', 'Em7': '022030',
    'Cmaj7': 'x32000', 'Fmaj7': 'xx3210', 'Gmaj7': '320002',
    # Sus
    'Asus4': 'x02230', 'Asus2': 'x02200', 'Dsus4': 'xx0233', 'Dsus2': 'xx0230',
}

_ENHARMONIC = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}


def get_fingering(chord_name):
    """Kembalikan pola jari (mis. 'x32010') atau None bila belum ada di kamus."""
    from . import transposer as tr
    parsed = tr.parse_chord(chord_name.strip())
    if parsed is None:
        return None
    root, suffix, _ = parsed
    # Suffix disederhanakan ke kualitas yang ada di kamus
    s = suffix
    if s in ('maj7', 'M7'):
        q = 'maj7'
    elif s in ('m7', 'min7'):
        q = 'm7'
    elif s in ('maj', 'M'):
        q = ''
    elif s.startswith('sus2'):
        q = 'sus2'
    elif s.startswith('sus'):
        q = 'sus4'
    elif s.startswith('m') and not s.startswith('maj'):
        q = 'm'
    elif s == '':
        q = ''
    elif s in ('7',):
        q = '7'
    else:
        q = None
    if q is None:
        return None
    cand = [root + q, _ENHARMONIC.get(root, root) + q]
    for c in cand:
        if c in FINGERINGS:
            return FINGERINGS[c]
    return None


def fingering_text(chord_name):
    f = get_fingering(chord_name)
    if not f:
        return '%-8s : (belum ada di kamus)' % chord_name
    strings = ['E', 'A', 'D', 'G', 'B', 'e']
    parts = []
    for s_name, ch in zip(strings, f):
        if ch == 'x':
            parts.append('%s:x' % s_name)
        elif ch == '0':
            parts.append('%s:0' % s_name)
        else:
            parts.append('%s:fret%s' % (s_name, ch))
    return '%-8s : %s  (%s)' % (chord_name, f, ', '.join(parts))
