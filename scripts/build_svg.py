from __future__ import annotations

import logging
import sys
import random
from pathlib import Path
from typing import List

import svgwrite

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import ProjectConfig, load_config, THEMES


class TerminalSVGBuilder:
    """Builds a premium Linux-style terminal SVG with a living ASCII portrait and developer resume."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self.logger = logging.getLogger("svg-builder")
        # Load active theme colors
        self.palette = THEMES.get(self.config.theme, THEMES["tokyo_night"])

    def perturb_ascii(self, lines: List[str], char_set: str, probability: float = 0.25, seed: int = 42) -> List[str]:
        """Generates a slightly shifted frame of ASCII characters to create a shimmering effect."""
        random.seed(seed)
        clean_set = [c for c in char_set if c != " "]
        if not clean_set:
            return lines

        perturbed_lines = []
        for line in lines:
            new_chars = []
            for char in line:
                if char in clean_set and random.random() < probability:
                    idx = clean_set.index(char)
                    # cycle characters
                    new_char = clean_set[(idx + 1) % len(clean_set)]
                    new_chars.append(new_char)
                else:
                    new_chars.append(char)
            perturbed_lines.append("".join(new_chars))
        return perturbed_lines

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
        grad.add_stop_color(0, self.palette["terminal"])
        grad.add_stop_color(1, self.palette["background"])
        defs.add(grad)

        # Glow filter (fix double spaces in color matrix)
        glow_filter = dwg.filter(id="glow", x="-30%", y="-30%", width="160%", height="160%")
        glow_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation=f"{self.config.glow_intensity}", result="blur")
        glow_filter.feColorMatrix(type="matrix", values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1.7 0", result="glow")
        defs.add(glow_filter)

        # Noise filter (fix double spaces in color matrix)
        noise_filter = dwg.filter(id="noise", x="0", y="0", width="100%", height="100%")
        noise_filter.feTurbulence(type="fractalNoise", baseFrequency="0.8", numOctaves="2", seed="3", result="noise")
        noise_filter.feColorMatrix(type="matrix", values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0.08 0")
        defs.add(noise_filter)

        # Main terminal frame group
        main_panel = dwg.g(id="main-terminal")
        # Soft shadow
        main_panel.add(dwg.rect(insert=(40, 38), size=(width - 80, height - 76), rx=24, ry=24, fill="none", stroke="#000000", stroke_width=4.0, opacity=0.3))
        # Glow border
        main_panel.add(dwg.rect(insert=(40, 38), size=(width - 80, height - 76), rx=24, ry=24, fill="none", stroke=self.palette["accent"], stroke_width=1.2, filter="url(#glow)", opacity=0.35))
        # Actual body
        main_panel.add(dwg.rect(insert=(40, 38), size=(width - 80, height - 76), rx=24, ry=24, fill=self.palette["terminal"], stroke=self.palette["border"], stroke_width=1.5))
        # Glassmorphism overlay
        main_panel.add(dwg.rect(insert=(40, 38), size=(width - 80, height - 76), rx=24, ry=24, fill="url(#grad)", opacity=0.18))

        # Title bar & macOS window buttons
        title_bar = dwg.g(id="title-bar")
        title_bar.add(dwg.circle(center=(70, 68), r=6, fill="#FF5F56"))
        title_bar.add(dwg.circle(center=(90, 68), r=6, fill="#FFBD2E"))
        title_bar.add(dwg.circle(center=(110, 68), r=6, fill="#27C93F"))
        # Window Address/Console header
        title_bar.add(dwg.rect(insert=(160, 54), size=(320, 24), rx=12, ry=12, fill=self.palette["background"], stroke=self.palette["border"], stroke_width=1))
        title_bar.add(dwg.text("animesh@developer-console: ~/resume", insert=(175, 70), fill=self.palette["muted"], font_size="11px", font_family=self.config.font_family))
        main_panel.add(title_bar)

        # ==========================================
        # LEFT REGION (ASCII CANVAS & CONSOLE)
        # ==========================================
        left_area = dwg.g(id="left-area")
        
        # Left Panel 1: ASCII Canvas
        left_area.add(dwg.rect(insert=(60, 100), size=(560, 380), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        left_area.add(dwg.text("LIVING ASCII PORTRAIT", insert=(80, 128), fill=self.palette["accent"], font_size="10px", font_weight="bold", font_family=self.config.font_family))
        left_area.add(dwg.line(start=(80, 136), end=(600, 136), stroke=self.palette["border"], stroke_width=1))

        # Generate three frames of character shifted ASCII for the morphing/living effect
        perturbed_1 = self.perturb_ascii(ascii_lines, self.config.ascii_chars, 0.25, seed=42)
        perturbed_2 = self.perturb_ascii(ascii_lines, self.config.ascii_chars, 0.25, seed=43)

        # Portrait dimensions: width of characters ~4.3px at 7.2px font-size.
        # Center in 560px width left panel. 90 chars * 4.3px = ~387px. Padding = (560 - 387)//2 = 86px.
        # x_start = 60 + 86 = 146.
        x_start = 146
        y_start = 158
        line_height = 6.4

        # Group A (Base Frame)
        port_a = dwg.g(id="ascii-portrait-a", class_="shimmer-a")
        for idx, line in enumerate(ascii_lines[:48]):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size="7.2px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_a.add(text_el)
        left_area.add(port_a)

        # Group B (Frame 2 - Shimmer Frame)
        port_b = dwg.g(id="ascii-portrait-b", class_="shimmer-b", opacity="0")
        for idx, line in enumerate(perturbed_1[:48]):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size="7.2px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_b.add(text_el)
        left_area.add(port_b)

        # Group C (Frame 3 - Shimmer Frame)
        port_c = dwg.g(id="ascii-portrait-c", class_="shimmer-c", opacity="0")
        for idx, line in enumerate(perturbed_2[:48]):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size="7.2px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_c.add(text_el)
        left_area.add(port_c)

        # Left Panel 2: Bottom left Console (Boot logs area)
        left_area.add(dwg.rect(insert=(60, 495), size=(560, 72), rx=12, ry=12, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Placeholder Group for boot sequence logs (populated by animate_terminal.py)
        boot_logs = dwg.g(id="boot-logs")
        left_area.add(boot_logs)
        main_panel.add(left_area)

        # ==========================================
        # RIGHT REGION (DEVELOPER DASHBOARD)
        # ==========================================
        right_panel = dwg.g(id="right-panel")
        right_panel.add(dwg.rect(insert=(635, 100), size=(285, 467), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Dashboard Header
        right_panel.add(dwg.text("DEVELOPER DASHBOARD", insert=(655, 128), fill=self.palette["accent"], font_size="10px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.line(start=(655, 136), end=(900, 136), stroke=self.palette["border"], stroke_width=1))

        # Personal Identity
        right_panel.add(dwg.text(self.config.developer_name, insert=(655, 164), fill=self.palette["text"], font_size="16px", font_weight="700", font_family=self.config.font_family))
        right_panel.add(dwg.text(self.config.role, insert=(655, 182), fill=self.palette["secondary"], font_size="10.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"📍 {self.config.location}", insert=(655, 198), fill=self.palette["muted"], font_size="9.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"🎓 {self.config.university}", insert=(655, 212), fill=self.palette["muted"], font_size="9.5px", font_family=self.config.font_family))
        
        # Section Divider
        right_panel.add(dwg.line(start=(655, 226), end=(900, 226), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Professional Experience
        right_panel.add(dwg.text("INTERNSHIPS", insert=(655, 246), fill=self.palette["accent"], font_size="9.5px", font_weight="bold", font_family=self.config.font_family))
        # Bluestock
        right_panel.add(dwg.text("• Bluestock Fintech", insert=(655, 264), fill=self.palette["text"], font_size="9.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text("  Software Developer Intern", insert=(655, 276), fill=self.palette["muted"], font_size="8.5px", font_family=self.config.font_family))
        # Infotact
        right_panel.add(dwg.text("• Infotact Solutions", insert=(655, 292), fill=self.palette["text"], font_size="9.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text("  AI/ML Developer Intern", insert=(655, 304), fill=self.palette["muted"], font_size="8.5px", font_family=self.config.font_family))

        # Core Projects
        right_panel.add(dwg.text("FEATURED PROJECTS", insert=(655, 326), fill=self.palette["accent"], font_size="9.5px", font_weight="bold", font_family=self.config.font_family))
        for p_idx, project in enumerate(self.config.projects[:3]):
            desc = "Advanced AI Systems Builder" if "NeuroPath" in project else "B2B Strategy Engine" if "Forge" in project else "Digital Twin Simulator"
            y_proj = 344 + p_idx * 26
            right_panel.add(dwg.text(f"• {project}", insert=(655, y_proj), fill=self.palette["highlight"], font_size="9.5px", font_family=self.config.font_family))
            right_panel.add(dwg.text(f"  {desc}", insert=(655, y_proj + 11), fill=self.palette["muted"], font_size="8.5px", font_family=self.config.font_family))

        # Skills & Tech
        right_panel.add(dwg.text("TECHNICAL SPECIALIZATION", insert=(655, 432), fill=self.palette["accent"], font_size="9.5px", font_weight="bold", font_family=self.config.font_family))
        langs_str = " • ".join(self.config.languages)
        frame_str = " • ".join(self.config.frameworks)
        right_panel.add(dwg.text(f"Langs: {langs_str}", insert=(655, 450), fill=self.palette["text"], font_size="9px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"Tools: {frame_str}", insert=(655, 462), fill=self.palette["text"], font_size="9px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"Focus: {self.config.status}", insert=(655, 474), fill=self.palette["secondary"], font_size="9px", font_family=self.config.font_family))

        # Divider
        right_panel.add(dwg.line(start=(655, 488), end=(900, 488), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Links/Socials
        right_panel.add(dwg.text(f"🌐 portfolio: {self.config.portfolio.replace('https://', '')}", insert=(655, 508), fill=self.palette["highlight"], font_size="9px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"🐱 github: github.com/{self.config.github.split('/')[-1]}", insert=(655, 520), fill=self.palette["highlight"], font_size="9px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"📧 email: {self.config.email}", insert=(655, 532), fill=self.palette["highlight"], font_size="9px", font_family=self.config.font_family))
        
        # Git stats horizontal meters
        right_panel.add(dwg.rect(insert=(655, 545), size=(245, 3), rx=1.5, ry=1.5, fill="#161B22"))
        right_panel.add(dwg.rect(insert=(655, 545), size=(180, 3), rx=1.5, ry=1.5, fill=self.palette["accent"]))
        right_panel.add(dwg.rect(insert=(655, 552), size=(245, 3), rx=1.5, ry=1.5, fill="#161B22"))
        right_panel.add(dwg.rect(insert=(655, 552), size=(140, 3), rx=1.5, ry=1.5, fill=self.palette["secondary"]))

        main_panel.add(right_panel)

        # ==========================================
        # OVERLAYS & SCANLINE (Pure SVG SMIL)
        # ==========================================
        scanline_group = dwg.g(id="scanline-group", opacity=0.22)
        scanline_rect = dwg.rect(insert=(40, 40), size=(width - 80, 4), fill="#ffffff", opacity=0.08)
        scanline_rect.add(svgwrite.animate.Animate("y", from_="40", to_="540", dur=f"{self.config.scanline_speed}s", repeatCount="indefinite"))
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
        dwg.add(dwg.rect(insert=(24, 24), size=(width - 48, height - 48), rx=24, ry=24, fill="#111827", stroke=self.palette["accent"], stroke_width=1.2))
        for index, line in enumerate(ascii_lines[:44]):
            y = 80 + index * 8
            text = dwg.text(line, insert=(70, y), fill=self.palette["text"], font_size="8px", font_family=self.config.font_family)
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
