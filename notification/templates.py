"""Notification templates for MCPulse."""

from typing import Dict


DEFAULT_TEMPLATES = {
    "offline": (
        "⚠️ 服务器 {server_name} ({server_address}) 已离线\n"
        "错误: {error}\n"
        "时间: {time}"
    ),
    "recovery": (
        "✅ 服务器 {server_name} ({server_address}) 已恢复在线\n"
        "当前人数: {players_online}/{players_max}\n"
        "延迟: {latency}ms\n"
        "时间: {time}"
    ),
    "high_latency": (
        "⚠️ 服务器 {server_name} ({server_address}) 延迟异常\n"
        "当前延迟: {latency}ms (阈值: {threshold}ms)\n"
        "时间: {time}"
    ),
}

TEMPLATE_VARS = {
    "{server_name}": "服务器名称",
    "{server_address}": "服务器地址",
    "{status}": "当前状态(在线/离线)",
    "{players_online}": "当前在线人数",
    "{players_max}": "最大人数",
    "{latency}": "当前延迟(ms)",
    "{version}": "服务器版本",
    "{error}": "错误信息",
    "{time}": "事件发生时间",
    "{threshold}": "延迟阈值(ms)",
}


class TemplateManager:
    """Manager for notification templates."""

    def __init__(self):
        self._templates: Dict[str, str] = DEFAULT_TEMPLATES.copy()

    def get_template(self, template_type: str) -> str:
        """Get a template by type."""
        return self._templates.get(template_type, "未知通知类型: {template_type}")

    def set_template(self, template_type: str, template: str):
        """Set or update a template."""
        self._templates[template_type] = template

    def render(self, template_type: str, variables: Dict[str, str]) -> str:
        """Render a template with variables."""
        template = self.get_template(template_type)
        result = template
        for key, value in variables.items():
            result = result.replace(key, str(value))
        return result

    def get_available_variables(self) -> Dict[str, str]:
        """Get all available template variables."""
        return TEMPLATE_VARS.copy()
