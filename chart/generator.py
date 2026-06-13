"""Chart generation for MCPulse using matplotlib."""

import io
from datetime import datetime
from typing import List

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


CHART_STYLE = {
    "figure.figsize": (10, 5),
    "figure.dpi": 100,
    "axes.grid": True,
    "axes.spines.top": False,
    "axes.spines.right": False,
}

COLORS = {
    "latency": "#FF6B6B",
    "players": "#4ECDC4",
    "online_rate": "#45B7D1",
}


class ChartGenerator:
    """Generator for server statistics charts."""

    def __init__(self):
        plt.rcParams.update(CHART_STYLE)

    def generate_latency_chart(
        self, timestamps: List[datetime], latencies: List[float],
        server_name: str = "Server", days: int = 7,
    ) -> bytes:
        """Generate a latency trend chart."""
        fig, ax = plt.subplots()
        ax.plot(timestamps, latencies, color=COLORS["latency"], linewidth=2)
        ax.fill_between(timestamps, latencies, alpha=0.3, color=COLORS["latency"])
        ax.set_title(f"{server_name} - 延迟趋势 (最近{days}天)")
        ax.set_xlabel("时间")
        ax.set_ylabel("延迟 (ms)")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def generate_players_chart(
        self, timestamps: List[datetime], players_online: List[int],
        players_max: List[int], server_name: str = "Server", days: int = 7,
    ) -> bytes:
        """Generate a players trend chart."""
        fig, ax = plt.subplots()
        ax.plot(timestamps, players_online, color=COLORS["players"], linewidth=2, label="在线人数")
        ax.fill_between(timestamps, players_online, alpha=0.3, color=COLORS["players"])
        if players_max and any(p > 0 for p in players_max):
            ax.plot(timestamps, players_max, color="#888888", linewidth=1, linestyle='--', label="最大人数")
        ax.set_title(f"{server_name} - 在线人数趋势 (最近{days}天)")
        ax.set_xlabel("时间")
        ax.set_ylabel("人数")
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    def generate_online_rate_chart(
        self, dates: List[str], rates: List[float],
        server_name: str = "Server", days: int = 7,
    ) -> bytes:
        """Generate an online rate bar chart."""
        fig, ax = plt.subplots()
        bars = ax.bar(dates, rates, color=COLORS["online_rate"], alpha=0.8)
        for bar, rate in zip(bars, rates):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
        ax.set_title(f"{server_name} - 在线率统计 (最近{days}天)")
        ax.set_xlabel("日期")
        ax.set_ylabel("在线率 (%)")
        ax.set_ylim(0, 105)
        plt.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
