# 🎸 CARI KUNCI GITAR (ChordKu)

Aplikasi desktop Windows untuk **deteksi chord dari audio/YouTube** dan
**transposisi kunci gitar** — misalnya lagu *Pujaan Hati* (Kangen Band) yang
aslinya kunci **C** bisa langsung digeser menjadi kunci **D**, lengkap dengan
semua chord alternatifnya dan saran posisi capo.

> Inspirasi: aplikasi "Chord AI". Dibangun dengan **Python + Tkinter**,
> database **SQLite**, tampilan **futuristik merah-putih-emas** (v1.0.2) —
> tanpa server, semuanya berjalan lokal di PC-mu.

## ✨ Fitur

| Fitur | Penjelasan |
|---|---|
| **Transposisi chord (v1.0.4)** | Tempel sheet chord (boleh pakai lirik; chord besar/kecil, kurung `[Am]`, sejajar lirik, atau di atas lirik), pilih kunci asal & tujuan → semua chord bergeser otomatis. Pustaka **7 contoh lagu** bawaan (Pujaan Hati + tradisional + template) dengan kunci asal terisi otomatis. Kata lirik tidak ikut tergeser. |
| **12 kunci alternatif** | Satu klik menampilkan lagu yang sama di semua kunci (C sampai B). |
| **Saran capo** | Misal kunci D cukup capo fret 2 lalu pakai bentuk kunci C. |
| **Deteksi chord** | Chroma + template matching + Viterbi (metode buku teks MIR) menebak urutan chord berwaktu dari file audio, plus estimasi kunci lagu (Krumhansl-Schmuckler). |
| **Ilustrasi chord (v1.0.2)** | Diagram fretboard (papan kayu, titik jari merah bernomor, penanda O/X, bentuk barre otomatis dengan label `2fr`/`4fr`) untuk semua chord unik dalam lagu — muncul di tab Transposisi & Deteksi. |
| **YouTube** | **Browser YouTube tersemat (v1.0.3, mesin WebView2/Edge)**: jelajahi YouTube di dalam aplikasi — begitu video terbuka, URL otomatis masuk Unduhan Bawaan `yt-dlp` → unduh MP3 (ffmpeg ter-bundle). Plus pencarian terintegrasi & tool eksternal **Zac Downloader** (opsional). |
| **Kamus jari** | Pola jari chord yang dipakai ditampilkan otomatis (format `x32010`). |
| **Simpan lagu** | Sheet tersimpan di `chordku.db` (SQLite) — muat ulang, ekspor `.txt`, hapus. |

Contoh hasil transposisi *Pujaan Hati* C → D:

```
Kunci C : Intro : C  G  Am  Em  F  C  Dm  G
Kunci D : Intro : D  A  Bm  F#m G  D  Em  A
```

## 🚀 Cara Menjalankan (paling cepat)

1. Pasang **Python 3.10+** → centang *"Add Python to PATH"* saat instalasi.
2. Klik dua kali **`setup.bat`** (memasang `numpy` dan `yt-dlp`).
3. Klik dua kali **`jalankan.bat`**.

## 📦 Membuat ChordKu.exe

- **Otomatis**: repo ini punya GitHub Actions — tag `v*` memicu build di
  runner Windows dan melampirkan `ChordKu.exe` ke Release.
- **Manual**: di Windows jalankan **`build_exe.bat`** → hasilnya
  `dist/ChordKu.exe` (PyInstaller onefile, windowed).
- **ffmpeg ter-bundle (v1.0.1+)**: `ChordKu.exe` membawa `ffmpeg.exe` di
  dalamnya (`--add-binary` PyInstaller) — deteksi MP3/WEBM/M4A/FLAC dan
  konversi MP3 langsung jalan tanpa instalasi apa pun. Saat build dari
  sumber, `build_exe.bat` dan CI mengunduh ffmpeg otomatis lalu
  membundle-nya ke dalam exe.

## 🎵 Alur YouTube

```
Browser tersemat (WebView2) ──► buka video ──► URL otomatis ──► Unduhan Bawaan
Cari musik (terintegrasi) ──► klik-dua-kali hasil ──► URL masuk Unduhan Bawaan
URL tempel manual ────────────────────────────────────────────┤
                                                              ▼
                        yt-dlp + ffmpeg ter-bundle ──► MP3 ──► tab Deteksi
                                                              ▼
                                                      tab Transposisi
                                                      (+ ilustrasi chord)

Alternatif: Zac Downloader (tool eksternal) ──► "Muat File Terakhir"
```

Catatan: sejak v1.0.3 ChordKu membawa **browser YouTube tersemat** (pywebview +
WebView2/Edge bawaan Windows 10-11): YouTube dibuka penuh di dalam aplikasi
dan URL video mengalir otomatis ke unduhan. Slot `zac-downloader` eksternal
tetap tersedia sebagai cadangan.

## ⚠️ Ketentuan

- Hasil deteksi chord adalah **perkiraan** — selalu periksa dengan telinga.
- Audio/video dari YouTube tetap milik pemilik hak ciptanya; gunakan untuk
  pembelajaran pribadi saja.

## 🗂 Struktur

```
chordku.py            # launcher (+ mode CLI transposisi)
app/                  # engine transposisi, detektor, downloader, UI Tkinter
samples/pujaan_hati.txt
requirements.txt      # numpy, yt-dlp
setup.bat / jalankan.bat / build_exe.bat
PANDUAN.txt           # panduan lengkap bahasa Indonesia
```

## 📄 Lisensi

MIT — lihat [LICENSE](LICENSE).
