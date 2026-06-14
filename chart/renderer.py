"""Server status image renderer using Pillow — premium dark gaming aesthetic."""

import io
from datetime import datetime
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from core.models import ServerStatus, ServerInfo

# ── Premium Dark Palette ──────────────────────────────────────────────
BG = (10, 10, 15)          # near-black canvas
SURFACE = (18, 18, 28)     # card surface
SURFACE_ALT = (24, 24, 36) # sub-card surface
BORDER = (38, 38, 52)      # subtle border
GREEN = (72, 220, 140)     # online / positive
RED = (240, 90, 90)        # offline / error
BLUE = (90, 170, 250)      # accent / info
WHITE = (255, 255, 255)
TEXT_PRIMARY = (220, 220, 235)
TEXT_SECONDARY = (130, 130, 155)
TEXT_MUTED = (80, 80, 105)
BADGE_ONLINE = (55, 180, 120, 35)  # green tinted
BADGE_OFFLINE = (200, 70, 70, 35)   # red tinted

CARD_W = 500
PAD = 24
GAP = 14


def _font(size: int = 13, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Resolve font with fallbacks."""
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
    """Word-wrap text to pixel width."""
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
    return ", ".join(players[:limit]) + f" … +{len(players) - limit}"


def render_server_status(server: ServerInfo, status: ServerStatus) -> bytes:
    """Render a premium server-status card as PNG bytes.

    Design language — dark gaming / dev-tool inspired:
    • near-black canvas with lifted card surface
    • fine 1 px borders instead of heavy shadows
    • asymmetrical stats grid (left label, right value)
    • mono-style section labels, generous whitespace
    • soft accent badge for online/offline
    """
    motd = status.motd or ""
    m_lines = len(_wrap(motd, _font(12), CARD_W - PAD * 2 - 20))
    ps = _fmt_players(status.players_sample)
    p_lines = len(_wrap(ps, _font(12), CARD_W - PAD * 2 - 20)) if ps else 0

    # Height computation
    HEADER_H = 64
    STATS_H = 72 if status.online else 44
    MOTD_H = m_lines * 20 + 34 if motd and status.online else 0
    PLAYER_H = p_lines * 20 + 34 if ps and status.online else 0

    H = (PAD + HEADER_H + GAP + STATS_H +
         (MOTD_H + GAP if MOTD_H else 0) +
         (PLAYER_H + GAP if PLAYER_H else 0) +
         12 + 32 + PAD)

    img = Image.new("RGB", (CARD_W, H), BG)
    draw = ImageDraw.Draw(img)

    # Fonts
    f_display = _font(18, bold=True)
    f_title = _font(15, bold=True)
    f_body = _font(12)
    f_sm = _font(10)
    f_val = _font(17, bold=True)
    f_label = _font(9)

    y = PAD

    # ── Header ──────────────────────────────────────────────────────
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + HEADER_H), 12, SURFACE)
    draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + HEADER_H), 12, None, BORDER, 1)

    # Icon circle
    ic = GREEN if status.online else RED
    ix, iy = PAD + 14, y + 10
    draw.ellipse((ix, iy, ix + 44, iy + 44), fill=ic)

    # Server name
    draw.text((PAD + 72, y + 8), server.display_name, WHITE, f_display)
    draw.text((PAD + 72, y + 36), server.address, TEXT_SECONDARY, f_body)

    # Status badge
    badge_t = "ONLINE" if status.online else "OFFLINE"
    badge_bg = BADGE_ONLINE if status.online else BADGE_OFFLINE
    bb = draw.textbbox((0, 0), badge_t, f_sm)
    bw, bh = bb[2] - bb[0] + 20, bb[3] - bb[1] + 8
    bx, by_ = CARD_W - PAD - bw - 6, y + 14
    draw.rounded_rectangle((bx, by_, bx + bw, by_ + bh), 10, badge_bg)
    draw.text((bx + 10, by_ + 3), badge_t, GREEN if status.online else RED, f_sm)

    y += HEADER_H + GAP

    # ── Stats Row ───────────────────────────────────────────────────
    if status.online:
        row_w = CARD_W - PAD * 2
        col_w = (row_w - 10) // 2

        items = [
            ("PLAYERS", f"{status.players_online:,} / {status.players_max:,}", GREEN),
            ("LATENCY", f"{status.latency:.0f} ms", BLUE),
        ]
        for i, (label, val, accent) in enumerate(items):
            cx = PAD + i * (col_w + 10)
            draw.rounded_rectangle((cx, y, cx + col_w, y + 36), 8, SURFACE_ALT)
            draw.text((cx + 12, y + 4), label, TEXT_MUTED, f_label)
            draw.text((cx + 12, y + 16), val, accent, f_val)

        y += 40

        items2 = [
            ("VERSION", status.version or "?", TEXT_SECONDARY),
            ("PROTOCOL", str(status.protocol or "?"), TEXT_SECONDARY),
        ]
        for i, (label, val, accent) in enumerate(items2):
            cx = PAD + i * (col_w + 10)
            draw.rounded_rectangle((cx, y, cx + col_w, y + 30), 8, SURFACE_ALT)
            draw.text((cx + 12, y + 3), label, TEXT_MUTED, f_label)
            draw.text((cx + 12, y + 15), val, accent, f_body)
        y += 34
    else:
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + 40), 8, (30, 18, 18))
        draw.text((PAD + 14, y + 11), f"⛔  {status.error or 'Unknown'}", RED, f_body)
        y += 44

    # ── MOTD ─────────────────────────────────────────────────────────
    if status.online and motd:
        box_h = m_lines * 20 + 34
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + box_h), 8, SURFACE)
        draw.text((PAD + 14, y + 10), "MOTD", TEXT_MUTED, f_label)
        ly = y + 27
        for line in _wrap(motd, f_body, CARD_W - PAD * 2 - 28):
            draw.text((PAD + 14, ly), line, TEXT_PRIMARY, f_body)
            ly += 20
        y += box_h + GAP

    # ── Online Players ──────────────────────────────────────────────
    if status.online and ps:
        box_h = p_lines * 20 + 34
        draw.rounded_rectangle((PAD, y, CARD_W - PAD, y + box_h), 8, SURFACE)
        draw.text((PAD + 14, y + 10), "ONLINE PLAYERS", TEXT_MUTED, f_label)
        ly = y + 27
        for line in _wrap(ps, f_body, CARD_W - PAD * 2 - 28):
            draw.text((PAD + 14, ly), line, BLUE, f_body)
            ly += 20
        y += box_h + GAP

    # ── Footer ──────────────────────────────────────────────────────
    y += 2
    draw.line((PAD, y, CARD_W - PAD, y), BORDER, 1)
    y += 10
    draw.text(
        (PAD, y),
        f"MCPulse  ·  {status.queried_at.strftime('%Y-%m-%d %H:%M:%S')}",
        TEXT_MUTED, f_sm,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
