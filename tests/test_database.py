"""Tests for database operations."""

import pytest
import asyncio
from storage.database import Database


@pytest.fixture
async def db():
    database = Database(":memory:")
    await database.initialize()
    yield database
    await database.close()


@pytest.mark.asyncio
async def test_initialize_creates_tables(db):
    async with db._db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
        tables = [row[0] for row in await cursor.fetchall()]
    assert "servers" in tables
    assert "ping_records" in tables
    assert "status_changes" in tables


@pytest.mark.asyncio
async def test_add_server(db):
    server_id = await db.add_server(host="mc.hypixel.net", port=25565, server_type="auto", name="Hypixel", group_name="小游戏")
    assert server_id > 0
    server = await db.get_server(server_id)
    assert server is not None
    assert server.host == "mc.hypixel.net"
    assert server.port == 25565
    assert server.name == "Hypixel"


@pytest.mark.asyncio
async def test_get_server_by_address(db):
    await db.add_server(host="mc.hypixel.net", port=25565)
    server = await db.get_server_by_address("mc.hypixel.net", 25565)
    assert server is not None
    assert server.host == "mc.hypixel.net"


@pytest.mark.asyncio
async def test_get_all_servers(db):
    await db.add_server(host="server1.com", port=25565)
    await db.add_server(host="server2.com", port=25565)
    servers = await db.get_all_servers()
    assert len(servers) == 2


@pytest.mark.asyncio
async def test_delete_server(db):
    server_id = await db.add_server(host="mc.hypixel.net", port=25565)
    result = await db.delete_server(server_id)
    assert result is True
    server = await db.get_server(server_id)
    assert server is None


@pytest.mark.asyncio
async def test_update_server(db):
    server_id = await db.add_server(host="mc.hypixel.net", port=25565)
    result = await db.update_server(server_id, name="Hypixel Network")
    assert result is True
    server = await db.get_server(server_id)
    assert server.name == "Hypixel Network"


@pytest.mark.asyncio
async def test_add_ping_record(db):
    server_id = await db.add_server(host="mc.hypixel.net", port=25565)
    record_id = await db.add_ping_record(server_id, True, 50.0, 100, 200, "1.20.4")
    assert record_id > 0


@pytest.mark.asyncio
async def test_get_ping_records(db):
    server_id = await db.add_server(host="mc.hypixel.net", port=25565)
    await db.add_ping_record(server_id, True, 50.0, 100, 200, "1.20.4")
    await db.add_ping_record(server_id, True, 45.0, 110, 200, "1.20.4")
    records = await db.get_ping_records(server_id, limit=10)
    assert len(records) == 2


@pytest.mark.asyncio
async def test_add_status_change(db):
    server_id = await db.add_server(host="mc.hypixel.net", port=25565)
    change_id = await db.add_status_change(server_id, "online", "offline")
    assert change_id > 0


@pytest.mark.asyncio
async def test_cleanup_old_data(db):
    server_id = await db.add_server(host="mc.hypixel.net", port=25565)
    deleted = await db.cleanup_old_data(days=30)
    assert isinstance(deleted, int)
