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

        # 1. Locate <defs> and inject Stylesheet & ClipPaths
        defs = root.find("svg:defs", ns)
        if defs is None:
            defs = ET.Element("{http://www.w3.org/2000/svg}defs")
            root.insert(0, defs)

        # CSS Stylesheet
        style_content = """
        @keyframes crt-flicker {
            0% { opacity: 0.988; }
            50% { opacity: 0.998; }
            100% { opacity: 0.988; }
        }
        @keyframes blink-cursor {
            0%, 49% { opacity: 1; }
            50%, 100% { opacity: 0; }
        }
        @keyframes border-pulse {
            0% { stroke-opacity: 0.35; }
            50% { stroke-opacity: 0.75; }
            100% { stroke-opacity: 0.35; }
        }
        @keyframes portrait-glow {
            0% { opacity: 0.35; filter: drop-shadow(0 0 1px #00F7FF); }
            50% { opacity: 0.85; filter: drop-shadow(0 0 5px #00F7FF); }
            100% { opacity: 0.35; filter: drop-shadow(0 0 1px #00F7FF); }
        }
        
        /* Apply animations */
        #main-terminal {
            animation: crt-flicker 0.18s infinite;
        }
        .blinking-cursor {
            animation: blink-cursor 0.8s infinite;
        }
        .pulse-border {
            animation: border-pulse 4s ease-in-out infinite;
        }
        .glowing-portrait {
            animation: portrait-glow 3s ease-in-out infinite;
        }
        """
        style_el = ET.Element("{http://www.w3.org/2000/svg}style")
        style_el.text = style_content
        defs.append(style_el)

        # 2. Add ClipPaths for Boot Logs & Prompt Typing Animations
        # Boot Logs: 7 lines, spaced 20px apart starting at y=160.
        boot_lines = [
            "> Booting Terminal...",
            "Loading Environment...",
            "Loading AI Modules...",
            "Loading GitHub Data...",
            "Rendering ASCII Portrait...",
            "Loading Metrics...",
            "System Ready."
        ]
        
        # Add boot log clipping paths (starts at 0 width and expands to 300)
        # Delay timeline (seconds): each boot line takes 0.25s, starts at idx * 0.3s
        for idx in range(len(boot_lines)):
            clip_id = f"boot-clip-{idx}"
            clip_path = ET.Element("{http://www.w3.org/2000/svg}clipPath", attrib={"id": clip_id})
            
            y_pos = 160 + idx * 20
            rect = ET.Element("{http://www.w3.org/2000/svg}rect", attrib={
                "x": "315",
                "y": str(y_pos - 12),
                "width": "0",
                "height": "16"
            })
            
            begin_time = f"{idx * 0.28 * self.config.animation_speed}s"
            anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "width",
                "from": "0",
                "to": "300",
                "dur": "0.22s",
                "begin": begin_time,
                "fill": "freeze"
            })
            rect.append(anim)
            clip_path.append(rect)
            defs.append(clip_path)

        # ClipPath for Command Prompt typing animation (Types from 2.2s to 2.8s)
        prompt_clip = ET.Element("{http://www.w3.org/2000/svg}clipPath", attrib={"id": "prompt-clip"})
        prompt_rect = ET.Element("{http://www.w3.org/2000/svg}rect", attrib={
            "x": "315",
            "y": "452",
            "width": "0",
            "height": "20"
        })
        prompt_begin = f"{len(boot_lines) * 0.28 * self.config.animation_speed + 0.1}s"
        prompt_dur = f"{0.5 * self.config.animation_speed}s"
        prompt_anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
            "attributeName": "width",
            "from": "0",
            "to": "320",
            "dur": prompt_dur,
            "begin": prompt_begin,
            "fill": "freeze"
        })
        prompt_rect.append(prompt_anim)
        prompt_clip.append(prompt_rect)
        defs.append(prompt_clip)

        # 3. Animate Boot Logs Group
        boot_logs_g = root.find(".//svg:g[@id='boot-logs']", ns)
        if boot_logs_g is not None:
            # Let the entire boot logs group fade out once system is ready (at 2.2 seconds)
            fade_begin = f"{(len(boot_lines) * 0.28) * self.config.animation_speed}s"
            fade_anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "opacity",
                "from": "1",
                "to": "0",
                "dur": "0.2s",
                "begin": fade_begin,
                "fill": "freeze"
            })
            boot_logs_g.append(fade_anim)

            # Add the boot lines
            for idx, text_str in enumerate(boot_lines):
                y_pos = 160 + idx * 20
                text_el = ET.Element("{http://www.w3.org/2000/svg}text", attrib={
                    "insert": f"315, {y_pos}",  # Standard ET insert translation fallback
                    "x": "315",
                    "y": str(y_pos),
                    "fill": self.config.ascii_chars and "#E6EDF3" or "#58A6FF",
                    "font-size": "11px",
                    "font-family": "JetBrains Mono, Fira Code, Courier New, monospace",
                    "clip-path": f"url(#boot-clip-{idx})",
                    "opacity": "0"
                })
                # Set text color accenting
                if idx == 0:
                    text_el.set("fill", "#00F7FF")  # Cyan for booting
                elif idx == len(boot_lines) - 1:
                    text_el.set("fill", "#22C55E")  # Green for system ready
                
                text_el.text = text_str
                
                # Make text visible when it starts typing
                vis_begin = f"{idx * 0.28 * self.config.animation_speed}s"
                vis_anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                    "attributeName": "opacity",
                    "from": "0",
                    "to": "1",
                    "dur": "0.01s",
                    "begin": vis_begin,
                    "fill": "freeze"
                })
                text_el.append(vis_anim)
                boot_logs_g.append(text_el)

        # 4. Animate Interactive Command Prompt
        prompt_g = root.find(".//svg:g[@id='interactive-prompt']", ns)
        if prompt_g is not None:
            # Command Prompt: guest@animesh:~$ python -m profile
            # X coordinate for text is 315. Prompt prefix takes 17 characters.
            # Total width of characters at 11px font size is ~6.6px per character.
            # 17 chars * 6.6px = ~112px.
            # Total command length = 35 chars * 6.6px = ~231px.
            prompt_text_el = ET.Element("{http://www.w3.org/2000/svg}text", attrib={
                "x": "315",
                "y": "466",
                "fill": "#00F7FF",
                "font-size": "11px",
                "font-family": "JetBrains Mono, Fira Code, Courier New, monospace",
                "clip-path": "url(#prompt-clip)",
                "opacity": "0"
            })
            prompt_text_el.text = "guest@animesh6532:~$ python -m profile"
            
            # Make prompt visible when it starts typing
            prompt_vis_anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "opacity",
                "from": "0",
                "to": "1",
                "dur": "0.01s",
                "begin": prompt_begin,
                "fill": "freeze"
            })
            prompt_text_el.append(prompt_vis_anim)
            prompt_g.append(prompt_text_el)

            # Blinking cursor block: █
            # Starting x = 315 + 18*6.6 = 434 (follows the typed command)
            # Ending x = 315 + 38*6.6 = 566
            cursor_el = ET.Element("{http://www.w3.org/2000/svg}text", attrib={
                "x": "434",
                "y": "466",
                "fill": "#22C55E",
                "font-size": "11px",
                "font-family": "JetBrains Mono, Fira Code, Courier New, monospace",
                "class": "blinking-cursor",
                "opacity": "0"
            })
            cursor_el.text = "█"
            
            # Cursor opacity timeline: show up at prompt_begin
            cursor_vis = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "opacity",
                "from": "0",
                "to": "1",
                "dur": "0.01s",
                "begin": prompt_begin,
                "fill": "freeze"
            })
            cursor_el.append(cursor_vis)
            
            # Cursor position translation animation
            cursor_move = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                "attributeName": "x",
                "from": "434",
                "to": "566",
                "dur": prompt_dur,
                "begin": prompt_begin,
                "fill": "freeze"
            })
            cursor_el.append(cursor_move)
            
            prompt_g.append(cursor_el)

        # 5. Stagger ASCII Portrait Row Rendering
        portrait_g = root.find(".//svg:g[@id='ascii-portrait']", ns)
        if portrait_g is not None:
            # Initially hide the ASCII portrait group, starts drawing after boot sequence finishes (e.g. 2.2 seconds)
            portrait_start_delay = (len(boot_lines) * 0.28) * self.config.animation_speed
            
            # Find parent element to insert glowing background copy
            parent_el = root.find(".//svg:g[@id='center-panel']", ns)
            if parent_el is not None:
                # Duplicate the portrait group to create a glowing base layer underneath
                glow_portrait_g = ET.Element("{http://www.w3.org/2000/svg}g", attrib={
                    "id": "ascii-portrait-glow",
                    "class": "glowing-portrait",
                    "opacity": "0"
                })
                # Add the fade-in delay for glow layer (enable at t = 3.3s, once all rows finish rendering)
                glow_enable_time = f"{portrait_start_delay + 1.0}s"
                glow_fade = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                    "attributeName": "opacity",
                    "from": "0",
                    "to": "0.6",
                    "dur": "0.5s",
                    "begin": glow_enable_time,
                    "fill": "freeze"
                })
                glow_portrait_g.append(glow_fade)

                # Clone text children of portrait_g into glow_portrait_g
                for text_child in list(portrait_g):
                    cloned_text = ET.Element("{http://www.w3.org/2000/svg}text", attrib=text_child.attrib)
                    cloned_text.text = text_child.text
                    glow_portrait_g.append(cloned_text)

                # Find index of portrait_g to insert glow group before it
                for index, child in enumerate(parent_el):
                    if child.attrib.get("id") == "ascii-portrait":
                        parent_el.insert(index, glow_portrait_g)
                        break

            # Stagger opacity and minor translation of rows in BOTH groups
            for group in [portrait_g, root.find(".//svg:g[@id='ascii-portrait-glow']", ns)]:
                if group is None:
                    continue
                rows = group.findall("svg:text", ns)
                for r_idx, row in enumerate(rows):
                    # Hide initially
                    row.set("opacity", "0")
                    # Delay timing: each row is delayed by 0.015s
                    row_delay = portrait_start_delay + r_idx * 0.015 * self.config.animation_speed
                    
                    row_fade = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                        "attributeName": "opacity",
                        "from": "0",
                        "to": "1",
                        "dur": "0.2s",
                        "begin": f"{row_delay}s",
                        "fill": "freeze"
                    })
                    row.append(row_fade)

        # 6. Animate Left & Right Panel Fades (Fades in after ASCII portrait starts rendering, e.g. at 3.0 seconds)
        for panel_id in ["left-panel", "right-panel"]:
            panel = root.find(f".//svg:g[@id='{panel_id}']", ns)
            if panel is not None:
                # Wrap all panel children (except background rect) in a sub-group to fade in
                children = list(panel)
                rect_child = None
                for child in children:
                    if child.tag == "{http://www.w3.org/2000/svg}rect" and child.attrib.get("rx") == "16":
                        rect_child = child
                        break

                # Create a subgroup for elements
                content_g = ET.Element("{http://www.w3.org/2000/svg}g", attrib={
                    "id": f"{panel_id}-content",
                    "opacity": "0"
                })
                # Add fade animation
                fade_time = f"{(len(boot_lines) * 0.28 + 0.8) * self.config.animation_speed}s"
                fade_anim = ET.Element("{http://www.w3.org/2000/svg}animate", attrib={
                    "attributeName": "opacity",
                    "from": "0",
                    "to": "1",
                    "dur": "0.6s",
                    "begin": fade_time,
                    "fill": "freeze"
                })
                content_g.append(fade_anim)
                
                # Add slide up animation
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

                # Move elements into sub-group
                for child in children:
                    if child is not rect_child:
                        panel.remove(child)
                        content_g.append(child)
                panel.append(content_g)

        # 7. Add subtle pulsing to glow border
        main_terminal = root.find(".//svg:g[@id='main-terminal']", ns)
        if main_terminal is not None:
            # Find the border rect with url(#glow) filter
            for rect in main_terminal.findall("svg:rect", ns):
                if rect.attrib.get("filter") == "url(#glow)":
                    rect.set("class", "pulse-border")

        # Write output back to SVG file
        self.logger.info("Writing updated SVG with animations to %s", svg_path)
        tree.write(svg_path, encoding="utf-8", xml_declaration=True)
        self.logger.info("SVG Animation Injection Complete!")


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
