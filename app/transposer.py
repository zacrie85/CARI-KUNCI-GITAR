# -*- coding: utf-8 -*-
"""
ChordKu - Engine transposisi chord.
Menggeser seluruh chord dalam sebuah lagu ke kunci lain (mis. C -> D),
menampilkan semua versi kunci alternatif, dan memberi saran capo.

Format sheet yang didukung:
  - Baris chord murni:      "Intro : C G Am Em F C Dm G"
  - Chord inline + lirik:   "C G hei pujaan hati.. apa kabarmu"
  - Chord di atas lirik:    dua baris (baris chord lalu baris lirik)
Token yang TIDAK dikenali sebagai chord (kata lirik seperti "Aku",
"Cinta", "Bagai") dibiarkan apa adanya.
"""
import re

# ---------------------------------------------------------------- konstanta
SHARP_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FLAT_NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
# Kunci yang lazim ditulis pakai mol (F, Bb, Eb, Ab, Db, Gb)
FLAT_PREFERRED = {5, 1, 3, 6, 8, 10}

NOTE_RE = re.compile(r'^([A-G])([#b]?)$')
# Root + suffix kualitas chord + opsional bass note (slash chord).
# Suffix hanya boleh terdiri dari atom kualitas chord, supaya kata lirik
# seperti "Aku" / "Bagai" / "Cinta" tidak dianggap chord.
CHORD_RE = re.compile(
    r'^([A-G][#b]?)'
    r'((?:maj|min|dim|aug|sus|add|alt|m|M|\d|#|b|\+|\-|\u00b0|\u00ba|\u00f8|\^)*)'
    r'(?:/([A-G][#b]?))?$'
)
PUNCT_CHARS = '(){}[],."\'\u201c\u201d\u2018\u2019:;!?*-'
_TOKEN_SPLIT = re.compile(r'(\s+)')

KEY_DISPLAY = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F', 'F#/Gb', 'G',
               'G#/Ab', 'A', 'A#/Bb', 'B']

# ---------------------------------------------------------------- dasar nada
def note_to_pc(name):
    """Nama nada -> pitch class 0-11 (C=0). None jika tidak valid."""
    if not name:
        return None
    m = NOTE_RE.match(name.strip())
    if not m:
        m2 = re.match(r'^([A-Ga-g])([#b]?)$', name.strip())
        if not m2:
            return None
        letter, acc = m2.group(1).upper(), m2.group(2)
    else:
        letter, acc = m.group(1), m.group(2)
    base = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[letter]
    acc_val = 1 if acc == '#' else (-1 if acc == 'b' else 0)
    return (base + acc_val) % 12


def pc_to_name(pc, use_flats=False):
    names = FLAT_NAMES if use_flats else SHARP_NAMES
    return names[pc % 12]


def key_to_pc(key_name):
    """'D#/Eb' / 'Bb' / 'Am' -> pitch class root kunci. None jika tidak valid."""
    if not key_name:
        return None
    head = key_name.strip().split('/')[0].strip()
    head = re.sub(r'(m|min|maj)\d*$', '', head,
                  flags=re.IGNORECASE) if len(head) > 2 else head
    if head and head[-1].lower() == 'm' and len(head) >= 2 and head[-2] in '#b':
        head = head[:-1]
    elif head.endswith('m'):
        head = head[:-1]
    return note_to_pc(head)


def use_flats_for(key_pc):
    return key_pc % 12 in FLAT_PREFERRED

# ---------------------------------------------------------------- chord
def parse_chord(token):
    """Token -> (root, suffix, bass) atau None bukan chord.

    Chord huruf kecil DENGAN suffix kualitas juga diterima (am, em7,
    f#m, cmaj7, b7...). Satu huruf kecil polos ('a', 'c', 'e') tetap
    dianggap lirik supaya kata seperti itu tidak salah geser."""
    t = token.strip()
    if not t or t.upper() in ('N.C.', 'NC', 'N/C'):
        return None
    m = CHORD_RE.match(t)
    if m:
        return m.group(1), m.group(2) or '', m.group(3)
    if t[0] in 'abcdefg' and len(t) >= 2:
        m2 = CHORD_RE.match(t[0].upper() + t[1:])
        if m2 and m2.group(2):
            return m2.group(1), m2.group(2) or '', m2.group(3)
    return None


def has_any_chord(text):
    """True bila sheet memuat minimal satu chord yang dikenali."""
    for line in text.splitlines():
        for tok in line.split():
            if parse_chord(tok.strip(PUNCT_CHARS)):
                return True
    return False


# ---- deteksi baris chord (untuk chord huruf kecil polos, gaya WA) ----
_STRUCTURAL_WORDS = {'intro', 'reff', 'chorus', 'verse', 'musik',
                     'interlude', 'intermek', 'solo', 'bridge', 'coda',
                     'adlib', 'outro', 'end', 'kunci', 'asli', 'asal',
                     'modulasi', 'n.c.', 'nc'}
_SINGLE_LOW = re.compile(r'^([a-g])$')


def _is_structural(tok):
    core = tok.strip(PUNCT_CHARS).lower()
    return (not core) or core in _STRUCTURAL_WORDS


def _looks_like_chord_line(line):
    """True bila baris tampak sebagai BARIS CHORD: memuat >= 1 chord
    dikenali dan tidak ada kata lirik panjang. Dipakai supaya chord
    huruf kecil polos ('intro : am g c f') tetap digeser, sementara
    kata lirik seperti 'g' di tengah kalimat tetap aman."""
    toks = [t for t in line.split() if t.strip()]
    if not toks:
        return False
    n_strict = 0
    for t in toks:
        if parse_chord(t):
            n_strict += 1
        elif not _is_structural(t) and not _SINGLE_LOW.match(t):
            return False
    return n_strict >= 1


def transpose_chord_name(chord, semitones, use_flats=False):
    """'G/B' + 2 -> 'A/C#'."""
    parsed = parse_chord(chord)
    if parsed is None:
        return chord
    root, suffix, bass = parsed
    rpc = note_to_pc(root)
    new_root = pc_to_name((rpc + semitones) % 12, use_flats)
    out = new_root + suffix
    if bass:
        bpc = note_to_pc(bass)
        out += '/' + pc_to_name((bpc + semitones) % 12, use_flats)
    return out


def _transpose_token(token, semitones, use_flats, aggressive=False):
    """Transpose token bila chord; pertahankan tanda baca di sekelilingnya.
    Mode agresif (baris chord) juga menerima huruf kecil polos 'g' -> 'A'."""
    pre, core, post = '', token, ''
    stripped = token.strip(PUNCT_CHARS)
    if stripped and (token != stripped):
        idx = token.find(stripped)
        pre, core, post = token[:idx], stripped, token[idx + len(stripped):]
    if parse_chord(core) is None:
        if aggressive:
            m = _SINGLE_LOW.match(core)
            if m:
                return (pre + transpose_chord_name(core.upper(), semitones,
                                                   use_flats) + post)
        return token
    return pre + transpose_chord_name(core, semitones, use_flats) + post


def transpose_line(line, semitones, use_flats=False, aggressive=None):
    if aggressive is None:
        aggressive = _looks_like_chord_line(line)
    parts = _TOKEN_SPLIT.split(line)
    return ''.join(
        p if not p.strip() else
        _transpose_token(p, semitones, use_flats, aggressive)
        for p in parts
    )


def transpose_sheet(text, semitones, use_flats=False):
    """Transpose seluruh teks sheet chord. Semitones boleh negatif."""
    out_lines = []
    for line in text.splitlines():
        out_lines.append(transpose_line(line, semitones, use_flats)
                         if line.strip() else line)
    return '\n'.join(out_lines)


def shift_between_keys(from_key, to_key):
    """Jumlah semitone naik dari kunci asal ke kunci tujuan (-6..+6, dibulatkan)."""
    a, b = key_to_pc(from_key), key_to_pc(to_key)
    if a is None or b is None:
        raise ValueError('Kunci tidak dikenali: %r -> %r' % (from_key, to_key))
    s = (b - a) % 12
    return s - 12 if s > 6 else s


def transpose_sheet_by_key(text, from_key, to_key):
    """C + D -> semitones=+2; notasi (#/b) mengikuti kunci tujuan."""
    semis = shift_between_keys(from_key, to_key)
    flats = use_flats_for(key_to_pc(to_key))
    new_text = transpose_sheet(text, semis, flats)
    return new_text, semis, flats


def guess_sheet_key(text):
    """Penduga kunci asal sederhana: chord pertama pada sheet."""
    for line in text.splitlines():
        for tok in line.split():
            core = tok.strip(PUNCT_CHARS)
            parsed = parse_chord(core)
            if parsed:
                root, suffix, _ = parsed
                return root + ('m' if suffix.startswith('m') and
                               not suffix.startswith('maj') else '')
    return None

# ---------------------------------------------------------------- capo
EASY_MAJOR = {0: ('C', 3), 2: ('D', 3), 4: ('E', 3), 7: ('G', 3),
              9: ('A', 3), 5: ('F', 2), 11: ('B', 1)}
EASY_MINOR = {9: ('Am', 3), 4: ('Em', 3), 2: ('Dm', 3), 11: ('Bm', 2),
              7: ('Gm', 1), 0: ('Cm', 1)}


def capo_suggestions(target_key, is_minor=False, top=3):
    """
    Saran posisi capo agar bentuk chord yang dimainkan mudah.
    Misal target D: capo fret 2 lalu bentuk kunci C.
    Return list [(fret, nama_kunci_bentuk, skor)].
    """
    tp = key_to_pc(target_key)
    if tp is None:
        return []
    table = EASY_MINOR if is_minor else EASY_MAJOR
    cands = []
    for capo in range(0, 8):
        play_pc = (tp - capo) % 12
        if play_pc in table:
            name, score = table[play_pc]
            cands.append((capo, name, score))
    cands.sort(key=lambda c: (-c[2], c[0]))
    return cands[:top]


def describe_shift(from_key, to_key):
    """Teks ringkas arah pergeseran, mis. 'naik +2 semitone (C -> D)'."""
    s = shift_between_keys(from_key, to_key)
    arah = 'tetap' if s == 0 else ('naik +%d' % s if s > 0 else 'turun %d' % s)
    return '%s semitone (%s -> %s)' % (arah, from_key, to_key)


def all_key_versions(text, from_key):
    """
    Versi sheet di 12 kunci. Return list (label_kunci, semitones, teks).
    Nama kunci memakai notasi lazim (D#/Eb, F#/Gb, A#/Bb).
    """
    base_pc = key_to_pc(from_key)
    results = []
    for step in range(12):
        pc = (base_pc + step) % 12
        label = KEY_DISPLAY[pc]
        to_key = label.split('/')[0]
        flats = use_flats_for(pc)
        txt = transpose_sheet(text, step, flats) if step else text
        results.append((label, step, txt))
    return results
