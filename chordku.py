# -*- coding: utf-8 -*-
"""
CARI KUNCI GITAR (ChordKu)
==========================
Aplikasi desktop Windows untuk:
  - transposisi chord (geser kunci C -> D, dll),
  - melihat 12 kunci alternatif + saran capo,
  - deteksi chord dari audio (hasil unduhan YouTube / file lokal),
  - mengunduh audio YouTube (yt-dlp / tool eksternal),
  - menyimpan lagu ke database SQLite.

Menjalankan GUI          : python chordku.py
Transpose lewat terminal : python chordku.py --cli-transpose sheet.txt --from C --to D
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_cli_transpose(path, from_key, to_key):
    from app import transposer as tr
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    new_text, semis, flats = tr.transpose_sheet_by_key(text, from_key, to_key)
    print('Kunci  : %s -> %s (%s)' %
          (from_key, to_key, tr.describe_shift(from_key, to_key)))
    print('-' * 60)
    print(new_text)


def main():
    args = sys.argv[1:]
    if '--cli-transpose' in args:
        i = args.index('--cli-transpose')
        try:
            path = args[i + 1]
        except IndexError:
            print('Pemakaian: chordku.py --cli-transpose <file> --from C --to D')
            return 2
        from_key, to_key = 'C', 'D'
        if '--from' in args:
            from_key = args[args.index('--from') + 1]
        if '--to' in args:
            to_key = args[args.index('--to') + 1]
        run_cli_transpose(path, from_key, to_key)
        return 0

    from app.gui import launch
    return launch()


if __name__ == '__main__':
    sys.exit(main() or 0)
