"""Render the profile README cards as standalone SVGs ("dark stage" design).

A nod to vjcraft: near-black stage, one neon accent, the contribution graph as an
LED wall with a snake hunting the lit days, and projects as a setlist.

Reads the contribution calendar from the GitHub GraphQL API (needs GITHUB_TOKEN)
and writes every card into cards/. Standard library only, so the workflow needs
no installs. Fonts are system stacks: SVGs loaded through <img> cannot fetch fonts.
"""
import datetime as dt
import html
import json
import os
import random
from collections import deque
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
USER = os.environ.get("PROFILE_USER", "victorserpa")

W = 880
STAGE = "#0a0c0b"
SURFACE = "#111513"
LINE = "#1f2522"
INK = "#eef1ee"
MUTE = "#9aa39d"
NEON = "#3dff8f"
DIM = "#1a2a21"
SANS = "'Helvetica Neue',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
SNAKE = "#ffb547"
BODY = 5  # head + 4 segments
BACK_PENALTY = 4  # extra steps a target behind the head must save to be chosen
LED = ["#18201b", "#174a2c", "#1d7a44", "#28b862", "#3dff8f"]

SETLIST = [
    {"slug": "smk", "name": "smk.", "what": "My product studio. Where the apps below are made.",
     "stack": "Next.js", "status": "live"},
    {"slug": "right-of-way", "name": "Right of Way", "what": "Multiplayer game for iOS and Android, daily challenge.",
     "stack": "React Native · Expo", "status": "soon"},
    {"slug": "lumeclip", "name": "LumeClip", "what": "Long videos in, short vertical clips with captions out.",
     "stack": "Next.js · FFmpeg", "status": "live"},
    {"slug": "notchwake", "name": "Notchwake", "what": "Mac notch island: music, agenda, timers and coding agents.",
     "stack": "Swift · SwiftUI", "status": "live"},
    {"slug": "objection", "name": "objection", "what": "AI agents put the PR on trial. No approval, no merge.",
     "stack": "Shell · ★ {objection_stars}", "status": "open"},
    {"slug": "vjcraft", "name": "vjcraft", "what": "Live visuals app: layers, effects, LED via Art-Net, NDI.",
     "stack": "Rust", "status": "open"},
]
STATUS = {"live": ("ON AIR", NEON), "soon": ("SOON", "#ffb547"), "open": ("OPEN SOURCE", "#7cc4ff")}


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        raise SystemExit(body["errors"])
    return body["data"]


def fetch():
    q = """query($login:String!){ user(login:$login){
      repository(name:"objection"){ stargazerCount }
      contributionsCollection{ contributionCalendar{ totalContributions
        weeks{ contributionDays{ date contributionCount } } } } } }"""
    u = gql(q, {"login": USER})["user"]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return {"days": days, "objection_stars": (u.get("repository") or {}).get("stargazerCount", 0)}


def reveal(attr, start, end, delay, dur):
    """Animate attr from start to end after delay. Before the timeline runs the
    element keeps its final value, so static renderers still show everything."""
    total = delay + dur
    k = delay / total
    return (f'<animate attributeName="{attr}" values="{start};{start};{end}" keyTimes="0;{k:.3f};1" '
            f'dur="{total:.2f}s" begin="0s" fill="freeze"/>')


def esc(s):
    return html.escape(str(s), quote=True)


def svg(h, body, label, w=W):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(label)}">{body}</svg>')


def panel(h, w=W):
    return (f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="10" fill="{SURFACE}" stroke="{LINE}"/>')


GLOW = ('<defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')


def hero():
    h = 340
    body = panel(h) + f'''
<circle cx="50" cy="62" r="5" fill="{NEON}"><animate attributeName="opacity" values="1;.25;1" dur="1.6s" repeatCount="indefinite"/></circle>
<text x="64" y="67" font-family="{MONO}" font-size="13" fill="{NEON}">live from Joinville, Brazil</text>
<text x="40" y="160" font-family="{SANS}" font-weight="700" font-size="76" letter-spacing="-2" fill="{INK}">Victor Serpa</text>
<text x="42" y="214" font-family="{SANS}" font-size="20" fill="{MUTE}">Fullstack developer at <tspan fill="{INK}">Instivo</tspan>.</text>
<text x="42" y="244" font-family="{SANS}" font-size="20" fill="{MUTE}">After hours I ship my own apps at <tspan fill="{INK}">smk.</tspan></text>
<text x="42" y="296" font-family="{MONO}" font-size="13" fill="{NEON}">victorserpa.dev →</text>'''
    return svg(h, body, "Victor Serpa. Fullstack developer at Instivo. After hours I ship my own apps at smk.")


def level(n, mx):
    if n == 0:
        return 0
    return min(4, 1 + int(3.999 * n / max(mx, 1)))


def ledwall(d):
    h = 270
    days = d["days"]
    start = days[0][0]
    mx = sorted(c for _, c in days)[int(len(days) * 0.95)] or 1
    pitch = 15
    offset = start.isoweekday() % 7
    cols = (len(days) + offset + 6) // 7
    x0 = (W - cols * pitch) / 2 + pitch / 2
    y0 = 82
    # The snake hunts: from where it is, it heads for the nearest lit LED still
    # on the wall (grid moves only), eats it and picks the next one, like the
    # classic game. The wall lights up again when the loop restarts. Without
    # SMIL (static renderers) the wall simply shows fully lit.
    lit = set()
    for i, (_, n) in enumerate(days):
        if level(n, mx):
            lit.add(divmod(i + offset, 7))
    # Fixed seed: the route looks random but stays the same between runs, so the
    # daily job only commits when the contributions actually change.
    rng = random.Random(7)
    pos = (0, 3)
    route = [pos]
    left = set(lit)
    while left:
        # One breadth-first search from the head gives the real travel distance to
        # every cell, avoiding the body cells still occupied at that moment (the
        # tail end frees up as the snake moves). Neighbour order is shuffled so
        # equal-length paths vary, which reads as staircases instead of L shapes.
        seen = {pos: (None, 0)}
        queue = deque([pos])
        recent = route[-BODY:]
        while queue:
            cur = queue.popleft()
            dist = seen[cur][1] + 1
            blocked = set(recent[dist:]) if dist < len(recent) else set()
            nbrs = [(cur[0] + dc, cur[1] + dr) for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            rng.shuffle(nbrs)
            for nb in nbrs:
                if 0 <= nb[0] < cols and 0 <= nb[1] < 7 and nb not in seen and nb not in blocked:
                    seen[nb] = (cur, dist)
                    queue.append(nb)
        # go for the closest lit day it can actually reach, preferring what lies
        # ahead over what is behind it (turning back costs a U-turn round its body);
        # ties are broken at random
        hc, hr = (pos[0] - route[-2][0], pos[1] - route[-2][1]) if len(route) > 1 else (1, 0)

        def cost(c):
            behind = (c[0] - pos[0]) * hc + (c[1] - pos[1]) * hr < 0
            return seen[c][1] + (BACK_PENALTY if behind else 0)

        reachable = [c for c in left if c in seen]
        best = min(cost(c) for c in reachable)
        target = rng.choice(sorted(c for c in reachable if cost(c) == best))
        leg = []
        node = target
        while node != pos:
            leg.append(node)
            node = seen[node][0]
        leg.reverse()
        route.extend(leg)
        pos = target
        left.difference_update(leg)  # anything lit it crossed on the way is eaten too
    step, pause = 0.2, 3.0
    order = {}
    for idx, cell in enumerate(route):
        order.setdefault(cell, idx)
    moving = (len(route) - 1) * step
    loop = moving + pause
    dots, months, seen = [], [], set()
    for i, (day, n) in enumerate(days):
        col, row = divmod(i + offset, 7)
        cx, cy = x0 + col * pitch, y0 + row * pitch
        lv = level(n, mx)
        glow = ' filter="url(#glow)"' if lv >= 3 else ""
        dots.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="5.2" fill="{LED[0]}"/>')
        if lv:
            eat = order[(col, row)] * step / loop
            dots.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="5.2" fill="{LED[lv]}"{glow}>'
                        f'<title>{day.isoformat()}: {n}</title>'
                        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{eat:.4f};{min(eat + 0.002, 0.999):.4f};1" '
                        f'dur="{loop:.2f}s" repeatCount="indefinite"/></circle>')
        if day.day <= 7 and row == 0 and col > 0 and (day.year, day.month) not in seen:
            seen.add((day.year, day.month))
            months.append(f'<text x="{cx - 5:.1f}" y="{y0 + 7 * pitch + 10}" font-family="{MONO}" font-size="10" fill="{MUTE}">{day.strftime("%b").lower()}</text>')
    path = "M" + " L".join(f"{x0 + c * pitch:.1f},{y0 + r * pitch}" for c, r in route)
    f = moving / loop
    snake = []
    for k in range(BODY - 1, -1, -1):  # tail first so the head draws on top
        lag = k * step
        size = 11 if k == 0 else 10 - k * 0.8
        color = INK if k == 0 else SNAKE
        snake.append(
            f'<rect x="{-size / 2:.1f}" y="{-size / 2:.1f}" width="{size:.1f}" height="{size:.1f}" rx="3" fill="{color}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.001;{f - 0.001:.4f};{f:.4f};1" '
            f'dur="{loop:.2f}s" begin="{lag:.3f}s" repeatCount="indefinite"/>'
            f'<animateMotion path="{path}" keyPoints="0;1;1" keyTimes="0;{f:.4f};1" calcMode="linear" '
            f'dur="{loop:.2f}s" begin="{lag:.3f}s" repeatCount="indefinite"/></rect>')
    dots.append(f'<g filter="url(#glow)">{"".join(snake)}</g>')
    total = sum(n for _, n in days)
    cur, best = streaks(days)
    active = sum(1 for _, n in days if n)
    peak = max(n for _, n in days)
    stats = (f'<tspan fill="{INK}">{cur}</tspan>-day streak   ·   longest <tspan fill="{INK}">{best}</tspan>   ·   '
             f'<tspan fill="{INK}">{active}</tspan> active days   ·   best day <tspan fill="{INK}">{peak}</tspan>')
    body = panel(h) + GLOW + f'''
<text x="40" y="50" font-family="{SANS}" font-weight="700" font-size="20" fill="{INK}">{total:,} contributions</text>
<text x="{W - 40}" y="50" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTE}">last 12 months · updated daily</text>
{''.join(dots)}{''.join(months)}
<text x="{W / 2}" y="{h - 24}" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{MUTE}" xml:space="preserve">{stats}</text>'''
    return svg(h, body, f"LED wall of {total} contributions in the last 12 months")


def streaks(days):
    seq = list(days)
    if seq and seq[-1][1] == 0:
        seq = seq[:-1]
    cur = 0
    for _, n in reversed(seq):
        if n == 0:
            break
        cur += 1
    best = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        best = max(best, run)
    return cur, best


def setlist_head():
    h = 64
    body = (f'<text x="8" y="44" font-family="{SANS}" font-weight="700" font-size="22" fill="{INK}">Setlist</text>'
            f'<text x="{W - 8}" y="44" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTE}">what I’m playing right now</text>')
    return svg(h, body, "Setlist: what I'm working on")


def track(i, p, d):
    h = 76
    label, color = STATUS[p["status"]]
    stack = p["stack"].format(**d)
    pill_w = 12 + len(label) * 7.4
    body = f'''<rect x="4" y="4" width="{W - 8}" height="{h - 8}" rx="10" fill="{SURFACE}" stroke="{LINE}"/>
<text x="28" y="46" font-family="{MONO}" font-size="13" fill="{MUTE}">{i:02d}</text>
<text x="70" y="36" font-family="{SANS}" font-weight="700" font-size="19" fill="{INK}">{esc(p["name"])}</text>
<text x="70" y="58" font-family="{SANS}" font-size="14" fill="{MUTE}">{esc(p["what"])}</text>
<text x="{W - 40 - pill_w}" y="46" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTE}">{esc(stack)}</text>
<rect x="{W - 28 - pill_w}" y="27" width="{pill_w}" height="22" rx="11" fill="none" stroke="{color}"/>
<text x="{W - 28 - pill_w / 2}" y="42" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{color}">{label}</text>'''
    return svg(h, body, f'{p["name"]}: {p["what"]}')


def main():
    d = fetch()
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    files = {"hero.svg": hero(), "ledwall.svg": ledwall(d), "setlist.svg": setlist_head()}
    for i, p in enumerate(SETLIST, 1):
        files[f"track-{p['slug']}.svg"] = track(i, p, d)
    for name, content in files.items():
        (OUT / name).write_text(content)
    print("wrote", len(files), "cards")


if __name__ == "__main__":
    main()
