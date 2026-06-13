"""Data models for MCPulse plugin."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class ServerStatus:
    """Represents the current status of a Minecraft server."""

    online: bool
    version: Optional[str]
    protocol: Optional[int]
    players_online: int
    players_max: int
    players_sample: List[str]
    motd: str
    latency: float
    favicon: Optional[bytes]
    error: Optional[str]
    queried_at: datetime

    def __str__(self) -> str:
        if not self.online:
            return f"服务器离线: {self.error}"
        return (
            f"状态: 在线 | "
            f"人数: {self.players_online}/{self.players_max} | "
            f"延迟: {self.latency:.0f}ms | "
            f"版本: {self.version}"
        )


@dataclass
class ServerInfo:
    """Represents a monitored server configuration."""

    id: int
    host: str
    port: int
    server_type: str
    name: Optional[str]
    group_name: Optional[str]
    enabled: bool

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def display_name(self) -> str:
        return self.name or self.host


@dataclass
class ServerStats:
    """Represents statistical data for a server over a time period."""

    server_id: int
    days: int
    avg_latency: float
    min_latency: float
    max_latency: float
    online_rate: float
    total_online_hours: float
    total_offline_hours: float
    max_players: int
    avg_players: float
