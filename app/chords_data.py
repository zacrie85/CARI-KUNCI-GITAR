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

# Lagu tradisional (domain publik, lirik bebas digandakan).
# Chord adalah susunan sederhana ChordKu untuk belajar transposisi.
SAMPLE_RASA_SAYANGE = """RASA SAYANGE - Lagu Tradisional Maluku
Kunci Asli: G
(Lagu tradisional, domain publik - susunan chord ChordKu)

Intro : G Em Am D G

G         Em
rasa sayange.. rasa sayange
Am           D        G
eee.. rasa sayang sayange..
G         Em
rasa sayange.. rasa sayange
Am           D        G
eee.. rasa sayang sayange..

Reff:
C           D
mana bisa hancur hatiku
G          Em
walau jauh di perantauan
C           D
mana bisa hilang kasihku
G      D        G
walau jauh di perantauan..

Musik : G Em Am D G
"""

SAMPLE_GAMBANG_SULING = """GAMBANG SULING - Lagu Tradisional Cirebon
Kunci Asli: C
(Lagu tradisional, domain publik - susunan chord ChordKu)

Intro : C F G C

C            F
gambang suling.. sulingnya bwis
G               C
gambang suling sulingnya bwis..
C            F
kapal kencang nyang ke Cirebon
G               C
gambang suling sulingnya bwis..

C            F
gambang suling.. sulingnya bwis
G               C
gambang suling sulingnya bwis..
C            F
kapal kencang nyang ke Cirebon
G               C
gambang suling sulingnya bwis..

Musik : C F G C
"""

SAMPLE_AMPAR_PISANG = """AMPAR-AMPAR PISANG - Lagu Tradisional Maluku
Kunci Asli: D
(Lagu tradisional, domain publik - susunan chord ChordKu)

Intro : D A G D

D              A
ampar ampar pisang..
G                D
pisangku ku makan..
D              A
kulitnya kubuang keluar..
G           A        D
terkambil macang..

D              A
macang datang memakan..
G                D
sisa pisangku tu sanang..
D              A
ampar ampar pisang..
G           A        D
pisangku ku makan..

Musik : D A G D
"""

SAMPLE_SUWE_ORA_JAMU = """SUWE ORA JAMU - Lagu Tradisional Jawa
Kunci Asli: C
(Lagu tradisional, domain publik - susunan chord ChordKu)

Intro : C F G C

C            F
suwe ora jamu..
G              C
jamu godhong telo..
C            F
suwe ora ketemu..
G          C
kumpul tang gapura..

C            F
suwe ora jamu..
G              C
jamu godhong kates..
C            F
suwe ora ketemu..
G          C
kapan ketemu maneh..

Musik : C F G C
"""

SAMPLE_BINTANG_KECIL = """BINTANG KECIL - Lagu Anak Tradisional
Kunci Asli: C
(Lagu tradisional, domain publik - susunan chord ChordKu)

Intro : C F G C

C             F
bintang kecil..
G             C
di langit yang biru..
C             F
banyak sekali..
G             C
masing-masing berpendar..

C             F
bilang bintang..
G             C
ehem, ehem, ehem..
C             F
saling bersaut..
G             C
menembus angkasa..

Musik : C F G C
"""

SAMPLE_TEMPLATE = """TEMPLATE - SHEET CHORD LATIHAN
Kunci Asli: C
(Isi dengan lagumu sendiri: chord boleh di atas lirik,
 sejajar dengan lirik, atau di dalam kurung [Am])

Intro : C G Am F

C        G
tulis lirik bait pertama di sini
Am        F
chord bisa sejajar lirik atau di atasnya

Reff:
C      G
lirik reff baris satu
Am       F        G        C
lirik reff baris dua, chord di dalam baris
"""

SAMPLE_SONGS = {
    'Pujaan Hati - Kangen Band (Kunci C)': SAMPLE_PUJAAN_HATI,
    'Rasa Sayange - Trad. Maluku (Kunci G)': SAMPLE_RASA_SAYANGE,
    'Gambang Suling - Trad. Cirebon (Kunci C)': SAMPLE_GAMBANG_SULING,
    'Ampar-Ampar Pisang - Trad. Maluku (Kunci D)': SAMPLE_AMPAR_PISANG,
    'Suwe Ora Jamu - Trad. Jawa (Kunci C)': SAMPLE_SUWE_ORA_JAMU,
    'Bintang Kecil - Lagu Anak Trad. (Kunci C)': SAMPLE_BINTANG_KECIL,
    'Template Sheet Kosong (Kunci C)': SAMPLE_TEMPLATE,
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
