"""Tests for core data models."""

import pytest
from datetime import datetime
from core.models import ServerStatus, ServerInfo, ServerStats


class TestServerStatus:
    def test_online_server(self):
        status = ServerStatus(
            online=True,
            version="1.20.4",
            protocol=765,
            players_online=100,
            players_max=200,
            players_sample=["Player1", "Player2"],
            motd="A Minecraft Server",
            latency=50.0,
            favicon=None,
            error=None,
            queried_at=datetime.now(),
        )
        assert status.online is True
        assert status.version == "1.20.4"
        assert status.players_online == 100

    def test_offline_server(self):
        status = ServerStatus(
            online=False,
            version=None,
            protocol=None,
            players_online=0,
            players_max=0,
            players_sample=[],
            motd="",
            latency=0.0,
            favicon=None,
            error="Connection refused",
            queried_at=datetime.now(),
        )
        assert status.online is False
        assert status.error == "Connection refused"

    def test_server_status_str_online(self):
        status = ServerStatus(
            online=True,
            version="1.20.4",
            protocol=765,
            players_online=100,
            players_max=200,
            players_sample=[],
            motd="Test",
            latency=50.0,
            favicon=None,
            error=None,
            queried_at=datetime.now(),
        )
        result = str(status)
        assert "在线" in result
        assert "100" in result

    def test_server_status_str_offline(self):
        status = ServerStatus(
            online=False,
            version=None,
            protocol=None,
            players_online=0,
            players_max=0,
            players_sample=[],
            motd="",
            latency=0.0,
            favicon=None,
            error="Connection refused",
            queried_at=datetime.now(),
        )
        result = str(status)
        assert "离线" in result
        assert "Connection refused" in result


class TestServerInfo:
    def test_create_server_info(self):
        info = ServerInfo(
            id=1,
            host="mc.hypixel.net",
            port=25565,
            server_type="auto",
            name="Hypixel",
            group_name="小游戏",
            enabled=True,
        )
        assert info.host == "mc.hypixel.net"
        assert info.address == "mc.hypixel.net:25565"

    def test_display_name_with_name(self):
        info = ServerInfo(
            id=1,
            host="mc.hypixel.net",
            port=25565,
            server_type="auto",
            name="Hypixel",
            group_name=None,
            enabled=True,
        )
        assert info.display_name == "Hypixel"

    def test_display_name_without_name(self):
        info = ServerInfo(
            id=1,
            host="mc.hypixel.net",
            port=25565,
            server_type="auto",
            name=None,
            group_name=None,
            enabled=True,
        )
        assert info.display_name == "mc.hypixel.net"


class TestServerStats:
    def test_stats_creation(self):
        stats = ServerStats(
            server_id=1,
            days=7,
            avg_latency=50.0,
            min_latency=30.0,
            max_latency=100.0,
            online_rate=99.5,
            total_online_hours=167.0,
            total_offline_hours=1.0,
            max_players=200,
            avg_players=100,
        )
        assert stats.online_rate == 99.5
        assert stats.avg_latency == 50.0
        assert stats.max_players == 200
