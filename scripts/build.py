#!/usr/bin/env python3
"""Builds every SVG in assets/ for the GitHub profile README.

Run locally or from the daily GitHub Action. Standard library only.
Live numbers (stars, npm downloads) are fetched; if a fetch fails the
last known value in assets/stats.json is kept, so a build never breaks.
"""
import json, os, random, urllib.request, datetime
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets")
os.makedirs(OUT, exist_ok=True)

USER = "Sepantapouya"
KASHI_PKGS = ["tokens", "css", "persian", "bank-logos", "icons", "react", "elements", "tailwind", "mcp"]

THEMES = {
    "dark": dict(bg="#0A0C0F", surface="#11151A", surface2="#161B22", line="#222A33", line2="#2C3540",
                 text="#F2F4F7", muted="#8B95A3", faint="#5A6472",
                 accent="#D2145A", accent_txt="#F2457F", tint="#F59AB9", ink="#F2F4F7", glow="0.38"),
    "light": dict(bg="#FFFFFF", surface="#F7F8FA", surface2="#F1F3F6", line="#E4E7EC", line2="#D5DAE1",
                  text="#0B0D10", muted="#5B6472", faint="#98A2B3",
                  accent="#D2145A", accent_txt="#D2145A", tint="#F4B3C9", ink="#0B0D10", glow="0.13"),
}

SANS = "-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'SF Mono', 'JetBrains Mono', Menlo, Consolas, monospace"
MONO_W = 0.602  # advance width of a monospace glyph, in em


# ------------------------------------------------------------------ data
def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-builder"})
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def load_stats():
    path = os.path.join(OUT, "stats.json")
    stats = json.load(open(path)) if os.path.exists(path) else {
        "kashi_stars": 42, "npm_month": 72000, "exportease_stars": 2, "toad_stars": 1}
    try:
        stats["kashi_stars"] = fetch_json(f"https://api.github.com/repos/{USER}/Kashi")["stargazers_count"]
        stats["exportease_stars"] = fetch_json(f"https://api.github.com/repos/{USER}/Exportease")["stargazers_count"]
        stats["toad_stars"] = fetch_json(f"https://api.github.com/repos/{USER}/Toad-redesigned")["stargazers_count"]
    except Exception as e:
        print("github fetch failed, keeping cached:", e)
    try:
        total = 0
        for p in KASHI_PKGS:
            total += fetch_json(f"https://api.npmjs.org/downloads/point/last-month/@kashi-ui/{p}").get("downloads", 0)
        if total:
            stats["npm_month"] = total
    except Exception as e:
        print("npm fetch failed, keeping cached:", e)
    numbers = {k: v for k, v in stats.items() if k not in ("updated", "_last")}
    if numbers != stats.get("_last") or "updated" not in stats:
        stats["updated"] = datetime.date.today().isoformat()
    stats["_last"] = numbers
    json.dump(stats, open(path, "w"), indent=2)
    return stats


def compact(n):
    if n >= 1000:
        v = n / 1000
        return (f"{v:.1f}".rstrip("0").rstrip(".")) + "k"
    return str(n)


# ------------------------------------------------------------------ helpers
def svg(w, h, body, t, title):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>
  .sans{{font-family:{SANS}}} .mono{{font-family:{MONO}}}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
{body}
</svg>
"""


def frame(w, h, t, r=20, fill=None):
    return (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{r}" '
            f'fill="{fill or t["surface"]}" stroke="{t["line"]}"/>')


def chip(x, y, label, t, size=12, color=None, pad=10, h=26, dot=None):
    w = len(label) * size * MONO_W + pad * 2 + (14 if dot else 0)
    tx = x + pad + (14 if dot else 0)
    s = (f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h/2}" fill="{t["surface2"]}" stroke="{t["line"]}"/>'
         f'<text x="{tx:.1f}" y="{y+h/2+size*0.36:.1f}" class="mono" font-size="{size}" fill="{color or t["muted"]}">{escape(label)}</text>')
    if dot:
        s += f'<circle cx="{x+pad+4}" cy="{y+h/2}" r="3.5" fill="{dot}"/>'
    return s, w


def chips_row(x, y, labels, t, gap=8, **kw):
    out = []
    for lab in labels:
        s, w = chip(x, y, lab, t, **kw)
        out.append(s)
        x += w + gap
    return "".join(out), x


def text_width(s, size):
    """Rough advance width of proportional sans text (no font metrics in an <img> SVG)."""
    em = 0
    for ch in s:
        if ch in "ilj.,:;|!'I ": em += 0.27
        elif ch in "frt/()-": em += 0.36
        elif ch in "mwMW": em += 0.86
        elif ch.isupper(): em += 0.68
        else: em += 0.56
    return em * size


# ------------------------------------------------------------------ tile motif
def tile(x, y, s, kind, rot, color, t, cls=""):
    """One Kashi tile: a rounded cell carrying a simple geometric figure."""
    cx, cy = x + s / 2, y + s / 2
    base = f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="6" fill="{t["surface2"]}" stroke="{t["line"]}"/>'
    g = f'<g transform="rotate({rot} {cx} {cy})">'
    if kind == "quarter":
        fig = f'<path d="M{x+3} {y+3} L{x+s-3} {y+3} A{s-6} {s-6} 0 0 1 {x+3} {y+s-3} Z" fill="{color}"/>'
    elif kind == "half":
        fig = f'<path d="M{x+3} {cy} A{s/2-3} {s/2-3} 0 0 1 {x+s-3} {cy} Z" fill="{color}"/>'
    elif kind == "circle":
        fig = f'<circle cx="{cx}" cy="{cy}" r="{s/2-8}" fill="{color}"/>'
    elif kind == "ring":
        fig = f'<circle cx="{cx}" cy="{cy}" r="{s/2-10}" fill="none" stroke="{color}" stroke-width="5"/>'
    elif kind == "tri":
        fig = f'<path d="M{x+3} {y+3} L{x+s-3} {y+3} L{x+3} {y+s-3} Z" fill="{color}"/>'
    elif kind == "dot":
        fig = f'<circle cx="{cx}" cy="{cy}" r="4" fill="{color}"/>'
    else:  # solid
        fig = f'<rect x="{x+3}" y="{y+3}" width="{s-6}" height="{s-6}" rx="4" fill="{color}"/>'
    return f'<g class="{cls}">{base}{g}{fig}</g></g>'


def tile_field(ox, oy, cols, rows, s, gap, t, seed=7, animate=True):
    rnd = random.Random(seed)
    kinds = ["quarter", "quarter", "half", "circle", "ring", "tri", "dot", "solid"]
    palette = [t["accent"], t["accent"], t["accent"], t["tint"], t["ink"], t["line2"]]
    out = []
    n = 0
    for r in range(rows):
        for c in range(cols):
            # fade the field towards the top-left so it melts into the text
            fade = min(1.0, (c / cols) * 1.25 + (r / rows) * 0.25)
            if rnd.random() > fade - 0.05:
                continue
            k = rnd.choice(kinds)
            col = rnd.choice(palette)
            rot = rnd.choice([0, 90, 180, 270])
            cls = ""
            if animate and rnd.random() < 0.22:
                cls = f"spin d{n % 6}"
                n += 1
            x, y = ox + c * (s + gap), oy + r * (s + gap)
            out.append(f'<g opacity="{0.35 + 0.65 * fade:.2f}">' + tile(x, y, s, k, rot, col, t, cls) + "</g>")
    return "".join(out)


TILE_CSS = """
  .spin{transform-box:fill-box;transform-origin:center;animation:turn 9s cubic-bezier(.65,0,.35,1) infinite}
  .d0{animation-delay:0s}.d1{animation-delay:1.5s}.d2{animation-delay:3s}
  .d3{animation-delay:4.5s}.d4{animation-delay:6s}.d5{animation-delay:7.5s}
  @keyframes turn{0%,80%{transform:rotate(0)}90%,100%{transform:rotate(90deg)}}
"""


# ------------------------------------------------------------------ assets
def hero(t, mode, stats):
    W, H = 1200, 460
    defs = f"""<defs>
  <radialGradient id="g1" cx="78%" cy="20%" r="60%"><stop offset="0" stop-color="{t['accent']}" stop-opacity="{t['glow']}"/><stop offset="1" stop-color="{t['accent']}" stop-opacity="0"/></radialGradient>
  <radialGradient id="g2" cx="100%" cy="100%" r="55%"><stop offset="0" stop-color="{t['tint']}" stop-opacity="{float(t['glow'])*0.8}"/><stop offset="1" stop-color="{t['tint']}" stop-opacity="0"/></radialGradient>
  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="{t['line']}" stroke-width="1" opacity=".35"/></pattern>
  <linearGradient id="gridfade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".55" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
  <mask id="gm"><rect width="{W}" height="{H}" fill="url(#gridfade)"/></mask>
  <clipPath id="clip"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="23"/></clipPath>
</defs>"""
    style = f"""<style>{TILE_CSS}
  .pulse{{animation:pulse 2.4s ease-out infinite;transform-box:fill-box;transform-origin:center}}
  @keyframes pulse{{0%{{opacity:.55;transform:scale(1)}}100%{{opacity:0;transform:scale(3.2)}}}}
  .rise{{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}}
  .r2{{animation-delay:.12s}}.r3{{animation-delay:.24s}}.r4{{animation-delay:.36s}}
  @keyframes rise{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
</style>"""
    stat_items = [("6+", "years designing products"), ("30+", "products shipped"),
                  ("400+", "hours of mentoring"), (compact(stats["npm_month"]), "Kashi installs / month")]
    sx, stats_svg = 64, []
    for big, small in stat_items:
        stats_svg.append(f'<text x="{sx}" y="392" class="sans" font-size="30" font-weight="650" letter-spacing="-1" fill="{t["text"]}">{big}</text>'
                         f'<text x="{sx}" y="416" class="sans" font-size="13" fill="{t["muted"]}">{small}</text>')
        sx += 168
    pill_w = 268
    body = f"""{defs}{style}
<g clip-path="url(#clip)">
  <rect width="{W}" height="{H}" fill="{t['bg']}"/>
  <rect width="{W}" height="{H}" fill="url(#grid)" mask="url(#gm)"/>
  <rect width="{W}" height="{H}" fill="url(#g1)"/>
  <rect width="{W}" height="{H}" fill="url(#g2)"/>
  {tile_field(800, 56, 6, 6, 50, 10, t, seed=11)}
</g>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="23.5" fill="none" stroke="{t['line']}"/>

<g class="rise">
  <rect x="64" y="60" width="{pill_w}" height="30" rx="15" fill="{t['surface']}" stroke="{t['line']}"/>
  <circle cx="84" cy="75" r="4" fill="{t['accent']}"/><circle class="pulse" cx="84" cy="75" r="4" fill="{t['accent']}"/>
  <text x="98" y="79.5" class="sans" font-size="13" font-weight="500" fill="{t['text']}">Open to projects &amp; mentorship</text>
</g>
<g class="rise r2">
  <text x="60" y="176" class="sans" font-size="76" font-weight="700" letter-spacing="-3.2" fill="{t['text']}">Sepanta Pouya</text>
</g>
<g class="rise r3">
  <text x="64" y="224" class="sans" font-size="23" font-weight="500" letter-spacing="-.3" fill="{t['text']}">Senior Product Designer, UX mentor &amp; design-system builder.</text>
  <text x="64" y="256" class="sans" font-size="18" fill="{t['muted']}">I turn messy, complex problems into clear, friendly products —</text>
  <text x="64" y="280" class="sans" font-size="18" fill="{t['muted']}">and lately, I ship the code behind them too.</text>
</g>
<line x1="64" x2="720" y1="334" y2="334" stroke="{t['line']}"/>
<g class="rise r4">{''.join(stats_svg)}</g>
"""
    return svg(W, H, body, t, "Sepanta Pouya — Senior Product Designer, UX mentor and design-system builder")


def section(t, label, num):
    W, H = 1200, 64
    body = f"""<text x="2" y="40" class="mono" font-size="14" fill="{t['accent_txt']}">{num}</text>
<text x="40" y="40" class="mono" font-size="14" letter-spacing="2.5" fill="{t['muted']}">{escape(label.upper())}</text>
<line x1="{40 + len(label) * 14 * (MONO_W + 2.5/14) + 18:.0f}" x2="{W}" y1="35.5" y2="35.5" stroke="{t['line']}"/>"""
    return svg(W, H, body, t, label)


def kashi_card(t, stats):
    W, H = 1200, 400
    rnd_preview = f"""
  <!-- miniature UI built from Kashi parts, set right-to-left -->
  <g transform="translate(700 56)">
    <rect width="436" height="288" rx="16" fill="{t['bg']}" stroke="{t['line']}"/>
    <rect x="1" y="1" width="434" height="40" rx="15" fill="{t['surface2']}"/>
    <rect x="1" y="26" width="434" height="15" fill="{t['surface2']}"/>
    <line x1="1" x2="435" y1="41" y2="41" stroke="{t['line']}"/>
    <circle cx="410" cy="21" r="5" fill="{t['line2']}"/><circle cx="392" cy="21" r="5" fill="{t['line2']}"/><circle cx="374" cy="21" r="5" fill="{t['line2']}"/>
    <text x="408" y="82" text-anchor="end" class="sans" font-size="20" font-weight="700" fill="{t['text']}">سلام، خوش آمدید</text>
    <text x="408" y="108" text-anchor="end" class="sans" font-size="13" fill="{t['muted']}">دیزاین‌سیستم فارسی، راست‌به‌چپ از پایه</text>
    <rect x="148" y="130" width="260" height="40" rx="10" fill="{t['surface']}" stroke="{t['accent']}" stroke-width="1.5"/>
    <text x="394" y="155" text-anchor="end" class="sans" font-size="13" fill="{t['faint']}">کد ملی</text>
    <text x="164" y="155" class="mono" font-size="13" fill="{t['text']}">۰۰۱۲۳۴۵۶۷۸</text>
    <rect x="28" y="130" width="104" height="40" rx="10" fill="{t['accent']}"/>
    <text x="80" y="155" text-anchor="middle" class="sans" font-size="14" font-weight="600" fill="#FFFFFF">ادامه</text>
    <rect x="28" y="190" width="380" height="68" rx="12" fill="{t['surface']}" stroke="{t['line']}"/>
    <rect class="sw" x="44" y="214" width="40" height="22" rx="11" fill="{t['accent']}"/>
    <circle class="knob" cx="73" cy="225" r="8" fill="#FFFFFF"/>
    <text x="392" y="220" text-anchor="end" class="sans" font-size="14" font-weight="600" fill="{t['text']}">حالت تیره</text>
    <text x="392" y="242" text-anchor="end" class="sans" font-size="12" fill="{t['muted']}">۱۴۰۵/۰۸/۲۷ · ۱۳٬۰۰۰ آیکون</text>
  </g>"""
    style = """<style>
  .knob{animation:knob 4s cubic-bezier(.65,0,.35,1) infinite}
  @keyframes knob{0%,40%{transform:translateX(0)}50%,90%{transform:translateX(-18px)}100%{transform:translateX(0)}}
  .sw{animation:sw 4s cubic-bezier(.65,0,.35,1) infinite}
  @keyframes sw{0%,40%{opacity:1}50%,90%{opacity:.35}100%{opacity:1}}
</style>"""
    tags, _ = chips_row(56, 236, ["React", "Web Components", "Tokens", "Tailwind", "Figma kit", "MCP"], t)
    meta = [(f"★ {stats['kashi_stars']}", "stars"), (compact(stats["npm_month"]), "npm / month"),
            ("60+", "components"), ("13k", "icons")]
    mx, meta_svg = 56, []
    for a, b in meta:
        meta_svg.append(f'<text x="{mx}" y="328" class="sans" font-size="26" font-weight="650" letter-spacing="-.8" fill="{t["text"]}">{a}</text>'
                        f'<text x="{mx}" y="350" class="sans" font-size="12.5" fill="{t["muted"]}">{b}</text>')
        mx += 140
    body = f"""{style}
<defs><radialGradient id="kg" cx="85%" cy="0%" r="70%"><stop offset="0" stop-color="{t['accent']}" stop-opacity="{float(t['glow'])*0.7}"/><stop offset="1" stop-color="{t['accent']}" stop-opacity="0"/></radialGradient></defs>
{frame(W, H, t, 24)}
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="23" fill="url(#kg)"/>
<g transform="translate(56 56)">{tile(0, 0, 44, 'quarter', 0, t['accent'], t)}</g>
<text x="116" y="78" class="sans" font-size="26" font-weight="700" letter-spacing="-.6" fill="{t['text']}">Kashi <tspan fill="{t['muted']}" font-weight="500">کاشی</tspan></text>
<text x="116" y="100" class="mono" font-size="12.5" fill="{t['accent_txt']}">FEATURED · OPEN SOURCE · MIT</text>
<text x="56" y="152" class="sans" font-size="19" font-weight="500" fill="{t['text']}">An open-source Persian design system.</text>
<text x="56" y="180" class="sans" font-size="16" fill="{t['muted']}">RTL-first, dark-first and accessible — React, Web Components,</text>
<text x="56" y="202" class="sans" font-size="16" fill="{t['muted']}">tokens, a Figma kit and an MCP server for AI assistants.</text>
{tags}
<line x1="56" x2="640" y1="286" y2="286" stroke="{t['line']}"/>
{''.join(meta_svg)}
{rnd_preview}"""
    return svg(W, H, body, t, f"Kashi — open-source Persian design system. {stats['kashi_stars']} stars, {stats['npm_month']} npm installs a month")


def small_card(t, name, kicker, lines, tags, foot, accent, glyph, title):
    W, H = 588, 310
    tg, _ = chips_row(40, 210, tags, t, size=11.5, h=24, pad=9)
    ls = "".join(f'<text x="40" y="{142 + i*24}" class="sans" font-size="15.5" fill="{t["muted"] if i else t["text"]}">{escape(l)}</text>'
                 for i, l in enumerate(lines))
    body = f"""{frame(W, H, t, 22)}
<g transform="translate(40 40)">{tile(0, 0, 40, glyph[0], glyph[1], accent, t)}</g>
<text x="96" y="62" class="sans" font-size="22" font-weight="700" letter-spacing="-.5" fill="{t['text']}">{escape(name)}</text>
<text x="96" y="82" class="mono" font-size="11.5" letter-spacing=".5" fill="{t['accent_txt'] if accent == t['accent'] else t['muted']}">{escape(kicker)}</text>
<text x="{W-40}" y="66" text-anchor="end" class="sans" font-size="20" fill="{t['faint']}">↗</text>
{ls}
{tg}
<line x1="40" x2="{W-40}" y1="256" y2="256" stroke="{t['line']}"/>
<text x="40" y="282" class="mono" font-size="12" fill="{t['muted']}">{escape(foot)}</text>"""
    return svg(W, H, body, t, title)


def toolkit(t):
    W = 1200
    groups = [
        ("Design", t["accent"], ["Figma", "Design systems", "Prototyping", "UX research", "Usability testing", "Information architecture", "Interaction design"]),
        ("Build", t["tint"], ["React", "TypeScript", "Next.js", "Tailwind", "Web Components", "Capacitor", "Figma plugins"]),
        ("AI & automation", t["ink"], ["Claude Code", "MCP servers", "Agent skills", "n8n", "Prompt design", "Vercel"]),
    ]
    out, y = [], 48
    for name, col, items in groups:
        out.append(f'<circle cx="52" cy="{y+13}" r="4.5" fill="{col}"/>'
                   f'<text x="68" y="{y+18}" class="sans" font-size="15" font-weight="600" fill="{t["text"]}">{escape(name)}</text>')
        x, row = 230, []
        for it in items:
            s, w = chip(x, y, it, t, size=12.5, h=28, pad=12)
            if x + w > W - 40:
                break
            row.append(s)
            x += w + 8
        out.append("".join(row))
        y += 56
    H = y + 16
    body = frame(W, H, t, 22) + "".join(out)
    return svg(W, H, body, t, "Toolkit: design, build, AI and automation")


def link_button(t, label, primary=False):
    size = 14
    w = int(text_width(label, size) + 66)
    H = 44
    fill = t["text"] if primary else t["surface"]
    fg = t["bg"] if primary else t["text"]
    stroke = t["text"] if primary else t["line2"]
    body = (f'<rect x="0.5" y="0.5" width="{w-1}" height="{H-1}" rx="{H/2}" fill="{fill}" stroke="{stroke}"/>'
            f'<text x="22" y="27.5" class="sans" font-size="{size}" font-weight="550" fill="{fg}">{escape(label)}</text>'
            f'<text x="{w-22}" y="27.5" text-anchor="end" class="sans" font-size="{size}" fill="{fg}" opacity=".6">↗</text>')
    return svg(w, H, body, t, label)


def footer(t, stats):
    W, H = 1200, 120
    body = f"""<defs><linearGradient id="fl" x1="0" x2="1"><stop offset="0" stop-color="{t['line']}" stop-opacity="0"/><stop offset=".5" stop-color="{t['line2']}"/><stop offset="1" stop-color="{t['line']}" stop-opacity="0"/></linearGradient></defs>
<line x1="0" x2="{W}" y1="20" y2="20" stroke="url(#fl)"/>
<g transform="translate({W/2 - 74} 44)">
  {tile(0, 0, 28, 'quarter', 0, t['accent'], t)}{tile(36, 0, 28, 'circle', 0, t['tint'], t)}{tile(72, 0, 28, 'half', 180, t['ink'], t)}{tile(108, 0, 28, 'tri', 90, t['accent'], t)}
</g>
<text x="{W/2}" y="104" text-anchor="middle" class="mono" font-size="12" fill="{t['faint']}">every graphic on this page is hand-made SVG · numbers refresh daily · updated {stats['updated']}</text>"""
    return svg(W, H, body, t, "Footer")


# ------------------------------------------------------------------ main
def main():
    stats = load_stats()
    buttons = [("website", "sepantapouya.com", True), ("linkedin", "LinkedIn", False), ("medium", "Medium", False),
               ("dribbble", "Dribbble", False), ("podcast", "SepiCast podcast", False), ("telegram", "Telegram", False),
               ("x", "X / Twitter", False)]
    for mode, t in THEMES.items():
        files = {
            f"hero-{mode}.svg": hero(t, mode, stats),
            f"kashi-{mode}.svg": kashi_card(t, stats),
            f"toolkit-{mode}.svg": toolkit(t),
            f"footer-{mode}.svg": footer(t, stats),
            f"s-work-{mode}.svg": section(t, "Selected work", "01"),
            f"s-toolkit-{mode}.svg": section(t, "Toolkit", "02"),
            f"s-elsewhere-{mode}.svg": section(t, "Elsewhere", "03"),
            f"exportease-{mode}.svg": small_card(
                t, "Exportease", "FIGMA PLUGIN",
                ["Design tokens → clean code files.", "Export Figma variables to CSS, JS & Tailwind,", "organised by collection."],
                ["Figma API", "TypeScript", "Tokens"], f"★ {stats['exportease_stars']}  ·  github.com/{USER}/Exportease",
                t["tint"], ("half", 0), "Exportease — Figma plugin that exports design tokens to code"),
            f"toad-{mode}.svg": small_card(
                t, "Toad, redesigned", "CONCEPT · LIVE DEMO",
                ["A ground-up UX redesign, shipped as code.", "From audit and flows to a working,", "deployed front end."],
                ["UX audit", "TypeScript", "Vercel"], "toad-redesigned.vercel.app",
                t["ink"], ("circle", 0), "Toad redesigned — UX redesign concept with live demo"),
            f"ux-{mode}.svg": small_card(
                t, "Writing & mentoring", "UX COLLECTIVE · SEPICAST",
                ["Published contributor at UX Collective,", "host of SepiCast (a Persian design podcast)", "and 400+ hours of 1:1 mentoring."],
                ["Medium", "Podcast", "Mentoring"], "sepantapouya.medium.com",
                t["accent"], ("ring", 0), "Writing and mentoring — UX Collective, SepiCast podcast, mentoring"),
            f"site-{mode}.svg": small_card(
                t, "Case studies", "PORTFOLIO",
                ["Shopify apps, B2B dashboards and", "consumer products — the full stories,", "from problem to shipped result."],
                ["Polaris", "Material", "B2B · B2C"], "sepantapouya.com",
                t["tint"], ("quarter", 180), "Case studies on sepantapouya.com"),
        }
        for key, label, primary in buttons:
            files[f"btn-{key}-{mode}.svg"] = link_button(t, label, primary)
        for name, content in files.items():
            open(os.path.join(OUT, name), "w").write(content)
    print("built", len(os.listdir(OUT)), "files; stats:", stats)


if __name__ == "__main__":
    main()
