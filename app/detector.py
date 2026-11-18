# -*- coding: utf-8 -*-
"""
ChordKu - Deteksi chord dari audio.

Metode (buku teks Music Information Retrieval):
  1. Dekode audio -> WAV mono 22050 Hz (ffmpeg bila tersedia, fallback modul wave).
  2. STFT -> spektrogram magnitude -> kompresi logaritmik.
  3. Lipat bin frekuensi menjadi vektor chroma 12 nada (C..B).
  4. Cocokkan tiap frame dengan template chord (mayor, minor, 7, maj7, m7)
     memakai cosine similarity.
  5. Viterbi decoding dengan penalti perpindahan chord -> urutan chord halus.
  6. Estimasi kunci lagu dengan profil Krumhansl-Schmuckler.

Hasil deteksi adalah PERKIRAAN. Selalu periksa kembali dengan telinga.
"""
import os
import shutil
import subprocess
import tempfile
import wave

import numpy as np

SR = 22050
FRAME_SIZE = 8192
HOP_SIZE = 2048
FMIN_HZ = 65.0
FMAX_HZ = 2100.0
MIN_SEG_SEC = 0.8

# Penalti perpindahan chord (delta Viterbi). Skala skor cosine 0..1 dan
# selisih antar template per frame biasanya 0.05..0.2, jadi delta 1.5
# membuat jalur "nyangkut" di satu chord bermenit-menit (bug v1.0.5-:
# lagu 4 menit hanya 4 segmen). Nilai di bawah dikalibrasi ulang.
SENSITIVITY = {'kasar': 0.80, 'normal': 0.45, 'halus': 0.25}
DEFAULT_SENS = 'normal'
SMOOTH_FRAMES = 5  # perataan temporal ringan (~0.46 detik)

# ---------------------------------------------------------------- audio I/O
def find_ffmpeg():
    """
    Cari ffmpeg dengan urutan: PATH sistem -> ter-bundle di dalam
    ChordKu.exe (sys._MEIPASS, v1.0.1+) -> di sebelah aplikasi.
    """
    exe = shutil.which('ffmpeg')
    if exe:
        return exe
    import sys
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        bundled = os.path.join(meipass, 'ffmpeg.exe')
        if os.path.isfile(bundled):
            return bundled
    local = os.path.join(app_dir(), 'ffmpeg.exe')
    return local if os.path.isfile(local) else None


def app_dir():
    import sys
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read_wav(path):
    """Baca WAV PCM biasa -> array float mono. Return (y, sr) atau None."""
    try:
        with wave.open(path, 'rb') as w:
            sr = w.getframerate()
            n = w.getnframes()
            ch = w.getnchannels()
            sw = w.getsampwidth()
            raw = w.readframes(n)
        if sw == 2:
            y = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        elif sw == 4:
            y = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
        elif sw == 1:
            y = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
        else:
            return None
        if ch > 1:
            y = y.reshape(-1, ch).mean(axis=1)
        return y, sr
    except Exception:
        return None


def load_audio(path, progress_cb=None):
    """
    Muat file audio apa pun -> (y, sr=22050) mono.
    ffmpeg dipakai untuk format non-WAV dan resampling.
    """
    if progress_cb:
        progress_cb(0.05, 'Memuat audio...')
    ext = os.path.splitext(path)[1].lower()
    ffmpeg = find_ffmpeg()
    if ffmpeg and (ext != '.wav' or _read_wav(path) is None):
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        tmp.close()
        cmd = [ffmpeg, '-y', '-loglevel', 'error', '-i', path,
               '-ac', '1', '-ar', str(SR), '-sample_fmt', 's16', tmp.name]
        try:
            if progress_cb:
                progress_cb(0.15, 'Mengonversi audio (ffmpeg)...')
            res = subprocess.run(cmd, capture_output=True, timeout=600)
            if res.returncode != 0:
                raise RuntimeError('ffmpeg gagal: %s' %
                                   res.stderr.decode(errors='ignore')[:300])
            wav_path = tmp.name
        except Exception:
            os.unlink(tmp.name)
            raise
    elif ext == '.wav':
        wav_path = path
    else:
        raise RuntimeError(
            'Format %s butuh ffmpeg. Pasang ffmpeg (lihat tab Panduan) '
            'atau letakkan ffmpeg.exe di sebelah aplikasi.' % ext)
    if progress_cb:
        progress_cb(0.25, 'Membaca data audio...')
    data = _read_wav(wav_path)
    if wav_path != path and os.path.isfile(wav_path):
        os.unlink(wav_path)
    if data is None:
        raise RuntimeError('Tidak bisa membaca audio: %s' % path)
    y, sr = data
    if sr != SR:  # fallback sederhana bila ffmpeg tidak ada
        dur = len(y) / float(sr)
        t_new = np.arange(0, dur, 1.0 / SR)
        y = np.interp(t_new, np.arange(len(y)) / float(sr), y).astype(np.float32)
        sr = SR
    return y.astype(np.float32), sr

# ---------------------------------------------------------------- chroma
def _window(n):
    """Jendela Blackman-Harris (sidelobe sangat rendah, -92 dB)."""
    i = np.arange(n)
    return (0.35875 - 0.48829 * np.cos(2 * np.pi * i / (n - 1))
            + 0.14128 * np.cos(4 * np.pi * i / (n - 1))
            - 0.01168 * np.cos(6 * np.pi * i / (n - 1))).astype(np.float32)


def chromagram(y, sr=SR, progress_cb=None):
    """Audio -> matriks chroma (T x 12), ternormalisasi per frame."""
    win = _window(FRAME_SIZE)
    n_frames = max(1, (len(y) - FRAME_SIZE) // HOP_SIZE + 1)
    freqs = np.fft.rfftfreq(FRAME_SIZE, 1.0 / sr)
    band = (freqs >= FMIN_HZ) & (freqs <= FMAX_HZ)
    band_idx = np.nonzero(band)[0]
    freqs_b = freqs[band]
    # pitch class tiap bin (A4=440 Hz)
    midi = np.round(12.0 * np.log2(freqs_b / 440.0)) + 69
    pcs = (midi.astype(int) % 12)
    chroma = np.zeros((n_frames, 12), dtype=np.float32)
    for t in range(n_frames):
        seg = y[t * HOP_SIZE: t * HOP_SIZE + FRAME_SIZE]
        if len(seg) < FRAME_SIZE:
            seg = np.pad(seg, (0, FRAME_SIZE - len(seg)))
        mag = np.abs(np.fft.rfft(seg * win))[band]
        # buang bin sangat lemah (bocoran sidelobe) lalu kompresi log ringan
        mag = np.where(mag >= 0.01 * mag.max(), mag, 0.0)
        spec = np.log1p(100.0 * mag)
        chroma[t] = np.bincount(pcs, weights=spec, minlength=12)
        if progress_cb and t % 200 == 0:
            progress_cb(0.25 + 0.45 * t / max(1, n_frames),
                        'Menghitung chroma %d/%d...' % (t, n_frames))
    norm = np.linalg.norm(chroma, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    return chroma / norm

# ---------------------------------------------------------------- template
BASE_TEMPLATES = {
    '': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],       # mayor: 1 3 5
    'm': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],      # minor: 1 b3 5
    '7': [1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0],      # dom7: 1 3 5 b7
    'maj7': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],   # maj7: 1 3 5 7
    'm7': [1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],     # m7: 1 b3 5 b7
}
QUALITY_ORDER = ['', 'm', '7', 'maj7', 'm7']


def build_templates():
    from .transposer import SHARP_NAMES
    names, vectors = [], []
    for pc in range(12):
        for q, vec in BASE_TEMPLATES.items():
            # rotasi pola interval ke root nada ke-pc (C, C#, D, ...)
            names.append(SHARP_NAMES[pc] + q)
            vectors.append(np.roll(vec, pc))
    return names, np.array(vectors, dtype=np.float32)


def _cosine(emission, templates):
    """emission: T x 12; templates: S x 12 -> T x S skor cosine."""
    e = emission / (np.linalg.norm(emission, axis=1, keepdims=True) + 1e-9)
    t = templates / (np.linalg.norm(templates, axis=1, keepdims=True) + 1e-9)
    return e @ t.T

def _smooth_chroma(chroma, w=SMOOTH_FRAMES):
    """Perataan temporal ringan (rata-rata bergerak) per kelas nada.

    Menekan frame frame acak tanpa menghapus perubahan chord asli
    (jendela hanya ~0.46 detik). Tepi memakai replikasi (mode 'edge').
    """
    if w <= 1 or len(chroma) < 3:
        return chroma
    kernel = np.ones(w, dtype=np.float32) / float(w)
    pad = w // 2
    padded = np.pad(chroma, ((pad, pad), (0, 0)), mode='edge')
    sm = np.empty_like(chroma, dtype=np.float32)
    for k in range(chroma.shape[1]):
        sm[:, k] = np.convolve(padded[:, k], kernel, mode='valid')[:len(chroma)]
    norm = np.linalg.norm(sm, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    return sm / norm


# ---------------------------------------------------------------- viterbi
def viterbi_path(scores, delta=1.5, free_frames=None):
    """
    HMM sederhana: pindah chord dikenakan penalti `delta` (log),
    bertahan gratis.

    free_frames: boolean per frame. Pada frame bebas (mis. bagian
    sunyi/instrumental tanpa energi) perpindahan antar chord TIDAK
    dikenakan penalti, sehingga jalur bisa "meluncur" ke chord yang
    benar saat musik masuk lagi, bukan menempel di chord lama.
    """
    T, S = scores.shape
    trans = np.full((S, S), -delta, dtype=np.float32)
    np.fill_diagonal(trans, 0.0)
    trans_free = np.zeros((S, S), dtype=np.float32)
    dp = scores[0].copy()
    bp = np.zeros((T, S), dtype=np.int32)
    for t in range(1, T):
        tr = trans_free if (free_frames is not None and free_frames[t]) \
            else trans
        cand = dp[:, None] + tr          # S x S
        bp[t] = np.argmax(cand, axis=0)
        dp = cand[bp[t], np.arange(S)] + scores[t]
    path = np.zeros(T, dtype=np.int32)
    path[-1] = int(np.argmax(dp))
    for t in range(T - 2, -1, -1):
        path[t] = bp[t + 1, path[t + 1]]
    return path

# ---------------------------------------------------------------- kunci
KS_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19,
                     2.39, 3.66, 2.29, 2.88])
KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75,
                     3.98, 2.69, 3.34, 3.17])


def _corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


def estimate_key(mean_chroma):
    from .transposer import SHARP_NAMES, FLAT_NAMES, FLAT_PREFERRED
    best = (None, -2.0)
    for pc in range(12):
        r_maj = _corr(mean_chroma, np.roll(KS_MAJOR, pc))
        r_min = _corr(mean_chroma, np.roll(KS_MINOR, pc))
        if r_maj > best[1]:
            best = (SHARP_NAMES[pc] + ' mayor', r_maj)
        if r_min > best[1]:
            best = (FLAT_NAMES[pc] if pc in FLAT_PREFERRED
                    else SHARP_NAMES[pc] + ' minor', r_min)
    name, r = best
    conf = ('tinggi' if r >= 0.75 else
            'sedang' if r >= 0.5 else 'rendah')
    return name, r, conf

# ---------------------------------------------------------------- pipeline
def _fmt_time(sec):
    sec = int(round(sec))
    return '%02d:%02d' % (sec // 60, sec % 60)


def detect_file(path, progress_cb=None, sensitivity=DEFAULT_SENS):
    """
    Deteksi chord sebuah file audio.

    sensitivity: 'kasar' | 'normal' | 'halus' — seberapa mudah chord
    berganti (halus = lebih banyak perubahan tertangkap).
    Return dict: segments [(mulai, selesai, chord)], key, confidence,
    chord_line (LENGKAP sampai akhir lagu), duration, notation_flats.
    """
    sens = str(sensitivity or DEFAULT_SENS).strip().lower()
    delta = SENSITIVITY.get(sens, SENSITIVITY[DEFAULT_SENS])
    y, sr = load_audio(path, progress_cb)
    duration = len(y) / float(sr)
    if duration < 2.0:
        raise RuntimeError('Audio terlalu pendek (minimum 2 detik).')

    chroma = chromagram(y, sr, progress_cb)
    chroma = _smooth_chroma(chroma)
    if progress_cb:
        progress_cb(0.72, 'Mencocokkan template chord...')

    names, templates = build_templates()
    scores = _cosine(chroma, templates)
    # bobot energi: frame sunyi diabaikan (skor diturunkan)
    energy = chroma.max(axis=1)
    silent = ~(energy > 0.05)
    scores = scores * (~silent)[:, None]

    if progress_cb:
        progress_cb(0.80, 'Merapikan urutan chord (Viterbi, %s)...' % sens)
    path_states = viterbi_path(scores, delta=delta, free_frames=silent)
    times = np.arange(len(path_states)) * HOP_SIZE / float(sr)

    from .transposer import FLAT_NAMES
    segments = []
    for i, st in enumerate(path_states):
        if segments and segments[-1][2] == names[st]:
            segments[-1][1] = times[i]
        else:
            segments.append([times[i], times[i], names[st]])
    if segments:
        segments[-1][1] = times[-1] + FRAME_SIZE / float(sr)
    # buang segmen terlalu pendek -> serap ke tetangga
    merged = []
    for seg in segments:
        if seg[1] - seg[0] < MIN_SEG_SEC and merged:
            merged[-1][1] = seg[1]
        else:
            merged.append(seg)
    segments = [(a, b, c) for a, b, c in merged]

    mean_chroma = chroma.mean(axis=0)
    key_name, r, conf = estimate_key(mean_chroma)
    key_pc = None
    from .transposer import SHARP_NAMES
    for pc, nm in enumerate(SHARP_NAMES):
        if key_name.startswith(nm):
            key_pc = pc
            break
    use_flats = key_pc is not None and (
        key_pc in {5, 1, 3, 6, 8, 10})
    if use_flats:  # tulis ulang chord dengan notasi mol
        from .transposer import transpose_sheet
        chord_line = ' '.join(s[2] for s in segments)
        chord_line = transpose_sheet(chord_line, 0, True)
        segments = [(a, b, transpose_sheet(c, 0, True)) for a, b, c in segments]

    # chord line LENGKAP — tanpa potongan, sampai musiknya habis
    chord_line = ' '.join(s[2] for s in segments)

    if progress_cb:
        progress_cb(1.0, 'Selesai.')
    return {
        'segments': segments,
        'key': key_name,
        'key_root': key_name.split(' ')[0],
        'is_minor': key_name.endswith('minor'),
        'confidence': r,
        'confidence_label': conf,
        'duration': duration,
        'chord_line': chord_line,
        'timeline': '\n'.join('%s - %s  %s' % (_fmt_time(a), _fmt_time(b), c)
                              for a, b, c in segments),
    }
