"""MCPulse - Minecraft Server Status Monitoring Plugin for AstrBot."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add plugin directory to sys.path for local imports
_plugin_dir = str(Path(__file__).parent)
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from config.manager import ConfigManager
from core.ping import PingService
from core.models import ServerStatus, ServerInfo
from storage.database import Database
from notification.templates import TemplateManager
from chart.generator import ChartGenerator
from chart.renderer import render_server_status
from utils.motd_parser import strip_motd_colors

PLUGIN_DIR = Path(__file__).parent


@register(
    "astrbot_plugin_MCPulse",
    "Eostrehold",
    "Minecraft server status monitoring plugin with notifications, statistics, and charts.",
    "v0.1.0",
)
class MCPulsePlugin(Star):
    """MCPulse plugin for monitoring Minecraft servers."""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = ConfigManager(config)
        self.ping_service = PingService(timeout=self.config.monitor_timeout)
        self.db: Optional[Database] = None
        self.template_manager = TemplateManager()
        self.chart_generator = ChartGenerator()
        self._monitor_task: Optional[asyncio.Task] = None
        self._img_dir: Optional[Path] = None

    async def initialize(self):
        """Initialize the plugin."""
        data_dir = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = data_dir / "mcpulse.db"
        self.db = Database(str(db_path))
        await self.db.initialize()
        logger.info(f"MCPulse database initialized at {db_path}")
        if self.config.monitor_enabled:
            await self._start_monitor()

    async def terminate(self):
        """Cleanup when plugin is unloaded."""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        if self.db:
            await self.db.close()
        logger.info("MCPulse plugin terminated")

    async def _start_monitor(self):
        """Start the background monitoring task."""
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"MCPulse monitor started (interval: {self.config.monitor_interval}s)")

    async def _monitor_loop(self):
        """Background loop for monitoring servers."""
        while True:
            try:
                servers = await self.db.get_all_servers(enabled_only=True)
                for server in servers:
                    try:
                        await self._check_server(server)
                    except Exception as e:
                        logger.error(f"Error checking server {server.address}: {e}")
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
            await asyncio.sleep(self.config.monitor_interval)

    async def _check_server(self, server: ServerInfo):
        """Check a single server and update records."""
        status = await self.ping_service.query_server(server.host, server.port, server.server_type)
        records = await self.db.get_ping_records(server.id, limit=1)
        was_online = records[0]["online"] if records else None

        await self.db.add_ping_record(
            server_id=server.id, online=status.online, latency=status.latency,
            players_online=status.players_online, players_max=status.players_max,
            version=status.version, error=status.error,
        )

        if was_online is not None:
            if was_online and not status.online:
                await self.db.add_status_change(server.id, "online", "offline")
                if self.config.notify_on_offline:
                    await self._send_notification(server, status, "offline")
            elif not was_online and status.online:
                await self.db.add_status_change(server.id, "offline", "online")
                if self.config.notify_on_recovery:
                    await self._send_notification(server, status, "recovery")

        if status.online and self.config.notify_on_high_latency and status.latency > self.config.latency_threshold:
            await self._send_notification(server, status, "high_latency")

    async def _send_notification(self, server: ServerInfo, status: ServerStatus, notification_type: str):
        """Send a notification about server status change."""
        variables = {
            "{server_name}": server.display_name,
            "{server_address}": server.address,
            "{status}": "在线" if status.online else "离线",
            "{players_online}": str(status.players_online),
            "{players_max}": str(status.players_max),
            "{latency}": f"{status.latency:.0f}",
            "{version}": status.version or "Unknown",
            "{error}": status.error or "",
            "{time}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "{threshold}": str(self.config.latency_threshold),
        }
        message = self.template_manager.render(notification_type, variables)
        logger.info(f"Notification [{notification_type}] for {server.address}: {message}")

    # ---- Helper Methods ----

    async def _find_server(self, target: str) -> Optional[ServerInfo]:
        """Find a server by name or address."""
        servers = await self.db.get_all_servers()
        for server in servers:
            if server.name and server.name.lower() == target.lower():
                return server
        host, port = self._parse_address(target)
        return await self.db.get_server_by_address(host, port)

    def _parse_address(self, address: str) -> tuple:
        """Parse host:port address string."""
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                host = address
                port = 25565
        else:
            host = address
            port = 25565
        return host, port

    def _format_status(self, name: str, address: str, status: ServerStatus) -> str:
        """Format server status into a readable message."""
        if not status.online:
            return f"🔴 {name} ({address})\n─────────────────────\n状态: 离线\n错误: {status.error}"
        motd = strip_motd_colors(status.motd) if status.motd else ""
        players_sample = ""
        if status.players_sample:
            players_sample = f"\n👤 玩家: {', '.join(status.players_sample[:5])}"
        return (
            f"🎮 {name} ({address})\n"
            f"─────────────────────\n"
            f"📊 状态: 🟢 在线\n"
            f"👥 人数: {status.players_online:,} / {status.players_max:,}\n"
            f"📶 延迟: {status.latency:.0f}ms\n"
            f"📋 版本: {status.version}"
            f"{players_sample}\n"
            f"─────────────────────\n"
            f"💡 MOTD: {motd}"
        )

    async def _render_status_image(self, server: ServerInfo, status: ServerStatus) -> str:
        """Render server status as PNG via Pillow and return file path."""
        img_bytes = render_server_status(server, status)

        # Save to a temp file in plugin data directory
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        data_dir = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        data_dir.mkdir(parents=True, exist_ok=True)
        img_path = data_dir / f"status_{ts}.png"
        img_path.write_bytes(img_bytes)

        return str(img_path)

    async def _get_default_server(self, event: AstrMessageEvent) -> Optional[ServerInfo]:
        """Get the default server for the current group/user."""
        group_id = event.get_group_id() if hasattr(event, 'get_group_id') else None
        user_id = event.get_sender_id()

        if group_id:
            key = f"default_server_group_{group_id}"
            server_id = await self.get_kv_data(key, None)
            if server_id:
                return await self.db.get_server(server_id)

        key = f"default_server_user_{user_id}"
        server_id = await self.get_kv_data(key, None)
        if server_id:
            return await self.db.get_server(server_id)

        return None

    async def _check_admin(self, event: AstrMessageEvent) -> bool:
        """Check if the user has admin permissions."""
        if not self.config.admin_only:
            return True
        try:
            return event.is_admin()
        except Exception:
            return False

    # ---- Commands ----

    @filter.command("mcstatus")
    async def cmd_status(self, event: AstrMessageEvent):
        """查询 Minecraft 服务器状态"""
        args = event.message_str.strip().split()

        if len(args) < 2:
            default_server = await self._get_default_server(event)
            if default_server:
                server = default_server
            else:
                yield event.plain_result(
                    "用法: /mcstatus <服务器地址|名称>\n"
                    "提示: 使用 /mcsetdefault <地址|名称> 设置默认服务器"
                )
                return
        else:
            target = args[1]
            server = await self._find_server(target)
            if not server:
                host, port = self._parse_address(target)
                status = await self.ping_service.query_server(host, port)
                response = self._format_status(host, f"{host}:{port}", status)
                yield event.plain_result(response)
                return

        status = await self.ping_service.query_server(server.host, server.port, server.server_type)

        try:
            image_url = await self._render_status_image(server, status)
            yield event.image_result(image_url)
        except Exception as e:
            logger.error(f"Failed to render status image: {e}")
            response = self._format_status(server.display_name, server.address, status)
            yield event.plain_result(response)

    @filter.command("mcsetdefault")
    async def cmd_set_default(self, event: AstrMessageEvent):
        """设置默认服务器"""
        args = event.message_str.strip().split()
        if len(args) < 2:
            yield event.plain_result("用法: /mcsetdefault <服务器地址|名称>")
            return

        target = args[1]
        server = await self._find_server(target)
        if not server:
            yield event.plain_result(f"❌ 未找到服务器: {target}")
            return

        group_id = event.get_group_id() if hasattr(event, 'get_group_id') else None
        user_id = event.get_sender_id()

        if group_id:
            key = f"default_server_group_{group_id}"
            await self.put_kv_data(key, server.id)
            yield event.plain_result(f"✅ 已设置本群默认服务器: {server.display_name}")
        else:
            key = f"default_server_user_{user_id}"
            await self.put_kv_data(key, server.id)
            yield event.plain_result(f"✅ 已设置您的默认服务器: {server.display_name}")

    @filter.command("mcping")
    async def cmd_ping(self, event: AstrMessageEvent):
        """一次性查询服务器状态"""
        args = event.message_str.strip().split()
        if len(args) < 2:
            yield event.plain_result("用法: /mcping <服务器地址:端口>\n示例: /mcping mc.hypixel.net:25565")
            return
        target = args[1]
        host, port = self._parse_address(target)
        status = await self.ping_service.query_server(host, port)

        temp_server = ServerInfo(
            id=0, host=host, port=port, server_type="auto",
            name=host, group_name=None, enabled=True
        )

        try:
            image_url = await self._render_status_image(temp_server, status)
            yield event.image_result(image_url)
        except Exception as e:
            logger.error(f"Failed to render status image: {e}")
            response = self._format_status(host, f"{host}:{port}", status)
            yield event.plain_result(response)

    @filter.command("mcadd")
    async def cmd_add(self, event: AstrMessageEvent):
        """添加服务器监控"""
        if not await self._check_admin(event):
            yield event.plain_result("❌ 权限不足: 仅管理员可执行此操作")
            return
        args = event.message_str.strip().split()
        if len(args) < 2:
            yield event.plain_result("用法: /mcadd <地址:端口> [备注] [分组]\n示例: /mcadd mc.hypixel.net:25565 Hypixel 小游戏")
            return
        target = args[1]
        name = args[2] if len(args) > 2 else None
        group = args[3] if len(args) > 3 else None
        host, port = self._parse_address(target)
        existing = await self.db.get_server_by_address(host, port)
        if existing:
            yield event.plain_result(f"❌ 服务器已在监控列表中: {host}:{port}")
            return
        try:
            server_id = await self.db.add_server(host=host, port=port, server_type="auto", name=name, group_name=group)
            status = await self.ping_service.query_server(host, port)
            server = await self.db.get_server(server_id)
            await self.db.add_ping_record(
                server_id=server_id, online=status.online, latency=status.latency,
                players_online=status.players_online, players_max=status.players_max,
                version=status.version, error=status.error,
            )

            add_msg = f"✅ 已添加服务器监控\n地址: {host}:{port}\n备注: {name or '无'}\n分组: {group or '默认'}\n\n立即查询结果:"
            try:
                image_url = await self._render_status_image(server, status)
                yield event.plain_result(add_msg)
                yield event.image_result(image_url)
            except Exception as e:
                logger.error(f"Failed to render status image: {e}")
                status_text = self._format_status(name or host, f"{host}:{port}", status)
                yield event.plain_result(f"{add_msg}\n{status_text}")

        except Exception as e:
            yield event.plain_result(f"❌ 添加失败: {e}")

    @filter.command("mcdel")
    async def cmd_delete(self, event: AstrMessageEvent):
        """删除服务器监控"""
        if not await self._check_admin(event):
            yield event.plain_result("❌ 权限不足: 仅管理员可执行此操作")
            return
        args = event.message_str.strip().split()
        if len(args) < 2:
            yield event.plain_result("用法: /mcdel <地址|名称>")
            return
        target = args[1]
        server = await self._find_server(target)
        if not server:
            yield event.plain_result(f"❌ 未找到服务器: {target}")
            return
        await self.db.delete_server(server.id)
        yield event.plain_result(f"✅ 已删除服务器监控: {server.display_name}")

    @filter.command("mclist")
    async def cmd_list(self, event: AstrMessageEvent):
        """查看监控服务器列表"""
        servers = await self.db.get_all_servers()
        if not servers:
            yield event.plain_result("📋 暂无监控服务器\n使用 /mcadd 添加服务器")
            return
        lines = ["📋 监控服务器列表", "─────────────────────"]
        online_count = 0
        offline_count = 0
        for server in servers:
            records = await self.db.get_ping_records(server.id, limit=1)
            if records:
                latest = records[0]
                if latest["online"]:
                    status_icon = "🟢"
                    online_count += 1
                    status_text = f"人数: {latest['players_online']}/{latest['players_max']} | 延迟: {latest['latency']:.0f}ms"
                else:
                    status_icon = "🔴"
                    offline_count += 1
                    status_text = "状态: 离线"
            else:
                status_icon = "⚪"
                status_text = "未查询"
            lines.append(f"{status_icon} {server.display_name} - {server.host}\n   分组: {server.group_name or '默认'} | {status_text}")
        lines.append("─────────────────────")
        lines.append(f"共 {len(servers)} 台服务器 | {online_count} 台在线 | {offline_count} 台离线")

        default_server = await self._get_default_server(event)
        if default_server:
            lines.append(f"\n📌 当前默认服务器: {default_server.display_name}")

        yield event.plain_result("\n".join(lines))

    @filter.command("mcstats")
    async def cmd_stats(self, event: AstrMessageEvent):
        """查看服务器统计信息"""
        args = event.message_str.strip().split()

        if len(args) < 2:
            server = await self._get_default_server(event)
            if not server:
                yield event.plain_result("用法: /mcstats <地址|名称> [天数]")
                return
        else:
            target = args[1]
            server = await self._find_server(target)
            if not server:
                yield event.plain_result(f"❌ 未找到服务器: {target}")
                return

        days = int(args[2]) if len(args) > 2 else 7

        records = await self.db.get_ping_records(server.id, limit=1000, since=datetime.now().replace(hour=0, minute=0, second=0))
        if not records:
            yield event.plain_result(f"📊 {server.display_name} 暂无统计数据")
            return
        latencies = [r["latency"] for r in records if r["latency"] is not None]
        online_records = [r for r in records if r["online"]]
        online_rate = (len(online_records) / len(records)) * 100 if records else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        min_latency = min(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        players = [r["players_online"] for r in records if r["players_online"] is not None]
        max_players = max(players) if players else 0
        avg_players = sum(players) / len(players) if players else 0
        response = (
            f"📊 {server.display_name} - 最近{days}天统计\n"
            f"─────────────────────\n"
            f"📶 延迟统计:\n   平均: {avg_latency:.0f}ms | 最低: {min_latency:.0f}ms | 最高: {max_latency:.0f}ms\n"
            f"\n👥 人数统计:\n   平均: {avg_players:.0f} | 最高: {max_players}\n"
            f"\n📈 在线率: {online_rate:.1f}%"
        )
        yield event.plain_result(response)
