from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List
import random

import svgwrite

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import ProjectConfig, load_config


class TerminalSVGBuilder:
    """Build a 3-panel neon terminal SVG with animated ASCII portrait and system stats."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self.logger = logging.getLogger("svg-builder")
        self.palette = {
            "background": "#0B0E14",  # Deep dark space blue
            "terminal": "#10141D",    # Terminal background
            "panel": "#0D111A",       # Inner panels background
            "text": "#E6EDF3",        # Primary text
            "accent": "#00F7FF",      # Cyber cyan
            "highlight": "#58A6FF",   # Bright blue
            "secondary": "#8B5CF6",   # Electric purple
            "muted": "#7D8590",       # Muted gray
            "green": "#22C55E",       # Neon green
            "border": "#1F2937",      # Dark gray border
        }

    def build_terminal_svg(self, ascii_lines: List[str], output_path: Path) -> Path:
        width = self.config.terminal_width
        height = self.config.terminal_height
        
        # Initialize drawing
        dwg = svgwrite.Drawing(str(output_path), size=(f"{width}px", f"{height}px"), profile="full")
        
        # Outer background
        dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill=self.palette["background"]))

        defs = dwg.defs
        
        # Linear Gradient for terminal background fill
        grad = dwg.linearGradient((0, 0), (0, 1), gradientUnits="objectBoundingBox")
        grad.add_stop_color(0, "#161B22")
        grad.add_stop_color(1, "#0D1117")
        defs.add(grad)

        # Glow filter (fix double spaces in color matrix)
        glow_filter = dwg.filter(id="glow", x="-30%", y="-30%", width="160%", height="160%")
        glow_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation="2.4", result="blur")
        glow_filter.feColorMatrix(type="matrix", values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1.7 0", result="glow")
        defs.add(glow_filter)

        # Noise filter (fix double spaces in color matrix)
        noise_filter = dwg.filter(id="noise", x="0", y="0", width="100%", height="100%")
        noise_filter.feTurbulence(type="fractalNoise", baseFrequency="0.8", numOctaves="2", seed="3", result="noise")
        noise_filter.feColorMatrix(type="matrix", values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0.08 0")
        defs.add(noise_filter)

        # Main terminal frame
        main_panel = dwg.g(id="main-terminal")
        # Glow border
        main_panel.add(dwg.rect(insert=(40, 38), size=(width - 80, height - 76), rx=24, ry=24, fill="none", stroke=self.palette["accent"], stroke_width=1.2, filter="url(#glow)", opacity=0.4))
        # Actual body
        main_panel.add(dwg.rect(insert=(40, 38), size=(width - 80, height - 76), rx=24, ry=24, fill=self.palette["terminal"], stroke="#1F2937", stroke_width=1.4))
        # Subtle gradient overlay
        main_panel.add(dwg.rect(insert=(40, 38), size=(width - 80, height - 76), rx=24, ry=24, fill="url(#grad)", opacity=0.25))

        # Title bar & controls
        title_bar = dwg.g(id="title-bar")
        title_bar.add(dwg.circle(center=(70, 68), r=6, fill="#FF5F56"))
        title_bar.add(dwg.circle(center=(90, 68), r=6, fill="#FFBD2E"))
        title_bar.add(dwg.circle(center=(110, 68), r=6, fill="#27C93F"))
        title_bar.add(dwg.rect(insert=(160, 54), size=(260, 24), rx=12, ry=12, fill="#0B0E14", stroke="#1F2937", stroke_width=1))
        title_bar.add(dwg.text("guest@animesh6532: ~", insert=(175, 70), fill=self.palette["muted"], font_size="11px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        main_panel.add(title_bar)

        # ==========================================
        # LEFT PANEL: PROFILE CARD
        # ==========================================
        left_panel = dwg.g(id="left-panel")
        left_panel.add(dwg.rect(insert=(60, 110), size=(220, 380), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Header
        left_panel.add(dwg.text("PROFILE CARD", insert=(80, 140), fill=self.palette["accent"], font_size="11px", font_weight="bold", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        left_panel.add(dwg.line(start=(80, 150), end=(260, 150), stroke="#1F2937", stroke_width=1))
        
        # Developer Details
        left_panel.add(dwg.text(self.config.developer_name, insert=(80, 180), fill=self.palette["text"], font_size="15px", font_weight="700", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        left_panel.add(dwg.text(self.config.role, insert=(80, 200), fill=self.palette["secondary"], font_size="11px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        left_panel.add(dwg.text(f"⚡ {self.config.status}", insert=(80, 220), fill=self.palette["muted"], font_size="11px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        
        # Contact / Info items
        info_y = 250
        info_items = [
            ("Location", self.config.location),
            ("Portfolio", self.config.portfolio.replace("https://", "").replace("http://", "")),
            ("GitHub", f"@{self.config.github.split('/')[-1]}"),
        ]
        for label, val in info_items:
            left_panel.add(dwg.text(f"{label}:", insert=(80, info_y), fill=self.palette["muted"], font_size="10px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
            left_panel.add(dwg.text(val, insert=(80, info_y + 14), fill=self.palette["highlight"], font_size="10px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
            info_y += 32

        # System Stats Box (cool visual)
        stats_box = dwg.g(id="system-stats")
        stats_box.add(dwg.rect(insert=(75, 360), size=(190, 110), rx=8, ry=8, fill="#080C14", stroke="#1F2937", stroke_width=1))
        stats_box.add(dwg.text("SYSTEM MONITOR", insert=(85, 378), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        
        stats = [
            ("CPU UTIL", "12%", self.palette["accent"]),
            ("RAM LOAD", "4.8GB / 16GB", self.palette["secondary"]),
            ("SYS TEMP", "42°C", "#F59E0B"),
            ("STATUS", "ONLINE", self.palette["green"]),
        ]
        for idx, (lbl, value, col) in enumerate(stats):
            y_pos = 398 + idx * 16
            stats_box.add(dwg.text(lbl, insert=(85, y_pos), fill=self.palette["muted"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
            stats_box.add(dwg.text(value, insert=(170, y_pos), fill=col, font_size="9px", font_weight="bold", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
            if lbl == "STATUS":
                # Glowing status indicator
                stats_box.add(dwg.circle(center=(225, y_pos - 3), r=3.5, fill=self.palette["green"], filter="url(#glow)"))
        
        left_panel.add(stats_box)
        main_panel.add(left_panel)

        # ==========================================
        # CENTER PANEL: ASCII PORTRAIT & BOOT LOGS
        # ==========================================
        center_panel = dwg.g(id="center-panel")
        center_panel.add(dwg.rect(insert=(295, 110), size=(370, 380), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Header
        center_panel.add(dwg.text("TERMINAL CONSOLE", insert=(315, 140), fill=self.palette["accent"], font_size="11px", font_weight="bold", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        center_panel.add(dwg.line(start=(315, 150), end=(645, 150), stroke="#1F2937", stroke_width=1))

        # Placeholder Group for boot sequence logs (will be animated in animate_terminal.py)
        boot_logs = dwg.g(id="boot-logs")
        center_panel.add(boot_logs)

        # Portrait Group (lines added programmatically)
        portrait_group = dwg.g(id="ascii-portrait")
        # Each line will be added inside this group
        for index, line in enumerate(ascii_lines[:48]):
            # Center of center panel is x = 295 + 370/2 = 480.
            # Insert at x = 480 - 146 = 334.
            # Line height = 6.0px. Starting at y = 160. Ends at 160 + 48*6 = 448.
            y_pos = 160 + index * 6.0
            text_el = dwg.text(line, insert=(334, y_pos), fill=self.palette["text"], font_size="5.4px", font_family="JetBrains Mono, Fira Code, Courier New, monospace")
            text_el["xml:space"] = "preserve"
            portrait_group.add(text_el)
        center_panel.add(portrait_group)

        # Interactive Command Prompt area at the bottom of Center panel
        prompt_group = dwg.g(id="interactive-prompt")
        # Line prompt text: guest@animesh:~$
        center_panel.add(prompt_group)

        main_panel.add(center_panel)

        # ==========================================
        # RIGHT PANEL: SYSTEM INFORMATION & METRICS
        # ==========================================
        right_panel = dwg.g(id="right-panel")
        right_panel.add(dwg.rect(insert=(680, 110), size=(160, 380), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Header 1: SYSTEM INFO
        right_panel.add(dwg.text("SYSTEM INFO", insert=(695, 138), fill=self.palette["accent"], font_size="10px", font_weight="bold", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        right_panel.add(dwg.text(f"OS: {self.config.operating_system}", insert=(695, 156), fill=self.palette["text"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        right_panel.add(dwg.text(f"Editor: {self.config.editor}", insert=(695, 170), fill=self.palette["text"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        right_panel.add(dwg.text(f"Exp: {self.config.experience}", insert=(695, 184), fill=self.palette["text"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        right_panel.add(dwg.text(f"Learning: {self.config.learning}", insert=(695, 198), fill=self.palette["text"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        
        # Header 2: TECH STACK
        right_panel.add(dwg.text("TECH STACK", insert=(695, 226), fill=self.palette["accent"], font_size="10px", font_weight="bold", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        langs = " • ".join(self.config.languages[:3])
        frame = " • ".join(self.config.frameworks[:3])
        right_panel.add(dwg.text(langs, insert=(695, 244), fill=self.palette["text"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        right_panel.add(dwg.text(frame, insert=(695, 258), fill=self.palette["text"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        
        # Header 3: GIT METRICS
        right_panel.add(dwg.text("GIT STATISTICS", insert=(695, 286), fill=self.palette["accent"], font_size="10px", font_weight="bold", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        right_panel.add(dwg.text(f"Repos: {self.config.repository_count}  Stars: {self.config.stars}", insert=(695, 304), fill=self.palette["text"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        right_panel.add(dwg.text(f"Followers: {self.config.followers}", insert=(695, 318), fill=self.palette["text"], font_size="9px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        
        # Progress bar for Commits
        right_panel.add(dwg.text("Commits (1.8k)", insert=(695, 338), fill=self.palette["muted"], font_size="8px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        # Background bar
        right_panel.add(dwg.rect(insert=(695, 344), size=(130, 4), rx=2, ry=2, fill="#161B22"))
        # Filled bar (gradient / color)
        right_panel.add(dwg.rect(insert=(695, 344), size=(110, 4), rx=2, ry=2, fill=self.palette["accent"]))
        
        # Progress bar for Stars target
        right_panel.add(dwg.text("Stars Rating", insert=(695, 358), fill=self.palette["muted"], font_size="8px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        right_panel.add(dwg.rect(insert=(695, 364), size=(130, 4), rx=2, ry=2, fill="#161B22"))
        right_panel.add(dwg.rect(insert=(695, 364), size=(84, 4), rx=2, ry=2, fill=self.palette["secondary"]))

        # Header 4: CONTRIBUTIONS GRID
        right_panel.add(dwg.text("CONTRIBUTION HEATMAP", insert=(695, 392), fill=self.palette["accent"], font_size="10px", font_weight="bold", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        
        # Grid of contribution squares: 4 rows x 15 columns
        grid_group = dwg.g(id="contrib-grid")
        random.seed(42)  # Deterministic representation
        colors = ["#161B22", "#161B22", "#0e4429", "#006d32", "#26a641", "#39d353"]
        for r in range(4):
            for c in range(15):
                color = random.choice(colors)
                # Square size = 5x5, spacing = 8px.
                x_pos = 695 + c * 8
                y_pos = 406 + r * 8
                grid_group.add(dwg.rect(insert=(x_pos, y_pos), size=(6, 6), rx=1.2, ry=1.2, fill=color))
        right_panel.add(grid_group)
        
        right_panel.add(dwg.text("Metrics System Ready", insert=(695, 452), fill=self.palette["muted"], font_size="8px", font_family="JetBrains Mono, Fira Code, Courier New, monospace"))
        main_panel.add(right_panel)

        # ==========================================
        # OVERLAYS & SCANLINE (Pure SVG SMIL)
        # ==========================================
        # Scanline moving from top to bottom
        scanline_group = dwg.g(id="scanline-group", opacity=0.25)
        # A thin gradient/rect overlay
        scanline_rect = dwg.rect(insert=(40, 40), size=(width - 80, 4), fill="#ffffff", opacity=0.08)
        scanline_rect.add(svgwrite.animate.Animate("y", from_="40", to_="480", dur="8s", repeatCount="indefinite"))
        scanline_group.add(scanline_rect)
        main_panel.add(scanline_group)

        # Tiny random sparkles/noise dots to look like terminal noise
        noise_group = dwg.g(id="terminal-noise")
        for i in range(20):
            nx = 50 + (i * 47) % (width - 100)
            ny = 50 + (i * 29) % (height - 100)
            dot = dwg.circle(center=(nx, ny), r=0.8, fill="#ffffff", opacity=0.03)
            # Dot flashes
            dot.add(svgwrite.animate.Animate("opacity", values="0.01;0.06;0.01", dur="4s", begin=f"{i * 0.15}s", repeatCount="indefinite"))
            noise_group.add(dot)
        main_panel.add(noise_group)

        # Add the entire main panel
        dwg.add(main_panel)

        # Static noise backdrop
        dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill="#ffffff", opacity=0.01, filter="url(#noise)"))
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dwg.save()
        self.logger.info("Terminal SVG saved to %s", output_path)
        return output_path

    def build_portrait_svg(self, ascii_lines: List[str], output_path: Path) -> Path:
        """Standalone portrait SVG for compatibility."""
        width = 690
        height = 480
        dwg = svgwrite.Drawing(str(output_path), size=(f"{width}px", f"{height}px"), profile="full")
        dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill="#09090B"))
        dwg.add(dwg.rect(insert=(24, 24), size=(width - 48, height - 48), rx=24, ry=24, fill="#111827", stroke="#00F7FF", stroke_width=1.2))
        for index, line in enumerate(ascii_lines[:44]):
            y = 80 + index * 8
            text = dwg.text(line, insert=(70, y), fill="#E6EDF3", font_size="8px", font_family="JetBrains Mono, Fira Code, Courier New, monospace")
            dwg.add(text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dwg.save()
        return output_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    builder = TerminalSVGBuilder(load_config())
    ascii_path = builder.config.output_ascii_path
    if not ascii_path.exists():
        logging.error("ASCII portrait text file not found at %s. Please run generate_ascii.py first.", ascii_path)
        sys.exit(1)
    lines = ascii_path.read_text(encoding="utf-8").splitlines()
    builder.build_terminal_svg(lines, builder.config.output_terminal_path)
    builder.build_portrait_svg(lines, builder.config.output_portrait_path)


if __name__ == "__main__":
    main()
