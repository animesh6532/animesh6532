from __future__ import annotations

import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config


class TerminalAnimator:
    """Injects premium SMIL and CSS animations into the terminal dashboard SVG."""

    def __init__(self, config) -> None:
        self.config = config
        self.logger = logging.getLogger("terminal-animator")
        # Register namespaces to prevent ET from outputting ns0: prefixes
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

    def animate(self) -> None:
        svg_path = self.config.output_terminal_path
        if not svg_path.exists():
            raise FileNotFoundError(f"Terminal SVG not found: {svg_path}")

        self.logger.info("Parsing SVG at %s", svg_path)
        tree = ET.parse(svg_path)
        root = tree.getroot()
        ns = {"svg": "http://www.w3.org/2000/svg"}

        # 1. Locate or create <defs>
        defs = root.find("svg:defs", ns)
        if defs is None:
            defs = ET.Element("{http://www.w3.org/2000/svg}defs")
            root.insert(0, defs)

        # 2. Inject CSS Stylesheet
        # Loop animation cycle duration is based on config.animation_speed
        cycle_dur = 2.0 * self.config.animation_speed
        delay_time = 2.5 * self.config.animation_speed

        style_content = f"""
        @keyframes crt-flicker {{
            0%, 100% {{ opacity: 0.99; }}
            50% {{ opacity: 0.98; }}
        }}
        @keyframes blink-cursor {{
            0%, 49% {{ opacity: 1; }}
            50%, 100% {{ opacity: 0; }}
        }}
        @keyframes border-pulse {{
            0% {{ stroke-opacity: 0.35; }}
            50% {{ stroke-opacity: 0.75; }}
            100% {{ stroke-opacity: 0.35; }}
        }}
        @keyframes shimmer-a {{
            0%, 19.9% {{ opacity: 1; }}
            20%, 100% {{ opacity: 0; }}
        }}
        @keyframes shimmer-b {{
            0%, 19.9% {{ opacity: 0; }}
            20%, 39.9% {{ opacity: 1; }}
            40%, 100% {{ opacity: 0; }}
        }}
        @keyframes shimmer-c {{
            0%, 39.9% {{ opacity: 0; }}
            40%, 59.9% {{ opacity: 1; }}
            60%, 100% {{ opacity: 0; }}
        }}
        @keyframes shimmer-d {{
            0%, 59.9% {{ opacity: 0; }}
            60%, 79.9% {{ opacity: 1; }}
            80%, 100% {{ opacity: 0; }}
        }}
        @keyframes shimmer-e {{
            0%, 79.9% {{ opacity: 0; }}
            80%, 99.9% {{ opacity: 1; }}
            100% {{ opacity: 0; }}
        }}
        @keyframes glow-pulse {{
            0% {{ opacity: 0.25; filter: drop-shadow(0 0 1px {self.palette_color('accent')}); }}
            50% {{ opacity: 0.65; filter: drop-shadow(0 0 4px {self.palette_color('accent')}); }}
            100% {{ opacity: 0.25; filter: drop-shadow(0 0 1px {self.palette_color('accent')}); }}
        }}
        @keyframes brightness-pulse {{
            0%, 100% {{ filter: brightness(0.98); }}
            50% {{ filter: brightness(1.05); }}
        }}

        /* Apply Animations */
        #main-terminal {{
            animation: crt-flicker 0.15s infinite, brightness-pulse 4s ease-in-out infinite;
        }}
        .blinking-cursor {{
            animation: blink-cursor {self.config.cursor_speed}s infinite;
        }}
        .pulse-border {{
            animation: border-pulse 4s ease-in-out infinite;
        }}
        .shimmer-a {{
            animation: shimmer-a {cycle_dur}s infinite steps(1);
            animation-delay: {delay_time}s;
        }}
        .shimmer-b {{
            animation: shimmer-b {cycle_dur}s infinite steps(1);
            animation-delay: {delay_time}s;
        }}
        .shimmer-c {{
            animation: shimmer-c {cycle_dur}s infinite steps(1);
            animation-delay: {delay_time}s;
        }}
        .shimmer-d {{
            animation: shimmer-d {cycle_dur}s infinite steps(1);
            animation-delay: {delay_time}s;
        }}
        .shimmer-e {{
            animation: shimmer-e {cycle_dur}s infinite steps(1);
            animation-delay: {delay_time}s;
        }}
        .portrait-glow-layer {{
            animation: glow-pulse 3s ease-in-out infinite alternate;
            animation-delay: {delay_time + 0.1}s;
        }}
        """
        style_el = ET.Element("{http://www.w3.org/2000/svg}style")
        style_el.text = style_content
        defs.append(style_el)

        # 3. Create Clipping Paths for Console Logs (Bottom console: y=675, height=100)
        boot_timeline = [
            # Group 1 (y = 715, 727, 739, 751)
            ("Booting Developer Console...", 0.0, 0.4),
            ("Loading Developer Profile...", 0.4, 0.4),
            ("Loading Projects...", 0.8, 0.4),
            ("Loading GitHub Data...", 1.2, 0.4),
            # Group 2 (y = 715, 727)
            ("Rendering ASCII Portrait...", 1.8, 0.4),
            ("Dashboard Ready.", 2.2, 0.4)
        ]

        # Inject clip paths for boot lines
        for idx, (text_str, start, dur) in enumerate(boot_timeline):
            clip_id = f"boot-clip-{idx}"
            clip_path = ET.Element("{http://www.w3.org/2000/svg}clipPath", attrib={"id": clip_id})
            
            row_idx = idx % 4
            y_pos = 715 + row_idx * 12
            rect = ET.Element("{http://www.w3.org/2000/svg}rect", attrib={
                "x": "80",
                "y": str(y_pos - 10),
                "width": "0",
                "height": "14"
            })
            
            begin_time = f"{start * self.config.typing_speed}s"
            anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "width",
                "from": "0",
                "to": "450",
                "dur": f"{dur * self.config.typing_speed}s",
                "begin": begin_time,
                "fill": "freeze"
            })
            rect.append(anim)
            clip_path.append(rect)
            defs.append(clip_path)

        # ClipPath for Console final prompt (types from 2.6s to 3.2s on Row 2: y = 739)
        prompt_clip = ET.Element("{http://www.w3.org/2000/svg}clipPath", attrib={"id": "prompt-clip"})
        prompt_rect = ET.Element("{http://www.w3.org/2000/svg}rect", attrib={
            "x": "80",
            "y": "729",
            "width": "0",
            "height": "16"
        })
        prompt_begin = f"{2.6 * self.config.animation_speed}s"
        prompt_dur = f"{0.6 * self.config.typing_speed}s"
        prompt_anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
            "attributeName": "width",
            "from": "0",
            "to": "450",
            "dur": prompt_dur,
            "begin": prompt_begin,
            "fill": "freeze"
        })
        prompt_rect.append(prompt_anim)
        prompt_clip.append(prompt_rect)
        defs.append(prompt_clip)

        # 4. Populate and Animate Boot Logs
        boot_logs_g = root.find(".//svg:g[@id='boot-logs']", ns)
        if boot_logs_g is not None:
            # Subgroup 1: Boot Logs Group 1 (fades out at 1.7s)
            g1 = ET.Element("{http://www.w3.org/2000/svg}g", attrib={"id": "boot-group-1"})
            g1_fade = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "opacity",
                "from": "1",
                "to": "0",
                "dur": "0.15s",
                "begin": f"{1.7 * self.config.animation_speed}s",
                "fill": "freeze"
            })
            g1.append(g1_fade)
            
            # Subgroup 2: Boot Logs Group 2 (does NOT fade out, stays on screen!)
            g2 = ET.Element("{http://www.w3.org/2000/svg}g", attrib={"id": "boot-group-2"})

            boot_logs_g.append(g1)
            boot_logs_g.append(g2)

            # Insert texts into groups
            for idx, (text_str, start, dur) in enumerate(boot_timeline):
                row_idx = idx % 4
                y_pos = 715 + row_idx * 12
                text_el = ET.Element("{http://www.w3.org/2000/svg}text", attrib={
                    "x": "80",
                    "y": str(y_pos),
                    "fill": self.palette_color("text"),
                    "font-size": "9.5px",
                    "font-family": self.config.font_family,
                    "clip-path": f"url(#boot-clip-{idx})",
                    "opacity": "0"
                })
                
                # Apply colors
                if idx == 0 or idx == 4:
                    text_el.set("fill", self.palette_color("accent"))
                elif idx == 5:
                    text_el.set("fill", self.palette_color("green"))

                text_el.text = text_str
                
                # Make visible
                vis_anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                    "attributeName": "opacity",
                    "from": "0",
                    "to": "1",
                    "dur": "0.01s",
                    "begin": f"{start * self.config.typing_speed}s",
                    "fill": "freeze"
                })
                text_el.append(vis_anim)

                if idx < 4:
                    g1.append(text_el)
                else:
                    g2.append(text_el)

            # 5. Populate and Animate Interactive Console Prompt (Row 2: y = 739)
            prompt_text_el = ET.Element("{http://www.w3.org/2000/svg}text", attrib={
                "x": "80",
                "y": "739",
                "fill": self.palette_color("accent"),
                "font-size": "9.5px",
                "font-family": self.config.font_family,
                "clip-path": "url(#prompt-clip)",
                "opacity": "0"
            })
            prompt_text_el.text = "guest@animesh6532:~$ python -m profile_dashboard"
            
            prompt_vis = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "opacity",
                "from": "0",
                "to": "1",
                "dur": "0.01s",
                "begin": prompt_begin,
                "fill": "freeze"
            })
            prompt_text_el.append(prompt_vis)
            g2.append(prompt_text_el)

            # Blinking cursor block: █
            cursor_el = ET.Element("{http://www.w3.org/2000/svg}text", attrib={
                "x": "188",
                "y": "739",
                "fill": self.palette_color("green"),
                "font-size": "9.5px",
                "font-family": self.config.font_family,
                "class": "blinking-cursor",
                "opacity": "0"
            })
            cursor_el.text = "█"
            
            cursor_vis = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "opacity",
                "from": "0",
                "to": "1",
                "dur": "0.01s",
                "begin": prompt_begin,
                "fill": "freeze"
            })
            cursor_el.append(cursor_vis)
            
            cursor_move = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "x",
                "from": "188",
                "to": "340",
                "dur": prompt_dur,
                "begin": prompt_begin,
                "fill": "freeze"
            })
            cursor_el.append(cursor_move)
            g2.append(cursor_el)

        # 6. Duplicate and Animate Portrait Layers (Glow base uses A)
        stagger_start = 1.45 * self.config.animation_speed
        
        left_area = root.find(".//svg:g[@id='left-area']", ns)
        if left_area is not None:
            # Create a glow copy under the portrait layers
            glow_layer = ET.Element("{http://www.w3.org/2000/svg}g", attrib={
                "id": "ascii-portrait-glow",
                "class": "portrait-glow-layer",
                "opacity": "0"
            })
            
            glow_fade = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "opacity",
                "from": "0",
                "to": "0.45",
                "dur": "0.6s",
                "begin": f"{(stagger_start + 0.8) * self.config.animation_speed}s",
                "fill": "freeze"
            })
            glow_layer.append(glow_fade)

            # Copy characters from Group A to build glow base
            port_a = left_area.find(".//svg:g[@id='ascii-portrait-a']", ns)
            if port_a is not None:
                for text_el in list(port_a):
                    cloned_el = ET.Element("{http://www.w3.org/2000/svg}text", attrib=text_el.attrib)
                    cloned_el.text = text_el.text
                    glow_layer.append(cloned_el)

                # Insert glow layer before Group A
                for index, child in enumerate(left_area):
                    if child.attrib.get("id") == "ascii-portrait-a":
                        left_area.insert(index, glow_layer)
                        break

        # Stagger fade-in of rows in Group A
        port_a = root.find(".//svg:g[@id='ascii-portrait-a']", ns)
        if port_a is not None:
            rows = port_a.findall("svg:text", ns)
            for r_idx, row in enumerate(rows):
                row.set("opacity", "0")
                row_delay = stagger_start + r_idx * 0.012 * self.config.animation_speed
                row_fade = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                    "attributeName": "opacity",
                    "from": "0",
                    "to": "1",
                    "dur": "0.15s",
                    "begin": f"{row_delay}s",
                    "fill": "freeze"
                })
                row.append(row_fade)

        # 7. Animate Right Panel Content Loading (Fades in at t=2.3s)
        right_panel = root.find(".//svg:g[@id='right-panel']", ns)
        if right_panel is not None:
            children = list(right_panel)
            bg_rect = None
            for child in children:
                if child.tag == "{http://www.w3.org/2000/svg}rect" and child.attrib.get("rx") == "16":
                    bg_rect = child
                    break

            content_g = ET.Element("{http://www.w3.org/2000/svg}g", attrib={
                "id": "right-panel-content",
                "opacity": "0"
            })
            
            fade_time = f"{2.3 * self.config.animation_speed}s"
            fade_anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "opacity",
                "from": "0",
                "to": "1",
                "dur": "0.6s",
                "begin": fade_time,
                "fill": "freeze"
            })
            content_g.append(fade_anim)
            
            slide_anim = ET.Element("{http://www.w3.org/2000/svg}animateTransform", attrib={
                "attributeName": "transform",
                "type": "translate",
                "from": "0 15",
                "to": "0 0",
                "dur": "0.6s",
                "begin": fade_time,
                "fill": "freeze"
            })
            content_g.append(slide_anim)

            # Move children into content group
            for child in children:
                if child is not bg_rect:
                    right_panel.remove(child)
                    content_g.append(child)
            right_panel.append(content_g)

        # 8. Add Pulse Animation to Glow Borders
        main_terminal = root.find(".//svg:g[@id='main-terminal']", ns)
        if main_terminal is not None:
            for rect in main_terminal.findall("svg:rect", ns):
                if rect.attrib.get("filter") == "url(#glow)":
                    rect.set("class", "pulse-border")

        # Write output back to SVG file
        self.logger.info("Writing updated SVG with animations to %s", svg_path)
        tree.write(svg_path, encoding="utf-8", xml_declaration=True)
        self.logger.info("SVG Animation Injection Complete!")

    def palette_color(self, name: str) -> str:
        """Retrieves hex color code from active theme palette."""
        from config import THEMES
        palette = THEMES.get(self.config.theme, THEMES["tokyo_night"])
        return palette.get(name, "#ffffff")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = load_config()
    animator = TerminalAnimator(config)
    try:
        animator.animate()
    except Exception as e:
        logging.error("Failed to inject animations: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
