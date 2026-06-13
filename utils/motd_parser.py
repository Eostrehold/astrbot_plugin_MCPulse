"""Parser for Minecraft MOTD color codes and formatting."""

import re
from typing import Any, Dict, List, Union

# Minecraft color codes mapping
COLOR_CODES = {
    '0': '#000000',
    '1': '#0000AA',
    '2': '#00AA00',
    '3': '#00AAAA',
    '4': '#AA0000',
    '5': '#AA00AA',
    '6': '#FFAA00',
    '7': '#AAAAAA',
    '8': '#555555',
    '9': '#5555FF',
    'a': '#55FF55',
    'b': '#55FFFF',
    'c': '#FF5555',
    'd': '#FF55FF',
    'e': '#FFFF55',
    'f': '#FFFFFF',
}

FORMAT_CODES = {
    'l': 'bold',
    'o': 'italic',
    'n': 'underline',
    'm': 'strikethrough',
    'k': 'obfuscated',
    'r': 'reset',
}

COLOR_CODE_PATTERN = re.compile(r'§[0-9a-fk-or]')


def strip_motd_colors(motd: str) -> str:
    """Remove all Minecraft color/formatting codes from text."""
    if not motd:
        return ""
    return COLOR_CODE_PATTERN.sub('', motd)


def _parse_json_component(component: Dict[str, Any]) -> str:
    """Parse a single JSON text component."""
    text = component.get('text', '')
    if 'extra' in component:
        for child in component['extra']:
            text += _parse_json_component(child)
    if 'translate' in component:
        text += component['translate']
    return text


def parse_motd(motd: Union[str, Dict, List]) -> str:
    """Parse MOTD from various formats into plain text.

    Supports:
    - Plain text with § color codes
    - JSON text components (from mcstatus library)
    - List of JSON components
    """
    if motd is None:
        return ""
    if isinstance(motd, dict):
        return strip_motd_colors(_parse_json_component(motd))
    if isinstance(motd, list):
        text = ""
        for component in motd:
            if isinstance(component, dict):
                text += _parse_json_component(component)
            elif isinstance(component, str):
                text += component
        return strip_motd_colors(text)
    if isinstance(motd, str):
        return strip_motd_colors(motd)
    return str(motd)


def get_motd_color(color_code: str) -> str:
    """Get hex color for a Minecraft color code."""
    return COLOR_CODES.get(color_code.lower(), '#FFFFFF')
