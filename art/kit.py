"""Phosphor system kit: the one module every profile piece is built from.

Tokens, font, type scale, grid, frame, title strip and timing live here and
nowhere else, so every piece shares edges, type and motion exactly.

Rules every piece inherits:
- 1200-unit viewBox width, rendered at about 830px in a README column (x0.69).
- Type scale S/M/L/XL = 16/20/28/72. S16 is the floor (11px rendered).
- Margin 64 on both sides in both themes (light mode's sprocket strips sit in it).
- One frame: radius 14, 1px edge, title strip 56 tall, glass + scanlines + vignette
  (dark) or greenbar paper + print banding (light).
- One timing: 0.25s power-on (dark: beam collapse opens; light: form feed), one beam
  pass 0.25s to 1.45s, piece motion done by 2s, then hold. Cursors blink 8 times.
- The CSS base state of every animated element is its final state, so
  prefers-reduced-motion shows the finished frame.
"""

from __future__ import annotations

import base64
import html
from dataclasses import dataclass
from pathlib import Path

# ------------------------------------------------------------------ grid
W = 1200
M = 64  # side margin, both themes
STRIP = 56  # title strip height
RX = 14
CONTENT_R = W - M

# ------------------------------------------------------------------ type
S, MD, L, XL = 16, 20, 28, 72
LH = 32  # line pitch for MD rows


def cw(size: float) -> float:
    """JetBrains Mono advance width."""
    return size * 0.6


# ------------------------------------------------------------------ tokens
PH, PH_HI, PH_LO, PH_INK = "#ffb641", "#fed579", "#ba7e23", "#2a1500"
OK, OK_DIM, BETA, BETA_DIM = "#6ee7b7", "#285f47", "#67e8f9", "#155e75"
PROMPT = "C:\\TRACINE> "


@dataclass(frozen=True)
class Theme:
    name: str
    bg: str  # panel ground (glass edge / paper)
    bar: str  # glass center / greenbar stripe
    text: str
    display: str  # the big name
    muted: str
    edge: str  # 1px panel edge and rules
    label: str  # strip labels, prompts, axis labels
    accent: str  # amber text and marks
    ok: str
    dark: bool

    @property
    def rule(self) -> str:
        return self.edge


DARK = Theme("dark", "#0f0e0c", "#201a12", "#eae7e1", PH_HI, "#a29d96", "#302d29", PH_LO, PH, OK, True)
LIGHT = Theme("light", "#fffdf8", "#f6f3ec", "#1c1b19", "#1c1b19", "#6b665c", "#d9d3c5", "#9c5906", "#7a420a", "#0a6a4a", False)
THEMES = [DARK, LIGHT]

# ------------------------------------------------------------------ font
_MONO = base64.b64encode((Path(__file__).parent / "mono-subset.woff2").read_bytes()).decode()
FONT_CSS = (
    f'@font-face{{font-family:M;src:url(data:font/woff2;base64,{_MONO}) format("woff2");font-weight:100 800}}'
    "text{font-family:M,ui-monospace,'SF Mono',Menlo,Consolas,monospace}"
)
REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"

# ------------------------------------------------------------------ timing
POWER = 0.25  # power-on / form feed
BEAM_START, BEAM_DUR = 0.25, 1.2
DONE = 2.0  # every piece's own motion ends by here
CPS = 60  # typing speed, chars per second
BLINK = ".blink{animation:blink 1.1s steps(1) 8 2s}@keyframes blink{50%{opacity:0}}"


class Anim:
    """Per-piece keyframes on the shared DONE clock. Every sequence runs once and holds."""

    def __init__(self, dur: float = DONE):
        self.dur, self.css, self.n = dur, [], 0

    def p(self, t: float) -> str:
        return f"{min(max(t / self.dur * 100, 0), 100):.3f}%"

    def cls(self) -> str:
        self.n += 1
        return f"a{self.n}"

    def run(self, c: str) -> str:
        return f"animation:{c} {self.dur}s both"

    def type(self, start: float, s: str, pad: int = 16) -> str:
        """Reveal a line left to right at CPS."""
        c, n = self.cls(), max(len(s), 1)
        hid, show = f"inset(-{pad}px 100% -{pad}px 0)", f"inset(-{pad}px -{pad}px -{pad}px -{pad}px)"
        self.css.append(
            f".{c}{{{self.run(c)}}}@keyframes {c}{{0%,{self.p(start)}{{clip-path:{hid};animation-timing-function:steps({n},end)}}"
            f"{self.p(start + n / CPS)},100%{{clip-path:{show}}}}}"
        )
        return c

    def show(self, start: float) -> str:
        c = self.cls()
        self.css.append(f".{c}{{{self.run(c)}}}@keyframes {c}{{0%,{self.p(start)}{{opacity:0}}{self.p(start + 0.01)},100%{{opacity:1}}}}")
        return c

    def fade(self, start: float, dur: float = 0.2) -> str:
        c = self.cls()
        self.css.append(f".{c}{{{self.run(c)}}}@keyframes {c}{{0%,{self.p(start)}{{opacity:0}}{self.p(start + dur)},100%{{opacity:1}}}}")
        return c

    def grow(self, start: float, dur: float, axis: str = "Y", origin: str = "50% 100%") -> str:
        """scaleX/scaleY from 0 around a fill-box origin."""
        c = self.cls()
        self.css.append(
            f".{c}{{transform-box:fill-box;transform-origin:{origin};{self.run(c)}}}"
            f"@keyframes {c}{{0%,{self.p(start)}{{transform:scale{axis}(0)}}{self.p(start + dur)},100%{{transform:scale{axis}(1)}}}}"
        )
        return c

    def draw(self, start: float, dur: float) -> str:
        """Stroke draw-on for elements with pathLength=1."""
        c = self.cls()
        self.css.append(
            f".{c}{{stroke-dasharray:1;stroke-dashoffset:0;{self.run(c)}}}"
            f"@keyframes {c}{{0%,{self.p(start)}{{stroke-dashoffset:1}}{self.p(start + dur)},100%{{stroke-dashoffset:0}}}}"
        )
        return c

    def flash(self, start: float, prop: str, base: str, hot: str, dur: float = 0.4) -> str:
        c = self.cls()
        self.css.append(f".{c}{{{self.run(c)}}}@keyframes {c}{{0%,{self.p(start)}{{{prop}:{base}}}{self.p(start + 0.05)}{{{prop}:{hot}}}{self.p(start + dur)},100%{{{prop}:{base}}}}}")
        return c

    def raw(self, css: str) -> None:
        self.css.append(css)


# ------------------------------------------------------------------ primitives
def esc(s: str) -> str:
    return html.escape(s, quote=False)


def text(x: float, y: float, spans, size: float, cls: str = "", weight: int = 400, extra: str = "") -> str:
    """spans: [(color, str)] on one line."""
    t = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for c, s in spans)
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{x:g}" y="{y:g}" font-size="{size}" font-weight="{weight}" xml:space="preserve"{c}{extra}>{t}</text>'


def caps(x: float, y: float, s: str, color: str, size: float = S, anchor: str = "start", cls: str = "", weight: int = 500) -> str:
    return text(x, y, [(color, s.upper())], size, cls, weight, f' letter-spacing="1.9" text-anchor="{anchor}"')


def glow(t: Theme, which: str = "soft") -> str:
    """Filter attribute: phosphor bloom in dark, nothing on paper."""
    return f' filter="url(#g{which})"' if t.dark else ""


def display(t: Theme, x: float, y: float, s: str, size: float = XL, cls: str = "") -> str:
    """The big name: bloom on glass, two-color ribbon misregistration on paper."""
    ls = ' letter-spacing="-1.5"'
    if t.dark:
        return text(x, y, [(t.display, s)], size, cls, 700, ls + glow(t, "name"))
    return text(x + 2, y + 2, [(PH, s)], size, cls, 700, ls) + text(x, y, [(t.display, s)], size, cls, 700, ls)


def cursor(t: Theme, x: float, y: float, size: float = MD, cls: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<g{c}><rect class="blink" x="{x:g}" y="{y - size * 0.8:g}" width="{size * 0.55:g}" height="{size:g}" fill="{t.accent}"/></g>'


def badge(x: float, y: float, tier: str) -> str:
    """tracine.dev tier pill, fixed hues in both themes. y is the text baseline."""
    word, fg, bg, dashed = {
        "available": ("AVAILABLE", OK, OK_DIM, False),
        "beta": ("BETA", BETA, BETA_DIM, False),
        "soon": ("COMING SOON", "#a29d96", "none", True),
    }[tier]
    w = 32 + len(word) * 10.4
    stroke = ' stroke="#a29d96" stroke-dasharray="3 2"' if dashed else ""
    return (
        f'<rect x="{x:g}" y="{y - 18:g}" width="{w:.1f}" height="25" rx="4" fill="{bg}"{stroke}/>'
        f'<rect x="{x + 10:g}" y="{y - 10:g}" width="8" height="8" rx="1" fill="{fg}"/>'
        f'<text x="{x + 24:g}" y="{y:g}" font-size="{S}" font-weight="600" letter-spacing="1" fill="{fg}">{word}</text>'
    )


def badge_w(tier: str) -> float:
    return 32 + len({"available": "AVAILABLE", "beta": "BETA", "soon": "COMING SOON"}[tier]) * 10.4


MARK_NODES = [(27, 9, 6.5), (11, 34, 6), (43, 34, 6), (27, 50, 5.5)]
MARK_EDGES = [((27, 9), (11, 34)), ((27, 9), (43, 34)), ((11, 34), (27, 50)), ((43, 34), (27, 50))]


def mark(x: float, y: float, s: float, color: str, stroke: float, a: Anim | None = None, hi: str = PH_HI, pulse_at: float | None = None, filt: str = "") -> str:
    """Tracine node mark (viewBox 54x58) at scale s, optional single pulse top to bottom."""
    out = [
        f'<line x1="{x + x1 * s:.1f}" y1="{y + y1 * s:.1f}" x2="{x + x2 * s:.1f}" y2="{y + y2 * s:.1f}" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round"/>'
        for (x1, y1), (x2, y2) in MARK_EDGES
    ]
    out += [f'<circle cx="{x + cx * s:.1f}" cy="{y + cy * s:.1f}" r="{r * s:.1f}" fill="{color}"/>' for cx, cy, r in MARK_NODES]
    if a and pulse_at is not None:
        for i, (cx, cy, r) in enumerate(MARK_NODES):
            st = pulse_at + [0, 0.15, 0.15, 0.3][i]
            c = a.cls()
            a.raw(f".{c}{{opacity:0;{a.run(c)}}}@keyframes {c}{{0%,{a.p(st)}{{opacity:0}}{a.p(st + 0.06)}{{opacity:1}}{a.p(st + 0.5)},100%{{opacity:0}}}}")
            out.append(f'<circle class="{c}" cx="{x + cx * s:.1f}" cy="{y + cy * s:.1f}" r="{r * s * 0.62:.1f}" fill="{hi}"/>')
    return f"<g{filt}>{''.join(out)}</g>"


# ------------------------------------------------------------------ frame
def _glow_filter(fid: str, sd: float, opacity: float) -> str:
    return (
        f'<filter id="{fid}" x="-20%" y="-60%" width="140%" height="220%"><feGaussianBlur stdDeviation="{sd}" result="b"/>'
        f'<feComponentTransfer in="b" result="g"><feFuncA type="linear" slope="{opacity}"/></feComponentTransfer>'
        f'<feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
    )


def frame(t: Theme, H: int, a: Anim, label: str, piece: str, body: str, strip: bool = True, extra_defs: str = "") -> str:
    """The one panel. piece: the strip's right-hand label, e.g. 'WHOAMI'."""
    power = (
        f".pwr{{transform-origin:{W / 2}px {H / 2}px;animation:pwr {POWER}s both}}"
        "@keyframes pwr{0%{transform:scale(.02,.004)}40%{transform:scale(1,.004)}100%{transform:scale(1,1)}}"
        if t.dark
        else f".pwr{{animation:pwr {POWER}s ease-out both}}@keyframes pwr{{0%{{opacity:0;transform:translateY(-10px)}}100%{{opacity:1;transform:translateY(0)}}}}"
    )
    beam = f".beam{{animation:beam {BEAM_DUR}s linear {BEAM_START}s both}}@keyframes beam{{from{{transform:translateY(0)}}to{{transform:translateY({H + 100}px)}}}}"
    css = FONT_CSS + power + beam + BLINK + "".join(a.css) + REDUCED
    band_op = ".08" if t.dark else ".2"
    defs = (
        f'<linearGradient id="band" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PH}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{PH}" stop-opacity="{band_op}"/><stop offset="1" stop-color="{PH}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="panel"><rect width="{W}" height="{H}" rx="{RX}"/></clipPath>'
    )
    if t.dark:
        defs += (
            f'<radialGradient id="glass" cx=".3" cy=".2" r="1"><stop offset="0" stop-color="{t.bar}"/><stop offset=".85" stop-color="{t.bg}"/></radialGradient>'
            '<radialGradient id="vig" cx=".5" cy=".5" r=".8"><stop offset=".65" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".45"/></radialGradient>'
            '<pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" fill="#000" opacity=".3"/></pattern>'
            + _glow_filter("gname", 7, 0.85) + _glow_filter("gsoft", 3, 0.5) + _glow_filter("gline", 2.5, 0.8)
        )
        ground = f'<rect width="{W}" height="{H}" fill="url(#glass)"/>'
        over = f'<rect width="{W}" height="{H}" fill="url(#scan)"/><rect width="{W}" height="{H}" fill="url(#vig)"/>'
    else:
        defs += f'<pattern id="dot" width="3" height="3" patternUnits="userSpaceOnUse"><rect y="2" width="3" height="1" fill="{t.bg}" opacity=".4"/></pattern>'
        sp = 36  # sprocket strip, inside the margin
        bars = "".join(f'<rect x="{sp}" y="{y}" width="{W - 2 * sp}" height="32" fill="{t.bar}"/>' for y in range(STRIP if strip else 0, H, 64))
        holes = "".join(
            f'<circle cx="{sp / 2}" cy="{cy}" r="5.5" fill="#ffffff" stroke="{t.edge}"/><circle cx="{W - sp / 2}" cy="{cy}" r="5.5" fill="#ffffff" stroke="{t.edge}"/>'
            for cy in range(16, H - 8, 24)
        )
        perf = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{t.edge}" stroke-dasharray="3 4"/>' for x in (sp, W - sp))
        ground = f'<rect width="{W}" height="{H}" fill="{t.bg}"/>{bars}{perf}{holes}'
        over = f'<rect x="{sp}" width="{W - 2 * sp}" height="{H}" fill="url(#dot)"/>'
    head = ""
    if strip:
        brand = "TRACINE TERMINAL" if t.dark else "TRACINE · LPT1"
        tty = ("TTY1 · " if t.dark else "LPT1 · ") + piece
        head = (
            mark(M, 17, 0.4, t.accent, 1.8)
            + caps(M + 32, 35, brand, t.label)
            + caps(CONTENT_R, 35, tty, t.label, anchor="end")
            + f'<rect x="0" y="{STRIP}" width="{W}" height="1" fill="{t.accent if t.dark else t.edge}" opacity="{".18" if t.dark else "1"}"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(label)}">'
        f"<style>{css}</style><defs>{defs}{extra_defs}</defs>"
        f'<rect width="{W}" height="{H}" rx="{RX}" fill="{t.bg}"/>'
        f'<g clip-path="url(#panel)">'
        + (f'<rect width="{W}" height="{H}" fill="#000"/>' if t.dark else "")
        + f'<g class="pwr">{ground}{head}{body}<rect class="beam" x="0" y="-100" width="{W}" height="100" fill="url(#band)"/></g>'
        + over + "</g>"
        + f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="{RX}" fill="none" stroke="{t.edge}"/></svg>'
    )
