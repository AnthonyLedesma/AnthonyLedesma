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
  pass 0.25s to 1.45s, piece motion done by 2s, then hold. Cursors blink 4 times.
  The one exception is the contrib runner, which replays (see REPLAYS in build.py).
- The CSS base state of every animated element is its final state, so
  prefers-reduced-motion shows the finished frame.
"""

from __future__ import annotations

import base64
import html
import textwrap
from dataclasses import dataclass
from pathlib import Path

# ------------------------------------------------------------------ grid
W = 1200
M = 64  # side margin, both themes
STRIP = 56  # title strip height
RX = 14
CONTENT_R = W - M
SP = 36  # light mode sprocket strip, inside the margin

# narrow (phone) layout: 480 wide, served below 1012px viewports into GitHub's 238 to 578px
# column (x0.50 to x1.20). Small text is NS18 (about 11px at the 293px column of a 375 phone).
# Same frame, strip, tokens and timing; content re-flows.
NW, NM, NSP = 480, 32, 20
NCONTENT_R = NW - NM

# ------------------------------------------------------------------ type
S, MD, L, XL = 16, 20, 28, 72
NS = 18  # narrow small text
LH = 32  # line pitch for MD rows


def cw(size: float) -> float:
    """JetBrains Mono advance width."""
    return size * 0.6


# ------------------------------------------------------------------ tokens
PH, PH_HI, PH_LO, PH_INK = "#ffb641", "#fed579", "#ba7e23", "#2a1500"
PH_HOT, PH_DEEP = "#fff4d6", "#5c3d10"  # rev-video flash / estimate dot, darkest runner step
OK, OK_DIM, BETA, BETA_DIM = "#6ee7b7", "#1f4d3a", "#67e8f9", "#0f4c5f"
HOLE, SHADE = "#ffffff", "#000"  # sprocket hole fill, glass black (scanlines, vignette, power-off)
# runner sprite ramps, darkest first. The light ramp keeps the original label/accent inks on purpose.
RAMP_DARK = [PH_DEEP, PH_LO, PH, PH_HI]
RAMP_LIGHT = ["#1c1b19", "#7a420a", "#9c5906", PH]
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


DARK = Theme("dark", "#0f0e0c", "#201a12", "#eae7e1", PH_HI, "#a29d96", "#302d29", "#cc8d30", PH, OK, True)
LIGHT = Theme("light", "#fffdf8", "#f6f3ec", "#1c1b19", "#1c1b19", "#5f5a51", "#d9d3c5", "#874e06", "#7a420a", "#0a6a4a", False)
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
BLINK = ".blink{animation:blink 1.1s steps(1) 4 2s}@keyframes blink{50%{opacity:0}}"


class Anim:
    """Per-piece keyframes on the shared DONE clock. Every sequence runs once and holds.

    loop: a CSS iteration count ("infinite", "3"); empty runs once.
    """

    def __init__(self, dur: float = DONE, loop: str = ""):
        self.dur, self.css, self.n, self.loop = dur, [], 0, loop

    def p(self, t: float) -> str:
        assert t <= self.dur + 1e-9, (t, self.dur)  # a keyframe past the clock silently becomes a whole-clock fade
        return f"{max(t / self.dur * 100, 0):.3f}%"

    def cls(self) -> str:
        self.n += 1
        return f"a{self.n}"

    def run(self, c: str) -> str:
        return f"animation:{c} {self.dur}s{' ' + self.loop if self.loop else ''} both"

    def type(self, start: float, s: str, pad: int = 16) -> str:
        """Reveal a line left to right at CPS, one whole character per step, then release the glow pad."""
        c, n = self.cls(), max(len(s), 1)
        end = start + n / CPS
        self.css.append(
            f".{c}{{{self.run(c)}}}@keyframes {c}{{0%,{self.p(start)}{{clip-path:inset(-{pad}px 100% -{pad}px 0);animation-timing-function:steps({n},end)}}"
            f"{self.p(end)}{{clip-path:inset(-{pad}px 0 -{pad}px 0);animation-timing-function:steps(1,end)}}"
            f"{self.p(end + 0.01)},100%{{clip-path:inset(-{pad}px -{pad}px -{pad}px -{pad}px)}}}}"
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


def _wrap(s: str, width: int, hang: int) -> list[str]:
    lines = textwrap.wrap(s, width, subsequent_indent=" " * hang, break_long_words=False, break_on_hyphens=False)
    return [ln[hang:] if i else ln for i, ln in enumerate(lines)]


def wrap(s: str, width: int, hang: int = 0, balance: bool = False) -> list[str]:
    """Word wrap that never splits words or hyphenated tokens, and never leaves a " · " separator at a break.

    hang: continuation lines are that many columns narrower (the caller indents them).
    balance: the narrowest width that keeps the greedy line count, so lines come out even and no word is orphaned.
    """
    lines = _wrap(s, width, hang)
    if balance:
        for w2 in range(width - 1, 0, -1):
            alt = _wrap(s, w2, hang)
            if len(alt) != len(lines) or any(len(ln) + (hang if i else 0) > w2 for i, ln in enumerate(alt)):
                break
            lines = alt
    out = []
    for ln in lines:
        ln = ln[:-2] if ln.endswith(" ·") else ln
        out.append(ln[2:] if ln.startswith("· ") else ln)
    return out


def wrap_spans(spans, width: int, balance: bool = False) -> list[list[tuple[str, str]]]:
    """Wrap colored spans [(color, str)] into lines of spans, preserving every character but the break spaces."""
    plain = "".join(s for _, s in spans)
    owner = [c for c, s in spans for _ in s]
    out, pos = [], 0
    for line in wrap(plain, width, balance=balance):
        pos = plain.index(line, pos)
        cur: list[tuple[str, str]] = []
        for i in range(pos, pos + len(line)):
            if cur and cur[-1][0] == owner[i]:
                cur[-1] = (owner[i], cur[-1][1] + plain[i])
            else:
                cur.append((owner[i], plain[i]))
        out.append(cur)
        pos += len(line)
    return out


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
    return text(x + 2, y + 2, [(PH, s)], size, cls, 700, ls + ' aria-hidden="true"') + text(x, y, [(t.display, s)], size, cls, 700, ls)


def cursor(t: Theme, x: float, y: float, size: float = MD, cls: str = "") -> str:
    c = f' class="{cls}"' if cls else ""
    return f'<g{c}><rect class="blink" x="{x:g}" y="{y - size * 0.8:g}" width="{size * 0.55:g}" height="{size:g}" fill="{t.accent}"/></g>'


TIER_WORD = {"available": "AVAILABLE", "beta": "BETA", "soon": "COMING SOON"}


def badge_w(tier: str, size: float = S) -> float:
    """Pill width: 0.6em advance + .08em tracking per char (tracine.dev .badge), plus a 2em pip/padding allowance."""
    return 2 * size + len(TIER_WORD[tier]) * size * 0.68


def badge(x: float, y: float, tier: str, t: Theme, size: float = S) -> str:
    """tracine.dev tier pill. y is the text baseline. AVAILABLE and BETA keep fixed hues; COMING SOON follows the theme.

    The pip carries the tier as a shape too: solid (available), half-filled with outline (beta), hollow (soon).
    """
    word, fg, bg, dashed = {
        "available": (TIER_WORD["available"], OK, OK_DIM, False),
        "beta": (TIER_WORD["beta"], BETA, BETA_DIM, False),
        "soon": (TIER_WORD["soon"], t.muted, "none", True),
    }[tier]
    stroke = f' stroke="{t.muted}" stroke-dasharray="3 2"' if dashed else ""
    px, py = x + size * 0.625, y - size * 0.625
    ring = f'<rect x="{px + .5:g}" y="{py + .5:g}" width="7" height="7" rx="1" fill="none" stroke="{fg}"/>'
    pip = {
        "available": f'<rect x="{px:g}" y="{py:g}" width="8" height="8" rx="1" fill="{fg}"/>',
        "beta": ring + f'<rect x="{px:g}" y="{py:g}" width="4" height="8" fill="{fg}"/>',
        "soon": ring,
    }[tier]
    return (
        f'<rect x="{x:g}" y="{y - size - 2:g}" width="{badge_w(tier, size):.1f}" height="{size + 9:g}" rx="4" fill="{bg}"{stroke}/>'
        + pip
        + f'<text x="{x + 1.5 * size:g}" y="{y:g}" font-size="{size}" font-weight="600" letter-spacing="{size * 0.08:g}" fill="{fg}">{word}</text>'
    )


MARK_NODES = [(27, 9, 6.5), (11, 34, 6), (43, 34, 6), (27, 50, 5.5)]
MARK_EDGES = [((27, 9), (11, 34)), ((27, 9), (43, 34)), ((11, 34), (27, 50)), ((43, 34), (27, 50))]


def mark(x: float, y: float, s: float, color: str, a: Anim | None = None, hi: str = PH_HI, pulse_at: float | None = None, filt: str = "") -> str:
    """Tracine node mark (viewBox 54x58) at scale s, stroke 3 mark units with butt caps like tracine.dev, optional single pulse."""
    out = [
        f'<line x1="{x + x1 * s:.1f}" y1="{y + y1 * s:.1f}" x2="{x + x2 * s:.1f}" y2="{y + y2 * s:.1f}" stroke="{color}" stroke-width="{3 * s:.2f}"/>'
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


def frame(
    t: Theme, H: int, a: Anim, label: str, piece: str, body: str, strip: bool = True, extra_defs: str = "",
    w: int = W, m: int = M, sp: int = SP, ts: float = S,
) -> str:
    """The one panel. piece: the strip's right-hand label, e.g. 'WHOAMI'. w/m/sp pick the wide or narrow grid."""
    power = (
        f".pwr{{transform-origin:{w / 2}px {H / 2}px;animation:pwr {POWER}s both}}"
        "@keyframes pwr{0%{transform:scale(.02,.004)}40%{transform:scale(1,.004)}100%{transform:scale(1,1)}}"
        if t.dark
        else f".pwr{{animation:pwr {POWER}s ease-out both}}@keyframes pwr{{0%{{opacity:0;transform:translateY(10px)}}100%{{opacity:1;transform:translateY(0)}}}}"
    )
    beam = f".beam{{animation:beam {BEAM_DUR}s linear {BEAM_START}s both}}@keyframes beam{{from{{transform:translateY(0)}}to{{transform:translateY({H + 100}px)}}}}"
    css = FONT_CSS + power + beam + BLINK + "".join(a.css) + REDUCED
    band_op = ".08" if t.dark else ".2"
    defs = (
        f'<linearGradient id="band" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PH}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{PH}" stop-opacity="{band_op}"/><stop offset="1" stop-color="{PH}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="panel"><rect width="{w}" height="{H}" rx="{RX}"/></clipPath>'
    )
    if t.dark:
        defs += (
            f'<radialGradient id="glass" cx=".3" cy=".2" r="1"><stop offset="0" stop-color="{t.bar}"/><stop offset=".85" stop-color="{t.bg}"/></radialGradient>'
            f'<radialGradient id="vig" cx=".5" cy=".5" r=".8"><stop offset=".65" stop-color="{SHADE}" stop-opacity="0"/><stop offset="1" stop-color="{SHADE}" stop-opacity=".45"/></radialGradient>'
            f'<pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" fill="{SHADE}" opacity=".3"/></pattern>'
            + _glow_filter("gname", 7, 0.85) + _glow_filter("gsoft", 3, 0.5) + _glow_filter("gline", 2.5, 0.8)
        )
        ground = f'<rect width="{w}" height="{H}" fill="url(#glass)"/>'
        over = f'<rect width="{w}" height="{H}" fill="url(#scan)"/><rect width="{w}" height="{H}" fill="url(#vig)"/>'
    else:
        defs += f'<pattern id="dot" width="3" height="3" patternUnits="userSpaceOnUse"><rect y="2" width="3" height="1" fill="{t.bg}" opacity=".1"/></pattern>'
        bars = "".join(f'<rect x="{sp}" y="{y}" width="{w - 2 * sp}" height="32" fill="{t.bar}"/>' for y in range(STRIP if strip else 0, H, 64))
        holes = "".join(
            f'<circle cx="{sp / 2}" cy="{cy}" r="5.5" fill="{HOLE}" stroke="{t.edge}"/><circle cx="{w - sp / 2}" cy="{cy}" r="5.5" fill="{HOLE}" stroke="{t.edge}"/>'
            for cy in range(16, H - 8, 24)
        )
        perf = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{t.edge}" stroke-dasharray="3 4"/>' for x in (sp, w - sp))
        ground = f'<rect width="{w}" height="{H}" fill="{t.bg}"/>{bars}{perf}{holes}'
        over = f'<rect x="{sp}" width="{w - 2 * sp}" height="{H}" fill="url(#dot)"/>'
    head = ""
    if strip:
        brand = "TRACINE TERMINAL" if t.dark else "TRACINE PRINTOUT"
        tty = ("TTY1 · " if t.dark else "LPT1 · ") + piece
        # caps advance is 0.6em + 1.9 tracking. Drop the device prefix if it would crowd the brand on the longest
        # piece label (CONTRIB), so every piece in a theme and grid makes the same choice.
        if m + 32 + len(brand) * (cw(ts) + 1.9) + 24 > w - m - len(tty) * (cw(ts) + 1.9) - (7 - len(piece)) * (cw(ts) + 1.9):
            tty = piece
        head = (
            mark(m, 17, 0.4, t.accent)
            + caps(m + 32, 35, brand, t.label, ts)
            + caps(w - m, 35, tty, t.label, ts, anchor="end")
            + f'<rect x="0" y="{STRIP}" width="{w}" height="1" fill="{t.accent if t.dark else t.edge}" opacity="{".18" if t.dark else "1"}"/>'
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {H}" width="{w}" height="{H}" role="img" aria-label="{esc(label)}">'
        f"<style>{css}</style><defs>{defs}{extra_defs}</defs>"
        f'<rect width="{w}" height="{H}" rx="{RX}" fill="{t.bg}"/>'
        f'<g clip-path="url(#panel)">'
        + (f'<rect width="{w}" height="{H}" fill="{SHADE}"/>' if t.dark else "")
        + f'<g class="pwr">{ground}{head}{body}<rect class="beam" x="0" y="-100" width="{w}" height="100" fill="url(#band)"/></g>'
        + over + "</g>"
        + f'<rect x=".5" y=".5" width="{w - 1}" height="{H - 1}" rx="{RX}" fill="none" stroke="{t.edge}"/></svg>'
    )
