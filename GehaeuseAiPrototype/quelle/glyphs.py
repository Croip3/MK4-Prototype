"""Eckige 'Titan'-Schrift: Ziffern + wenige Buchstaben als Strichzuege (Centerlines).
Jede Glyphe liegt in einer Box 0..W x 0..H (Einheiten = mm bei Skalierung 1).
Striche werden mit trace() auf Strichbreite gebracht (Gehrungsecken)."""
from build123d import *

def _g(W=3.0, H=5.0, w=0.9, c=0.8):
    x0, x1 = w / 2, W - w / 2
    y0, y1 = w / 2, H - w / 2
    ym = H / 2
    xm = W / 2
    G = {}
    G["0"] = [[(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1),
               (x0 + c, y1), (x0, y1 - c), (x0, y0 + c), (x0 + c, y0)]]
    G["1"] = [[(xm + 0.35, 0), (xm + 0.35, H)], [(xm - 0.75, y1 - 1.05), (xm + 0.35, y1 + 0.05)]]
    G["2"] = [[(0, y1), (x1 - c, y1), (x1, y1 - c), (x1, ym + c * 0.6), (x1 - c * 0.6, ym),
               (x0 + c * 0.6, ym), (x0, ym - c * 0.6), (x0, y0), (W, y0)]]
    G["3"] = [[(0, y1), (x1 - c, y1), (x1, y1 - c), (x1, y0 + c), (x1 - c, y0), (0, y0)],
              [(x0 + 0.5, ym), (x1, ym)]]
    G["4"] = [[(x0, H), (x0, ym + c * 0.6), (x0 + c * 0.6, ym), (W, ym)],
              [(x1 - 0.2, H), (x1 - 0.2, 0)]]
    G["5"] = [[(W, y1), (x0, y1), (x0, ym), (x1 - c * 0.6, ym), (x1, ym - c * 0.6),
               (x1, y0 + c), (x1 - c, y0), (0, y0)]]
    G["6"] = [[(W, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c), (x0 + c, y0), (x1 - c, y0),
               (x1, y0 + c), (x1, ym - c * 0.6), (x1 - c * 0.6, ym)], [(x1 - c * 0.6, ym), (x0, ym)]]
    G["7"] = [[(0, y1), (x1 - c, y1), (x1, y1 - c), (x1, 0)]]
    xa, xb, cu = x0 + 0.2, x1 - 0.2, c * 0.6
    G["8"] = [[(xa + cu, ym), (xb - cu, ym), (xb, ym + cu), (xb, y1 - cu), (xb - cu, y1), (xa + cu, y1),
               (xa, y1 - cu), (xa, ym + cu), (xa + cu, ym)],
              [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, ym - cu), (x1 - cu, ym), (x0 + cu, ym),
               (x0, ym - cu), (x0, y0 + c), (x0 + c, y0)]]
    G["9"] = [[(0, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1),
               (x0, y1 - c), (x0, ym + c * 0.6), (x0 + c * 0.6, ym)], [(x0 + c * 0.6, ym), (x1, ym)]]
    # Buchstaben
    G["A"] = [[(x0, 0), (x0, y1 - c), (x0 + c, y1), (x1 - c, y1), (x1, y1 - c), (x1, 0)],
              [(x0, ym), (x1, ym)]]
    G["B"] = [[(x0, 0), (x0, H)],
              [(x0, y1), (x1 - c, y1), (x1, y1 - c), (x1, ym + c * 0.6), (x1 - c * 0.6, ym), (x0, ym)],
              [(x1 - c * 0.6, ym), (x1, ym - c * 0.6), (x1, y0 + c), (x1 - c, y0), (x0, y0)]]
    G["O"] = G["0"]
    G["P"] = [[(x0, 0), (x0, H)],
              [(x0, y1), (x1 - c, y1), (x1, y1 - c), (x1, ym + c * 0.6), (x1 - c * 0.6, ym), (x0, ym)]]
    G["R"] = [[(x0, 0), (x0, H)],
              [(x0, y1), (x1 - c, y1), (x1, y1 - c), (x1, ym + c * 0.6), (x1 - c * 0.6, ym), (x0, ym)],
              [(xm, ym), (x1, ym - 0.9), (x1, 0)]]
    G["S"] = [[(W, y1), (x0 + c, y1), (x0, y1 - c), (x0, ym + c * 0.6), (x0 + c * 0.6, ym), (x1 - c * 0.6, ym),
               (x1, ym - c * 0.6), (x1, y0 + c), (x1 - c, y0), (0, y0)]]
    G["T"] = [[(0, y1), (W, y1)], [(xm, y1), (xm, 0)]]
    G["V"] = [[(x0, H), (xm, 0)], [(x1, H), (xm, 0)], [(xm - 0.3, 0.0), (xm + 0.3, 0.0)]]
    G["K"] = [[(x0, 0), (x0, H)], [(x1, H), (x1, ym + 1.0), (x0 + 0.3, ym)], [(x0 + 0.3, ym), (x1, ym - 1.0), (x1, 0)]]
    return G

WIDE = {"M": 3.9, "W": 3.9}

def _wide(W, H, w):
    x0, x1 = w / 2, W - w / 2
    y0, y1 = w / 2, H - w / 2
    xm = W / 2
    c = 0.22 * W
    return {
        # eckige Formen mit Mittelsteg (besser lesbar als V-Diagonalen)
        "M": [[(x0, 0), (x0, y1 - c), (x0 + c, y1), (x1 - c, y1), (x1, y1 - c), (x1, 0)], [(xm, H), (xm, H * 0.38)]],
        "W": [[(x0, H), (x0, y0 + c), (x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, H)], [(xm, 0), (xm, H * 0.62)]],
    }


def glyph_face(ch, W=3.0, H=5.0, w=0.9, c=0.8):
    """2D-Flaeche einer Glyphe (Ursprung unten links)."""
    if ch in WIDE:
        Wg = WIDE[ch] * W / 3.0
        strokes = _wide(Wg, H, w)[ch]
    else:
        Wg = W
        strokes = _g(W, H, w, c)[ch]
    with BuildSketch() as sk:
        for pl in strokes:
            with BuildLine():
                Polyline(*pl)
            trace(line_width=w)
    clip = Pos(Wg / 2, H / 2) * Rectangle(Wg, H)
    return sk.sketch & clip, Wg

def text_face(s, H=5.0, W=3.0, w=0.9, gap=0.6, c=None):
    """Zentrierte Textflaeche (Mitte im Ursprung)."""
    if c is None:
        c = 0.27 * W
    faces = []
    x = 0.0
    for ch in s:
        if ch == " ":
            x += W * 0.7
            continue
        f, Wg = glyph_face(ch, W, H, w, c)
        faces.append(Pos(x, 0) * f)
        x += Wg + gap
    total = x - gap
    sk = faces[0]
    for f in faces[1:]:
        sk = sk + f
    return Pos(-total / 2, -H / 2) * sk, total
