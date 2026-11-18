# 🎸 CARI KUNCI GITAR (ChordKu)

Aplikasi desktop Windows untuk **deteksi chord dari audio/YouTube** dan
**transposisi kunci gitar** — misalnya lagu *Pujaan Hati* (Kangen Band) yang
aslinya kunci **C** bisa langsung digeser menjadi kunci **D**, lengkap dengan
semua chord alternatifnya dan saran posisi capo.

> Inspirasi: aplikasi "Chord AI". Dibangun dengan **Python + Tkinter**,
> database **SQLite**, tampilan **terang & minimalis** — tanpa server,
> semuanya berjalan lokal di PC-mu.

## ✨ Fitur

| Fitur | Penjelasan |
|---|---|
| **Transposisi chord** | Tempel sheet chord (boleh pakai lirik), pilih kunci asal & tujuan → semua chord bergeser otomatis. Kata lirik tidak ikut tergeser. |
| **12 kunci alternatif** | Satu klik menampilkan lagu yang sama di semua kunci (C sampai B). |
| **Saran capo** | Misal kunci D cukup capo fret 2 lalu pakai bentuk kunci C. |
| **Deteksi chord** | Chroma + template matching + Viterbi (metode buku teks MIR) menebak urutan chord berwaktu dari file audio, plus estimasi kunci lagu (Krumhansl-Schmuckler). |
| **YouTube** | Unduh audio langsung via `yt-dlp`, atau pakai tool eksternal seperti **Zac Downloader** lalu muat file hasilnya ke tab Deteksi. |
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
- Opsional: letakkan `ffmpeg.exe` di sebelah `ChordKu.exe` agar deteksi bisa
  memproses MP3/MP4/M4A (tanpa ffmpeg hanya file `.wav`).

## 🎵 Alur YouTube

```
URL YouTube ──► yt-dlp (bawaan) ──► MP3 ──► tab Deteksi ──► tab Transposisi
     └──► atau Zac Downloader (tool eksternal) ──► "Muat File Terakhir"
```

Catatan: `zac-downloader` (github.com/zacrie85/zac-downloader) adalah aplikasi
GUI terpisah, jadi integrasinya berupa slot *tool eksternal*: aplikasi
membukanya untukmu, lalu file hasil unduhannya dimuat kembali ke tab Deteksi.

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
