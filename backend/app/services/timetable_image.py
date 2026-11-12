import datetime
import io
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image, ImageDraw, ImageFont

MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]

# Couleurs des types de cours (mêmes teintes que l'application)
TYPE_COLORS = {
    "CM": (109, 91, 208),
    "TD": (47, 111, 214),
    "TP": (15, 138, 166),
    "DS": (209, 56, 91),
    "EXAMEN": (209, 56, 91),
    "SAE": (31, 157, 107),
}
OTHER_COLOR = (91, 102, 120)

BG = (255, 255, 255)
GRID = (230, 233, 240)
TEXT = (18, 20, 28)
MUTED = (110, 116, 134)


FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """DejaVu Sans embarquee (accents garantis, aucune dependance au systeme)."""
    try:
        return ImageFont.truetype(str(FONT_DIR / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")), size)
    except OSError:
        return ImageFont.load_default(size=size)


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _fit(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1]
    return text.rstrip() + "…"


def _week_label(monday: datetime.date) -> str:
    friday = monday + datetime.timedelta(days=4)
    if monday.month == friday.month:
        return f"Semaine du {monday.day} au {friday.day} {MONTHS[friday.month - 1]}"
    return f"Semaine du {monday.day} {MONTHS[monday.month - 1]} au {friday.day} {MONTHS[friday.month - 1]}"


def render_week_png(events: List[Dict[str, Any]], monday: datetime.date) -> bytes:
    """Dessine l'emploi du temps de la semaine commençant à `monday` et renvoie un PNG."""
    days = [monday + datetime.timedelta(days=i) for i in range(6)]
    week = [e for e in events if days[0].isoformat() <= e["date"] <= days[5].isoformat()]
    n_days = 6 if any(e["date"] == days[5].isoformat() for e in week) else 5
    days = days[:n_days]

    start_min = min([_minutes(e["start_time"]) for e in week] + [8 * 60])
    end_min = max([_minutes(e["end_time"]) for e in week] + [17 * 60])
    start_h, end_h = start_min // 60, -(-end_min // 60)
    hour_px = 78

    margin, axis_w, header_h, title_h = 36, 64, 54, 84
    col_w = 290
    width = margin * 2 + axis_w + col_w * n_days
    grid_h = (end_h - start_h) * hour_px
    height = title_h + header_h + grid_h + margin

    img = Image.new("RGBA", (width, height), BG + (255,))
    draw = ImageDraw.Draw(img)
    f_title, f_head, f_axis = _font(30, True), _font(19, True), _font(15)
    f_event, f_small = _font(16, True), _font(14)

    draw.text((margin, 28), _week_label(days[0]), font=f_title, fill=TEXT)
    gx = margin + axis_w
    gy = title_h + header_h

    for i, day in enumerate(days):
        x = gx + i * col_w
        draw.text((x + 12, title_h + 8), f"{DAYS[i]} {day.day}", font=f_head, fill=TEXT)

    for h in range(start_h, end_h + 1):
        y = gy + (h - start_h) * hour_px
        draw.line([(gx, y), (gx + col_w * n_days, y)], fill=GRID, width=1)
        if h < end_h:
            draw.text((margin, y - 8), f"{h:02d}:00", font=f_axis, fill=MUTED)
    for i in range(n_days + 1):
        x = gx + i * col_w
        draw.line([(x, title_h + header_h - 6), (x, gy + grid_h)], fill=GRID, width=1)

    for ev in week:
        i = days.index(datetime.date.fromisoformat(ev["date"])) if datetime.date.fromisoformat(ev["date"]) in days else None
        if i is None:
            continue
        s, e = _minutes(ev["start_time"]), max(_minutes(ev["end_time"]), _minutes(ev["start_time"]) + 30)
        x0 = gx + i * col_w + 6
        x1 = gx + (i + 1) * col_w - 6
        y0 = gy + (s - start_h * 60) / 60 * hour_px + 2
        y1 = gy + (e - start_h * 60) / 60 * hour_px - 2
        color = TYPE_COLORS.get(str(ev.get("type", "")).upper(), OTHER_COLOR)

        # Fond translucide (15 %) + liseré plein à gauche, comme dans l'application
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=color + (40,))
        od.rounded_rectangle([x0, y0, x0 + 6, y1], radius=3, fill=color + (255,))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        tx, tw = x0 + 16, x1 - x0 - 24
        ty = y0 + 8
        draw.text((tx, ty), _fit(draw, ev["title"], f_event, tw), font=f_event, fill=TEXT)
        lines = [f"{ev['start_time']} – {ev['end_time']}", ev.get("location") or "", ev.get("teacher") or ""]
        ty += 24
        for line in lines:
            if not line or ty + 16 > y1 - 4:
                continue
            draw.text((tx, ty), _fit(draw, line, f_small, tw), font=f_small, fill=MUTED)
            ty += 20

    if not week:
        draw.text((gx + 20, gy + 30), "Aucun cours cette semaine", font=f_head, fill=MUTED)

    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()
