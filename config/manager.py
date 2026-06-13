"""Configuration manager for MCPulse plugin."""

from typing import Any, Dict, Optional


class ConfigManager:
    """Manager for plugin configuration with WebUI support."""

    DEFAULTS = {
        "monitor": {"interval": 300, "enabled": True, "timeout": 10},
        "notification": {"enabled": True, "on_offline": True, "on_recovery": True, "on_high_latency": True, "latency_threshold": 500},
        "data_retention": 30,
        "permissions": {"admin_only": False},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = self._merge_with_defaults(config or {})

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, default_value in self.DEFAULTS.items():
            if key in config:
                if isinstance(default_value, dict) and isinstance(config[key], dict):
                    result[key] = {**default_value, **config[key]}
                else:
                    result[key] = config[key]
            else:
                result[key] = default_value
        return result

    def get(self, *keys: str, default: Any = None) -> Any:
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @property
    def monitor_interval(self) -> int:
        return self.get("monitor", "interval", default=300)

    @property
    def monitor_enabled(self) -> bool:
        return self.get("monitor", "enabled", default=True)

    @property
    def monitor_timeout(self) -> int:
        return self.get("monitor", "timeout", default=10)

    @property
    def notification_enabled(self) -> bool:
        return self.get("notification", "enabled", default=True)

    @property
    def notify_on_offline(self) -> bool:
        return self.get("notification", "on_offline", default=True)

    @property
    def notify_on_recovery(self) -> bool:
        return self.get("notification", "on_recovery", default=True)

    @property
    def notify_on_high_latency(self) -> bool:
        return self.get("notification", "on_high_latency", default=True)

    @property
    def latency_threshold(self) -> int:
        return self.get("notification", "latency_threshold", default=500)

    @property
    def data_retention_days(self) -> int:
        return self.get("data_retention", default=30)

    @property
    def admin_only(self) -> bool:
        return self.get("permissions", "admin_only", default=False)
