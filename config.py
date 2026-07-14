from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict

# Preset color palettes for switchable dashboard themes
THEMES: Dict[str, Dict[str, str]] = {
    "cyberpunk": {
        "background": "#080A10",
        "terminal": "#0D111A",
        "panel": "#121826",
        "text": "#E6EDF3",
        "accent": "#00F7FF",      # Cyber cyan
        "highlight": "#FFE600",   # Laser yellow
        "secondary": "#FF007F",   # Neon magenta
        "muted": "#7C8C9E",
        "green": "#39D353",
        "border": "#2C3D52"
    },
    "tokyo_night": {
        "background": "#0E0E16",
        "terminal": "#1A1B26",
        "panel": "#16161E",
        "text": "#C0CAF5",
        "accent": "#7DCFFF",      # Tokyo cyan
        "highlight": "#7AA2F7",   # Tokyo blue
        "secondary": "#BB9AF7",   # Tokyo purple
        "muted": "#565F89",
        "green": "#9ECE6A",
        "border": "#24283B"
    },
    "catppuccin": {
        "background": "#0C0D12",
        "terminal": "#1E1E2E",
        "panel": "#181825",
        "text": "#CDD6F4",
        "accent": "#89B4FA",      # Catppuccin blue
        "highlight": "#89DCEB",   # Sky blue
        "secondary": "#CBA6F7",   # Mauve
        "muted": "#6C7086",
        "green": "#A6E3A1",
        "border": "#313244"
    },
    "nord": {
        "background": "#1A1E24",
        "terminal": "#2E3440",
        "panel": "#3B4252",
        "text": "#D8DEE9",
        "accent": "#88C0D0",      # Nord ice cyan
        "highlight": "#81A1C1",   # Nord blue
        "secondary": "#B48EAD",   # Nord aurora purple
        "muted": "#4C566A",
        "green": "#A3BE8C",
        "border": "#434C5E"
    },
    "dracula": {
        "background": "#171820",
        "terminal": "#282A36",
        "panel": "#21222C",
        "text": "#F8F8F2",
        "accent": "#8BE9FD",      # Dracula cyan
        "highlight": "#FF79C6",   # Pink
        "secondary": "#BD93F9",   # Purple
        "muted": "#6272A4",
        "green": "#50FA7B",
        "border": "#44475A"
    },
    "github_dark": {
        "background": "#040406",
        "terminal": "#0D1117",
        "panel": "#161B22",
        "text": "#E6EDF3",
        "accent": "#58A6FF",      # GitHub blue
        "highlight": "#AB7DF6",   # Purple
        "secondary": "#FF7B72",   # Orange-red
        "muted": "#8B949E",
        "green": "#39D353",
        "border": "#30363D"
    }
}


@dataclass(slots=True)
class ProjectConfig:
    """Configuration settings and layout defaults for the terminal profile generator."""

    developer_name: str = "Animesh Sahoo"
    role: str = "AI/ML Engineer"
    languages: List[str] = field(default_factory=lambda: ["Python", "Java", "C", "SQL"])
    frameworks: List[str] = field(default_factory=lambda: ["Flask", "FastAPI", "PyTorch", "Docker"])
    operating_system: str = "Windows / Linux"
    editor: str = "VS Code"
    location: str = "India"
    status: str = "Building open source"
    experience: str = "5+ years"
    portfolio: str = "https://animesh6532.netlify.app/"
    github: str = "https://github.com/animesh6532"
    current_project: str = "GitHub Terminal Profile Generator"
    repository_count: int = 17
    stars: int = 120
    followers: int = 350
    commits: int = 1842
    skills: List[str] = field(default_factory=lambda: ["Python", "Pillow", "NumPy", "SVG", "GitHub Actions"])
    image_path: str = "assets/profile.jpg"
    ascii_width: int = 90
    theme: str = "tokyo_night"
    animation_speed: float = 1.0
    typing_speed: float = 1.0
    glow_intensity: float = 2.4
    scanline_speed: float = 8.0
    terminal_width: int = 900
    terminal_height: int = 560
    ascii_chars: str = "@%#*+=-:. "
    density_mode: str = "balanced"
    learning: str = "Deep Learning & Rust"
    font_family: str = "JetBrains Mono, Fira Code, Courier New, monospace"
    panel_padding: int = 20
    panel_margin: int = 15
    portrait_alignment: str = "center"
    contrast_enhancement: float = 1.45
    brightness_enhancement: float = 1.05

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent

    @property
    def assets_dir(self) -> Path:
        return self.project_root / "assets"

    @property
    def template_path(self) -> Path:
        return self.project_root / "templates" / "terminal_template.svg"

    @property
    def output_ascii_path(self) -> Path:
        return self.assets_dir / "ascii.txt"

    @property
    def output_terminal_path(self) -> Path:
        return self.assets_dir / "terminal.svg"

    @property
    def output_portrait_path(self) -> Path:
        return self.assets_dir / "portrait.svg"


def _get_env(name: str, default: object) -> object:
    value = os.getenv(name)
    if value is None:
        return default
    if isinstance(default, bool):
        return value.lower() in {"1", "true", "yes", "on"}
    if isinstance(default, int):
        return int(value)
    if isinstance(default, float):
        return float(value)
    return value


def load_config() -> ProjectConfig:
    """Create a config instance from environment overrides when present."""

    config = ProjectConfig()
    config.developer_name = str(_get_env("DEV_NAME", config.developer_name))
    config.role = str(_get_env("DEV_ROLE", config.role))
    config.image_path = str(_get_env("IMAGE_PATH", config.image_path))
    config.ascii_width = int(_get_env("ASCII_WIDTH", config.ascii_width))
    config.theme = str(_get_env("THEME", config.theme))
    config.animation_speed = float(_get_env("ANIMATION_SPEED", config.animation_speed))
    config.terminal_width = int(_get_env("TERMINAL_WIDTH", config.terminal_width))
    config.density_mode = str(_get_env("DENSITY_MODE", config.density_mode))
    config.learning = str(_get_env("DEV_LEARNING", config.learning))
    config.typing_speed = float(_get_env("TYPING_SPEED", config.typing_speed))
    config.glow_intensity = float(_get_env("GLOW_INTENSITY", config.glow_intensity))
    config.scanline_speed = float(_get_env("SCANLINE_SPEED", config.scanline_speed))
    config.font_family = str(_get_env("FONT_FAMILY", config.font_family))
    config.panel_padding = int(_get_env("PANEL_PADDING", config.panel_padding))
    config.panel_margin = int(_get_env("PANEL_MARGIN", config.panel_margin))
    config.portrait_alignment = str(_get_env("PORTRAIT_ALIGNMENT", config.portrait_alignment))
    config.contrast_enhancement = float(_get_env("CONTRAST_ENHANCEMENT", config.contrast_enhancement))
    config.brightness_enhancement = float(_get_env("BRIGHTNESS_ENHANCEMENT", config.brightness_enhancement))
    return config
