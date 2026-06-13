"""Tests for ping service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.ping import PingService
from core.models import ServerStatus


@pytest.fixture
def ping_service():
    return PingService(timeout=10)


@pytest.mark.asyncio
async def test_query_java_server(ping_service):
    mock_status = MagicMock()
    mock_status.version.name = "1.20.4"
    mock_status.version.protocol = 765
    mock_status.players.online = 100
    mock_status.players.max = 200
    mock_status.players.sample = None
    mock_status.description = "Test Server"
    mock_status.latency = 50.0
    mock_status.favicon = None

    mock_server = AsyncMock()
    mock_server.async_status.return_value = mock_status

    with patch("core.ping.JavaServer.lookup", return_value=mock_server):
        result = await ping_service.query_server("mc.example.com", 25565, "java")

    assert result.online is True
    assert result.version == "1.20.4"
    assert result.players_online == 100
    assert result.latency == 50.0


@pytest.mark.asyncio
async def test_query_offline_server(ping_service):
    mock_server = AsyncMock()
    mock_server.async_status.side_effect = ConnectionRefusedError()

    with patch("core.ping.JavaServer.lookup", return_value=mock_server):
        with patch("core.ping.BedrockServer.lookup", side_effect=Exception()):
            result = await ping_service.query_server("offline.server.com", 25565, "auto")

    assert result.online is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_query_server_auto_detect(ping_service):
    mock_status = MagicMock()
    mock_status.version.name = "1.20.4"
    mock_status.version.protocol = 765
    mock_status.players.online = 50
    mock_status.players.max = 100
    mock_status.players.sample = []
    mock_status.description = "Test"
    mock_status.latency = 30.0
    mock_status.favicon = None

    mock_server = AsyncMock()
    mock_server.async_status.return_value = mock_status

    with patch("core.ping.JavaServer.lookup", return_value=mock_server):
        result = await ping_service.query_server("mc.example.com", 25565, "auto")

    assert result.online is True
