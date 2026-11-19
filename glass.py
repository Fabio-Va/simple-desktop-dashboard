"""
Vetro liquido in stile Apple per SiDD.

La finestra è trasparente e Windows sfoca ciò che c'è dietro (sfocatura acrilica, vedi
enable_blur in sidd.py). Sopra, ogni pannello è disegnato come una lastra di vetro:
- superficie chiara semitrasparente con una lucentezza più forte in alto;
- bordo speculare: brilla dal lato rivolto verso la luce e, meno, dal lato opposto
  (come i riflessi del Liquid Glass), con un alone morbido verso l'interno;
- la "luce" è il puntatore del mouse: i riflessi lo seguono in tempo reale;
- un filo d'ombra sul bordo in basso dà spessore alla lastra.
"""
import math
import weakref

from PySide6.QtCore import QObject, QPointF, QRectF, QTimer
from PySide6.QtGui import (QColor, QConicalGradient, QCursor, QLinearGradient, QPainter, QPen,
                           QRadialGradient)


class Light(QObject):
    """Segue il puntatore: i riflessi dei pannelli in vetro si spostano con lui."""

    _inst = None

    @classmethod
    def get(cls):
        if cls._inst is None:
            cls._inst = Light()
        return cls._inst

    def __init__(self):
        super().__init__()
        self.widgets = weakref.WeakSet()
        self.pos = QCursor.pos()
        self.timer = QTimer(self, interval=33)  # ~30 aggiornamenti al secondo, solo se il mouse si muove
        self.timer.timeout.connect(self.poll)
        self.timer.start()

    def register(self, w):
        self.widgets.add(w)

    def poll(self):
        p = QCursor.pos()
        if (p - self.pos).manhattanLength() < 3:
            return
        self.pos = p
        for w in list(self.widgets):
            try:
                if w.isVisible() and not w.window().isMinimized():
                    w.update()
            except RuntimeError:  # widget già distrutto (cambio tema/lingua)
                pass


def paint_glass(widget, p: QPainter, path):
    """Disegna la lastra: superficie, lucentezza e bordo speculare che segue la luce."""
    r = QRectF(widget.rect())
    cur = QPointF(widget.mapFromGlobal(Light.get().pos))

    p.save()
    p.setClipPath(path)
    # superficie del vetro
    p.fillPath(path, QColor(255, 255, 255, 20))
    # lucentezza, più forte in alto
    g = QLinearGradient(0, 0, 0, min(r.height(), 220))
    g.setColorAt(0, QColor(255, 255, 255, 30))
    g.setColorAt(1, QColor(255, 255, 255, 0))
    p.fillPath(path, g)
    # riflesso morbido vicino al puntatore
    if r.adjusted(-60, -60, 60, 60).contains(cur):
        rg = QRadialGradient(cur, 240)
        rg.setColorAt(0, QColor(255, 255, 255, 34))
        rg.setColorAt(1, QColor(255, 255, 255, 0))
        p.fillPath(path, rg)
    p.restore()

    # bordo speculare: angolo verso la luce, in gradi antiorari come vuole QConicalGradient
    c = r.center()
    ang = math.degrees(math.atan2(-(cur.y() - c.y()), cur.x() - c.x()))
    cg = QConicalGradient(c, ang)
    for pos, a in ((0, 240), (0.07, 125), (0.17, 34), (0.33, 16), (0.5, 120), (0.58, 28),
                   (0.67, 16), (0.83, 34), (0.93, 125), (1, 240)):
        cg.setColorAt(pos, QColor(255, 255, 255, a))
    p.save()
    p.setClipPath(path)
    p.setOpacity(0.24)  # alone interno morbido
    p.setPen(QPen(cg, 10))
    p.drawPath(path)
    p.setOpacity(1.0)
    # spessore della lastra: un filo d'ombra sul bordo in basso
    sh = QLinearGradient(0, r.height() * 0.6, 0, r.height())
    sh.setColorAt(0, QColor(0, 0, 0, 0))
    sh.setColorAt(1, QColor(0, 0, 0, 70))
    p.setPen(QPen(sh, 3))
    p.drawPath(path)
    p.restore()
    p.setPen(QPen(cg, 1.3))
    p.drawPath(path)
