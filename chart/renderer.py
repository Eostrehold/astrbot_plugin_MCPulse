"""Image renderers for MCPulse - Notion-inspired clean aesthetic."""

import io
from datetime import datetime
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from core.models import ServerStatus, ServerInfo

# Design Tokens
CANVAS = (255, 255, 255)
SURFACE = (246, 245, 244)
HAIRLINE = (229, 227, 223)
INK = (26, 26, 26)
CHARCOAL = (55, 55, 47)
SLATE = (93, 91, 84)
STEEL = (120, 118, 113)
MUTED = (187, 184, 177)
PRIMARY = (86, 69, 212)
GREEN = (26, 174, 57)
RED = (224, 49, 49)
BLUE = (0, 117, 222)
WHITE = (255, 255, 255)
TINT_PEACH = (255, 232, 212)
TINT_MINT = (217, 243, 225)
TINT_LAVENDER = (230, 224, 245)
TINT_SKY = (220, 236, 250)
TINT_ROSE = (253, 224, 236)
TINT_YELLOW = (254, 247, 214)

CARD_W = 520
PAD = 24
GAP = 14


def _font(size: int = 13, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "msyhbd.ttc" if bold else "msyh.ttc",
        "seguisb.ttf" if bold else "segoeui.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    if not text:
        return [""]
    lines: List[str] = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            test = (cur + " " + w).strip()
            bb = font.getbbox(test)
            if bb[2] - bb[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines or [""]


def _fmt_players(players: List[str], limit: int = 8) -> str:
    if not players:
        return ""
    if len(players) <= limit:
        return ", ".join(players)
    return ", ".join(players[:limit]) + f" ... +{len(players) - limit}"


def _save_img(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()


def _draw_badge(draw, x, y, text, bg, fg):
    f = _font(11, bold=True)
    bb = draw.textbbox((0, 0), text, f)
    bw = bb[2] - bb[0] + 18
    bh = bb[3] - bb[1] + 10
    draw.rounded_rectangle((x, y, x + bw, y + bh), 12, bg)
    draw.text((x + 9, y + 4), text, fg, f)
    return x + bw


def _draw_metric_row(draw, x, y, w, items):
    col_w = (w - 10) // 2
    for i, (label, val, accent) in enumerate(items):
        cx = x + i * (col_w + 10)
        draw.rounded_rectangle((cx, y, cx + col_w, y + 34), 8, SURFACE)
        draw.rounded_rectangle((cx, y, cx + col_w, y + 34), 8, None, HAIRLINE, 1)
        draw.text((cx + 12, y + 3), label.upper(), MUTED, _font(9, bold=True))
        draw.text((cx + 12, y + 16), val, accent, _font(15, bold=True))


# 1. Server Status Card
def render_server_status(server: ServerInfo, status: ServerStatus) -> bytes:
    motd = status.motd or ""
    m_lines = len(_wrap(motd, _font(12), CARD_W - PAD * 2 - 20))
    ps = _fmt_players(status.players_sample)
    p_lines = len(_wrap(ps, _font(12), CARD_W - PAD * 2 - 20)) if ps else 0

    H = (PAD + 68 + GAP + 82 +
         (m_lines * 20 + 38 + GAP if motd and status.online else 0) +
         (p_lines * 20 + 38 + GAP if ps and status.online else 0) +
         12 + 34 + PAD)

    img = Image.new("RGB", (CARD_W, int(H)), CANVAS)
    draw = ImageDraw.Draw(img)

    y = PAD

    # Header
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 68), 10, SURFACE)
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 68), 10, None, HAIRLINE, 1)

    ic = GREEN if status.online else RED
    draw.ellipse((PAD + 14, y + 12, PAD + 56, y + 54), fill=ic)
    draw.text((PAD + 24, y + 20), server.display_name[0].upper(), WHITE, _font(20, bold=True))
    draw.text((PAD + 70, y + 12), server.display_name, INK, _font(18, bold=True))
    draw.text((PAD + 70, y + 40), server.address, STEEL, _font(12))

    badge = ("ONLINE", TINT_MINT, GREEN) if status.online else ("OFFLINE", TINT_ROSE, RED)
    _draw_badge(draw, CARD_W - PAD - 90, y + 18, badge[0], badge[1], badge[2])
    y += 68 + GAP

    # Stats
    if status.online:
        _draw_metric_row(draw, PAD, y, CARD_W - PAD * 2, [
            ("PLAYERS", f"{status.players_online:,} / {status.players_max:,}", PRIMARY),
            ("LATENCY", f"{status.latency:.0f} ms", BLUE),
        ])
        y += 38
        _draw_metric_row(draw, PAD, y, CARD_W - PAD * 2, [
            ("VERSION", status.version or "-", CHARCOAL),
            ("PROTOCOL", str(status.protocol or "-"), SLATE),
        ])
        y += 42
    else:
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 42), 8, TINT_ROSE)
        draw.text((PAD + 14, y + 12), f"! {status.error or 'Unknown'}", RED, _font(12))
        y += 48

    # MOTD
    if status.online and motd:
        box_h = m_lines * 20 + 38
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + box_h), 8, SURFACE)
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + box_h), 8, None, HAIRLINE, 1)
        draw.text((PAD + 14, y + 12), "MOTD".upper(), MUTED, _font(10, bold=True))
        ly = y + 30
        for line in _wrap(motd, _font(12), CARD_W - PAD * 2 - 28):
            draw.text((PAD + 14, ly), line, CHARCOAL, _font(12))
            ly += 20
        y += box_h + GAP

    # Players
    if status.online and ps:
        box_h = p_lines * 20 + 38
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + box_h), 8, TINT_LAVENDER)
        draw.text((PAD + 14, y + 12), "ONLINE PLAYERS".upper(), MUTED, _font(10, bold=True))
        ly = y + 30
        for line in _wrap(ps, _font(12), CARD_W - PAD * 2 - 28):
            draw.text((PAD + 14, ly), line, PRIMARY, _font(12))
            ly += 20
        y += box_h + GAP

    y += 2
    draw.line((PAD, y, CARD_W - PAD, y), HAIRLINE, 1)
    y += 10
    draw.text((PAD, y), f"MCPulse - {status.queried_at.strftime('%Y-%m-%d %H:%M:%S')}", MUTED, _font(10))
    return _save_img(img)


# 2. Server Stats Card
def render_server_stats(server: ServerInfo, records: List[dict], days: int) -> bytes:
    latencies = [r["latency"] for r in records if r.get("latency") is not None]
    online_r = [r for r in records if r.get("online")]
    players = [r["players_online"] for r in records if r.get("players_online") is not None]

    online_rate = (len(online_r) / len(records)) * 100 if records else 0
    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    min_lat = min(latencies) if latencies else 0
    max_lat = max(latencies) if latencies else 0
    max_pl = max(players) if players else 0
    avg_pl = sum(players) / len(players) if players else 0

    rows = 3
    row_h = 40 + GAP
    body_h = 18 + rows * row_h + 8
    H = PAD + 68 + GAP + body_h + 12 + 34 + PAD
    img = Image.new("RGB", (CARD_W, int(H)), CANVAS)
    draw = ImageDraw.Draw(img)

    y = PAD
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 68), 10, SURFACE)
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 68), 10, None, HAIRLINE, 1)
    draw.ellipse((PAD + 14, y + 12, PAD + 56, y + 54), fill=PRIMARY)
    draw.text((PAD + 24, y + 20), server.display_name[0].upper(), WHITE, _font(20, bold=True))
    draw.text((PAD + 70, y + 12), f"{server.display_name} - Statistics", INK, _font(16, bold=True))
    draw.text((PAD + 70, y + 40), f"Last {days} day(s)", STEEL, _font(12))
    y += 68 + GAP + 4

    def _stat_row(label, left_val, left_accent, right_val):
        nonlocal y
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 40), 8, SURFACE)
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 40), 8, None, HAIRLINE, 1)
        draw.text((PAD + 14, y + 4), label.upper(), MUTED, _font(9, bold=True))
        draw.text((PAD + 14, y + 20), left_val, left_accent, _font(14, bold=True))
        draw.text((PAD + 180, y + 22), right_val, SLATE, _font(11))
        y += 40 + GAP

    _stat_row("LATENCY", f"~{avg_lat:.0f} ms avg", CHARCOAL, f"min {min_lat:.0f}  max {max_lat:.0f}")
    _stat_row("PLAYERS", f"~{avg_pl:.0f} avg", INK, f"peak {max_pl}")
    rate_tint = TINT_MINT if online_rate >= 90 else (TINT_YELLOW if online_rate >= 70 else TINT_ROSE)
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 40), 8, rate_tint)
    draw.text((PAD + 14, y + 4), "ONLINE RATE".upper(), MUTED, _font(9, bold=True))
    draw.text((PAD + 14, y + 18), f"{online_rate:.1f}%", CHARCOAL, _font(20, bold=True))
    draw.text((PAD + 180, y + 22), f"{len(online_r)} online / {len(records)} checks", SLATE, _font(11))
    y += 40 + GAP + 2

    draw.line((PAD, y, CARD_W - PAD, y), HAIRLINE, 1)
    y += 10
    draw.text((PAD, y), f"MCPulse - {datetime.now().strftime('%Y-%m-%d %H:%M')}", MUTED, _font(10))
    return _save_img(img)


# 3. Server List Card
def render_server_list(servers: List[ServerInfo], latest_records: dict,
                       default_server: Optional[ServerInfo] = None) -> bytes:
    row_count = max(len(servers), 1)
    row_h = 44
    header_h = 60
    body_h = row_count * (row_h + 2)
    H = PAD + header_h + GAP + body_h + 12 + 34 + PAD + 8
    img = Image.new("RGB", (CARD_W, int(H)), CANVAS)
    draw = ImageDraw.Draw(img)

    y = PAD
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + header_h), 10, SURFACE)
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + header_h), 10, None, HAIRLINE, 1)
    draw.ellipse((PAD + 14, y + 8, PAD + 52, y + 46), fill=PRIMARY)
    draw.text((PAD + 26, y + 16), "S", WHITE, _font(18, bold=True))
    draw.text((PAD + 66, y + 12), "Monitored Servers", INK, _font(16, bold=True))

    online_count = sum(1 for r in latest_records.values() if r.get("online"))
    draw.text((CARD_W - PAD - 130, y + 14), f"{online_count} online - {len(servers)} total", SLATE, _font(11))
    y += header_h + GAP

    if not servers:
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 40), 8, TINT_YELLOW)
        draw.text((PAD + 14, y + 11), "No servers yet. Use /mcadd to add one.", SLATE, _font(12))
        y += 46
    else:
        for server in servers:
            rec = latest_records.get(server.id, {})
            is_online = rec.get("online", False)
            is_default = default_server and server.id == default_server.id
            sbg = TINT_MINT if is_online else TINT_ROSE
            sfg = GREEN if is_online else RED
            st = "ONLINE" if is_online else "OFFLINE"

            draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + row_h), 6, CANVAS)
            draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + row_h), 6, None, HAIRLINE, 1)
            draw.ellipse((PAD + 14, y + 14, PAD + 28, y + 28), fill=sfg)
            _draw_badge(draw, CARD_W - PAD - 78, y + 9, st, sbg, sfg)

            name = server.display_name
            if is_default:
                name += " *"
            draw.text((PAD + 36, y + 6), name, INK, _font(13, bold=True))
            draw.text((PAD + 36, y + 25), server.address, MUTED, _font(10))
            if is_online:
                extra = f"{rec.get('players_online', '?')}/{rec.get('players_max', '?')} pl | {rec.get('latency', 0):.0f} ms"
                draw.text((PAD + 140, y + 25), extra, SLATE, _font(10))
            y += row_h + 2

    y += 2
    draw.line((PAD, y, CARD_W - PAD, y), HAIRLINE, 1)
    y += 10
    draw.text((PAD, y), f"MCPulse - {datetime.now().strftime('%Y-%m-%d %H:%M')}", MUTED, _font(10))
    return _save_img(img)
