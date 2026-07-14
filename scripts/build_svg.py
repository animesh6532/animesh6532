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

        # Glow filter
        glow_filter = dwg.filter(id="glow", x="-30%", y="-30%", width="160%", height="160%")
        glow_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation=f"{self.config.glow_intensity}", result="blur")
        glow_filter.feColorMatrix(type="matrix", values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1.7 0", result="glow")
        defs.add(glow_filter)

        # Noise filter
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
        title_bar.add(dwg.rect(insert=(160, 54), size=(340, 24), rx=12, ry=12, fill=self.palette["background"], stroke=self.palette["border"], stroke_width=1))
        title_bar.add(dwg.text("animesh@developer-console: ~/profile", insert=(175, 70), fill=self.palette["muted"], font_size="11px", font_family=self.config.font_family))
        main_panel.add(title_bar)

        # ==========================================
        # LEFT REGION: 70% WIDTH - HUGE ASCII PORTRAIT
        # ==========================================
        left_area = dwg.g(id="left-area")
        left_panel_w = self.config.left_panel_width
        
        left_area.add(dwg.rect(insert=(60, 100), size=(left_panel_w, 370), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        left_area.add(dwg.text("HUGE LIVING ASCII PORTRAIT", insert=(80, 128), fill=self.palette["accent"], font_size="10px", font_weight="bold", font_family=self.config.font_family))
        left_area.add(dwg.line(start=(80, 136), end=(60 + left_panel_w - 20, 136), stroke=self.palette["border"], stroke_width=1))

        # Generate three frames of character shifted ASCII for the morphing/living effect
        perturbed_1 = self.perturb_ascii(ascii_lines, self.config.ascii_chars, 0.25, seed=42)
        perturbed_2 = self.perturb_ascii(ascii_lines, self.config.ascii_chars, 0.25, seed=43)

        # Portrait dimensions: width of characters ~5.1px at 8.5px font-size.
        # Center in Left panel. 90 chars * 5.1px = ~459px. Padding = (left_panel_w - 459)//2.
        x_start = 60 + (left_panel_w - 459) // 2
        y_start = 152
        line_height = 6.4

        # Group A (Base Frame)
        port_a = dwg.g(id="ascii-portrait-a", class_="shimmer-a")
        for idx, line in enumerate(ascii_lines[:48]):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size="8.5px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_a.add(text_el)
        left_area.add(port_a)

        # Group B (Frame 2 - Shimmer Frame)
        port_b = dwg.g(id="ascii-portrait-b", class_="shimmer-b", opacity="0")
        for idx, line in enumerate(perturbed_1[:48]):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size="8.5px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_b.add(text_el)
        left_area.add(port_b)

        # Group C (Frame 3 - Shimmer Frame)
        port_c = dwg.g(id="ascii-portrait-c", class_="shimmer-c", opacity="0")
        for idx, line in enumerate(perturbed_2[:48]):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size="8.5px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_c.add(text_el)
        left_area.add(port_c)

        main_panel.add(left_area)

        # ==========================================
        # RIGHT REGION: 30% WIDTH - DEVELOPER DASHBOARD
        # ==========================================
        right_panel = dwg.g(id="right-panel")
        right_panel_w = self.config.right_panel_width
        right_x = 60 + left_panel_w + 15
        
        right_panel.add(dwg.rect(insert=(right_x, 100), size=(right_panel_w, 370), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Dashboard Header
        right_panel.add(dwg.text("DEVELOPER DASHBOARD", insert=(right_x + 15, 128), fill=self.palette["accent"], font_size="9.5px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.line(start=(right_x + 15, 136), end=(right_x + right_panel_w - 15, 136), stroke=self.palette["border"], stroke_width=1))

        # Personal Identity
        right_panel.add(dwg.text(self.config.developer_name, insert=(right_x + 15, 158), fill=self.palette["text"], font_size="15px", font_weight="700", font_family=self.config.font_family))
        right_panel.add(dwg.text(self.config.role, insert=(right_x + 15, 174), fill=self.palette["secondary"], font_size="9.5px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"📍 {self.config.location}", insert=(right_x + 15, 188), fill=self.palette["muted"], font_size="8.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"🎓 {self.config.university}", insert=(right_x + 15, 200), fill=self.palette["muted"], font_size="8.5px", font_family=self.config.font_family))
        
        # Section Divider
        right_panel.add(dwg.line(start=(right_x + 15, 212), end=(right_x + right_panel_w - 15, 212), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Internship Experience
        right_panel.add(dwg.text("EXPERIENCE", insert=(right_x + 15, 228), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.text("• Bluestock Fintech (Intern)", insert=(right_x + 15, 244), fill=self.palette["text"], font_size="8.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text("• Infotact Solutions (Intern)", insert=(right_x + 15, 256), fill=self.palette["text"], font_size="8.5px", font_family=self.config.font_family))

        # Core Projects
        right_panel.add(dwg.text("PROJECTS", insert=(right_x + 15, 276), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        for p_idx, project in enumerate(self.config.projects[:3]):
            y_proj = 292 + p_idx * 12
            right_panel.add(dwg.text(f"• {project}", insert=(right_x + 15, y_proj), fill=self.palette["highlight"], font_size="8.5px", font_family=self.config.font_family))

        # Tech Specialization
        right_panel.add(dwg.text("SPECIALIZATION", insert=(right_x + 15, 336), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        langs_str = " • ".join(self.config.languages[:3])
        frame_str = " • ".join(self.config.frameworks[:3])
        right_panel.add(dwg.text(f"Langs: {langs_str}", insert=(right_x + 15, 350), fill=self.palette["text"], font_size="8px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"Tools: {frame_str}", insert=(right_x + 15, 362), fill=self.palette["text"], font_size="8px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"Focus: {self.config.status}", insert=(right_x + 15, 374), fill=self.palette["secondary"], font_size="8px", font_family=self.config.font_family))

        # Divider
        right_panel.add(dwg.line(start=(right_x + 15, 386), end=(right_x + right_panel_w - 15, 386), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Links & Contact
        right_panel.add(dwg.text("LINKS & CONTACT", insert=(right_x + 15, 402), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"🌐 portfolio: animesh6532.netlify.app", insert=(right_x + 15, 416), fill=self.palette["highlight"], font_size="8px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"🐱 github: github.com/{self.config.github.split('/')[-1]}", insert=(right_x + 15, 428), fill=self.palette["highlight"], font_size="8px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"📧 email: {self.config.email}", insert=(right_x + 15, 440), fill=self.palette["highlight"], font_size="8px", font_family=self.config.font_family))
        
        # Git stats horizontal meters
        right_panel.add(dwg.rect(insert=(right_x + 15, 452), size=(right_panel_w - 30, 2), rx=1, ry=1, fill="#161B22"))
        right_panel.add(dwg.rect(insert=(right_x + 15, 452), size=(150, 2), rx=1, ry=1, fill=self.palette["accent"]))
        right_panel.add(dwg.rect(insert=(right_x + 15, 458), size=(right_panel_w - 30, 2), rx=1, ry=1, fill="#161B22"))
        right_panel.add(dwg.rect(insert=(right_x + 15, 458), size=(120, 2), rx=1, ry=1, fill=self.palette["secondary"]))

        main_panel.add(right_panel)

        # ==========================================
        # BOTTOM REGION: WIDE ANIMATED TERMINAL CONSOLE
        # ==========================================
        bottom_area = dwg.g(id="bottom-area")
        console_h = self.config.bottom_panel_height
        
        # Bottom Console Canvas (spans width under both panels: x=60, width=860)
        bottom_area.add(dwg.rect(insert=(60, 485), size=(860, console_h), rx=12, ry=12, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Console Header
        bottom_area.add(dwg.text("SYSTEM CONSOLE LOGS", insert=(80, 502), fill=self.palette["accent"], font_size="9.5px", font_weight="bold", font_family=self.config.font_family))
        bottom_area.add(dwg.line(start=(80, 508), end=(900, 508), stroke=self.palette["border"], stroke_width=1))

        # Placeholder Group for boot sequence logs
        boot_logs = dwg.g(id="boot-logs")
        bottom_area.add(boot_logs)
        main_panel.add(bottom_area)

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
