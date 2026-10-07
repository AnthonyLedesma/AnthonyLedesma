"""Build the profile README art from kit.py, dark and light.

Run from any directory: python3 art/build.py
Reads art/contrib.json (written by fetch_contrib.py) and writes the SVGs next to this file.
"""

import datetime as dt
import json
import re
from pathlib import Path

from kit import (
    LH, M, MD, PH, PH_HI, PH_INK, PH_LO, PROMPT, S, THEMES, CONTENT_R, L,
    Anim, Theme, badge, caps, cursor, cw, display, frame, glow, mark, text,
)

HERE = Path(__file__).resolve().parent
WEEKS = json.loads((HERE / "contrib.json").read_text())["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
TAG = "Agent systems, and the evals that keep them honest."
# guard's real PreToolUse reason for rm -rf / (bash.always_deny), first sentence pair only
DENY_TAIL = " [permission_mode=default] denied: bash.always_deny."
DENY_WHY = "Recursive root/home deletion is never allowed."
INSTALL = ["/plugin marketplace add TracineHQ/plugins", "/plugin install guard@tracine", "/plugin install convo@tracine", "/plugin install eval-kit@tracine"]

# masthead rows
Y_PROMPT, Y_NAME, Y_SUB, Y_TAG, Y_RULE, Y_FOOT, H_HEAD = 108, 192, 236, 284, 318, 356, 388


def hrule(t: Theme, y: float) -> str:
    return f'<rect x="{M}" y="{y}" width="{CONTENT_R - M}" height="1" fill="{t.edge}"/>'


# ------------------------------------------------------------------ 1. header
def header(t: Theme) -> str:
    """Name dominant from the end of power-on (0.25s). Only the tagline types (0.3 to 1.15s)."""
    a = Anim()
    role = "Staff AI Engineer"
    body = (
        text(M, Y_PROMPT, [(t.label, PROMPT), (t.text, "whoami")], MD)
        + display(t, M - 3, Y_NAME, "Anthony Ledesma")
        + caps(M, Y_SUB, role, t.text, MD)
        + text(M, Y_TAG, [(t.accent, TAG)], L, a.type(0.3, TAG), extra=glow(t))
        + hrule(t, Y_RULE)
        + text(M, Y_FOOT, [(t.label, PROMPT)], MD)
        + cursor(t, M + len(PROMPT) * cw(MD), Y_FOOT, MD, a.show(1.15))
        + text(CONTENT_R, Y_FOOT, [(t.muted, "anthonyledesma.com · tracine.dev")], S, extra=' text-anchor="end"')
    )
    label = f"Anthony Ledesma, {role}. {TAG}"
    return frame(t, H_HEAD, a, label, "WHOAMI", body)


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


def contrib_runner(t: Theme) -> str:
    """Weekly totals as phosphor bars; the runner crosses once (0.3 to ~2.6s), bumping each week, +1 over the busiest, then stands."""
    a = Anim(3.0)
    totals = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in WEEKS]
    n = len(totals)
    partial = len(WEEKS[-1]["contributionDays"]) < 7
    x0, x1, ytop, ybase = M, CONTENT_R - 56, 128, 300
    peak = max(max(totals), 1)
    slot = (x1 - x0) / n
    bw = slot * 0.62
    sw, sh = 30, 48  # sprite 20x32 at 1.5
    xs, xe = M - 40, CONTENT_R - sw
    t_s, t_e = 0.3, 2.6
    v = (xe - xs) / (t_e - t_s)
    busy = sorted(range(n), key=lambda i: -totals[i])[:6]

    def X(i: float) -> float:
        return x0 + (i + 0.5) * slot

    body = [
        text(M, 100, [(t.accent, "contributions per week")], MD, weight=700, extra=glow(t)),
        text(CONTENT_R, 100, [(t.muted, "one bar per week, last 12 months")], S, extra=' text-anchor="end"'),
        f'<rect x="{M}" y="{ybase}" width="{CONTENT_R - M}" height="2" fill="{t.edge}"/>',
    ]
    bars, pluses, pts = [], [], [(0, xs, 0), (t_s, xs, 0)]
    for i, tot in enumerate(totals):
        xc = X(i)
        tc = t_s + (xc - sw / 2 - xs) / v
        h = max(tot / peak * (ybase - ytop), 2)
        op = ' opacity=".45"' if partial and i == n - 1 else ""
        c = a.cls()
        lift = 8 if i in busy else 4
        a.raw(f".{c}{{{a.run(c)}}}@keyframes {c}{{0%,{a.p(tc - .05)}{{transform:none}}{a.p(tc)}{{transform:translateY(-{lift}px)}}{a.p(tc + .15)},100%{{transform:none}}}}")
        bars.append(f'<rect class="{c}" x="{xc - bw / 2:.1f}" y="{ybase - h:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{t.label}"{op}/>')
        if i in busy:
            pts += [(tc - .1, xc - sw / 2 - .1 * v, 0), (tc, xc - sw / 2, -10), (tc + .1, xc - sw / 2 + .1 * v, 0)]
            pc = a.cls()
            a.raw(f".{pc}{{opacity:0;{a.run(pc)}}}@keyframes {pc}{{0%,{a.p(tc)}{{opacity:0;transform:translateY(0)}}{a.p(tc + .02)}{{opacity:1}}{a.p(tc + .55)}{{opacity:1;transform:translateY(-14px)}}{a.p(tc + .75)},100%{{opacity:0;transform:translateY(-18px)}}}}")
            pluses.append(text(xc, ybase - h - 12, [("#fff4d6" if t.dark else t.accent, "+1")], S, pc, 700, ' text-anchor="middle"' + glow(t)))
    body.append(f"<g{glow(t)}>{''.join(bars)}</g>")
    body += pluses
    last_m, last_x = None, -999
    for i, w in enumerate(WEEKS):
        d = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        if d.month != last_m:
            last_m = d.month
            x = X(i) - slot / 2
            if x - last_x > 70 and x < x1 - 30:
                body.append(text(x, ybase + 28, [(t.muted, d.strftime("%b"))], S))
                last_x = x + 30
    body.append(hrule(t, ybase + 48))
    body.append(text(CONTENT_R, ybase + 78, [(t.muted, "GitHub contribution calendar, weekly totals · updated daily")], S, extra=' text-anchor="end"'))
    # runner: run frames until t_e, then idle (idle is the CSS base, so it is also the still)
    ramp = ["#5c3d10", PH_LO, PH, PH_HI] if t.dark else ["#1c1b19", "#7a420a", "#9c5906", PH]
    sprites = {k: _recolor(_sprite(k), ramp) for k in ("idle", "a", "b")}
    k = max(1, round((t_e - t_s) / 0.24))
    a.raw(
        f".fi{{animation:fi {a.dur}s both}}@keyframes fi{{0%,{a.p(t_e)}{{opacity:0}}{a.p(t_e + .01)},100%{{opacity:1}}}}"
        f".fa,.fb{{opacity:0}}.fa{{animation:fa .24s steps(1) {k} {t_s}s}}.fb{{animation:fb .24s steps(1) {k} {t_s}s}}"
        "@keyframes fa{0%{opacity:1}50%{opacity:0}}@keyframes fb{0%{opacity:0}50%{opacity:1}}"
        f".fs{{animation:fs {a.dur}s both}}@keyframes fs{{0%,{a.p(t_s)}{{opacity:1}}{a.p(t_s + .01)},100%{{opacity:0}}}}"
    )
    one = lambda b, cls: f'<svg class="{cls}" width="{sw}" height="{sh}" viewBox="0 0 20 32" shape-rendering="crispEdges">{b}</svg>'  # noqa: E731
    frames = one(sprites["idle"], "fi") + one(sprites["idle"], "fs") + one(sprites["a"], "fa") + one(sprites["b"], "fb")
    pts += [(t_e, xe, 0), (a.dur, xe, 0)]
    kfs = "".join(f"{a.p(tt)}{{transform:translate({x - xe:.1f}px,{y}px)}}" for tt, x, y in pts)
    a.raw(f".run{{animation:run {a.dur}s linear both}}@keyframes run{{{kfs}}}")
    rglow = ' filter="url(#gline)"' if t.dark else ""
    body.append(f'<g transform="translate({xe:.1f} {ybase - sh + 1:.1f})"><g class="run"{rglow}>{frames}</g></g>')
    label = (
        "Anthony Ledesma's GitHub contributions per week for the last 12 months, as phosphor bars. A pixel runner, drawn in phosphor, "
        "crosses once, bumping each week, with a +1 over the busiest weeks, then stands at the right edge. Updated daily."
    )
    return frame(t, int(ybase + 100), a, label, "CONTRIB", "".join(body))


# ------------------------------------------------------------------ 3. showcase
def showcase(t: Theme) -> str:
    """dir listing and install block static. The only motion: the guard deny line types (0.35 to 1.4s)."""
    a = Anim()
    c = cw(MD)
    y = 104
    body = [text(M, y, [(t.label, PROMPT), (t.accent, "dir")], MD, extra=glow(t))]
    y += 46
    for name, tier, desc in [
        ("GUARD", "available", "Stdlib-only safety hooks for Claude Code."),
        ("CONVO", "available", "SQLite-backed analytics CLI for Claude Code sessions."),
        ("EVAL-KIT", "beta", "Did the eval get better, or is that noise?"),
        ("TRIAGE", "soon", "Planned. Not built yet."),
    ]:
        body.append(
            text(M, y, [(t.display if t.dark else t.text, f"{name:<10}"), (t.label, " <DIR>")], MD, weight=600, extra=glow(t))
            + badge(M + 18 * c, y, tier)
            + text(M + 31 * c, y, [(t.muted if tier == "soon" else t.text, desc)], MD)
        )
        y += 38
    y += 14
    body.append(text(M, y, [(t.label, PROMPT + "rem install, inside Claude Code")], MD))
    for cmd in INSTALL:
        y += LH
        body.append(text(M + 2 * c, y, [(t.accent, cmd)], MD, extra=glow(t)))
    y += LH + 14
    body.append(text(M, y, [(t.label, PROMPT), (t.accent, "claude")], MD, extra=glow(t)))
    y += LH
    body.append(f'<circle cx="{M + 6}" cy="{y - 6}" r="5.5" fill="{t.text}"/>' + text(M + 2 * c, y, [(t.text, "Bash"), (t.muted, "(rm -rf /)")], MD))
    y += LH
    dx, word = M + 4 * c, "guard"
    rv = a.flash(0.3, "fill", PH, "#fff4d6")
    body.append(
        f'<g class="{a.show(0.3)}"><path d="M{M + 2 * c + 3:g} {y - 20}v13h10" fill="none" stroke="{t.muted}" stroke-width="1.6"/>'
        f'<rect class="{rv}" x="{dx - 5:g}" y="{y - 19}" width="{len(word) * c + 10:g}" height="26" fill="{PH}"/>'
        + text(dx, y, [(PH_INK, word)], MD, weight=700)
        + text(dx + len(word) * c, y, [(t.accent, DENY_TAIL)], MD, a.type(0.35, DENY_TAIL), extra=glow(t))
        + text(dx, y + LH, [(t.accent, DENY_WHY)], MD, a.type(0.35 + len(DENY_TAIL) / 60, DENY_WHY), extra=glow(t))
        + "</g>"
    )
    t_rem = 0.35 + (len(DENY_TAIL) + len(DENY_WHY)) / 60 + 0.02
    y += 2 * LH
    body.append(text(M, y, [(t.label, PROMPT + "rem every decision lands in ~/.claude/guard-decisions.jsonl")], MD, a.show(t_rem)))
    y += LH
    body.append(text(M, y, [(t.label, PROMPT)], MD, a.show(t_rem)) + cursor(t, M + len(PROMPT) * c, y, MD, a.show(t_rem)))
    y += 26
    body.append(hrule(t, y))
    y += 30
    body.append(text(M, y, [(t.muted, "AVAILABLE: released · BETA: may change before 1.0")], S))
    body.append(text(CONTENT_R, y, [(t.muted, "tracine.dev")], S, extra=' text-anchor="end"'))
    H = int(y + 26)
    label = (
        "Tracine products. guard and convo are available, eval-kit is in beta, triage is coming soon. Install with /plugin marketplace add TracineHQ/plugins, "
        "then /plugin install guard@tracine, convo@tracine, eval-kit@tracine. Claude Code tries rm -rf / and guard denies it: bash.always_deny, recursive root/home deletion is never allowed."
    )
    return frame(t, H, a, label, "DIR", "".join(body))


# ------------------------------------------------------------------ 4. evals
ROWS = [  # eval-kit README, verbatim
    ("4 runs per arm", 2.7, -0.8, 6.2, "can't tell yet: need 16 per arm"),
    ("8 runs per arm", 3.8, 2.2, 5.3, "improved"),
    ("12 runs per arm", 0.0, -1.0, 1.0, "no shift of 3 or more"),
]


def evals(t: Theme) -> str:
    """Three separate comparisons against one baseline. All rows get identical treatment and reveal together."""
    a = Anim()
    xr, xs, xp0, xp1, xv = M, M + 192, M + 432, M + 648, M + 672
    lo, hi = -2, 8
    def X(v: float) -> float:
        return xp0 + (v - lo) / (hi - lo) * (xp1 - xp0)
    body = [
        text(M, 104, [(t.text, "Did the eval get better, or is that noise?")], L, weight=700),
        text(M, 136, [(t.muted, "three separate comparisons against one baseline, chasing a 3-point shift · eval-kit README")], S),
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
        yy = y - 7
        left = a.grow(0.3, 0.45, "X", "100% 50%")
        right = a.grow(0.3, 0.45, "X", "0% 50%")
        rows.append(
            f'<g{glow(t, "line")}><rect class="{left}" x="{X(l):.1f}" y="{yy - 1.5:.1f}" width="{X(est) - X(l):.1f}" height="3" fill="{t.accent}"/>'
            f'<rect class="{right}" x="{X(est):.1f}" y="{yy - 1.5:.1f}" width="{X(h) - X(est):.1f}" height="3" fill="{t.accent}"/>'
            f'<rect class="{a.fade(0.7, 0.1)}" x="{X(l) - 1:.1f}" y="{yy - 9:.1f}" width="2" height="18" fill="{t.accent}"/>'
            f'<rect class="{a.fade(0.7, 0.1)}" x="{X(h) - 1:.1f}" y="{yy - 9:.1f}" width="2" height="18" fill="{t.accent}"/>'
            f'<circle cx="{X(est):.1f}" cy="{yy:.1f}" r="6" fill="{"#fff4d6" if t.dark else t.text}"/></g>'
        )
        verdicts.append(text(xv, y, [(t.text, verdict)], MD, weight=600))
    body += rows
    body.append(f'<g class="{a.fade(0.8, 0.25)}">{"".join(verdicts)}</g>')
    ya = ys[-1] + 22
    body.append(f'<rect x="{xp0}" y="{ya}" width="{xp1 - xp0}" height="1" fill="{t.edge}"/>')
    for v in range(lo, hi + 1, 2):
        body.append(f'<rect x="{X(v):.1f}" y="{ya}" width="1" height="6" fill="{t.edge}"/>' + text(X(v), ya + 24, [(t.muted, f"{v:+d}" if v else "0")], S, extra=' text-anchor="middle"'))
    body.append(hrule(t, ya + 42))
    yf = ya + 72
    body.append(text(M, yf, [(t.muted, "with "), (t.accent, "--gate"), (t.muted, ", the CLI turns the first row into exit code 3, so CI holds the merge")], S))
    label = (
        "Did the eval get better, or is that noise? Three separate comparisons against one baseline, chasing a 3-point shift, from the eval-kit README: "
        "4 runs per arm, +2.7, 95% CI -0.8 to +6.2, can't tell yet: need 16 per arm; 8 runs per arm, +3.8, CI +2.2 to +5.3, improved; "
        "12 runs per arm, +0.0, CI -1.0 to +1.0, no shift of 3 or more."
    )
    return frame(t, int(yf + 26), a, label, "EVALS", "".join(body))


# ------------------------------------------------------------------ 5. footer
def footer(t: Theme) -> str:
    a = Anim()
    H = 88
    y = 52
    lead = "EOF · ANTHONY LEDESMA · "
    body = (
        mark(M, 25, 0.66, t.accent, 2.4, filt=glow(t, "line"))
        + text(M + 54, y, [(t.label, lead), (t.accent, "anthonyledesma.com")], MD, weight=600, extra=glow(t))
        + cursor(t, M + 54 + (len(lead) + 18) * cw(MD) + 8, y, MD)
        + text(CONTENT_R, y, [(t.muted, "tracine.dev · github.com/TracineHQ")], S, extra=' text-anchor="end"')
    )
    return frame(t, H, a, "EOF, Anthony Ledesma, anthonyledesma.com, tracine.dev, github.com/TracineHQ", "", body, strip=False)


PIECES = {
    "header": header,
    "showcase": showcase,
    "evals": evals,
    "contrib-runner-mono": contrib_runner,
    "footer": footer,
}

if __name__ == "__main__":
    for name, fn in PIECES.items():
        for t in THEMES:
            svg = fn(t)
            assert chr(0x2014) not in svg and chr(0x2013) not in svg and " infinite" not in svg, name
            out = HERE / f"{name}-{t.name}.svg"
            out.write_text(svg + "\n")
            print(f"{out.name:28} {len(svg.encode()) / 1024:6.1f} KB")
