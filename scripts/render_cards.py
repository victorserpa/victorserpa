"""Render the profile README cards as standalone SVGs.

Reads the contribution calendar from the GitHub GraphQL API (needs GITHUB_TOKEN)
and writes every card into cards/. Standard library only, so the workflow needs
no installs. Fonts are system stacks: SVGs loaded through <img> cannot fetch web fonts.
"""
import base64
import datetime as dt
import html
import json
import os
import urllib.request
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cards"
USER = os.environ.get("PROFILE_USER", "victorserpa")

W = 880
BG = "#f4f2ec"
INK = "#16161a"
MUTE = "#6b6b72"
ACC = "#1f8a5b"
SERIF = "Georgia,'Iowan Old Style','Times New Roman',serif"
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
LEVELS = ["#e4e1d8", "#bfe3cc", "#7fcb9d", "#3ea872", "#1f8a5b", "#0f5c3b"]

PROJECTS = [
    {"name": "right-of-way", "href": "https://playrightofway.com", "color": "#e8a33d",
     "desc": ["Multiplayer game for iOS and Android", "with a daily challenge."],
     "meta": "React Native · launching soon"},
    {"name": "lumeclip", "href": "https://lumeclip.com", "color": "#7a5cf0",
     "desc": ["Cuts long videos into short vertical", "clips with captions, ready to post."],
     "meta": "Next.js · live"},
    {"name": "objection", "href": "https://github.com/victorserpa/objection", "color": "#d9534f",
     "desc": ["AI agents review the PR as a trial:", "no approval, no merge."],
     "meta": "Shell · ★ {objection_stars}"},
]

TILES = [
    {"key": "WORK", "bg": ACC, "fg": "#ffffff", "big": ("Instivo", ""), "href": "https://instivo.com.br",
     "lines": ["Fullstack developer. Web products", "built with TypeScript and React."]},
    {"key": "STUDIO", "bg": INK, "fg": "#ffffff", "big": ("smk.", " studio"), "href": "https://wearesmk.com",
     "lines": ["My own apps, after hours:", "Right of Way and LumeClip."]},
    {"key": "OPEN SOURCE", "bg": "#f2c14e", "fg": INK, "big": ("{public_repos}", " repos"),
     "href": "https://github.com/victorserpa?tab=repositories",
     "lines": ["From a VJ app in Rust to", "a courtroom for code review."]},
]


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
      repositories(ownerAffiliations:OWNER, privacy:PUBLIC){ totalCount }
      repository(name:"objection"){ stargazerCount }
      contributionsCollection{ contributionCalendar{ totalContributions
        weeks{ contributionDays{ date contributionCount } } } } } }"""
    u = gql(q, {"login": USER})["user"]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"])
            for w in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return {
        "days": days,
        "total": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "public_repos": u["repositories"]["totalCount"],
        "objection_stars": (u.get("repository") or {}).get("stargazerCount", 0),
    }


def esc(s):
    return html.escape(str(s), quote=True)


def svg(h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" '
            f'role="img" aria-label="{esc(label)}">{body}</svg>')


def card_bg(h, pad=8):
    return f'<rect x="{pad}" y="{pad}" width="{W - 2 * pad}" height="{h - 2 * pad}" rx="14" fill="{BG}"/>'


def hero():
    h = 380
    avatar = base64.b64encode((ROOT / "assets" / "avatar-hero.webp").read_bytes()).decode()
    body = card_bg(h) + f'''
<image href="data:image/webp;base64,{avatar}" x="590" y="34" width="216" height="313" preserveAspectRatio="xMidYMid meet"/>
<rect x="44" y="48" width="8" height="8" fill="{ACC}"/>
<text x="62" y="57" font-family="{MONO}" font-size="12" letter-spacing="1.6" fill="{MUTE}">FULLSTACK DEVELOPER · JOINVILLE, BRAZIL</text>
<text x="38" y="160" font-family="{SERIF}" font-size="92" letter-spacing="-2" fill="{INK}">Victor</text>
<text x="38" y="250" font-family="{SERIF}" font-style="italic" font-size="92" letter-spacing="-2" fill="{INK}">Serpa<tspan fill="{ACC}">.</tspan></text>
<text x="44" y="298" font-family="{SANS}" font-size="17" fill="{MUTE}">Shipping web products at Instivo.</text>
<text x="44" y="322" font-family="{SANS}" font-size="17" fill="{MUTE}">After hours I build my own apps at smk.</text>'''
    return svg(h, body, "Victor Serpa. Fullstack developer at Instivo. After hours I build my own apps at smk.")


def level(n, mx):
    if n == 0:
        return 0
    return min(5, 1 + int(4 * n / max(mx, 1)))


def heatmap(d):
    h = 270
    days = d["days"]
    start = days[0][0]
    mx = sorted(c for _, c in days)[int(len(days) * 0.95)] or 1
    cell, gap = 12, 3
    cols = (len(days) + start.weekday() + 1) // 7 + 1
    x0 = (W - cols * (cell + gap)) / 2
    y0 = 96
    rects, months = [], []
    seen = set()
    for i, (day, n) in enumerate(days):
        idx = i + (start.isoweekday() % 7)
        col, row = divmod(idx, 7)
        x = x0 + col * (cell + gap)
        y = y0 + row * (cell + gap)
        delay = col * 0.025
        rects.append(f'<rect x="{x:.1f}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{LEVELS[level(n, mx)]}" opacity="0">'
                     f'<title>{day.isoformat()}: {n}</title>'
                     f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/></rect>')
        if day.day <= 7 and row == 0 and (day.year, day.month) not in seen and col > 0:
            seen.add((day.year, day.month))
            months.append(f'<text x="{x:.1f}" y="{y0 + 7 * (cell + gap) + 16}" font-family="{MONO}" font-size="10" fill="{MUTE}">{day.strftime("%b")}</text>')
    legend = "".join(f'<rect x="{W - 146 + i * 14}" y="{h - 38}" width="10" height="10" rx="3" fill="{c}"/>' for i, c in enumerate(LEVELS))
    body = card_bg(h) + f'''
<text x="40" y="66" font-family="{SERIF}" font-size="30" fill="{INK}">Every day, <tspan font-style="italic" fill="{ACC}">in green</tspan></text>
<text x="{W - 40}" y="62" text-anchor="end" font-family="{MONO}" font-size="11" letter-spacing="1.4" fill="{MUTE}">REFRESHED DAILY</text>
{''.join(rects)}{''.join(months)}
<text x="{W - 156}" y="{h - 29}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{MUTE}">less</text>
{legend}
<text x="{W - 52}" y="{h - 29}" font-family="{MONO}" font-size="10" fill="{MUTE}">more</text>'''
    return svg(h, body, f"Contribution graph for the last year, {d['total']} contributions, refreshed daily")


def streaks(days):
    today = days[-1][0]
    cur = 0
    seq = list(days)
    if seq and seq[-1][1] == 0 and seq[-1][0] == today:
        seq = seq[:-1]  # today still in progress
    for _, n in reversed(seq):
        if n == 0:
            break
        cur += 1
    best = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        best = max(best, run)
    return cur, best


def activity(d):
    h = 300
    days = d["days"]
    per = OrderedDict()
    for day, n in days[-365:]:
        per.setdefault((day.year, day.month), 0)
        per[(day.year, day.month)] += n
    months = list(per.items())[-12:]
    mx = max(v for _, v in months) or 1
    peak = max(range(len(months)), key=lambda i: months[i][1])
    cur, best = streaks(days)
    active = sum(1 for _, n in days[-365:] if n)
    busiest = max(n for _, n in days[-365:])
    total = sum(n for _, n in days[-365:])
    bx, by, bw, bh, step = 40, 268, 34, 140, 42
    bars = []
    for i, ((y, m), v) in enumerate(months):
        hh = max(6, bh * v / mx)
        x = bx + i * step
        fill = ACC if i == peak else INK
        if i == len(months) - 1:
            fill = "#cfccc2"
        bars.append(f'<rect x="{x}" y="{by - hh:.1f}" width="{bw}" height="{hh:.1f}" rx="3" fill="{fill}">'
                    f'<animate attributeName="height" from="0" to="{hh:.1f}" dur="0.8s" begin="{i * 0.05:.2f}s" fill="freeze"/>'
                    f'<animate attributeName="y" from="{by}" to="{by - hh:.1f}" dur="0.8s" begin="{i * 0.05:.2f}s" fill="freeze"/></rect>'
                    f'<text x="{x + bw / 2}" y="{by + 16}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{MUTE}">{dt.date(y, m, 1).strftime("%b")}</text>')
        if i == peak:
            bars.append(f'<text x="{x + bw / 2}" y="{by - hh - 6:.1f}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{ACC}">{v:,}</text>')
    sx = 600
    stat = lambda y, big, small, lab: (
        f'<text x="{sx}" y="{y}" font-family="{SERIF}" font-size="34" fill="{INK}">{big}<tspan font-style="italic" font-size="26">{small}</tspan></text>'
        f'<text x="{sx}" y="{y + 20}" font-family="{SANS}" font-size="12" fill="{MUTE}">{lab}</text>')
    sep = lambda y: f'<line x1="{sx}" x2="{W - 40}" y1="{y}" y2="{y}" stroke="#dcd9cf"/>'
    body = card_bg(h) + f'''
<text x="40" y="52" font-family="{MONO}" font-size="11" letter-spacing="1.4" fill="{MUTE}">THE LAST 12 MONTHS ON GITHUB</text>
<text x="38" y="98" font-family="{SERIF}" font-size="42" fill="{INK}">{total:,} <tspan font-style="italic">contributions</tspan></text>
{''.join(bars)}
{stat(96, cur, " days", f"current streak · longest {best}")}{sep(132)}
{stat(176, active, " / 365", "days with a contribution")}{sep(212)}
{stat(256, busiest, "", "on the busiest day")}'''
    return svg(h, body, f"{total} contributions in the last 12 months, current streak {cur} days, {active} active days")


TW = W / 3


def small_svg(h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{TW:.3f}" height="{h}" viewBox="0 0 {TW:.3f} {h}" '
            f'role="img" aria-label="{esc(label)}">{body}</svg>')


def tile(t, d):
    h = 176
    big_a, big_b = (s.format(**d) for s in t["big"])
    body = f'''<rect x="6" y="6" width="{TW - 12:.1f}" height="{h - 12}" rx="12" fill="{t["bg"]}"/>
<text x="22" y="34" font-family="{MONO}" font-size="9.5" letter-spacing="1.4" fill="{t["fg"]}" opacity=".85">{esc(t["key"])}</text>
<text x="{TW - 22:.1f}" y="34" text-anchor="end" font-family="{MONO}" font-size="11" fill="{t["fg"]}">→</text>
<text x="20" y="98" font-family="{SERIF}" font-size="34" fill="{t["fg"]}">{esc(big_a)}<tspan font-style="italic">{esc(big_b)}</tspan></text>
<text x="22" y="128" font-family="{SANS}" font-size="11.5" fill="{t["fg"]}" opacity=".9">{esc(t["lines"][0])}</text>
<text x="22" y="145" font-family="{SANS}" font-size="11.5" fill="{t["fg"]}" opacity=".9">{esc(t["lines"][1])}</text>'''
    return small_svg(h, body, f'{t["key"]}: {big_a}{big_b}')


def title(dark):
    h = 80
    fg = "#f0f0ee" if dark else INK
    body = f'<text x="14" y="52" font-family="{SERIF}" font-size="32" fill="{fg}">What I’m <tspan font-style="italic">building</tspan></text>'
    return svg(h, body, "What I'm building")


def repo(p, d):
    h = 150
    meta = p["meta"].format(**d)
    body = f'''<rect x="6" y="6" width="{TW - 12:.1f}" height="{h - 12}" rx="12" fill="{BG}"/>
<rect x="22" y="28" width="8" height="8" fill="{p["color"]}"/>
<text x="38" y="37" font-family="{SANS}" font-weight="700" font-size="14" fill="{INK}">{esc(p["name"])}</text>
<text x="22" y="70" font-family="{SANS}" font-size="11.5" fill="#3a3a40">{esc(p["desc"][0])}</text>
<text x="22" y="87" font-family="{SANS}" font-size="11.5" fill="#3a3a40">{esc(p["desc"][1])}</text>
<text x="22" y="122" font-family="{MONO}" font-size="10" fill="{MUTE}">{esc(meta)}</text>'''
    return small_svg(h, body, f'{p["name"]}: {" ".join(p["desc"])}')


def main():
    d = fetch()
    OUT.mkdir(exist_ok=True)
    files = {
        "hero.svg": hero(),
        "heatmap.svg": heatmap(d),
        "activity.svg": activity(d),
        "title-light.svg": title(False),
        "title-dark.svg": title(True),
    }
    for t in TILES:
        files[f"tile-{t['key'].lower().replace(' ', '-')}.svg"] = tile(t, d)
    for p in PROJECTS:
        files[f"repo-{p['name']}.svg"] = repo(p, d)
    for name, content in files.items():
        (OUT / name).write_text(content)
    print("wrote", len(files), "cards")


if __name__ == "__main__":
    main()
