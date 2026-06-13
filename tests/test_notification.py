"""Tests for notification templates."""

import pytest
from notification.templates import TemplateManager


@pytest.fixture
def template_manager():
    return TemplateManager()


class TestTemplateManager:
    def test_render_offline_template(self, template_manager):
        variables = {
            "{server_name}": "Hypixel",
            "{server_address}": "mc.hypixel.net:25565",
            "{error}": "Connection refused",
            "{time}": "2024-01-15 14:30:00",
        }
        result = template_manager.render("offline", variables)
        assert "Hypixel" in result
        assert "离线" in result
        assert "Connection refused" in result

    def test_render_recovery_template(self, template_manager):
        variables = {
            "{server_name}": "Hypixel",
            "{server_address}": "mc.hypixel.net:25565",
            "{players_online}": "100",
            "{players_max}": "200",
            "{latency}": "50",
            "{time}": "2024-01-15 14:35:00",
        }
        result = template_manager.render("recovery", variables)
        assert "Hypixel" in result
        assert "恢复" in result
        assert "100" in result

    def test_render_high_latency_template(self, template_manager):
        variables = {
            "{server_name}": "Hypixel",
            "{server_address}": "mc.hypixel.net:25565",
            "{latency}": "600",
            "{threshold}": "500",
            "{time}": "2024-01-15 14:40:00",
        }
        result = template_manager.render("high_latency", variables)
        assert "Hypixel" in result
        assert "延迟" in result
        assert "600" in result

    def test_render_unknown_template(self, template_manager):
        variables = {}
        result = template_manager.render("unknown_type", variables)
        assert "未知" in result

    def test_custom_template(self, template_manager):
        template_manager.set_template("custom", "Server {server_name} custom message")
        variables = {"{server_name}": "Test"}
        result = template_manager.render("custom", variables)
        assert result == "Server Test custom message"

    def test_get_available_variables(self, template_manager):
        vars = template_manager.get_available_variables()
        assert "{server_name}" in vars
        assert "{latency}" in vars
