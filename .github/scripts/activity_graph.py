"""Gera um gráfico de linha (SVG) com as contribuições dos últimos 31 dias."""
import json
import os
import sys
import urllib.request
from datetime import date

USER = os.environ["GITHUB_USER"]
TOKEN = os.environ["GITHUB_TOKEN"]
OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "dist"
DAYS = 31

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""

THEMES = {
    "activity-graph.svg": {"bg": "none", "line": "#6E5BD8", "area": "#6E5BD8", "point": "#6E5BD8",
                           "grid": "#d0d7de", "text": "#57606a", "title": "#24292f"},
    "activity-graph-dark.svg": {"bg": "none", "line": "#9D8CFF", "area": "#9D8CFF", "point": "#9D8CFF",
                                "grid": "#30363d", "text": "#8b949e", "title": "#e6edf3"},
}


def fetch_days():
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return days[-DAYS:]


def render(days, c):
    w, h = 840, 300
    left, right, top, bottom = 50, 20, 50, 45
    pw, ph = w - left - right, h - top - bottom
    counts = [d["contributionCount"] for d in days]
    peak = max(max(counts), 4)
    step = -(-peak // 4)
    ymax = step * 4

    def x(i):
        return left + pw * i / (len(days) - 1)

    def y(v):
        return top + ph - ph * v / ymax

    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(counts))
    area = f"{x(0):.1f},{y(0):.1f} {pts} {x(len(days) - 1):.1f},{y(0):.1f}"
    total = sum(counts)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
           f'font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           '<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0" stop-color="{c["area"]}" stop-opacity="0.35"/>'
           f'<stop offset="1" stop-color="{c["area"]}" stop-opacity="0"/></linearGradient></defs>',
           f'<text x="{w / 2}" y="28" text-anchor="middle" font-size="17" font-weight="600" fill="{c["title"]}">'
           f'Contribuições nos últimos {DAYS} dias · {total}</text>']
    for k in range(5):
        v = step * k
        out.append(f'<line x1="{left}" y1="{y(v):.1f}" x2="{w - right}" y2="{y(v):.1f}" '
                   f'stroke="{c["grid"]}" stroke-dasharray="3 4"/>')
        out.append(f'<text x="{left - 10}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="11" '
                   f'fill="{c["text"]}">{v}</text>')
    for i, d in enumerate(days):
        if i % 3 == 0 or i == len(days) - 1:
            dd = date.fromisoformat(d["date"])
            out.append(f'<text x="{x(i):.1f}" y="{h - bottom + 20}" text-anchor="middle" font-size="11" '
                       f'fill="{c["text"]}">{dd:%d/%m}</text>')
    out.append(f'<polygon points="{area}" fill="url(#g)"/>')
    out.append(f'<polyline points="{pts}" fill="none" stroke="{c["line"]}" stroke-width="2.5" '
               f'stroke-linejoin="round" stroke-linecap="round"/>')
    for i, v in enumerate(counts):
        out.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3" fill="{c["point"]}">'
                   f'<title>{days[i]["date"]}: {v}</title></circle>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    days = fetch_days()
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, colors in THEMES.items():
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
            f.write(render(days, colors))


if __name__ == "__main__":
    main()
