"""Build the profile README art from kit.py, dark and light.

Run from any directory: python3 art/build.py
Reads art/contrib.json (written by fetch_contrib.py) and writes the SVGs next to this file.
"""

import datetime as dt
import json
import re
from pathlib import Path

from kit import (
    CPS, M, MD, NS, PH_DEEP, PH_HI, PH_HOT, PH_LO, PROMPT, RAMP_DARK, RAMP_LIGHT, S, THEMES, CONTENT_R, L,
    NCONTENT_R, NM, NSP, NW, W,
    Anim, Theme, caps, cursor, cw, display, frame, glow, text, wrap, wrap_spans,
)

HERE = Path(__file__).resolve().parent
ACCOUNTS = ["AnthonyLedesma", "AnthonyLedesmaTR", "anthonyl-mf"]  # personal first; the rest stack as one work layer


def _weeks(cal: dict) -> list[tuple[dt.date, int, list[int]]]:
    """Both calendars aligned by date into Sunday-start weeks: (sunday, days seen, [count per account])."""
    by: dict[dt.date, tuple[set, list[int]]] = {}
    for k, login in enumerate(ACCOUNTS):
        for w in cal[login]["weeks"]:
            for d in w["contributionDays"]:
                day = dt.date.fromisoformat(d["date"])
                days, row = by.setdefault(day - dt.timedelta(days=(day.weekday() + 1) % 7), (set(), [0] * len(ACCOUNTS)))
                days.add(day)
                row[k] += d["contributionCount"]
    return [(sun, len(by[sun][0]), by[sun][1]) for sun in sorted(by)]


WEEKS = _weeks(json.loads((HERE / "contrib.json").read_text()))
TAG = "Agent systems, and the evals that keep them honest."
ROLE = "Staff AI Engineer"
NCOLS_S, NCOLS_L = (int((NCONTENT_R - NM) // cw(z)) for z in (NS, L))  # 38, 24 chars on the narrow grid

# contrib runner replay. README images can't detect scrolling, so a replay is how visitors actually get to see the run.
REPLAY = 20.0  # seconds from the start of one pass to the next
REPLAYS = None  # None = every 20s forever; an int caps the passes

# masthead rows
Y_PROMPT, Y_NAME, Y_TAG, Y_RULE, Y_FOOT, H_HEAD = 108, 192, 240, 274, 312, 344
NPAD_B = 24  # narrow: last baseline to frame edge


def hrule(t: Theme, y: float, m: int = M, r: int = CONTENT_R) -> str:
    return f'<rect x="{m}" y="{y}" width="{r - m}" height="1" fill="{t.edge}"/>'


# ------------------------------------------------------------------ 1. header
def header(t: Theme) -> str:
    """Name dominant from the end of power-on (0.25s). Only the tagline types (0.3 to 1.15s)."""
    a = Anim()
    body = (
        text(M, Y_PROMPT, [(t.label, PROMPT), (t.accent, "whoami")], MD, extra=glow(t))
        + display(t, M - 3, Y_NAME, "Anthony Ledesma")
        + text(M, Y_TAG, [(t.accent, TAG)], L, a.type(0.3, TAG), extra=glow(t))
        + hrule(t, Y_RULE)
        + text(M, Y_FOOT, [(t.label, PROMPT)], MD)
        + cursor(t, M + len(PROMPT) * cw(MD), Y_FOOT, MD, a.show(1.15))
    )
    return frame(t, H_HEAD, a, f"Anthony Ledesma, {ROLE}. {TAG}", "WHOAMI", body)


# ------------------------------------------------- 2. contrib with the runner
def _sprite(name: str) -> str:
    raw = (HERE / f"sprite-{name}.svg").read_text().strip()
    return re.sub(r"^<svg[^>]*>|</svg>$", "", raw)


def _lum(h: str) -> float:
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _recolor(body: str, ramp: list[str]) -> str:
    """Map each sprite color to a 4-step ramp by luminance (darkest first)."""
    def pick(m: re.Match) -> str:
        v = _lum(m.group(1))
        i = 0 if v < 0.1 else 1 if v < 0.3 else 2 if v < 0.6 else 3
        return f'fill="{ramp[i]}"'
    return re.sub(r'fill="(#[0-9a-fA-F]{6})"', pick, body)


def _replay_phrase() -> str:
    if REPLAYS is None:
        return ", and runs again every 20 seconds"
    if REPLAYS <= 1:
        return ""
    more = REPLAYS - 1
    return f", and runs {'once' if more == 1 else f'{more} times'} more, 20 seconds apart"


CONTRIB_ALT = (
    "Weekly GitHub contributions for the last 12 months: personal account AnthonyLedesma, plus work accounts "
    "AnthonyLedesmaTR and anthonyl-mf (private repos, counts only). A pixel runner crosses the bars "
    + ("every 20 seconds" if REPLAYS is None else "once" if REPLAYS <= 1 else f"{REPLAYS} times, 20 seconds apart")
    + ". Updated daily."
)
CONTRIB_NOTE = "calendars of @AnthonyLedesma, @AnthonyLedesmaTR, @anthonyl-mf · updated daily"
LEGEND_WORK = "private repos, counts only"
# second layer (the work accounts): a dimmer amber with a 45-degree hatch, so it differs from the solid layer in
# pattern as well as tone. Dark: lo amber stripes on deep amber. Light: the runner ramp's amber on a pale amber wash.
HATCH = {True: (PH_DEEP, PH_LO), False: ("#f3dfb8", RAMP_LIGHT[2])}


def _hatch(t: Theme) -> str:
    base, ink = HATCH[t.dark]
    return (
        '<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<rect width="6" height="6" fill="{base}"/><rect width="3" height="6" fill="{ink}"/></pattern>'
    )


def _legend(t: Theme, narrow: bool) -> tuple[list[str], float]:
    """Swatch per layer. Wide: one row (y 140). Narrow: stacked, the work note on its own line under its label."""
    m, sz = (NM, NS) if narrow else (M, S)
    k = 12 if narrow else 14
    def sw(x: float, y: float, fill: str) -> str:
        return f'<rect x="{x:g}" y="{y - k + 1:g}" width="{k}" height="{k}" fill="{fill}"/>'
    a_name, b_name = "personal", "work"  # handles live in the caption
    if narrow:
        tx = m + k + 10
        out = [
            sw(m, 166, t.label) + text(tx, 166, [(t.text, a_name)], sz),
            sw(m, 194, "url(#hatch)") + text(tx, 194, [(t.text, b_name)], sz),
            text(tx, 220, [(t.muted, LEGEND_WORK)], sz),
        ]
        return out, 220
    x2 = m + k + 10 + len(a_name) * cw(sz) + 36
    out = [
        sw(m, 140, t.label) + text(m + k + 10, 140, [(t.text, a_name)], sz),
        sw(x2, 140, "url(#hatch)") + text(x2 + k + 10, 140, [(t.text, b_name), (t.muted, " · " + LEGEND_WORK)], sz),
    ]
    return out, 140


def contrib_runner(t: Theme, narrow: bool = False) -> str:
    """Weekly totals as stacked bars: AnthonyLedesma solid phosphor at the base, the work accounts summed and
    hatched on top, on one linear scale whose top is the busiest combined week. The runner enters from off the left
    edge, crosses (0.3 to 2.6s) bumping each week with a +1 over the busiest combined weeks, then stands at the right
    edge. On replay he runs off the right edge and back in from the left, so the loop seam happens while he is hidden
    by the panel clip. Bars rise only once (they are static).

    narrow: same bars and runner on the 480 grid, a month label about every quarter, legend and caption stacked.
    """
    passes = 1 if REPLAYS is None else max(1, REPLAYS)
    a = Anim(REPLAY * passes, "infinite" if REPLAYS is None else "")
    counts = [(c[0], sum(c[1:])) for _, _, c in WEEKS]
    totals = [sum(c) for c in counts]
    n = len(totals)
    partial = WEEKS[-1][1] < 7
    m, cr, fw, sz = (NM, NCONTENT_R, NW, NS) if narrow else (M, CONTENT_R, W, S)
    legend, y_leg = _legend(t, narrow)
    ytop = y_leg + 42
    ybase = ytop + (178 if narrow else 172)
    x0, x1 = (m, cr - 36) if narrow else (M, CONTENT_R - 56)
    peak = max(max(totals), 1)
    slot = (x1 - x0) / n
    bw = slot * (0.72 if narrow else 0.62)
    gap = 2  # paper/glass between the two layers, taken out of the top layer so the stack height stays on scale
    sw, sh = 30, 48  # sprite 20x32 at 1.5
    xs, xe, xo = -sw - 2, cr - sw, fw + 2  # start and exit are both behind the panel clip
    t_s, t_e = 0.3, 2.6
    v = (xe - xs) / (t_e - t_s)
    t_x = REPLAY - 0.01 - (xo - xe) / v  # exit at run speed, gone just before the next pass
    busy: list[int] = []  # the six busiest combined weeks, at least 4 weeks apart so their +1s never overlap
    for i in sorted(range(n), key=lambda i: -totals[i]):
        if len(busy) < 6 and all(abs(i - j) >= 4 for j in busy):
            busy.append(i)
    offs = [p * REPLAY for p in range(passes)]
    exits = [REPLAYS is None or p < passes - 1 for p in range(passes)]

    def X(i: float) -> float:
        return x0 + (i + 0.5) * slot

    def at(tt: float) -> float:
        return xs + v * (tt - t_s)

    def tc_of(i: int) -> float:
        return t_s + (X(i) - sw / 2 - xs) / v

    sub = "one bar per week, last 12 months"
    body = [
        text(m, 100, [(t.accent, "contributions per week")], MD, weight=700, extra=glow(t)),
        text(m, 130, [(t.muted, sub)], NS) if narrow else text(CONTENT_R, 100, [(t.muted, sub)], S, extra=' text-anchor="end"'),
        *legend,
        f'<rect x="{m}" y="{ybase}" width="{cr - m}" height="2" fill="{t.edge}"/>',
    ]
    bars, pluses = [], []
    span = ybase - ytop
    for i, (own, work) in enumerate(counts):
        if not own + work:
            continue
        xc, tc = X(i), tc_of(i)
        h_all = max((own + work) / peak * span, 2)
        h_own = max(own / peak * span, 2) if own else 0
        segs, y_top = [], ybase - h_own
        if own:
            segs.append(f'<rect x="{xc - bw / 2:.1f}" y="{ybase - h_own:.1f}" width="{bw:.1f}" height="{h_own:.1f}" fill="{t.label}"/>')
        if work:
            top = ybase - max(h_all, h_own + gap + 2) if own else ybase - h_all
            bot = ybase - h_own - (gap if own else 0)
            segs.append(f'<rect x="{xc - bw / 2:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{bot - top:.1f}" fill="url(#hatch)"/>')
            y_top = top
        h = ybase - y_top
        op = ' opacity=".7"' if partial and i == n - 1 else ""
        c = a.cls()
        lift = 8 if i in busy else 4
        kf = "".join(f"{a.p(o + tc - .05)}{{transform:none}}{a.p(o + tc)}{{transform:translateY(-{lift}px)}}{a.p(o + tc + .15)}{{transform:none}}" for o in offs)
        a.raw(f".{c}{{{a.run(c)}}}@keyframes {c}{{0%{{transform:none}}{kf}100%{{transform:none}}}}")
        bars.append(f'<g class="{c}"{op}>{"".join(segs)}</g>')
        if i in busy:
            pc = a.cls()
            kf = "".join(
                f"{a.p(o + tc)}{{opacity:0;transform:translateY(0)}}{a.p(o + tc + .02)}{{opacity:1}}"
                f"{a.p(o + tc + .35)}{{opacity:1;transform:translateY(-14px)}}{a.p(o + tc + .5)}{{opacity:0;transform:translateY(-18px)}}"
                for o in offs
            )
            a.raw(f".{pc}{{opacity:0;{a.run(pc)}}}@keyframes {pc}{{0%{{opacity:0}}{kf}100%{{opacity:0;transform:translateY(-18px)}}}}")
            pluses.append(text(xc, ybase - h - 12, [(PH_HI if t.dark else t.accent, "+1")], sz, pc, 700, ' text-anchor="middle"' + glow(t)))
    body.append(f"<g{glow(t)}>{''.join(bars)}</g>")
    body += pluses
    last_m, last_x, mgap = None, -999, (56 if narrow else 70)
    for i, (sun, _, _) in enumerate(WEEKS):
        if sun.month != last_m:
            last_m = sun.month
            x = X(i) - slot / 2
            if x - last_x > mgap and x < x1 - 30:
                body.append(text(x, ybase + (30 if narrow else 28), [(t.muted, sun.strftime("%b"))], sz))
                last_x = x + 30
    body.append(hrule(t, ybase + 48, m, cr))
    if narrow:
        y = ybase + 80
        for line in wrap(CONTRIB_NOTE, NCOLS_S, balance=True):
            body.append(text(m, y, [(t.muted, line)], NS))
            y += 26
        H = y - 26 + NPAD_B
    else:
        body.append(text(CONTENT_R, ybase + 78, [(t.muted, CONTRIB_NOTE)], S, extra=' text-anchor="end"'))
        H = ybase + 100

    # hops: busy weeks closer than 0.08s share one hop, and no hop overlaps its neighbours or the run's ends
    tcs = sorted(tc_of(i) for i in busy)
    groups: list[list[float]] = []
    for tc in tcs:
        if groups and tc - groups[-1][1] < 0.08:
            groups[-1][1] = tc
        else:
            groups.append([tc, tc])
    hops = []
    for g, (g0, g1) in enumerate(groups):
        prev = groups[g - 1][1] if g else t_s
        nxt = groups[g + 1][0] if g + 1 < len(groups) else t_e
        hw = min(0.1, (g0 - prev) / 2, (nxt - g1) / 2)
        hops += [(g0 - hw, 0), (g0, -10), (g1, -10), (g1 + hw, 0)] if g1 > g0 else [(g0 - hw, 0), (g0, -10), (g0 + hw, 0)]
    pts: list[tuple[float, float, float]] = []
    for o, ex in zip(offs, exits):
        pts += [(o, xs, 0), (o + t_s, xs, 0)] + [(o + tt, at(tt), y) for tt, y in hops] + [(o + t_e, xe, 0)]
        pts += [(o + t_x, xe, 0), (o + REPLAY - 0.01, xo, 0)] if ex else [(a.dur, xe, 0)]
        if ex and o + REPLAY >= a.dur:  # infinite: pin 100% off-frame too, or it would snap to the base pose at the seam
            pts.append((a.dur, xo, 0))
    pts.sort(key=lambda q: q[0])
    pts = [q for i, q in enumerate(pts) if not i or abs(q[0] - pts[i - 1][0]) > 1e-9 or q[1:] != pts[i - 1][1:]]  # touching hops share a landing
    assert all(p[0] < q[0] for p, q in zip(pts, pts[1:])), "runner keyframes must be strictly increasing"
    keys = [a.p(q[0]) for q in pts]
    assert len(set(keys)) == len(keys), "runner keyframes collide after rounding"
    kfs = "".join(f"{k}{{transform:translate({x - xe:.1f}px,{y}px)}}" for k, (_, x, y) in zip(keys, pts))
    a.raw(f".run{{{a.run('run').replace(' both', ' linear both')}}}@keyframes run{{{kfs}}}")

    # sprite frames, held (steps(1,end)): idle only while standing, a/b poses only while running.
    # Pose rate is tied to speed: one swap per 0.75 sprite widths of travel, so the feet don't skate.
    sprites = {k: _recolor(_sprite(k), RAMP_DARK if t.dark else RAMP_LIGHT) for k in ("idle", "a", "b")}
    k = max(1, round((t_e - t_s) * v / (0.75 * sw)))
    iv = (t_e - t_s) / k
    fi, fa, fb = ["0%{opacity:0}"], ["0%{opacity:0}"], ["0%{opacity:0}"]

    def poses(t0: float, t1: float) -> None:
        j, tt = 0, t0
        while tt < t1 - 1e-6:
            fa.append(f"{a.p(tt)}{{opacity:{1 - j % 2}}}")
            fb.append(f"{a.p(tt)}{{opacity:{j % 2}}}")
            j, tt = j + 1, tt + iv
    for o, ex in zip(offs, exits):
        poses(o + t_s, o + t_e)
        fa.append(f"{a.p(o + t_e)}{{opacity:0}}")
        fb.append(f"{a.p(o + t_e)}{{opacity:0}}")
        fi.append(f"{a.p(o + t_e)}{{opacity:1}}")
        if ex:
            fi.append(f"{a.p(o + t_x)}{{opacity:0}}")
            poses(o + t_x, o + REPLAY - 0.01)
            fa.append(f"{a.p(o + REPLAY - 0.01)}{{opacity:0}}")
            fb.append(f"{a.p(o + REPLAY - 0.01)}{{opacity:0}}")
    loop = f" {a.loop}" if a.loop else ""
    a.raw(
        ".fa,.fb{opacity:0}"
        + "".join(f".{c}{{animation:{c} {a.dur}s steps(1,end){loop} both}}@keyframes {c}{{{''.join(kf)}}}" for c, kf in (("fi", fi), ("fa", fa), ("fb", fb)))
    )
    one = lambda b, cls: f'<svg class="{cls}" width="{sw}" height="{sh}" viewBox="0 0 20 32" shape-rendering="crispEdges">{b}</svg>'  # noqa: E731
    frames = one(sprites["idle"], "fi") + one(sprites["a"], "fa") + one(sprites["b"], "fb")
    rglow = ' filter="url(#gline)"' if t.dark else ""
    body.append(f'<g transform="translate({xe:.1f} {ybase - sh + 1:.1f})"><g class="run"{rglow}>{frames}</g></g>')
    label = (
        "Weekly GitHub contributions for the last 12 months: personal account AnthonyLedesma as solid phosphor bars, "
        "and work accounts AnthonyLedesmaTR and anthonyl-mf (private repos, counts only) summed as hatched bars "
        "stacked on top, on one linear scale. "
        "A pixel runner crosses, bumping each week, with a +1 over the busiest combined weeks, then stands at the right "
        f"edge{_replay_phrase()}. Updated daily."
    )
    if narrow:
        return nframe(t, H, a, label, "CONTRIB", "".join(body), extra_defs=_hatch(t))
    return frame(t, int(H), a, label, "CONTRIB", "".join(body), extra_defs=_hatch(t))


# ------------------------------------------------------------------ 3. evals
ROWS = [  # eval-kit README, verbatim
    ("4 runs per arm", 2.7, -0.8, 6.2, "can't tell yet: need 16 per arm"),
    ("8 runs per arm", 3.8, 2.2, 5.3, "improved"),
    ("12 runs per arm", 0.0, -1.0, 1.0, "no shift of 3 or more"),
]
EVAL_Q = "Did the eval get better, or is that noise?"
EVAL_SUB = "three separate comparisons against one baseline, chasing a 3-point shift · eval-kit README"
EVAL_GATE = [("muted", "with "), ("accent", "--gate"), ("muted", ", the CLI turns the first row into exit code 3, so CI holds the merge")]
EVAL_LABEL = (
    "Did the eval get better, or is that noise? Three separate comparisons against one baseline, chasing a 3-point shift, from the eval-kit README: "
    "4 runs per arm, +2.7, 95% CI -0.8 to +6.2, can't tell yet: need 16 per arm; 8 runs per arm, +3.8, CI +2.2 to +5.3, improved; "
    "12 runs per arm, +0.0, CI -1.0 to +1.0, no shift of 3 or more."
)


def _interval(t: Theme, a: Anim, X, l: float, est: float, h: float, yy: float, whisker: float, r: float) -> str:
    """One CI bar: grows out from the estimate (0.3 to 0.75s), whiskers at 0.7s. Identical for every row."""
    left = a.grow(0.3, 0.45, "X", "100% 50%")
    right = a.grow(0.3, 0.45, "X", "0% 50%")
    return (
        f'<g{glow(t, "line")}><rect class="{left}" x="{X(l):.1f}" y="{yy - 1.5:.1f}" width="{X(est) - X(l):.1f}" height="3" fill="{t.accent}"/>'
        f'<rect class="{right}" x="{X(est):.1f}" y="{yy - 1.5:.1f}" width="{X(h) - X(est):.1f}" height="3" fill="{t.accent}"/>'
        f'<rect class="{a.fade(0.7, 0.1)}" x="{X(l) - 1:.1f}" y="{yy - whisker / 2:.1f}" width="2" height="{whisker:g}" fill="{t.accent}"/>'
        f'<rect class="{a.fade(0.7, 0.1)}" x="{X(h) - 1:.1f}" y="{yy - whisker / 2:.1f}" width="2" height="{whisker:g}" fill="{t.accent}"/>'
        f'<circle cx="{X(est):.1f}" cy="{yy:.1f}" r="{r:g}" fill="{PH_HOT if t.dark else t.text}"/></g>'
    )


def evals(t: Theme) -> str:
    """Three separate comparisons against one baseline. All rows get identical treatment and reveal together."""
    a = Anim()
    xr, xs, xp0, xp1, xv = M, M + 192, M + 432, M + 648, M + 672
    lo, hi = -2, 8

    def X(v: float) -> float:
        return xp0 + (v - lo) / (hi - lo) * (xp1 - xp0)
    body = [
        text(M, 104, [(t.text, EVAL_Q)], L, weight=700),
        text(M, 136, [(t.muted, EVAL_SUB)], S),
    ]
    yh = 182
    body.append(caps(xr, yh, "runs", t.label) + caps(xs, yh, "shift  95% ci", t.label) + caps(xv, yh, "verdict", t.label))
    body.append(text(X(0), yh, [(t.muted, "no change")], S, extra=' text-anchor="middle"') + text(X(3) + 4, yh, [(t.accent, "target +3")], S))
    body.append(hrule(t, yh + 14))
    ys = [232, 274, 316]
    body.append(f'<line x1="{X(0):.1f}" y1="{yh + 22}" x2="{X(0):.1f}" y2="{ys[-1] + 18}" stroke="{t.muted}" stroke-dasharray="2 4"/>')
    body.append(f'<line x1="{X(3):.1f}" y1="{yh + 22}" x2="{X(3):.1f}" y2="{ys[-1] + 18}" stroke="{t.accent}" stroke-dasharray="6 4"/>')
    rows, verdicts = [], []
    for (runs, est, l, h, verdict), y in zip(ROWS, ys):
        rows.append(text(xr, y, [(t.text, runs)], MD) + text(xs, y, [(t.text, f"{est:+.1f}  [{l:+.1f}, {h:+.1f}]")], MD))
        rows.append(_interval(t, a, X, l, est, h, y - 7, 18, 6))
        verdicts.append(text(xv, y, [(t.text, verdict)], MD, weight=600))
    body += rows
    body.append(f'<g class="{a.fade(0.8, 0.25)}">{"".join(verdicts)}</g>')
    ya = ys[-1] + 22
    body.append(f'<rect x="{xp0}" y="{ya}" width="{xp1 - xp0}" height="1" fill="{t.edge}"/>')
    for v in range(lo, hi + 1, 2):
        body.append(f'<rect x="{X(v):.1f}" y="{ya}" width="1" height="6" fill="{t.edge}"/>' + text(X(v), ya + 24, [(t.muted, f"{v:+d}" if v else "0")], S, extra=' text-anchor="middle"'))
    body.append(hrule(t, ya + 42))
    yf = ya + 72
    body.append(text(M, yf, [(getattr(t, c), s) for c, s in EVAL_GATE], S))
    return frame(t, int(yf + 26), a, EVAL_LABEL, "EVALS", "".join(body))


# ------------------------------------------------------------------ narrow (phone) layouts
# Same copy, frame, tokens and timing on the 480 grid. Only line breaks and layout change (a " · " that lands on a
# break is dropped).
NC = NCONTENT_R
TAG_LINES = ["Agent systems,", "and the evals that", "keep them honest."]
assert " ".join(TAG_LINES) == TAG


NDW = 480  # phone art shows at its native width, so on wide phones it stays 480px instead of stretching to the column


def nframe(t: Theme, H: float, a: Anim, label: str, piece: str, body: str, strip: bool = True, extra_defs: str = "") -> str:
    """Narrow frame on the 480 grid (viewBox 0 0 480 H), displayed at its native 480 width."""
    svg = frame(t, int(H), a, label, piece, body, strip, extra_defs, w=NW, m=NM, sp=NSP, ts=NS)
    root = f'viewBox="0 0 {NW} {int(H)}" width="{NW}" height="{int(H)}"'
    assert svg.count(root) == 1
    return svg.replace(root, f'viewBox="0 0 {NW} {int(H)}" width="{NDW}" height="{round(int(H) * NDW / NW)}"')


def header_m(t: Theme) -> str:
    """Name on two lines at XL, role, tagline on three phrase lines at L, typed line by line (0.3 to 1.15s)."""
    a = Anim()
    first, last = "Anthony Ledesma".split(" ")
    body = [text(NM, 100, [(t.label, PROMPT), (t.accent, "whoami")], MD, extra=glow(t)), display(t, NM - 3, 172, first), display(t, NM - 3, 244, last)]
    y, start = 290, 0.3
    for line in TAG_LINES:
        body.append(text(NM, y, [(t.accent, line)], L, a.type(start, line), extra=glow(t)))
        start += (len(line) + 1) / CPS
        y += 36
    y -= 8
    body.append(hrule(t, y, NM, NC))
    y += 38
    body.append(text(NM, y, [(t.label, PROMPT)], MD) + cursor(t, NM + len(PROMPT) * cw(MD), y, MD, a.show(1.15)))
    return nframe(t, y + NPAD_B, a, f"Anthony Ledesma, {ROLE}. {TAG}", "WHOAMI", "".join(body))


def evals_m(t: Theme) -> str:
    """Each comparison as a stacked block: runs and shift/CI, its interval bar, then its verdict, grouped tighter to
    its own bar than to the next row. One-line column header. Same clock as wide."""
    a = Anim()
    lo, hi = -2, 8
    xp0, xp1 = NM + 14, NC - 14

    def X(v: float) -> float:
        return xp0 + (v - lo) / (hi - lo) * (xp1 - xp0)

    body, y = [], 100
    for line in wrap(EVAL_Q, NCOLS_L, balance=True):
        body.append(text(NM, y, [(t.text, line)], L, weight=700))
        y += 34
    y -= 2
    for line in wrap(EVAL_SUB, NCOLS_S, balance=True):
        body.append(text(NM, y, [(t.muted, line)], NS))
        y += 26
    y += 12
    body.append(caps(NM, y, "runs", t.label, NS) + caps(NC, y, "shift  95% ci", t.label, NS, anchor="end"))
    y += 14
    body.append(hrule(t, y, NM, NC))
    y += 30
    body.append(text(X(0), y, [(t.muted, "no change")], NS, extra=' text-anchor="middle"') + text(X(3) + 4, y, [(t.accent, "target +3")], NS))
    y += 40
    rows, verdicts = [], []
    for runs, est, l, h, verdict in ROWS:
        rows.append(text(NM, y, [(t.text, runs)], MD) + text(NC, y, [(t.text, f"{est:+.1f}  [{l:+.1f}, {h:+.1f}]")], MD, extra=' text-anchor="end"'))
        yy = y + 20
        rows.append(
            f'<line x1="{X(0):.1f}" y1="{yy - 11}" x2="{X(0):.1f}" y2="{yy + 11}" stroke="{t.muted}" stroke-dasharray="2 4"/>'
            f'<line x1="{X(3):.1f}" y1="{yy - 11}" x2="{X(3):.1f}" y2="{yy + 11}" stroke="{t.accent}" stroke-dasharray="6 4"/>'
        )
        rows.append(_interval(t, a, X, l, est, h, yy, 16, 5))
        verdicts.append(text(NM, yy + 30, [(t.text, verdict)], MD, weight=600))
        y += 96
    body += rows
    body.append(f'<g class="{a.fade(0.8, 0.25)}">{"".join(verdicts)}</g>')
    ya = y - 30
    body.append(f'<rect x="{xp0}" y="{ya}" width="{xp1 - xp0}" height="1" fill="{t.edge}"/>')
    for v in range(lo, hi + 1, 2):
        body.append(f'<rect x="{X(v):.1f}" y="{ya}" width="1" height="6" fill="{t.edge}"/>' + text(X(v), ya + 26, [(t.muted, f"{v:+d}" if v else "0")], NS, extra=' text-anchor="middle"'))
    body.append(hrule(t, ya + 44, NM, NC))
    y = ya + 76
    for line in wrap_spans([(getattr(t, c), s) for c, s in EVAL_GATE], 34):  # 34 keeps "exit code 3," together
        body.append(text(NM, y, line, NS))
        y += 26
    return nframe(t, y - 26 + NPAD_B, a, EVAL_LABEL, "EVALS", "".join(body))


PIECES = {
    "header": header,
    "evals": evals,
    "contrib-runner-mono": contrib_runner,
    "header-m": header_m,
    "evals-m": evals_m,
    "contrib-runner-mono-m": lambda t: contrib_runner(t, narrow=True),
}
# The only intentional infinite animation: README images can't detect scrolling, so a replay is how visitors actually see the run.
LOOPING = {"contrib-runner-mono", "contrib-runner-mono-m"}

if __name__ == "__main__":
    readme = (HERE.parent / "README.md").read_text()
    assert f'alt="{CONTRIB_ALT}"' in readme, f"README contrib alt must read: {CONTRIB_ALT}"
    for name, fn in PIECES.items():
        for t in THEMES:
            svg = fn(t)
            assert all(ch.isascii() or ch == "·" for ch in svg), name  # no em/en dashes or other non-ASCII
            assert name in LOOPING or " infinite" not in svg, name
            out = HERE / f"{name}-{t.name}.svg"
            out.write_text(svg + "\n")
            print(f"{out.name:32} {len(svg.encode()) / 1024:6.1f} KB")
