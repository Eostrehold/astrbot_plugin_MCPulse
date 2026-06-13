"""Tests for MOTD parser."""

import pytest
from utils.motd_parser import parse_motd, strip_motd_colors


class TestMotdParser:
    def test_plain_text(self):
        assert parse_motd("Hello World") == "Hello World"

    def test_color_codes(self):
        result = parse_motd("§aHello §bWorld")
        assert "Hello" in result
        assert "World" in result

    def test_formatting_codes(self):
        result = parse_motd("§lBold §oItalic §rReset")
        assert "Bold" in result
        assert "Italic" in result

    def test_strip_colors(self):
        assert strip_motd_colors("§aHello §bWorld") == "Hello World"

    def test_complex_motd(self):
        motd = "§6§lHypixel §r§7Network §a[1.8-1.21]"
        stripped = strip_motd_colors(motd)
        assert "Hypixel" in stripped
        assert "Network" in stripped
        assert "§" not in stripped

    def test_empty_motd(self):
        assert parse_motd("") == ""
        assert strip_motd_colors("") == ""

    def test_none_motd(self):
        assert parse_motd(None) == ""

    def test_json_motd(self):
        json_motd = {"text": "Hello ", "extra": [{"text": "World", "color": "green"}]}
        result = parse_motd(json_motd)
        assert "Hello" in result
        assert "World" in result

    def test_list_motd(self):
        list_motd = [{"text": "Hello "}, {"text": "World"}]
        result = parse_motd(list_motd)
        assert "Hello" in result
        assert "World" in result
