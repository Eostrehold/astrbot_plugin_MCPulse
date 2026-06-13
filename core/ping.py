"""Minecraft server ping service using mcstatus library."""

from datetime import datetime
from typing import Optional

from mcstatus import JavaServer, BedrockServer

from core.models import ServerStatus
from utils.motd_parser import parse_motd


class PingService:
    """Service for querying Minecraft server status."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    async def query_server(self, host: str, port: int = 25565, server_type: str = "auto") -> ServerStatus:
        """Query a Minecraft server for its status."""
        if server_type == "java":
            return await self._query_java(host, port)
        elif server_type == "bedrock":
            return await self._query_bedrock(host, port)
        else:
            return await self._auto_detect(host, port)

    async def _auto_detect(self, host: str, port: int) -> ServerStatus:
        """Auto-detect server type and query status."""
        try:
            result = await self._query_java(host, port)
            if result.online:
                return result
        except Exception:
            pass

        try:
            result = await self._query_bedrock(host, port)
            if result.online:
                return result
        except Exception:
            pass

        return ServerStatus(
            online=False, version=None, protocol=None,
            players_online=0, players_max=0, players_sample=[],
            motd="", latency=0.0, favicon=None,
            error="Connection failed (tried Java and Bedrock)",
            queried_at=datetime.now(),
        )

    async def _query_java(self, host: str, port: int) -> ServerStatus:
        """Query a Java edition server."""
        try:
            server = JavaServer.lookup(f"{host}:{port}", timeout=self.timeout)
            status = await server.async_status()

            players_sample = []
            if status.players.sample:
                players_sample = [p.name for p in status.players.sample]

            motd = parse_motd(status.description)
            favicon = status.favicon if hasattr(status, 'favicon') else None

            return ServerStatus(
                online=True, version=status.version.name, protocol=status.version.protocol,
                players_online=status.players.online, players_max=status.players.max,
                players_sample=players_sample, motd=motd, latency=status.latency,
                favicon=favicon, error=None, queried_at=datetime.now(),
            )
        except Exception as e:
            return ServerStatus(
                online=False, version=None, protocol=None,
                players_online=0, players_max=0, players_sample=[],
                motd="", latency=0.0, favicon=None,
                error=str(e), queried_at=datetime.now(),
            )

    async def _query_bedrock(self, host: str, port: int) -> ServerStatus:
        """Query a Bedrock edition server."""
        try:
            server = BedrockServer.lookup(f"{host}:{port}", timeout=self.timeout)
            status = await server.async_status()
            motd = parse_motd(status.motd)

            return ServerStatus(
                online=True, version=status.version.name, protocol=status.version.protocol,
                players_online=status.players_online, players_max=status.players_max,
                players_sample=[], motd=motd, latency=status.latency,
                favicon=None, error=None, queried_at=datetime.now(),
            )
        except Exception as e:
            return ServerStatus(
                online=False, version=None, protocol=None,
                players_online=0, players_max=0, players_sample=[],
                motd="", latency=0.0, favicon=None,
                error=str(e), queried_at=datetime.now(),
            )
