"""Render assets/banner-sdlc-lite.png with headless Chrome.

Usage: python3 assets/banner-sdlc-lite.py   (CHROME=<path> to override the browser)
"""
import math
import os
import pathlib
import random
import subprocess
import tempfile

W, H = 1536, 1024
NODE_Y = 470
OUTER_R, INNER_R = 92, 80
NODES = [  # x, label, sublabel, color, icon
    (256, "prepare-plan", "spec.md · plan.md", "#3f7dff", "doc"),
    (596, "implement-plan", ".worktrees/<plan>", "#5f6bff", "gears"),
    (940, "review-build", "fresh context · ship@SHA", "#8a5cff", "lens"),
    (1280, "retro-build", "amend · prune", "#b066ff", "cycle"),
]
STATE_X, STATE_Y, STATE_R = 768, 168, 62


def hexagon(cx, cy, r):
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(0, 360, 60)]
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def icon(kind, cx, cy, color):
    s = f'stroke="{color}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "doc":
        return (f'<path d="M{cx-26},{cy-34} h34 l18,18 v50 h-52 z M{cx+8},{cy-34} v18 h18" {s}/>'
                f'<path d="M{cx-14},{cy-4} h28 M{cx-14},{cy+10} h28 M{cx-14},{cy+24} h18" {s}/>')
    if kind == "gears":
        def gear(gx, gy, r):
            teeth = 2 * math.pi * (r + 5) / 16
            return (f'<circle cx="{gx}" cy="{gy}" r="{r+5}" stroke="{color}" stroke-width="9" fill="none" '
                    f'stroke-dasharray="{teeth/2:.2f} {teeth/2:.2f}"/>'
                    f'<circle cx="{gx}" cy="{gy}" r="{r}" {s}/><circle cx="{gx}" cy="{gy}" r="{r/2.6:.1f}" {s}/>')
        return gear(cx - 12, cy + 12, 17) + gear(cx + 19, cy - 17, 12)
    if kind == "lens":
        return (f'<circle cx="{cx-8}" cy="{cy-8}" r="24" {s}/>'
                f'<path d="M{cx+10},{cy+10} L{cx+32},{cy+32}" stroke="{color}" stroke-width="7" stroke-linecap="round"/>')
    if kind == "cycle":
        return (f'<path d="M{cx-28},{cy-6} A30,30 0 0 1 {cx+22},{cy-20}" {s}/>'
                f'<path d="M{cx+12},{cy-28} L{cx+24},{cy-19} L{cx+12},{cy-8}" {s}/>'
                f'<path d="M{cx+28},{cy+6} A30,30 0 0 1 {cx-22},{cy+20}" {s}/>'
                f'<path d="M{cx-12},{cy+28} L{cx-24},{cy+19} L{cx-12},{cy+8}" {s}/>')
    if kind == "folder":
        return (f'<path d="M{cx-26},{cy-18} h18 l6,7 h28 v32 h-52 z" {s}/>'
                f'<path d="M{cx-10},{cy+2} h20 M{cx-10},{cy+10} h14" {s} stroke-width="3"/>')


def node(cx, cy, r_out, r_in, color, kind):
    return (f'<polygon points="{hexagon(cx, cy, r_out)}" fill="none" stroke="{color}" stroke-opacity="0.35" stroke-width="1.5"/>'
            f'<g filter="url(#glow)"><polygon points="{hexagon(cx, cy, r_in)}" fill="url(#hexfill)" stroke="{color}" stroke-width="3"/>'
            f'{icon(kind, cx, cy, color)}'
            f'<circle cx="{cx-r_out}" cy="{cy}" r="4" fill="{color}"/><circle cx="{cx+r_out}" cy="{cy}" r="4" fill="{color}"/></g>')


def arrow(x1, y1, x2, y2, color, dashed=False):
    dash = ' stroke-dasharray="10 9"' if dashed else ""
    return (f'<g filter="url(#glow)"><path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="3"{dash}/>'
            f'<path d="M{x2-12},{y2-9} L{x2},{y2} L{x2-12},{y2+9}" stroke="{color}" stroke-width="3" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round" transform="rotate({math.degrees(math.atan2(y2-y1, x2-x1)):.1f} {x2} {y2})"/></g>')


def label(x, y, text, size=27, color="#dfe4ff", mono=False, anchor="middle"):
    family = "Menlo, monospace" if mono else "'Helvetica Neue', Helvetica, Arial, sans-serif"
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{family}" font-size="{size}" fill="{color}">{text}</text>'


random.seed(7)
parts = []
grid = "".join(f'<path d="M{x},0 V{H}" />' for x in range(0, W, 32)) + "".join(f'<path d="M0,{y} H{W}" />' for y in range(0, H, 32))
parts.append(f'<g stroke="#3a4a9a" stroke-opacity="0.10" stroke-width="1">{grid}</g>')
parts.append("".join(f'<circle cx="{random.uniform(0, W):.0f}" cy="{random.uniform(0, H):.0f}" r="{random.choice([0.8, 1, 1.4])}" '
                     f'fill="#7d8cff" fill-opacity="{random.uniform(0.25, 0.8):.2f}"/>' for _ in range(160)))

# state folder feeds every skill
parts.append(node(STATE_X, STATE_Y, STATE_R + 10, STATE_R, "#4fb4ff", "folder"))
parts.append(label(STATE_X + 96, STATE_Y - 2, "docs/plans/&lt;plan&gt;/", 22, "#7fc8ff", mono=True, anchor="start"))
parts.append(label(STATE_X + 96, STATE_Y + 28, "state on disk", 20, "#8a93c4", anchor="start"))
for x, *_ in NODES:
    parts.append(f'<path d="M{STATE_X},{STATE_Y + STATE_R + 8} L{x},{NODE_Y - INNER_R - 4}" stroke="#4fb4ff" stroke-opacity="0.45" '
                 f'stroke-width="2" stroke-dasharray="4 8" stroke-linecap="round"/>')

# main chain
(x0, *_), (x1, *_), (x2, *_), (x3, *_) = NODES
parts.append(arrow(x0 + OUTER_R + 6, NODE_Y, x1 - OUTER_R - 8, NODE_Y, "#4f78ff"))
parts.append(arrow(x1 + OUTER_R + 6, NODE_Y - 14, x2 - OUTER_R - 8, NODE_Y - 14, "#7563ff"))
parts.append(arrow(x2 - OUTER_R - 6, NODE_Y + 14, x1 + OUTER_R + 8, NODE_Y + 14, "#7563ff"))
parts.append(label((x1 + x2) / 2, NODE_Y - 32, "until ship", 18, "#a99cff", mono=True))
parts.append(arrow(x2 + OUTER_R + 6, NODE_Y, x3 - OUTER_R - 8, NODE_Y, "#a061ff", dashed=True))
parts.append(label((x2 + x3) / 2, NODE_Y - 18, "merge", 18, "#c9a6ff", mono=True))

# retro feeds amendments back into the skills
loop_y = 800
parts.append(f'<g filter="url(#glow)" stroke="#5b8bff" stroke-width="3" fill="none" stroke-linecap="round">'
             f'<path d="M{x3},{NODE_Y + 175} V{loop_y - 20} Q{x3},{loop_y} {x3 - 20},{loop_y} H{x0 + 20} Q{x0},{loop_y} {x0},{loop_y - 20} V{NODE_Y + 180}"/>'
             f'<path d="M{x0 - 12},{NODE_Y + 192} L{x0},{NODE_Y + 178} L{x0 + 12},{NODE_Y + 192}"/></g>')
for x in (x1, x2):
    parts.append(arrow(x, loop_y, x, NODE_Y + 180, "#5b8bff"))
parts.append(f'<circle cx="{x3}" cy="{NODE_Y + 175}" r="5" fill="#b066ff" filter="url(#glow)"/>')
parts.append(label(W / 2, loop_y + 46, "fewer rules as models improve", 19, "#8a93c4", mono=True))

for x, name, sub, color, kind in NODES:
    parts.append(node(x, NODE_Y, OUTER_R, INNER_R, color, kind))
    parts.append(label(x, NODE_Y + 136, name))
    parts.append(label(x, NODE_Y + 166, sub.replace("<", "&lt;").replace(">", "&gt;"), 17, "#7f97ff", mono=True))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <radialGradient id="bg" cx="50%" cy="45%" r="75%"><stop offset="0" stop-color="#0b0d22"/><stop offset="1" stop-color="#020208"/></radialGradient>
  <radialGradient id="hexfill" cx="50%" cy="40%" r="70%"><stop offset="0" stop-color="#141a46"/><stop offset="1" stop-color="#05061a"/></radialGradient>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="b1"/>
    <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="b2"/>
    <feMerge><feMergeNode in="b1"/><feMergeNode in="b2"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{"".join(parts)}
</svg>'''

chrome = os.environ.get("CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
out = pathlib.Path(__file__).with_suffix(".png")
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
    f.write(f'<!doctype html><html><body style="margin:0;background:#000">{svg}</body></html>')
subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                f"--window-size={W},{H}", f"--screenshot={out}", f"file://{f.name}"],
               check=True, stderr=subprocess.DEVNULL)
os.unlink(f.name)
print(out)
