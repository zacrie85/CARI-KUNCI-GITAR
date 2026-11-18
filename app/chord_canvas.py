# -*- coding: utf-8 -*-
"""
ChordKu - widget ilustrasi chord: diagram fretboard digambar di Canvas.

Warna mengikuti tema merah-putih-emas; papan senar bernuansa kayu
seperti gambar referensi chord gitar.
"""
import tkinter as tk

from . import chord_shapes as cs
from .gui import GOLD, RED, RED_SOFT, TEXT, MUTED

WOOD = '#5C3A21'        # papan senar (nuansa kayu, seperti referensi)
WOOD_DARK = '#4A2E19'
FRET_LINE = '#E8D5A8'
STRING_C = '#F2E8DA'
NUT_C = '#120B06'
MARK_C = GOLD
FRET_LABEL_C = '#C9A85C'


class ChordDiagram(tk.Canvas):
    """Satu diagram chord (senar vertikal, fret horizontal)."""

    def __init__(self, parent, chord=None, width=104, height=128, **kw):
        self._cw = width             # hindari _w: dipakai internal Tkinter
        self._ch = height
        self._colors = kw.pop('colors', None) or {}
        super().__init__(parent, width=width, height=height,
                         bg=self._colors.get('panel', '#1D1218'),
                         highlightthickness=0, **kw)
        if chord:
            self.set_chord(chord)

    def set_chord(self, chord):
        self.delete('all')
        c = self._colors
        w, h = self._cw, self._ch
        shape = cs.get_shape(chord)
        if not shape:
            self.create_text(w / 2, h / 2 - 8, text=chord,
                             fill=c.get('muted', MUTED),
                             font=('Segoe UI', 10, 'bold'))
            self.create_text(w / 2, h / 2 + 10,
                             text='bentuk belum\ntersedia',
                             fill=c.get('muted', MUTED), justify='center',
                             font=('Segoe UI', 7))
            return

        name = shape['name']
        frets = shape['frets']
        base = shape['base']
        fingers = shape['fingers'] or [0] * 6
        barre = shape['barre']

        x0, sp = 30, 12               # posisi senar 6..1
        nut_y, fret_h, n_fret = 40, 18, 4
        xs = [x0 + i * sp for i in range(6)]

        # nama chord
        self.create_text(w / 2, 14, text=name,
                         fill=c.get('gold', GOLD),
                         font=('Segoe UI', 11, 'bold'))
        # papan senar
        gy1 = nut_y
        gy2 = nut_y + n_fret * fret_h
        self.create_rectangle(x0 - 7, gy1 - 4, xs[5] + 7, gy2 + 4,
                              fill=c.get('wood', WOOD),
                              outline=c.get('wood_dark', WOOD_DARK))
        # fret horizontal
        for i in range(n_fret + 1):
            y = gy1 + i * fret_h
            width = 3 if (i == 0 and base == 1) else 1
            color = c.get('nut', NUT_C) if width == 3 else \
                c.get('fret_line', FRET_LINE)
            self.create_line(x0 - 7, y, xs[5] + 7, y, fill=color,
                             width=width)
        # senar vertikal
        for x in xs:
            self.create_line(x, gy1 - 4, x, gy2 + 4,
                             fill=c.get('string', STRING_C), width=1)
        # label posisi fret (mis. '5fr')
        if base > 1:
            self.create_text(14, gy1 + fret_h / 2, text='%dfr' % base,
                             fill=c.get('fret_label', FRET_LABEL_C),
                             font=('Segoe UI', 7, 'bold'))

        # penanda senar terbuka / tidak dipetik
        for i, x in enumerate(xs):
            f = frets[i]
            if f == 0:
                self.create_oval(x - 3, gy1 - 11, x + 3, gy1 - 5,
                                 outline=c.get('mark', MARK_C), width=1)
            elif f < 0:
                self.create_line(x - 3, gy1 - 11, x + 3, gy1 - 5,
                                 fill=c.get('mark', MARK_C), width=1)
                self.create_line(x - 3, gy1 - 5, x + 3, gy1 - 11,
                                 fill=c.get('mark', MARK_C), width=1)

        # barre (jari telunjuk menyilang)
        if barre:
            bf, lo, hi = barre
            yb = gy1 + (bf - base) * fret_h + fret_h / 2
            if gy1 <= yb <= gy2:
                self.create_rectangle(xs[lo - 1] - 5, yb - 4,
                                      xs[hi - 1] + 5, yb + 4,
                                      fill=c.get('dot', RED),
                                      outline=c.get('dot', RED))
        # titik jari
        for i, x in enumerate(xs):
            f = frets[i]
            if f <= 0:
                continue
            if barre and fingers[i] == 1:
                continue                  # sudah tergambar sebagai barre
            y = gy1 + (f - base) * fret_h + fret_h / 2
            self.create_oval(x - 6, y - 6, x + 6, y + 6,
                             fill=c.get('dot', RED),
                             outline=c.get('dot_soft', RED_SOFT))
            if fingers[i]:
                self.create_text(x, y, text=str(fingers[i]),
                                 fill=c.get('dot_text', '#FFFFFF'),
                                 font=('Segoe UI', 7, 'bold'))


class ChordGrid(tk.Frame):
    """Baris diagram chord yang bisa digulir horizontal."""

    def __init__(self, parent, colors=None, diagram_h=132, **kw):
        super().__init__(parent, **kw)
        self._colors = colors or {}
        self.canvas = tk.Canvas(self, bg=self._colors.get('panel', '#1D1218'),
                                highlightthickness=0, height=diagram_h)
        sb = tk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=sb.set)
        self.canvas.pack(side='top', fill='x', expand=True)
        sb.pack(side='top', fill='x')
        self.canvas.bind('<MouseWheel>', self._wheel)          # Windows
        self.canvas.bind('<Button-4>', self._wheel)            # Linux
        self.canvas.bind('<Button-5>', self._wheel)

    def _wheel(self, event):
        delta = -1 if (event.num == 4 or getattr(event, 'delta', 0) > 0) else 1
        self.canvas.xview_scroll(delta, 'units')

    def set_chords(self, chords, limit=14):
        self.canvas.delete('all')
        seen, uniq = set(), []
        for ch in chords:
            ch = ch.strip()
            if ch and ch not in seen:
                seen.add(ch)
                uniq.append(ch)
                if len(uniq) >= limit:
                    break
        if not uniq:
            # state kosong: petunjuk, bukan kanvas kosong yang tampak rusak
            self.canvas.create_text(
                12, 66, anchor='w',
                text='Belum ada chord — muat contoh, tempel sheet, buka file '
                     '.txt, atau jalankan deteksi/transposisi.',
                fill=self._colors.get('muted', MUTED),
                font=('Segoe UI', 9, 'italic'))
            self.canvas.configure(scrollregion=(0, 0, 1, 140))
            return
        x = 6
        for ch in uniq:
            d = ChordDiagram(self.canvas, ch, colors=self._colors)
            self.canvas.create_window(x, 4, anchor='nw', window=d)
            x += 108
        self.canvas.configure(scrollregion=(0, 0, max(x, 1), 140))
