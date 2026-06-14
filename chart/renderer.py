"""HTML template renderers for MCPulse — delegates to AstrBot's html_render."""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

from core.models import ServerInfo, ServerStatus
from utils.motd_parser import strip_motd_colors


class ImageRenderer:
    """Renders server info as images via AstrBot's html_render (Playwright)."""

    def __init__(self, html_render_fn: Callable[..., Coroutine[Any, Any, str]],
                 template_dir: Path):
        self._render = html_render_fn
        self._templates: Dict[str, str] = {}
        if template_dir.exists():
            for f in template_dir.iterdir():
                if f.suffix == ".html":
                    self._templates[f.stem] = f.read_text(encoding="utf-8")

    def _fmt_players(self, players: List[str], limit: int = 8) -> str:
        if not players:
            return ""
        if len(players) <= limit:
            return ", ".join(players)
        return ", ".join(players[:limit]) + f" \u2026 +{len(players) - limit}"

    def _fmt_motd(self, motd: Any) -> str:
        if not motd:
            return ""
        return strip_motd_colors(motd) if isinstance(motd, str) else str(motd)

    async def _call(self, name: str, ctx: dict) -> str:
        tmpl = self._templates.get(name)
        if not tmpl:
            raise FileNotFoundError(f"Template '{name}' not found.")
        return await self._render(tmpl, ctx)

    # --- Status Card ---

    async def render_status(self, server: ServerInfo,
                            status: ServerStatus) -> str:
        online = status.online
        ctx = {
            "status_class": "online" if online else "offline",
            "initial": server.display_name[0].upper(),
            "server_name": server.display_name,
            "server_address": server.address,
            "status_text": "在线" if online else "离线",
            "online": online,
            "players_online": f"{status.players_online:,}",
            "players_max": f"{status.players_max:,}",
            "latency": f"{status.latency:.0f}",
            "version": status.version or "\u2014",
            "protocol": str(status.protocol or "\u2014"),
            "error": status.error or "Unknown",
            "motd": self._fmt_motd(status.motd),
            "players": self._fmt_players(status.players_sample),
            "queried_at": status.queried_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return await self._call("status_card", ctx)

    # --- Stats Card ---

    async def render_stats(self, server: ServerInfo,
                           records: List[dict], days: int) -> str:
        latencies = [r["latency"] for r in records if r.get("latency") is not None]
        online = [r for r in records if r.get("online")]
        players = [r["players_online"] for r in records if r.get("players_online") is not None]
        total = len(records)
        rate = (len(online) / total * 100) if total else 0.0

        ctx = {
            "initial": server.display_name[0].upper(),
            "server_name": server.display_name,
            "days": days,
            "total_checks": total,
            "avg_latency": f"{sum(latencies)/len(latencies):.0f}" if latencies else "\u2014",
            "min_latency": f"{min(latencies):.0f}" if latencies else "\u2014",
            "max_latency": f"{max(latencies):.0f}" if latencies else "\u2014",
            "avg_players": f"{sum(players)/len(players):.0f}" if players else "\u2014",
            "max_players": str(max(players)) if players else "\u2014",
            "online_rate": f"{rate:.1f}",
            "online_count": len(online),
            "rate_class": "good" if rate >= 90 else ("ok" if rate >= 70 else "bad"),
            "queried_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        return await self._call("stats_card", ctx)

    # --- List Card ---

    async def render_list(self, servers: List[ServerInfo],
                          latest_records: Dict[int, dict],
                          default_server: Optional[ServerInfo] = None) -> str:
        rows, online_count = [], 0
        for s in servers:
            rec = latest_records.get(s.id, {})
            online = rec.get("online", False)
            if online:
                online_count += 1
            sc = "online" if online else "offline"
            st = "在线" if online else "离线"
            meta = ""
            if online:
                pl = rec.get("players_online", "?")
                pm = rec.get("players_max", "?")
                lt = rec.get("latency", 0)
                meta = f"{pl}/{pm} pl | {lt:.0f} ms"
            rows.append({
                "name": s.display_name,
                "address": s.address,
                "status_class": sc,
                "status_text": st,
                "meta": meta,
                "is_default": bool(default_server and s.id == default_server.id),
            })

        ctx = {
            "servers": rows,
            "online_count": online_count,
            "total": len(servers),
            "queried_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        return await self._call("list_card", ctx)
