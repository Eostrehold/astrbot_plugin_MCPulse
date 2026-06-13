"""SQLite database operations for MCPulse."""

import aiosqlite
from datetime import datetime, timedelta
from typing import List, Optional

from core.models import ServerInfo


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Initialize database connection and create tables."""
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._create_tables()

    async def close(self):
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def _create_tables(self):
        """Create required database tables."""
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 25565,
                server_type TEXT DEFAULT 'auto',
                name TEXT,
                group_name TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(host, port)
            );

            CREATE TABLE IF NOT EXISTS ping_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                online BOOLEAN NOT NULL,
                latency REAL,
                players_online INTEGER,
                players_max INTEGER,
                version TEXT,
                error TEXT,
                queried_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES servers(id)
            );

            CREATE TABLE IF NOT EXISTS status_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                old_status TEXT,
                new_status TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES servers(id)
            );

            CREATE INDEX IF NOT EXISTS idx_ping_records_server_id
                ON ping_records(server_id);
            CREATE INDEX IF NOT EXISTS idx_ping_records_queried_at
                ON ping_records(queried_at);
            CREATE INDEX IF NOT EXISTS idx_status_changes_server_id
                ON status_changes(server_id);
        """)
        await self._db.commit()

    # ---- Server Operations ----

    async def add_server(
        self,
        host: str,
        port: int = 25565,
        server_type: str = "auto",
        name: Optional[str] = None,
        group_name: Optional[str] = None,
    ) -> int:
        """Add a new server to monitor. Returns server ID."""
        cursor = await self._db.execute(
            "INSERT INTO servers (host, port, server_type, name, group_name) VALUES (?, ?, ?, ?, ?)",
            (host, port, server_type, name, group_name),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_server(self, server_id: int) -> Optional[ServerInfo]:
        """Get a server by its ID."""
        async with self._db.execute(
            "SELECT id, host, port, server_type, name, group_name, enabled FROM servers WHERE id = ?",
            (server_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return ServerInfo(id=row[0], host=row[1], port=row[2], server_type=row[3], name=row[4], group_name=row[5], enabled=bool(row[6]))
        return None

    async def get_server_by_address(self, host: str, port: int = 25565) -> Optional[ServerInfo]:
        """Get a server by host and port."""
        async with self._db.execute(
            "SELECT id, host, port, server_type, name, group_name, enabled FROM servers WHERE host = ? AND port = ?",
            (host, port),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return ServerInfo(id=row[0], host=row[1], port=row[2], server_type=row[3], name=row[4], group_name=row[5], enabled=bool(row[6]))
        return None

    async def get_all_servers(self, enabled_only: bool = False) -> List[ServerInfo]:
        """Get all monitored servers."""
        query = "SELECT id, host, port, server_type, name, group_name, enabled FROM servers"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY group_name, name, host"

        servers = []
        async with self._db.execute(query) as cursor:
            async for row in cursor:
                servers.append(ServerInfo(id=row[0], host=row[1], port=row[2], server_type=row[3], name=row[4], group_name=row[5], enabled=bool(row[6])))
        return servers

    async def update_server(self, server_id: int, **kwargs) -> bool:
        """Update server configuration."""
        allowed_fields = {"name", "group_name", "enabled", "server_type", "port"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [server_id]

        cursor = await self._db.execute(f"UPDATE servers SET {set_clause} WHERE id = ?", values)
        await self._db.commit()
        return cursor.rowcount > 0

    async def delete_server(self, server_id: int) -> bool:
        """Delete a server and its associated records."""
        await self._db.execute("DELETE FROM ping_records WHERE server_id = ?", (server_id,))
        await self._db.execute("DELETE FROM status_changes WHERE server_id = ?", (server_id,))
        cursor = await self._db.execute("DELETE FROM servers WHERE id = ?", (server_id,))
        await self._db.commit()
        return cursor.rowcount > 0

    # ---- Ping Record Operations ----

    async def add_ping_record(
        self,
        server_id: int,
        online: bool,
        latency: Optional[float] = None,
        players_online: Optional[int] = None,
        players_max: Optional[int] = None,
        version: Optional[str] = None,
        error: Optional[str] = None,
    ) -> int:
        """Add a ping record. Returns record ID."""
        cursor = await self._db.execute(
            "INSERT INTO ping_records (server_id, online, latency, players_online, players_max, version, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (server_id, online, latency, players_online, players_max, version, error),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_ping_records(self, server_id: int, limit: int = 100, since: Optional[datetime] = None) -> List[dict]:
        """Get ping records for a server."""
        query = "SELECT online, latency, players_online, players_max, version, error, queried_at FROM ping_records WHERE server_id = ?"
        params = [server_id]
        if since:
            query += " AND queried_at >= ?"
            params.append(since.isoformat())
        query += " ORDER BY queried_at DESC LIMIT ?"
        params.append(limit)

        records = []
        async with self._db.execute(query, params) as cursor:
            async for row in cursor:
                records.append({"online": bool(row[0]), "latency": row[1], "players_online": row[2], "players_max": row[3], "version": row[4], "error": row[5], "queried_at": row[6]})
        return records

    # ---- Status Change Operations ----

    async def add_status_change(self, server_id: int, old_status: str, new_status: str) -> int:
        """Record a status change event. Returns change ID."""
        cursor = await self._db.execute(
            "INSERT INTO status_changes (server_id, old_status, new_status) VALUES (?, ?, ?)",
            (server_id, old_status, new_status),
        )
        await self._db.commit()
        return cursor.lastrowid

    # ---- Cleanup Operations ----

    async def cleanup_old_data(self, days: int = 30) -> int:
        """Delete data older than specified days. Returns count of deleted records."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor1 = await self._db.execute("DELETE FROM ping_records WHERE queried_at < ?", (cutoff,))
        cursor2 = await self._db.execute("DELETE FROM status_changes WHERE changed_at < ?", (cutoff,))
        await self._db.commit()
        return cursor1.rowcount + cursor2.rowcount
