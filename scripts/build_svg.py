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

    def perturb_ascii(self, lines: List[str], seed: int = 42) -> List[str]:
        """Generates a slightly shifted frame of ASCII characters by morphing a small percentage of characters."""
        random.seed(seed)
        morph_seq = ["@", "%", "#", "*", "+", "-"]
        # 1.5% morph rate
        change_rate = 0.015
        
        perturbed_lines = []
        for line in lines:
            new_chars = []
            for char in line:
                if char in morph_seq and random.random() < change_rate:
                    idx = morph_seq.index(char)
                    new_char = morph_seq[(idx + 1) % len(morph_seq)]
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
        glow_filter.fefeGaussianBlur = glow_filter.feGaussianBlur(in_="SourceGraphic", stdDeviation=f"{self.config.glow_intensity}", result="blur")
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
        left_panel_h = self.config.left_panel_height
        
        # Panel Background
        left_area.add(dwg.rect(insert=(60, 100), size=(left_panel_w, left_panel_h), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))

        # Generate 5 frames of character shifted ASCII for the morphing/living effect
        frame1 = ascii_lines
        frame2 = self.perturb_ascii(frame1, seed=101)
        frame3 = self.perturb_ascii(frame2, seed=102)
        frame4 = self.perturb_ascii(frame3, seed=103)
        frame5 = self.perturb_ascii(frame4, seed=104)

        # Compute dynamic font-size and alignment
        char_width = self.config.ascii_char_width_ratio * self.config.ascii_font_size
        line_height = self.config.ascii_line_height
        font_size = self.config.ascii_font_size

        portrait_w_px = len(ascii_lines[0]) * char_width if ascii_lines else 0
        portrait_h_px = len(ascii_lines) * line_height

        x_start = 60 + (left_panel_w - portrait_w_px) // 2
        y_start = 100 + (left_panel_h - portrait_h_px) // 2

        # Group A (Frame 1)
        port_a = dwg.g(id="ascii-portrait-a", class_="shimmer-a")
        for idx, line in enumerate(frame1):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size=f"{font_size}px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_a.add(text_el)
        left_area.add(port_a)

        # Group B (Frame 2)
        port_b = dwg.g(id="ascii-portrait-b", class_="shimmer-b", opacity="0")
        for idx, line in enumerate(frame2):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size=f"{font_size}px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_b.add(text_el)
        left_area.add(port_b)

        # Group C (Frame 3)
        port_c = dwg.g(id="ascii-portrait-c", class_="shimmer-c", opacity="0")
        for idx, line in enumerate(frame3):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size=f"{font_size}px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_c.add(text_el)
        left_area.add(port_c)

        # Group D (Frame 4)
        port_d = dwg.g(id="ascii-portrait-d", class_="shimmer-d", opacity="0")
        for idx, line in enumerate(frame4):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size=f"{font_size}px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_d.add(text_el)
        left_area.add(port_d)

        # Group E (Frame 5)
        port_e = dwg.g(id="ascii-portrait-e", class_="shimmer-e", opacity="0")
        for idx, line in enumerate(frame5):
            y_pos = y_start + idx * line_height
            text_el = dwg.text(line, insert=(x_start, y_pos), fill=self.palette["text"], font_size=f"{font_size}px", font_family=self.config.font_family)
            text_el["xml:space"] = "preserve"
            port_e.add(text_el)
        left_area.add(port_e)

        main_panel.add(left_area)

        # ==========================================
        # RIGHT REGION: 30% WIDTH - DEVELOPER DASHBOARD
        # ==========================================
        right_panel = dwg.g(id="right-panel")
        right_panel_w = self.config.right_panel_width
        right_panel_h = self.config.right_panel_height
        right_x = 60 + left_panel_w + 15
        
        right_panel.add(dwg.rect(insert=(right_x, 100), size=(right_panel_w, right_panel_h), rx=16, ry=16, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Dashboard Header
        right_panel.add(dwg.text("DEVELOPER DASHBOARD", insert=(right_x + 15, 128), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.line(start=(right_x + 15, 136), end=(right_x + right_panel_w - 15, 136), stroke=self.palette["border"], stroke_width=1))

        # Personal Identity
        right_panel.add(dwg.text(self.config.developer_name, insert=(right_x + 15, 160), fill=self.palette["text"], font_size="15px", font_weight="700", font_family=self.config.font_family))
        right_panel.add(dwg.text(self.config.role, insert=(right_x + 15, 176), fill=self.palette["secondary"], font_size="9.5px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"📍 {self.config.location}", insert=(right_x + 15, 190), fill=self.palette["muted"], font_size="9px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"🎓 {self.config.university}", insert=(right_x + 15, 202), fill=self.palette["muted"], font_size="9px", font_family=self.config.font_family))
        
        # Section Divider
        right_panel.add(dwg.line(start=(right_x + 15, 216), end=(right_x + right_panel_w - 15, 216), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Internship Experience
        right_panel.add(dwg.text("EXPERIENCE", insert=(right_x + 15, 232), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.text("• Bluestock Fintech (Intern)", insert=(right_x + 15, 248), fill=self.palette["text"], font_size="9px", font_family=self.config.font_family))
        right_panel.add(dwg.text("• Infotact Solutions (Intern)", insert=(right_x + 15, 260), fill=self.palette["text"], font_size="9px", font_family=self.config.font_family))

        # Divider
        right_panel.add(dwg.line(start=(right_x + 15, 274), end=(right_x + right_panel_w - 15, 274), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Featured Projects
        right_panel.add(dwg.text("FEATURED PROJECTS", insert=(right_x + 15, 290), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        for p_idx, project in enumerate(self.config.projects[:3]):
            y_proj = 306 + p_idx * 12
            right_panel.add(dwg.text(f"• {project}", insert=(right_x + 15, y_proj), fill=self.palette["highlight"], font_size="9px", font_family=self.config.font_family))

        # Divider
        right_panel.add(dwg.line(start=(right_x + 15, 344), end=(right_x + right_panel_w - 15, 344), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Core Skills / Specialization
        right_panel.add(dwg.text("CORE SKILLS", insert=(right_x + 15, 360), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        langs_str = " • ".join(self.config.languages)
        frame_str = " • ".join(self.config.frameworks)
        right_panel.add(dwg.text(f"Langs: {langs_str}", insert=(right_x + 15, 376), fill=self.palette["text"], font_size="8.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"Tech: {frame_str}", insert=(right_x + 15, 388), fill=self.palette["text"], font_size="8.5px", font_family=self.config.font_family))

        # Divider
        right_panel.add(dwg.line(start=(right_x + 15, 402), end=(right_x + right_panel_w - 15, 402), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Current Focus
        right_panel.add(dwg.text("CURRENT FOCUS", insert=(right_x + 15, 418), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.text(self.config.status, insert=(right_x + 15, 434), fill=self.palette["secondary"], font_size="8.5px", font_family=self.config.font_family))

        # Divider
        right_panel.add(dwg.line(start=(right_x + 15, 448), end=(right_x + right_panel_w - 15, 448), stroke=self.palette["border"], stroke_width=0.8, stroke_dasharray="4 4"))

        # Contact
        right_panel.add(dwg.text("LINKS & CONTACT", insert=(right_x + 15, 464), fill=self.palette["accent"], font_size="9px", font_weight="bold", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"🌐 portfolio: animesh6532.netlify.app", insert=(right_x + 15, 480), fill=self.palette["highlight"], font_size="8.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"🐱 github: github.com/animesh6532", insert=(right_x + 15, 492), fill=self.palette["highlight"], font_size="8.5px", font_family=self.config.font_family))
        right_panel.add(dwg.text(f"📧 email: {self.config.email}", insert=(right_x + 15, 504), fill=self.palette["highlight"], font_size="8.5px", font_family=self.config.font_family))
        
        # Git stats horizontal meters
        right_panel.add(dwg.rect(insert=(right_x + 15, 524), size=(right_panel_w - 30, 2), rx=1, ry=1, fill="#161B22"))
        right_panel.add(dwg.rect(insert=(right_x + 15, 524), size=(160, 2), rx=1, ry=1, fill=self.palette["accent"]))
        right_panel.add(dwg.rect(insert=(right_x + 15, 532), size=(right_panel_w - 30, 2), rx=1, ry=1, fill="#161B22"))
        right_panel.add(dwg.rect(insert=(right_x + 15, 532), size=(130, 2), rx=1, ry=1, fill=self.palette["secondary"]))

        main_panel.add(right_panel)

        # ==========================================
        # BOTTOM REGION: WIDE ANIMATED TERMINAL CONSOLE
        # ==========================================
        bottom_area = dwg.g(id="bottom-area")
        console_h = self.config.bottom_panel_height
        
        # Bottom Console Canvas (spans width under both panels: x=60, width=860)
        bottom_area.add(dwg.rect(insert=(60, 675), size=(860, console_h), rx=12, ry=12, fill=self.palette["panel"], stroke=self.palette["border"], stroke_width=1.2))
        
        # Console Header
        bottom_area.add(dwg.text("SYSTEM CONSOLE LOGS", insert=(80, 692), fill=self.palette["accent"], font_size="9.5px", font_weight="bold", font_family=self.config.font_family))
        bottom_area.add(dwg.line(start=(80, 698), end=(900, 698), stroke=self.palette["border"], stroke_width=1))

        # Placeholder Group for boot sequence logs
        boot_logs = dwg.g(id="boot-logs")
        bottom_area.add(boot_logs)
        main_panel.add(bottom_area)

        # ==========================================
        # OVERLAYS & SCANLINE (Pure SVG SMIL)
        # ==========================================
        scanline_group = dwg.g(id="scanline-group", opacity=0.22)
        scanline_rect = dwg.rect(insert=(40, 40), size=(width - 80, 4), fill="#ffffff", opacity=0.08)
        scanline_rect.add(svgwrite.animate.Animate("y", from_="40", to_=str(height - 40), dur=f"{self.config.scanline_speed}s", repeatCount="indefinite"))
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
        for index, line in enumerate(ascii_lines):
            y = 80 + index * 7
            text = dwg.text(line, insert=(70, y), fill=self.palette["text"], font_size="7.5px", font_family=self.config.font_family)
            text["xml:space"] = "preserve"
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
