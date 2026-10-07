"""Build the profile README art from kit.py, dark and light.

Run from any directory: python3 art/build.py
Reads art/contrib.json (written by fetch_contrib.py) and writes the SVGs next to this file.
"""

import datetime as dt
import json
import re
from pathlib import Path

from kit import (
    CPS, DONE, LH, M, MD, NS, PH, PH_HI, PH_HOT, PH_INK, PROMPT, RAMP_DARK, RAMP_LIGHT, S, THEMES, CONTENT_R, L,
    NCONTENT_R, NM, NSP, NW, W,
    Anim, Theme, badge, caps, cursor, cw, display, frame, glow, mark, text, wrap, wrap_spans,
)

HERE = Path(__file__).resolve().parent
WEEKS = json.loads((HERE / "contrib.json").read_text())["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
TAG = "Agent systems, and the evals that keep them honest."
ROLE = "Staff AI Engineer"
HEAD_LINKS = "anthonyledesma.com · tracine.dev"
NCOLS_S, NCOLS_MD, NCOLS_L = (int((NCONTENT_R - NM) // cw(z)) for z in (NS, MD, L))  # 38, 34, 24 chars on the narrow grid
# guard's deny output for rm -rf /: the rule id plus the reason sentence, abbreviated (the "Blocked: ..." wrapper and
# the override hint are left out). Source: guard registry.py bash.always_deny, bash_command_validator._format_deny_reason.
DENY_TAIL = " [permission_mode=default] denied: bash.always_deny."
DENY_WHY = "Recursive root/home deletion is never allowed."
INSTALL = ["/plugin marketplace add TracineHQ/plugins", "/plugin install guard@tracine", "/plugin install convo@tracine", "/plugin install eval-kit@tracine"]

# contrib runner replay. README images can't detect scrolling, so a replay is how visitors actually get to see the run.
REPLAY = 20.0  # seconds from the start of one pass to the next
REPLAYS = None  # None = every 20s forever; an int caps the passes

# masthead rows
Y_PROMPT, Y_NAME, Y_SUB, Y_TAG, Y_RULE, Y_FOOT, H_HEAD = 108, 192, 236, 284, 318, 356, 388
NPAD_B = 24  # narrow: last baseline to frame edge


def hrule(t: Theme, y: float, m: int = M, r: int = CONTENT_R) -> str:
    return f'<rect x="{m}" y="{y}" width="{r - m}" height="1" fill="{t.edge}"/>'


def hot(t: Theme) -> str:
    """Rev-video flash color: hot white on glass, phosphor-hi on paper (hot white would vanish into it)."""
    return PH_HOT if t.dark else PH_HI


# ------------------------------------------------------------------ 1. header
def header(t: Theme) -> str:
    """Name dominant from the end of power-on (0.25s). Only the tagline types (0.3 to 1.15s)."""
    a = Anim()
    body = (
        text(M, Y_PROMPT, [(t.label, PROMPT), (t.accent, "whoami")], MD, extra=glow(t))
        + display(t, M - 3, Y_NAME, "Anthony Ledesma")
        + caps(M, Y_SUB, ROLE, t.text, MD)
        + text(M, Y_TAG, [(t.accent, TAG)], L, a.type(0.3, TAG), extra=glow(t))
        + hrule(t, Y_RULE)
        + text(M, Y_FOOT, [(t.label, PROMPT)], MD)
        + cursor(t, M + len(PROMPT) * cw(MD), Y_FOOT, MD, a.show(1.15))
        + text(CONTENT_R, Y_FOOT, [(t.muted, HEAD_LINKS)], S, extra=' text-anchor="end"')
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
    "Anthony Ledesma's GitHub contributions per week for the last 12 months, with a pixel runner that crosses the bars "
    + ("every 20 seconds" if REPLAYS is None else "once" if REPLAYS <= 1 else f"{REPLAYS} times, 20 seconds apart")
    + ". Updated daily."
)


def contrib_runner(t: Theme, narrow: bool = False) -> str:
    """Weekly totals as phosphor bars. The runner enters from off the left edge, crosses (0.3 to 2.6s) bumping each week
    with a +1 over the busiest, then stands at the right edge. On replay he runs off the right edge and back in from the
    left, so the loop seam happens while he is hidden by the panel clip. Bars rise only once (they are static).

    narrow: same bars and runner on the 480 grid, taller bars, a month label about every quarter, captions stacked.
    """
    passes = 1 if REPLAYS is None else max(1, REPLAYS)
    a = Anim(REPLAY * passes, "infinite" if REPLAYS is None else "")
    totals = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in WEEKS]
    n = len(totals)
    partial = len(WEEKS[-1]["contributionDays"]) < 7
    m, cr, fw, sz = (NM, NCONTENT_R, NW, NS) if narrow else (M, CONTENT_R, W, S)
    x0, x1, ytop, ybase = (m, cr - 36, 172, 360) if narrow else (M, CONTENT_R - 56, 128, 300)
    peak = max(max(totals), 1)
    slot = (x1 - x0) / n
    bw = slot * 0.62
    sw, sh = 30, 48  # sprite 20x32 at 1.5
    xs, xe, xo = -sw - 2, cr - sw, fw + 2  # start and exit are both behind the panel clip
    t_s, t_e = 0.3, 2.6
    v = (xe - xs) / (t_e - t_s)
    t_x = REPLAY - 0.01 - (xo - xe) / v  # exit at run speed, gone just before the next pass
    busy = sorted(range(n), key=lambda i: -totals[i])[:6]
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
        f'<rect x="{m}" y="{ybase}" width="{cr - m}" height="2" fill="{t.edge}"/>',
    ]
    bars, pluses = [], []
    for i, tot in enumerate(totals):
        xc, tc = X(i), tc_of(i)
        h = max(tot / peak * (ybase - ytop), 2)
        op = ' opacity=".7"' if partial and i == n - 1 else ""
        c = a.cls()
        lift = 8 if i in busy else 4
        kf = "".join(f"{a.p(o + tc - .05)}{{transform:none}}{a.p(o + tc)}{{transform:translateY(-{lift}px)}}{a.p(o + tc + .15)}{{transform:none}}" for o in offs)
        a.raw(f".{c}{{{a.run(c)}}}@keyframes {c}{{0%{{transform:none}}{kf}100%{{transform:none}}}}")
        bars.append(f'<rect class="{c}" x="{xc - bw / 2:.1f}" y="{ybase - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{t.label}"{op}/>')
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
    last_m, last_x, gap = None, -999, (56 if narrow else 70)
    for i, w in enumerate(WEEKS):
        d = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        if d.month != last_m:
            last_m = d.month
            x = X(i) - slot / 2
            if x - last_x > gap and x < x1 - 30:
                body.append(text(x, ybase + (30 if narrow else 28), [(t.muted, d.strftime("%b"))], sz))
                last_x = x + 30
    body.append(hrule(t, ybase + 48, m, cr))
    note = "GitHub contribution calendar, weekly totals · updated daily"
    if narrow:
        y = ybase + 80
        for line in wrap(note, NCOLS_S, balance=True):
            body.append(text(m, y, [(t.muted, line)], NS))
            y += 26
        H = y - 26 + NPAD_B
    else:
        body.append(text(CONTENT_R, ybase + 78, [(t.muted, note)], S, extra=' text-anchor="end"'))
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
        "Anthony Ledesma's GitHub contributions per week for the last 12 months, as phosphor bars. A pixel runner, drawn in phosphor, "
        f"crosses, bumping each week, with a +1 over the busiest weeks, then stands at the right edge{_replay_phrase()}. Updated daily."
    )
    if narrow:
        return frame(t, int(H), a, label, "CONTRIB", "".join(body), w=NW, m=NM, sp=NSP, ts=NS)
    return frame(t, int(H), a, label, "CONTRIB", "".join(body))


# ------------------------------------------------------------------ 3. showcase
PRODUCTS = [
    ("GUARD", "available", "Stdlib-only safety hooks for Claude Code."),
    ("CONVO", "available", "SQLite-backed analytics CLI for Claude Code sessions."),
    ("EVAL-KIT", "beta", "Did the eval get better, or is that noise?"),
    ("TRIAGE", "soon", "Planned. Not built yet."),
]
SHOW_LABEL = (
    "Tracine products. guard and convo are available, eval-kit is in beta, triage is coming soon. Install with /plugin marketplace add TracineHQ/plugins, "
    "then /plugin install guard@tracine, convo@tracine, eval-kit@tracine. Claude Code tries rm -rf / and guard denies it: bash.always_deny, recursive root/home deletion is never allowed."
)
REM_INSTALL = "rem install, inside Claude Code"
REM_LOG = "rem every decision lands in ~/.claude/guard-decisions.jsonl"
TIERS_NOTE = "AVAILABLE: released · BETA: may change before 1.0"
T_REM = min(0.35 + (len(DENY_TAIL) + len(DENY_WHY)) / CPS + 0.02, DONE - 0.01)  # rem lines pop as the deny finishes


def showcase(t: Theme) -> str:
    """dir listing and install block static. The only motion: the guard deny line types (0.35 to ~2s)."""
    a = Anim()
    c = cw(MD)
    y = 104
    body = [text(M, y, [(t.label, PROMPT), (t.accent, "dir")], MD, extra=glow(t))]
    y += 46
    for name, tier, desc in PRODUCTS:
        body.append(
            text(M, y, [(t.display if t.dark else t.text, f"{name:<10}"), (t.label, " <DIR>")], MD, weight=600, extra=glow(t))
            + badge(M + 18 * c, y, tier, t)
            + text(M + 32 * c, y, [(t.muted if tier == "soon" else t.text, desc)], MD)
        )
        y += 38
    y += 14
    body.append(text(M, y, [(t.label, PROMPT + REM_INSTALL)], MD))
    for cmd in INSTALL:
        y += LH
        body.append(text(M + 2 * c, y, [(t.accent, cmd)], MD, extra=glow(t)))
    y += LH + 14
    body.append(text(M, y, [(t.label, PROMPT), (t.accent, "claude")], MD, extra=glow(t)))
    y += LH
    body.append(f'<circle cx="{M + 6}" cy="{y - 6}" r="5.5" fill="{t.text}"/>' + text(M + 2 * c, y, [(t.text, "Bash"), (t.muted, "(rm -rf /)")], MD))
    y += LH
    dx, word = M + 4 * c, "guard"
    rv = a.flash(0.3, "fill", PH, hot(t))
    body.append(
        f'<g class="{a.show(0.3)}"><path d="M{M + 2 * c + 3:g} {y - 20}v13h10" fill="none" stroke="{t.muted}" stroke-width="1.6"/>'
        f'<rect class="{rv}" x="{dx - 5:g}" y="{y - 19}" width="{len(word) * c + 10:g}" height="26" fill="{PH}"/>'
        + text(dx, y, [(PH_INK, word)], MD, weight=700)
        + text(dx + len(word) * c, y, [(t.accent, DENY_TAIL)], MD, a.type(0.35, DENY_TAIL), extra=glow(t))
        + text(dx, y + LH, [(t.accent, DENY_WHY)], MD, a.type(0.35 + len(DENY_TAIL) / CPS, DENY_WHY), extra=glow(t))
        + "</g>"
    )
    y += 2 * LH
    body.append(text(M, y, [(t.label, PROMPT + REM_LOG)], MD, a.show(T_REM)))
    y += LH
    body.append(text(M, y, [(t.label, PROMPT)], MD, a.show(T_REM)) + cursor(t, M + len(PROMPT) * c, y, MD, a.show(T_REM)))
    y += 26
    body.append(hrule(t, y))
    y += 30
    body.append(text(M, y, [(t.muted, TIERS_NOTE)], S))
    body.append(text(CONTENT_R, y, [(t.muted, "tracine.dev")], S, extra=' text-anchor="end"'))
    return frame(t, int(y + 26), a, SHOW_LABEL, "DIR", "".join(body))


# ------------------------------------------------------------------ 4. evals
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


# ------------------------------------------------------------------ 5. footer
FOOT_LEAD = "EOF · ANTHONY LEDESMA · "
FOOT_LINKS = "tracine.dev · github.com/TracineHQ"
FOOT_LABEL = "EOF, Anthony Ledesma, anthonyledesma.com, tracine.dev, github.com/TracineHQ"


def footer(t: Theme) -> str:
    a = Anim()
    y = 52
    body = (
        mark(M, 25, 0.66, t.accent, filt=glow(t, "line"))
        + text(M + 54, y, [(t.label, FOOT_LEAD), (t.accent, "anthonyledesma.com")], MD, weight=600, extra=glow(t))
        + cursor(t, M + 54 + (len(FOOT_LEAD) + 18) * cw(MD) + 8, y, MD)
        + text(CONTENT_R, y, [(t.muted, FOOT_LINKS)], S, extra=' text-anchor="end"')
    )
    return frame(t, 88, a, FOOT_LABEL, "", body, strip=False)


# ------------------------------------------------------------------ narrow (phone) layouts
# Same copy, frame, tokens and timing on the 480 grid. Only line breaks and layout change (a " · " that lands on a
# break is dropped, and the phone showcase leaves out the product one-liners the README bullets right above repeat).
NC = NCONTENT_R
NCS = cw(NS)
TAG_LINES = ["Agent systems,", "and the evals that", "keep them honest."]
assert " ".join(TAG_LINES) == TAG
GREENBAR = 78  # first greenbar band baseline (STRIP 56 + 22); bands repeat every 64, rows every 32


def nframe(t: Theme, H: float, a: Anim, label: str, piece: str, body: str, strip: bool = True) -> str:
    return frame(t, int(H), a, label, piece, body, strip, w=NW, m=NM, sp=NSP, ts=NS)


def header_m(t: Theme) -> str:
    """Name on two lines at XL, role, tagline on three phrase lines at L, typed line by line (0.3 to 1.15s)."""
    a = Anim()
    first, last = "Anthony Ledesma".split(" ")
    body = [text(NM, 100, [(t.label, PROMPT), (t.accent, "whoami")], MD, extra=glow(t)), display(t, NM - 3, 172, first), display(t, NM - 3, 244, last)]
    body.append(caps(NM, 286, ROLE, t.text, MD))
    y, start = 330, 0.3
    for line in TAG_LINES:
        body.append(text(NM, y, [(t.accent, line)], L, a.type(start, line), extra=glow(t)))
        start += (len(line) + 1) / CPS
        y += 36
    y -= 8
    body.append(hrule(t, y, NM, NC))
    y += 38
    body.append(text(NM, y, [(t.label, PROMPT)], MD) + cursor(t, NM + len(PROMPT) * cw(MD), y, MD, a.show(1.15)))
    y += 28
    body.append(text(NM, y, [(t.muted, HEAD_LINKS)], NS))
    return nframe(t, y + NPAD_B, a, f"Anthony Ledesma, {ROLE}. {TAG}", "WHOAMI", "".join(body))


def showcase_m(t: Theme) -> str:
    """dir listing (name, <DIR>, tier pill) at MD, then the session transcript at NS on 32-unit rows that sit on the
    greenbar. Continuations of a wrapped line hang 4 columns in. Same deny typing clock as the wide piece (0.35 to ~2s)."""
    a = Anim()
    c, ls = cw(MD), 32

    def snap(y: float) -> float:
        return y + (GREENBAR - y) % ls

    def lines(x: float, y: float, s: str, color: str, width: int, cls: str = "", glw: str = "") -> tuple[str, float]:
        out = []
        for j, ln in enumerate(wrap(s, width, hang=4, balance=True)):
            out.append(text(x + (4 * NCS if j else 0), y, [(color, ln)], NS, cls, extra=glw))
            y += ls
        return "".join(out), y

    y = 100
    body = [text(NM, y, [(t.label, PROMPT), (t.accent, "dir")], MD, extra=glow(t))]
    y += 44
    for name, tier, _ in PRODUCTS:
        body.append(text(NM, y, [(t.display if t.dark else t.text, f"{name:<10}"), (t.label, " <DIR>")], MD, weight=600, extra=glow(t)) + badge(NM + 18 * c, y, tier, t, NS))
        y += 36
    y = snap(y + 4)
    s, y = lines(NM, y, PROMPT + REM_INSTALL, t.label, NCOLS_S)
    body.append(s)
    for cmd in INSTALL:
        s, y = lines(NM + 2 * NCS, y, cmd, t.accent, NCOLS_S - 2, glw=glow(t))
        body.append(s)
    y += ls
    body.append(text(NM, y, [(t.label, PROMPT), (t.accent, "claude")], NS, extra=glow(t)))
    y += ls
    body.append(f'<circle cx="{NM + 5}" cy="{y - 6}" r="5" fill="{t.text}"/>' + text(NM + 2 * NCS, y, [(t.text, "Bash"), (t.muted, "(rm -rf /)")], NS))
    y += ls
    dx, word = NM + 4 * NCS, "guard"
    deny = wrap(word + DENY_TAIL + " " + DENY_WHY, NCOLS_S - 4)
    assert deny[0].startswith(word + " ") and " ".join(deny) == word + DENY_TAIL + " " + DENY_WHY
    rv = a.flash(0.3, "fill", PH, hot(t))
    out = [
        f'<path d="M{NM + 2 * NCS + 3:g} {y - 18}v12h10" fill="none" stroke="{t.muted}" stroke-width="1.6"/>'
        f'<rect class="{rv}" x="{dx - 4:g}" y="{y - 17}" width="{len(word) * NCS + 8:g}" height="23" fill="{PH}"/>'
        + text(dx, y, [(PH_INK, word)], NS, weight=700)
    ]
    start = 0.35
    for j, line in enumerate(deny):
        seg = line[len(word):] if j == 0 else line
        x = dx + len(word) * NCS if j == 0 else dx
        out.append(text(x, y + j * ls, [(t.accent, seg)], NS, a.type(start, seg), extra=glow(t)))
        start += len(seg) / CPS
    body.append(f'<g class="{a.show(0.3)}">{"".join(out)}</g>')
    y += len(deny) * ls
    shown = a.show(T_REM)
    s, y = lines(NM, y, PROMPT + REM_LOG, t.label, NCOLS_S, shown)
    body.append(s)
    body.append(text(NM, y, [(t.label, PROMPT)], NS, shown) + cursor(t, NM + len(PROMPT) * NCS, y, NS, shown))
    y += 22
    body.append(hrule(t, y, NM, NC))
    a1, a2 = TIERS_NOTE.split(" · ")
    y += 30
    body.append(text(NM, y, [(t.muted, a1)], NS) + text(NC, y, [(t.muted, "tracine.dev")], NS, extra=' text-anchor="end"'))
    y += 26
    body.append(text(NM, y, [(t.muted, a2)], NS))
    return nframe(t, y + NPAD_B, a, SHOW_LABEL, "DIR", "".join(body))


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


def footer_m(t: Theme) -> str:
    """Stacked: EOF lead by the mark, the site with the cursor, then the other links full width."""
    a = Anim()
    x = NM + 54
    body = (
        mark(NM, 25, 0.66, t.accent, filt=glow(t, "line"))
        + text(x, 52, [(t.label, FOOT_LEAD.rstrip(" ·"))], MD, weight=600, extra=glow(t))
        + text(x, 84, [(t.accent, "anthonyledesma.com")], MD, weight=600, extra=glow(t))
        + cursor(t, x + 18 * cw(MD) + 8, 84, MD)
        + text(NM, 120, [(t.muted, FOOT_LINKS)], NS)
    )
    return nframe(t, 120 + NPAD_B, a, FOOT_LABEL, "", body, strip=False)


PIECES = {
    "header": header,
    "showcase": showcase,
    "evals": evals,
    "contrib-runner-mono": contrib_runner,
    "footer": footer,
    "header-m": header_m,
    "showcase-m": showcase_m,
    "evals-m": evals_m,
    "contrib-runner-mono-m": lambda t: contrib_runner(t, narrow=True),
    "footer-m": footer_m,
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
