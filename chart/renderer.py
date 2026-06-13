"""Server status image renderer using Pillow (local rendering)."""

import io
from datetime import datetime
from typing import List

from PIL import Image, ImageDraw, ImageFont

from core.models import ServerStatus, ServerInfo

# Color palette
BG_COLOR = (30, 30, 46)
CARD_COLOR = (40, 42, 60)
ACCENT_GREEN = (72, 199, 142)
ACCENT_RED = (237, 85, 85)
ACCENT_BLUE = (89, 166, 246)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (148, 150, 170)
TEXT_DIM = (100, 102, 120)
BORDER_COLOR = (50, 52, 72)
CARD_WIDTH = 480
CARD_PADDING = 20
SECTION_GAP = 12


def _get_font(size: int = 13, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try system fonts, fall back to default."""
    names = ["msyhbd.ttc" if bold else "msyh.ttc",
             "seguisb.ttf" if bold else "segoeui.ttf",
             "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    """Wrap text to fit max_w pixels."""
    if not text:
        return [""]
    lines = []
    for para in text.split("\n"):
        words = para.split()
        cur = ""
        for w in words:
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
    return lines


def _fmt_players(players: List[str], limit: int = 8) -> str:
    if not players:
        return ""
    if len(players) <= limit:
        return ", ".join(players)
    return ", ".join(players[:limit]) + f" ... (+{len(players) - limit})"


def render_server_status(server: ServerInfo, status: ServerStatus) -> bytes:
    """Render server status as a PNG image bytes."""
    motd = status.motd if status.motd else ""
    m_lines = len(_wrap(motd, _get_font(12), CARD_WIDTH - CARD_PADDING * 2 - 20))
    ps = _fmt_players(status.players_sample)
    p_lines = len(_wrap(ps, _get_font(12), CARD_WIDTH - CARD_PADDING * 2 - 20)) if ps else 0

    hh = 60
    gh = 90 if status.online else 40
    mh = m_lines * 18 + 30 if motd and status.online else 0
    ph = p_lines * 18 + 30 if ps and status.online else 0

    ch = CARD_PADDING + hh + SECTION_GAP + gh + 12 + 30 + CARD_PADDING
    if mh:
        ch += mh + SECTION_GAP
    if ph:
        ch += ph + SECTION_GAP

    img = Image.new("RGB", (CARD_WIDTH, ch), BG_COLOR)
    draw = ImageDraw.Draw(img)

    ft_title = _get_font(16, bold=True)
    ft_sub = _get_font(11)
    ft_body = _get_font(12)
    ft_sm = _get_font(10)
    ft_big = _get_font(18, bold=True)
    ft_val = _get_font(16, bold=True)

    y = CARD_PADDING
    r = 10
    draw.rounded_rectangle((CARD_PADDING, y, CARD_WIDTH - CARD_PADDING, y + hh), r, CARD_COLOR)

    # Icon
    ic = ACCENT_GREEN if status.online else ACCENT_RED
    draw.ellipse((CARD_PADDING + 12, y + 10, CARD_PADDING + 50, y + 50), fill=ic)
    draw.text((CARD_PADDING + 21, y + 17), server.display_name[0].upper(), TEXT_WHITE, ft_big)

    draw.text((CARD_PADDING + 62, y + 10), server.display_name, TEXT_WHITE, ft_title)
    draw.text((CARD_PADDING + 62, y + 34), server.address, TEXT_GRAY, ft_sub)

    # Badge
    bt = "● ONLINE" if status.online else "● OFFLINE"
    bc = ACCENT_GREEN if status.online else ACCENT_RED
    bb = draw.textbbox((0, 0), bt, ft_sub)
    bw = bb[2] - bb[0] + 16
    bh = bb[3] - bb[1] + 6
    bx = CARD_WIDTH - CARD_PADDING - bw - 10
    by2 = y + 12
    draw.rounded_rectangle((bx, by2, bx + bw, by2 + bh), 12, (*bc, 40))
    draw.text((bx + 8, by2 + 2), bt, bc, ft_sub)

    y += hh + SECTION_GAP
    gw = (CARD_WIDTH - CARD_PADDING * 2 - 8) // 2

    if status.online:
        cards = [
            (CARD_PADDING, y, "PLAYERS", f"{status.players_online:,} / {status.players_max:,}", ACCENT_GREEN),
            (CARD_PADDING + gw + 8, y, "LATENCY", f"{status.latency:.0f}ms", ACCENT_BLUE),
        ]
        for cx, cy2, cl, cv, cc in cards:
            draw.rounded_rectangle((cx, cy2, cx + gw, cy2 + 36), 8, (50, 52, 72))
            draw.text((cx + 10, cy2 + 6), cl, TEXT_GRAY, ft_sm)
            draw.text((cx + 10, cy2 + 18), cv, cc, ft_val)
        y += 42

        cards = [
            (CARD_PADDING, y, "VERSION", status.version or "?", TEXT_WHITE),
            (CARD_PADDING + gw + 8, y, "PROTOCOL", str(status.protocol or "?"), TEXT_GRAY),
        ]
        for cx, cy2, cl, cv, cc in cards:
            draw.rounded_rectangle((cx, cy2, cx + gw, cy2 + 36), 8, (50, 52, 72))
            draw.text((cx + 10, cy2 + 6), cl, TEXT_GRAY, ft_sm)
            draw.text((cx + 10, cy2 + 18), cv, cc, ft_val)
        y += 48
    else:
        rw = CARD_WIDTH - CARD_PADDING * 2
        draw.rounded_rectangle((CARD_PADDING, y, CARD_PADDING + rw, y + 36), 8, (60, 40, 40))
        draw.text((CARD_PADDING + 12, y + 8), f"Error: {status.error or 'Unknown'}", ACCENT_RED, ft_body)
        y += 48

    # MOTD
    if status.online and motd:
        rw = CARD_WIDTH - CARD_PADDING * 2
        draw.rounded_rectangle((CARD_PADDING, y, CARD_PADDING + rw, y + m_lines * 18 + 30), 8, CARD_COLOR)
        draw.text((CARD_PADDING + 12, y + 8), "MOTD", TEXT_GRAY, ft_sm)
        ly = y + 24
        for line in _wrap(motd, ft_body, CARD_WIDTH - CARD_PADDING * 2 - 24):
            draw.text((CARD_PADDING + 12, ly), line, TEXT_WHITE, ft_body)
            ly += 18
        y += m_lines * 18 + 36

    # Players
    if status.online and ps:
        rw = CARD_WIDTH - CARD_PADDING * 2
        draw.rounded_rectangle((CARD_PADDING, y, CARD_PADDING + rw, y + p_lines * 18 + 30), 8, CARD_COLOR)
        draw.text((CARD_PADDING + 12, y + 8), "ONLINE PLAYERS", TEXT_GRAY, ft_sm)
        ly = y + 24
        for line in _wrap(ps, ft_body, CARD_WIDTH - CARD_PADDING * 2 - 24):
            draw.text((CARD_PADDING + 12, ly), line, ACCENT_BLUE, ft_body)
            ly += 18
        y += p_lines * 18 + 36

    y += 4
    draw.line((CARD_PADDING, y, CARD_WIDTH - CARD_PADDING, y), BORDER_COLOR, 1)
    y += 8
    draw.text((CARD_PADDING, y),
              f"MCPulse  .  {status.queried_at.strftime('%Y-%m-%d %H:%M:%S')}",
              TEXT_DIM, ft_sm)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
