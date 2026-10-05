"""Mini-bibliothèque de graphiques SVG (sans dépendance) : barres, barres groupées, barres horizontales, lignes.

Règles de lisibilité appliquées partout : 1 axe, <= 3 séries, légende dès 2 séries, étiquettes directes,
quadrillage discret, texte en couleur de texte (jamais la couleur de la série), info-bulle sur chaque marque,
et une vue "tableau" associée (accessibilité + vérifiabilité).
"""
from __future__ import annotations

import html
import math

from .answers import n


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def nice_max(v: float) -> tuple[float, float]:
    """Retourne (max, pas) 'jolis' pour 4 intervalles."""
    if v <= 0:
        return 1.0, 0.25
    raw = v / 4
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            step = m * mag
            break
    return step * 4, step


def _fmt_axis(v: float) -> str:
    if abs(v) >= 1000:
        return n(v / 1000, 0 if v % 1000 == 0 else 1) + " k"
    return n(v, 0 if float(v).is_integer() else 1)


def _wrap(label: str, width: int) -> list[str]:
    words, lines, cur = str(label).split(" "), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width or not cur:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines[:3]


def _svg_open(w, h, label):
    return f'<svg class="ch" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}" preserveAspectRatio="xMidYMid meet">'


def bars(data, *, title="", w=560, h=260, fmt=None, hi=(), cls="s1", unit="", ymax=None, label_all=True, xwrap=11):
    """data : [(label, value)] ; hi : labels mis en avant (couleur 'alerte')."""
    fmt = fmt or (lambda v: n(v, 0 if float(v).is_integer() else 1))
    l, r, t, b = 46, 10, 24, 46
    ymax_, step = nice_max(ymax or max(v for _, v in data))
    iw, ih = w - l - r, h - t - b
    band = iw / len(data)
    bw = min(band * 0.62, 64)
    out = [_svg_open(w, h, title)]
    for i in range(5):
        y = t + ih - ih * i / 4
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="ax" x="{l - 6}" y="{y + 3.5:.1f}" text-anchor="end">{_fmt_axis(step * i)}{unit if i == 4 else ""}</text>')
    for k, (lab, v) in enumerate(data):
        x = l + band * k + (band - bw) / 2
        bh = ih * (v / ymax_) if ymax_ else 0
        y = t + ih - bh
        c = "bad" if lab in hi else cls
        tip = f"{lab} : {fmt(v)}{unit}"
        out.append(f'<path class="mk {c}" data-tip="{esc(tip)}" d="M{x:.1f},{t + ih:.1f} V{y + 4:.1f} Q{x:.1f},{y:.1f} {x + 4:.1f},{y:.1f} H{x + bw - 4:.1f} Q{x + bw:.1f},{y:.1f} {x + bw:.1f},{y + 4:.1f} V{t + ih:.1f} Z"/>')
        if label_all or lab in hi:
            out.append(f'<text class="vl" x="{x + bw / 2:.1f}" y="{y - 5:.1f}" text-anchor="middle">{fmt(v)}</text>')
        for j, ln in enumerate(_wrap(lab, xwrap)):
            out.append(f'<text class="ax" x="{x + bw / 2:.1f}" y="{t + ih + 15 + j * 12:.1f}" text-anchor="middle">{esc(ln)}</text>')
    out.append(f'<line class="base" x1="{l}" x2="{w - r}" y1="{t + ih}" y2="{t + ih}"/></svg>')
    return "".join(out)


def grouped_bars(cats, series, *, title="", w=560, h=270, fmt=None, unit="", xwrap=12, label_values=True):
    """series : [(nom, [valeurs])] (2 ou 3 séries max). Légende au-dessus."""
    assert 2 <= len(series) <= 3
    fmt = fmt or (lambda v: n(v, 0 if float(v).is_integer() else 1))
    l, r, t, b = 46, 10, 40, 46
    ymax_, step = nice_max(max(max(v) for _, v in series))
    iw, ih = w - l - r, h - t - b
    band = iw / len(cats)
    k = len(series)
    bw = min(band * 0.78 / k, 36)
    out = [_svg_open(w, h, title)]
    x0 = l
    for si, (name, _) in enumerate(series):
        out.append(f'<rect class="mk s{si + 1}" x="{x0}" y="8" width="11" height="11" rx="2"/><text class="lg" x="{x0 + 16}" y="17.5">{esc(name)}</text>')
        x0 += 16 + 7 * len(name) + 22
    for i in range(5):
        y = t + ih - ih * i / 4
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="ax" x="{l - 6}" y="{y + 3.5:.1f}" text-anchor="end">{_fmt_axis(step * i)}{unit if i == 4 else ""}</text>')
    for ci, lab in enumerate(cats):
        gx = l + band * ci + (band - bw * k - 2 * (k - 1)) / 2
        for si, (name, vals) in enumerate(series):
            v = vals[ci]
            bh = ih * v / ymax_
            x, y = gx + si * (bw + 2), t + ih - bh
            out.append(f'<path class="mk s{si + 1}" data-tip="{esc(f"{lab} · {name} : {fmt(v)}{unit}")}" d="M{x:.1f},{t + ih:.1f} V{y + 3:.1f} Q{x:.1f},{y:.1f} {x + 3:.1f},{y:.1f} H{x + bw - 3:.1f} Q{x + bw:.1f},{y:.1f} {x + bw:.1f},{y + 3:.1f} V{t + ih:.1f} Z"/>')
            if label_values and bw >= 20:
                out.append(f'<text class="vl sm" x="{x + bw / 2:.1f}" y="{y - 4:.1f}" text-anchor="middle">{fmt(v)}</text>')
        cx = l + band * ci + band / 2
        for j, ln in enumerate(_wrap(lab, xwrap)):
            out.append(f'<text class="ax" x="{cx:.1f}" y="{t + ih + 15 + j * 12:.1f}" text-anchor="middle">{esc(ln)}</text>')
    out.append(f'<line class="base" x1="{l}" x2="{w - r}" y1="{t + ih}" y2="{t + ih}"/></svg>')
    return "".join(out)


def hbars(data, *, title="", w=560, fmt=None, hi=(), cls="s1", unit="", row=26, left=150, xmax=None, signed=False):
    """Barres horizontales. signed=True : valeurs +/- autour d'un zéro central (couleur alerte si négatif)."""
    fmt = fmt or (lambda v: n(v, 0 if float(v).is_integer() else 1))
    t, b, r = 8, 24, 56
    h = t + b + row * len(data)
    vmax = xmax or max(abs(v) for _, v in data)
    vmax, step = nice_max(vmax)
    iw = w - left - r
    zero = left + (iw / 2 if signed else 0)
    scale = (iw / 2 if signed else iw) / vmax
    out = [_svg_open(w, h, title)]
    for i in range(0, 5):
        if signed:
            xs = [zero + (i - 2) * step * scale * (2 / 2) for _ in [0]]
        x = (zero + (i - 2) * step * scale) if signed else left + iw * i / 4
        out.append(f'<line class="gl" x1="{x:.1f}" x2="{x:.1f}" y1="{t}" y2="{h - b}"/>')
        val = ((i - 2) * step) if signed else step * i
        out.append(f'<text class="ax" x="{x:.1f}" y="{h - 8}" text-anchor="middle">{_fmt_axis(val)}{unit if i == 4 else ""}</text>')
    for k, (lab, v) in enumerate(data):
        y = t + row * k + 4
        bh = row - 9
        x = zero if v >= 0 else zero + v * scale
        wv = abs(v) * scale
        c = "bad" if (lab in hi or (signed and v < 0)) else cls
        out.append(f'<text class="ax lab" x="{left - 8}" y="{y + bh / 2 + 4:.1f}" text-anchor="end">{esc(lab)}</text>')
        out.append(f'<rect class="mk {c}" data-tip="{esc(f"{lab} : {fmt(v)}{unit}")}" x="{x:.1f}" y="{y}" width="{max(wv, 1):.1f}" height="{bh}" rx="3"/>')
        out.append(f'<text class="vl" x="{(x + wv + 6) if v >= 0 else (x - 6):.1f}" y="{y + bh / 2 + 4:.1f}" text-anchor="{"start" if v >= 0 else "end"}">{fmt(v)}</text>')
    out.append("</svg>")
    return "".join(out)


def line(xlabels, series, *, title="", w=560, h=260, fmt=None, unit="", tick_every=12, ymin=None, band=None, note=None):
    """series : [(nom, [valeurs])] ; band : (i0, i1, libellé) zone surlignée ; note : [(index, texte)] annotations."""
    fmt = fmt or (lambda v: n(v, 0 if float(v).is_integer() else 1))
    l, r, t, b = 50, 70 if len(series) > 1 or True else 16, 28, 34
    allv = [v for _, vals in series for v in vals]
    lo = min(0, min(allv)) if ymin is None else ymin
    hi_v = max(allv)
    span_max, step = nice_max(hi_v - lo)
    top = lo + span_max
    iw, ih = w - l - r, h - t - b
    nx = len(xlabels)
    X = lambda i: l + iw * i / max(nx - 1, 1)
    Y = lambda v: t + ih - ih * (v - lo) / (top - lo)
    out = [_svg_open(w, h, title)]
    if len(series) > 1:
        x0 = l
        for si, (name, _) in enumerate(series):
            out.append(f'<line class="ln s{si + 1}" x1="{x0}" x2="{x0 + 16}" y1="14" y2="14"/><text class="lg" x="{x0 + 21}" y="18">{esc(name)}</text>')
            x0 += 21 + 7 * len(name) + 20
    for i in range(5):
        v = lo + step * i
        y = Y(v)
        out.append(f'<line class="gl" x1="{l}" x2="{w - r}" y1="{y:.1f}" y2="{y:.1f}"/><text class="ax" x="{l - 6}" y="{y + 3.5:.1f}" text-anchor="end">{_fmt_axis(v)}{unit if i == 4 else ""}</text>')
    if band:
        i0, i1, lab = band
        out.append(f'<rect class="band" x="{X(i0):.1f}" y="{t}" width="{X(i1) - X(i0):.1f}" height="{ih}"/><text class="ax" x="{(X(i0) + X(i1)) / 2:.1f}" y="{t + 11}" text-anchor="middle">{esc(lab)}</text>')
    for i, lab in enumerate(xlabels):
        if i % tick_every == 0:
            out.append(f'<text class="ax" x="{X(i):.1f}" y="{h - 12}" text-anchor="middle">{esc(lab)}</text><line class="tick" x1="{X(i):.1f}" x2="{X(i):.1f}" y1="{t + ih}" y2="{t + ih + 4}"/>')
    for si, (name, vals) in enumerate(series):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        out.append(f'<polyline class="ln s{si + 1}" points="{pts}"/>')
        for i, v in enumerate(vals):
            out.append(f'<circle class="hit" cx="{X(i):.1f}" cy="{Y(v):.1f}" r="{max(3, min(7, iw / nx / 2)):.1f}" data-tip="{esc(f"{xlabels[i]} · {name} : {fmt(v)}{unit}")}"/>')
        lx, ly = X(nx - 1), Y(vals[-1])
        out.append(f'<circle class="dot s{si + 1}" cx="{lx:.1f}" cy="{ly:.1f}" r="3.5"/><text class="vl" x="{lx + 7:.1f}" y="{ly + 4:.1f}">{fmt(vals[-1])}</text>')
    for idx, txt in (note or []):
        v = series[0][1][idx]
        out.append(f'<circle class="ring" cx="{X(idx):.1f}" cy="{Y(v):.1f}" r="5"/><text class="ax em" x="{X(idx):.1f}" y="{Y(v) + 20:.1f}" text-anchor="middle">{esc(txt)}</text>')
    out.append(f'<line class="base" x1="{l}" x2="{w - r}" y1="{t + ih}" y2="{t + ih}"/></svg>')
    return "".join(out)


def table_html(headers, rows, caption=None) -> str:
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>" for r in rows)
    cap = f"<caption>{esc(caption)}</caption>" if caption else ""
    return f'<div class="tw"><table>{cap}<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'
