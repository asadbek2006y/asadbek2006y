"""Build the retro (neo-brutalist) SVG panels for the GitHub profile README.

Only the header, the stat tiles, the section labels and the contact banner are images.
Everything else lives in README.md as text, so it stays searchable, clickable and readable on phones.

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

CHARS = "".join(chr(c) for c in range(32, 127)) + "·→—–•"


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
        "camera": '<rect x="3" y="7" width="13" height="10"/><path d="m16 11 5-3v8l-5-3"/>',
    }
    return t + g + paths[kind] + "</g>"



# ---------- 1. header ----------
def header():
    W, H = 1000, 300
    b = box(8, 8, W - 22, H - 22, PAPER)
    # monogram block (a logo, not a control)
    b += f'<rect x="8" y="8" width="230" height="{H - 22}" fill="{YELLOW}" stroke="{INK}" stroke-width="3"/>'
    b += f'<rect x="44" y="52" width="158" height="158" fill="{INK}"/>'
    b += text(123, 162, "AO", "g", 86, YELLOW, anchor="middle")
    b += text(123, 248, "SEOUL · KR", "mb", 15, INK, anchor="middle", spacing=2)
    # name, role, status
    x = 270
    b += text(x, 98, "ASADBEK OTABEKOV", "g", 58)
    b += highlight(x + 2, 146, "SOFTWARE ENGINEER · BACKEND · AI · SECURITY", 19)
    b += text(x, 200, "now → maintainer, RedTeam Subnet (Bittensor SN61)", "m", 19, MUTED)
    c, w1 = chip(x, 228, "HUMBLEBEE AI · 2025–NOW", PAPER, size=16, h=38, pad=14)
    b += c
    c, _ = chip(x + w1 + 18, 228, "OPEN TO REMOTE", INK, PAPER, size=16, h=38, pad=14)
    b += c
    return svg(W, H, b, "Asadbek Otabekov. Software engineer: backend, AI and security. Seoul, South Korea, open to remote. "
                         "Now a maintainer on RedTeam Subnet (Bittensor subnet 61) at HumbleBee AI, 2025 to now.")


# ---------- 2. stat tiles (2 x 2 so the numbers stay readable on phones) ----------
STATS = [
    ("target", "OS FINGERPRINTING", "1.000", "macro-F1 · 200,000 rows", "ML", YELLOW),
    ("bolt", "PORTAL DATA API", "24 → 5 ms", "page 2.3 → 0.76 MB", "PERF", PAPER),
    ("check", "AI SUPPORT AGENT", "838 tests", "RBAC + TOTP · audit log", "AGENTS", PAPER),
    ("camera", "LIVE CAMERA STREAMS", "27–30 fps", "RTSP → LiveKit", "VISION", TEAL),
]


def stats():
    W, H = 1000, 404
    b = ""
    cw, ch, gx, gy = 475, 176, 28, 28
    for i, (ic, label, value, sub, tag, fill) in enumerate(STATS):
        x, y = 8 + (i % 2) * (cw + gx), 8 + (i // 2) * (ch + gy)
        b += box(x, y, cw, ch, fill)
        b += icon(ic, x + 22, y + 22, 44)
        b += text(x + 82, y + 52, label, "mb", 17, spacing=1)
        tw = MB.width(tag, 13, 1) + 20
        b += f'<rect x="{x + cw - 22 - tw}" y="{y + 26}" width="{tw}" height="28" fill="{GREY}"/>'
        b += text(x + cw - 22 - tw / 2, y + 45, tag, "mb", 13, anchor="middle", spacing=1)
        b += text(x + 22, y + 122, value, "mb", 48, spacing=0)
        b += text(x + 22, y + 156, sub, "m", 18, INK if fill != PAPER else MUTED)
    alt = "Selected results: " + "; ".join(f"{l.lower()}: {v} ({s})" for _, l, v, s, _, _ in STATS) + "."
    return svg(W, H, b, alt)


# ---------- 3. contact banner ----------
def contact():
    W, H = 1000, 190
    b = box(8, 8, W - 22, 160, YELLOW)
    b += text(36, 70, "HAVE A HARD BACKEND OR SECURITY PROBLEM?", "g", 30)
    b += text(36, 108, "Engineering work, collaboration and remote roles welcome.", "m", 19)
    c, _ = chip(36, 124, "EMAIL ME  →", INK, PAPER, size=16, h=34, shadow=4, pad=14)
    b += c
    return svg(W, H, b, "Have a hard backend or security problem? Engineering work, collaboration and remote roles welcome. Email me.")


# ---------- section labels: a black tab on a yellow rule, visible on light and dark pages ----------
def divider(label):
    W, H = 1000, 60
    b = f'<rect x="8" y="30" width="{W - 16}" height="8" fill="{YELLOW}" stroke="{INK}" stroke-width="2"/>'
    w = MB.width(label, 17, 2) + 32
    b += f'<rect x="8" y="12" width="{w}" height="42" fill="{INK}" stroke="{YELLOW}" stroke-width="2"/>'
    b += text(24, 40, label, "mb", 17, YELLOW, spacing=2)
    return svg(W, H, b, label.title())


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    files = {
        "header.svg": header(), "stats.svg": stats(), "contact.svg": contact(),
        "label-built.svg": divider("WHAT I'VE BUILT"),
        "label-experience.svg": divider("EXPERIENCE & TOOLBOX"),
        "label-path.svg": divider("THE PATH HERE"),
    }
    for name, data in files.items():
        (OUT / name).write_text(data)
        print(f"{name}: {len(data) // 1024} KB")
