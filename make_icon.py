# -*- coding: utf-8 -*-
"""Генератор фирменной иконки Phantom Browser → app.ico + app.png (на PyQt6, без Pillow).
Тёмный скруглённый квадрат + градиентный ромб (синий→мовэ→зелёный) со свечением и бликом."""

import os
import sys
import struct
from PyQt6.QtCore import Qt, QPointF, QRectF, QBuffer, QIODevice
from PyQt6.QtGui import (
    QGuiApplication, QImage, QPainter, QColor, QLinearGradient,
    QBrush, QPen, QPainterPath, QPolygonF,
)

HERE = os.path.dirname(os.path.abspath(__file__))


def render(s: int) -> QImage:
    img = QImage(s, s, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # тёмный скруглённый фон + обводка
    bg = QPainterPath()
    rad = s * 0.227
    bg.addRoundedRect(QRectF(0.5, 0.5, s - 1.0, s - 1.0), rad, rad)
    p.fillPath(bg, QColor("#181825"))
    p.setPen(QPen(QColor("#313244"), max(1.0, s / 128.0)))
    p.drawPath(bg)

    c = s / 2.0
    r = s * 0.34

    def diamond(rr):
        return QPolygonF([QPointF(c, c - rr), QPointF(c + rr, c),
                          QPointF(c, c + rr), QPointF(c - rr, c)])

    # свечение (несколько крупных ромбов с низкой альфой)
    p.setPen(Qt.PenStyle.NoPen)
    for grow, alpha in ((1.40, 20), (1.20, 32)):
        col = QColor("#89B4FA")
        col.setAlpha(alpha)
        p.setBrush(col)
        p.drawPolygon(diamond(r * grow))

    # основной ромб с градиентом
    grad = QLinearGradient(0.0, 0.0, float(s), 0.0)
    grad.setColorAt(0.0, QColor("#89B4FA"))
    grad.setColorAt(0.55, QColor("#CBA6F7"))
    grad.setColorAt(1.0, QColor("#A6E3A1"))
    p.setBrush(QBrush(grad))
    p.drawPolygon(diamond(r))

    # блик на верхней грани (с клипом по ромбу)
    p.save()
    clip = QPainterPath()
    clip.addPolygon(diamond(r))
    p.setClipPath(clip)
    p.setBrush(QColor(255, 255, 255, 55))
    p.drawPolygon(QPolygonF([QPointF(c, c - r), QPointF(c + r * 0.5, c - r * 0.5),
                             QPointF(c, c), QPointF(c - r * 0.5, c - r * 0.5)]))
    p.restore()
    p.end()
    return img


def png_bytes(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def main():
    QGuiApplication(sys.argv)
    base = render(256)
    base.save(os.path.join(HERE, "app.png"), "PNG")

    sizes = [16, 24, 32, 48, 64, 128, 256]
    blobs = []
    for sz in sizes:
        im = base if sz == 256 else base.scaled(
            sz, sz, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        blobs.append((sz, png_bytes(im)))

    n = len(blobs)
    header = struct.pack("<HHH", 0, 1, n)
    entries = b""
    datas = b""
    offset = 6 + 16 * n
    for sz, data in blobs:
        wh = 0 if sz >= 256 else sz
        entries += struct.pack("<BBBBHHII", wh, wh, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
        datas += data
    with open(os.path.join(HERE, "app.ico"), "wb") as f:
        f.write(header + entries + datas)
    print("OK: app.ico + app.png созданы (PyQt6)")


if __name__ == "__main__":
    main()
