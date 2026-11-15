"""Build the retro (neo-brutalist) SVG panels for the GitHub profile README.

Usage: python tools/build.py <fonts_dir>
fonts_dir must contain grotesk-700.ttf (Space Grotesk Bold), mono-400.ttf and
mono-700.ttf (Space Mono). Fonts are subset and embedded so the SVGs render the
same everywhere (GitHub serves README images as <img>, which cannot load web fonts).
"""
import base64
import io
import sys
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
FONTS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tools" / "fonts"

INK = "#111111"
PAPER = "#FFFFFF"
GROUND = "#F3F3EF"
YELLOW = "#FFE45C"
TEAL = "#4ECDC4"
SALMON = "#FF8A80"
LILAC = "#B794F4"
GREY = "#E4E4E0"
MUTED = "#5B5B57"

CHARS = "".join(chr(c) for c in range(32, 127)) + "·→↗—–▸•"


class Face:
    def __init__(self, file, family):
        self.family = family
        font = TTFont(FONTS / file)
        self.upm = font["head"].unitsPerEm
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"]
        missing = [ch for ch in CHARS if ord(ch) not in self.cmap]
        if missing:
            print(f"{family}: no glyph for {''.join(missing)!r}")
        opts = Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga"]
        sub = Subsetter(opts)
        sub.populate(text=CHARS)
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        self.b64 = base64.b64encode(buf.getvalue()).decode()

    def width(self, text, size, spacing=0.0):
        units = 0
        for ch in text:
            g = self.cmap.get(ord(ch))
            units += self.hmtx[g][0] if g else self.upm * 0.6
        return units * size / self.upm + spacing * max(len(text) - 1, 0)


G = Face("grotesk-700.ttf", "SG")
M = Face("mono-400.ttf", "SM")
MB = Face("mono-700.ttf", "SMB")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, body, title):
    style = (
        f"@font-face{{font-family:SG;src:url(data:font/woff2;base64,{G.b64}) format('woff2');}}"
        f"@font-face{{font-family:SM;src:url(data:font/woff2;base64,{M.b64}) format('woff2');}}"
        f"@font-face{{font-family:SMB;src:url(data:font/woff2;base64,{MB.b64}) format('woff2');}}"
        ".g{font-family:SG,'Arial Black',Arial,sans-serif;font-weight:700}"
        ".m{font-family:SM,'Courier New',monospace}"
        ".mb{font-family:SMB,'Courier New',monospace;font-weight:700}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
        f"<style>{style}</style>{body}</svg>"
    )


def box(x, y, w, h, fill=PAPER, shadow=6, stroke=3):
    s = f'<rect x="{x + shadow}" y="{y + shadow}" width="{w}" height="{h}" fill="{INK}"/>' if shadow else ""
    return s + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{INK}" stroke-width="{stroke}"/>'


def text(x, y, s, cls, size, fill=INK, anchor="start", spacing=0, opacity=None):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' opacity="{opacity}"' if opacity else ""
    return (f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}"{ls}{op}>{esc(s)}</text>')


def wrap(s, face, size, max_w):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if face.width(trial, size) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def chip(x, y, label, fill=PAPER, fg=INK, size=12, pad=10, h=24, face=MB, cls="mb", shadow=3):
    w = face.width(label, size, 0.5) + pad * 2
    out = box(x, y, w, h, fill, shadow=shadow, stroke=2)
    out += text(x + pad, y + h / 2 + size * 0.36, label, cls, size, fg, spacing=0.5)
    return out, w


def highlight(x, y, label, size=14):
    w = MB.width(label, size, 1) + 12
    return (f'<rect x="{x}" y="{y - size - 3}" width="{w}" height="{size + 9}" fill="{YELLOW}"/>'
            f'<line x1="{x}" y1="{y + 7}" x2="{x + w}" y2="{y + 7}" stroke="{INK}" stroke-width="1.5" stroke-dasharray="4 3"/>'
            + text(x + 6, y, label, "mb", size, spacing=1))


# ---------- icons (24x24 units, drawn in white on a black tile) ----------
def icon(kind, x, y, s=40, fg=PAPER, bg=INK):
    t = f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{bg}"/>'
    k = s / 24
    g = f'<g transform="translate({x},{y}) scale({k})" fill="none" stroke="{fg}" stroke-width="2.2" stroke-linecap="square">'
    paths = {
        "target": '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>',
        "bolt": '<path d="M13 3 6 13h5l-1 8 7-10h-5z"/>',
        "check": '<rect x="4" y="4" width="16" height="16"/><path d="m8 12 3 3 5-6"/>',
        "pulse": '<path d="M3 13h4l2-6 4 11 2-5h6"/>',
        "user": '<rect x="8" y="4" width="8" height="8"/><path d="M5 20v-3h14v3"/>',
        "pin": '<path d="M12 21s-6-6-6-11a6 6 0 0 1 12 0c0 5-6 11-6 11z"/><rect x="10.5" y="8.5" width="3" height="3"/>',
        "globe": '<circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c3 3 3 13 0 16M12 4c-3 3-3 13 0 16"/>',
        "bell": '<path d="M6 17V11a6 6 0 0 1 12 0v6zM4 17h16M10 20h4"/>',
    }
    return t + g + paths[kind] + "</g>"


def arrow_ne(x, y, s=9, color=INK):
    return (f'<path d="M{x} {y + s} L{x + s} {y} M{x + 3} {y} H{x + s} V{y + s - 3}" '
            f'stroke="{color}" stroke-width="2" fill="none"/>')


# ---------- 1. header ----------
def header():
    W, H = 1000, 330
    b = box(8, 8, W - 22, H - 22, PAPER)
    # sidebar
    b += f'<rect x="8" y="8" width="250" height="{H - 22}" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>'
    b += f'<rect x="8" y="8" width="250" height="78" fill="{YELLOW}" stroke="{INK}" stroke-width="3"/>'
    b += f'<rect x="30" y="31" width="32" height="32" fill="{INK}"/><rect x="38" y="39" width="10" height="10" fill="{YELLOW}"/>'
    b += text(76, 57, "ASADBEK", "g", 26)
    b += text(30, 116, "INDEX", "mb", 11, MUTED, spacing=1.5)
    items = [("01", "METRICS", True), ("02", "PROJECTS", False), ("03", "EXPERIENCE", False), ("04", "TOOLBOX", False), ("05", "CONTACT", False)]
    for i, (n, label, active) in enumerate(items):
        y = 128 + i * 36
        fill, fg = (INK, PAPER) if active else (PAPER, INK)
        b += box(30, y, 206, 28, fill, shadow=3, stroke=2)
        b += text(42, y + 19, n, "mb", 12, YELLOW if active else MUTED)
        b += text(72, y + 19, label, "mb", 12, fg, spacing=1)
    # top bar
    b += f'<line x1="258" y1="70" x2="{W - 14}" y2="70" stroke="{INK}" stroke-width="3"/>'
    b += text(282, 47, "PROFILE", "g", 20)
    sb_x = 560
    b += box(sb_x, 24, 250, 32, PAPER, shadow=0, stroke=2)
    b += icon("pin", sb_x + 8, 30, 20, INK, PAPER)
    b += text(sb_x + 36, 45, "SOUTH KOREA · REMOTE OK", "m", 12, MUTED, spacing=1)
    b += box(826, 24, 32, 32, PAPER, shadow=0, stroke=2) + icon("bell", 832, 30, 20, INK, PAPER)
    b += f'<rect x="870" y="24" width="32" height="32" fill="{LILAC}" stroke="{INK}" stroke-width="2"/>'
    b += text(886, 45, "AO", "mb", 13, PAPER, anchor="middle")
    # hero
    b += text(282, 140, "ASADBEK OTABEKOV", "g", 46)
    b += highlight(284, 176, "SOFTWARE ENGINEER · BACKEND · APPLIED SECURITY")
    lines = wrap("I engineer systems that work beyond the happy path, and trace failures across layers until the fix is proven.", M, 15, 660)
    for i, line in enumerate(lines):
        b += text(282, 220 + i * 24, line, "m", 15, MUTED)
    cy = 220 + len(lines) * 24
    c, w1 = chip(282, cy, "HUMBLEBEE AI · 2025–NOW", PAPER, size=12, h=30)
    b += c
    c, w2 = chip(282 + w1 + 16, cy, "OPEN TO REMOTE", INK, PAPER, size=12, h=30)
    b += c
    return svg(W, H, b, "Asadbek Otabekov. Software engineer: backend, applied security. Based in South Korea, open to remote. I engineer systems that work beyond the happy path.")


# ---------- 2. stat cards ----------
def stats():
    W, H = 1000, 220
    cards = [
        ("target", "MACRO-F1", "1.000", "200K ROWS", YELLOW),
        ("bolt", "INFERENCE / ROW", "0.32 ms", "RF MODEL", PAPER),
        ("check", "PASSING TESTS", "126", "AUTOMATION", PAPER),
        ("pulse", "DETECTION SCORE", "0.35→0.926", "1 EVAL", PAPER),
    ]
    b = ""
    cw, gap = 226, 22
    for i, (ic, label, value, tag, fill) in enumerate(cards):
        x, y = 8 + i * (cw + gap), 8
        b += box(x, y, cw, 190, fill)
        # faded big icon
        b += f'<g opacity="0.12">{icon(ic, x + cw - 92, y + 40, 76, INK, "none")}</g>'
        b += icon(ic, x + 20, y + 20, 40)
        cx = x + cw - 20 - (MB.width(tag, 11, 0.5) + 30)
        b += box(cx, y + 22, MB.width(tag, 11, 0.5) + 30, 24, PAPER, shadow=0, stroke=2)
        b += arrow_ne(cx + 8, y + 29, 9)
        b += text(cx + 22, y + 38, tag, "mb", 11, spacing=0.5)
        b += text(x + 20, y + 112, label, "mb", 12, spacing=1)
        b += f'<line x1="{x + 20}" y1="{y + 118}" x2="{x + 20 + MB.width(label, 12, 1)}" y2="{y + 118}" stroke="{INK}" stroke-width="2"/>'
        size = 34 if MB.width(value, 34, 1) < cw - 40 else 24
        b += text(x + 20, y + 162, value, "mb", size, spacing=1)
    return svg(W, H, b, "Engineering, measured: 1.000 macro-F1 on 200,000 rows for passive OS fingerprinting; 0.32 ms per row Random Forest inference; 126 passing tests in an automation system; one browser-detection evaluation improved from 0.35 to 0.926.")


# ---------- 3. project cards ----------
PROJECTS = [
    ("01", "PASSIVE OS FINGERPRINTING", TEAL,
     "ML fingerprinting from TCP-level features with a Random Forest classifier.",
     ["1.000 macro-F1 across 200,000 rows", "0.32 ms/row inference", "Feature engineering, fast prediction"]),
    ("02", "AUTHENTICATION ARCHITECTURE", YELLOW,
     "Multi-device sessions and refresh tokens across FastAPI, React and PostgreSQL.",
     ["Concurrency-safe: SELECT ... FOR UPDATE", "Cross-layer auth debugging", "19 regression + integration tests"]),
    ("03", "RELIABLE AUTOMATION", SALMON,
     "Continuous event capture and scheduled reporting that survives real interruptions.",
     ["Reconnect-safe recovery", "Negative caching, scheduled jobs", "126 passing tests"]),
    ("04", "BROWSER AUTOMATION DETECTION", LILAC,
     "Telling automation signals apart from real human activity in the browser.",
     ["Behavior and detection-signal analysis", "False-positive awareness", "One evaluation: 0.35 → 0.926"]),
]


def projects():
    W, H = 1000, 560
    b = ""
    cw, ch = 475, 255
    for i, (n, title, color, desc, bullets) in enumerate(PROJECTS):
        x = 8 + (i % 2) * (cw + 28)
        y = 8 + (i // 2) * (ch + 32)
        b += box(x, y, cw, ch)
        b += f'<rect x="{x}" y="{y}" width="{cw}" height="52" fill="{color}" stroke="{INK}" stroke-width="3"/>'
        b += text(x + 20, y + 34, n, "mb", 16)
        b += f'<line x1="{x + 52}" y1="{y + 14}" x2="{x + 52}" y2="{y + 38}" stroke="{INK}" stroke-width="2"/>'
        size = 19 if G.width(title, 19) < cw - 160 else 16
        b += text(x + 66, y + 34, title, "g", size)
        b += text(x + cw - 20, y + 32, "•••", "mb", 14, anchor="end")
        ty = y + 86
        for line in wrap(desc, M, 14, cw - 40):
            b += text(x + 20, ty, line, "m", 14, MUTED)
            ty += 21
        b += f'<line x1="{x + 20}" y1="{ty - 4}" x2="{x + cw - 20}" y2="{ty - 4}" stroke="{INK}" stroke-width="2"/>'
        ty += 22
        for bl in bullets:
            b += f'<rect x="{x + 20}" y="{ty - 10}" width="10" height="10" fill="{color}" stroke="{INK}" stroke-width="1.5"/>'
            b += text(x + 42, ty, bl, "mb", 13)
            ty += 27
    alt = "What I build. " + " ".join(f"{n} {t.title()}: {d} {'; '.join(bl)}." for n, t, _, d, bl in PROJECTS)
    return svg(W, H, b, alt)


# ---------- 4. experience timeline + toolbox ----------
JOBS = [("NAPA", "Backend Laravel Developer", 2022.0, 2024.0, TEAL),
        ("DORA", "Junior Full-Stack Engineer", 2024.0, 2025.0, YELLOW),
        ("HUMBLEBEE AI", "Software Engineer", 2025.0, 2026.9, SALMON)]
DAILY = [("PYTHON", YELLOW), ("FASTAPI", TEAL), ("POSTGRESQL", PAPER), ("SQLALCHEMY", PAPER), ("REACT", SALMON), ("DOCKER", TEAL)]
ALSO = ["LARAVEL", "PHP", "JAVASCRIPT", "REDIS", "OPENCV", "SCIKIT-LEARN"]


def experience():
    W, H = 1000, 360
    b = ""
    # left: career panel
    lx, lw = 8, 590
    b += box(lx, 8, lw, 330)
    b += text(lx + 24, 52, "WHERE I'VE WORKED", "g", 22)
    b += text(lx + 24, 74, "Role timeline · 2022 → now", "m", 12, MUTED)
    oc, ow = chip(lx + lw - 112, 30, "CAREER", GREY, size=11, h=24, shadow=0)
    b += oc
    b += f'<line x1="{lx + 24}" y1="92" x2="{lx + lw - 24}" y2="92" stroke="{INK}" stroke-width="2"/>'
    ax0, ax1 = lx + 222, lx + lw - 30
    def xpos(year):
        return ax0 + (year - 2022) / (2027 - 2022) * (ax1 - ax0)
    for yr in range(2022, 2028):
        xx = xpos(yr)
        b += f'<line x1="{xx}" y1="104" x2="{xx}" y2="290" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="3 4"/>'
        b += text(xx, 312, str(yr), "m", 11, MUTED, anchor="middle")
    for i, (co, role, s, e, color) in enumerate(JOBS):
        y = 116 + i * 58
        b += text(lx + 24, y + 18, co, "mb", 13)
        b += text(lx + 24, y + 36, role, "m", 10, MUTED)
        b += f'<rect x="{xpos(s) + 3}" y="{y + 3}" width="{xpos(e) - xpos(s)}" height="34" fill="{INK}"/>'
        b += f'<rect x="{xpos(s)}" y="{y}" width="{xpos(e) - xpos(s)}" height="34" fill="{color}" stroke="{INK}" stroke-width="2.5"/>'
        label = "2025–NOW" if co.startswith("HUMBLEBEE") else (f"{int(s)}–{int(e) - 1}" if e - s > 1 else f"{int(s)}")
        b += text(xpos(s) + 10, y + 22, label, "mb", 12)
    # right: toolbox
    rx, rw = 626, 352
    b += box(rx, 8, rw, 330)
    b += text(rx + 22, 52, "TOOLBOX", "g", 22)
    tc, tw = chip(rx + rw - 96, 30, "DAILY", GREY, size=11, h=24, shadow=0)
    b += tc
    b += f'<line x1="{rx + 22}" y1="70" x2="{rx + rw - 22}" y2="70" stroke="{INK}" stroke-width="2"/>'
    cx, cy = rx + 22, 88
    for name, fill in DAILY:
        w = MB.width(name, 12, 0.5) + 20
        if cx + w > rx + rw - 22:
            cx, cy = rx + 22, cy + 42
        c, w = chip(cx, cy, name, fill, size=12, h=28)
        b += c
        cx += w + 14
    cy += 56
    b += text(rx + 22, cy, "ALSO WORKED WITH", "mb", 11, MUTED, spacing=1.5)
    cx, cy = rx + 22, cy + 14
    for name in ALSO:
        w = M.width(name, 11, 0.5) + 16
        if cx + w > rx + rw - 22:
            cx, cy = rx + 22, cy + 34
        b += f'<rect x="{cx}" y="{cy}" width="{w}" height="24" fill="{PAPER}" stroke="{INK}" stroke-width="1.5" stroke-dasharray="3 2"/>'
        b += text(cx + 8, cy + 16, name, "m", 11, spacing=0.5)
        cx += w + 10
    alt = ("Where I've worked: Humblebee AI, Software Engineer, 2025 to now; DORA, Junior Full-Stack Engineer, 2024; "
           "NAPA, Backend Laravel Developer, 2022 to 2023. Toolbox, daily: Python, FastAPI, PostgreSQL, SQLAlchemy, React, Docker. "
           "Also worked with: Laravel, PHP, JavaScript, Redis, OpenCV, scikit-learn.")
    return svg(W, H, b, alt)


# ---------- 5. contact banner ----------
def contact():
    W, H = 1000, 170
    b = box(8, 8, W - 22, 140, YELLOW)
    b += text(36, 66, "HAVE A HARD BACKEND OR SECURITY PROBLEM?", "g", 28)
    b += text(36, 100, "Engineering work, collaboration and remote roles welcome.", "m", 15)
    c, w = chip(W - 260, 104, "LET'S TALK  →", INK, PAPER, size=14, h=34, shadow=4)
    b += c
    return svg(W, H, b, "Have a hard backend or security problem? Engineering work, collaboration and remote roles welcome. Let's talk.")


def divider(label):
    W, H = 1000, 56
    b = f'<line x1="8" y1="34" x2="{W - 8}" y2="34" stroke="{INK}" stroke-width="3"/>'
    w = MB.width(label, 14, 2) + 28
    b += f'<rect x="8" y="16" width="{w}" height="34" fill="{INK}"/>'
    b += text(22, 39, label, "mb", 14, YELLOW, spacing=2)
    return svg(W, H, b, label)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    files = {
        "header.svg": header(), "stats.svg": stats(), "projects.svg": projects(),
        "experience.svg": experience(), "contact.svg": contact(),
        "label-path.svg": divider("THE PATH HERE"),
    }
    for name, data in files.items():
        (OUT / name).write_text(data)
        print(f"{name}: {len(data) // 1024} KB")
