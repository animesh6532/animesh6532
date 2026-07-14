from __future__ import annotations

import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import load_config
from scripts.generate_ascii import ASCIIImageGenerator
from scripts.optimize_ascii import ASCIIOptimizer
from scripts.build_svg import TerminalSVGBuilder
from scripts.animate_terminal import TerminalAnimator


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    config = load_config()

    logging.info("Step 1: Generating raw ASCII portrait...")
    generator = ASCIIImageGenerator(config)
    generator.generate()

    logging.info("Step 2: Optimizing ASCII art layout...")
    optimizer = ASCIIOptimizer(config)
    optimizer.optimize()

    logging.info("Step 3: Building base terminal SVG...")
    builder = TerminalSVGBuilder(config)
    ascii_lines = config.output_ascii_path.read_text(encoding="utf-8").splitlines()
    builder.build_terminal_svg(ascii_lines, config.output_terminal_path)
    builder.build_portrait_svg(ascii_lines, config.output_portrait_path)

    logging.info("Step 4: Injecting terminal animations...")
    animator = TerminalAnimator(config)
    animator.animate()

    logging.info("Step 5: Verifying generated SVG syntax...")
    try:
        ET.parse(config.output_terminal_path)
        logging.info("Verification passed! SVG is valid XML.")
    except Exception as e:
        logging.error("Verification failed: %s is not valid XML: %s", config.output_terminal_path, e)
        sys.exit(1)

    logging.info("Export pipeline complete! Animated terminal SVG saved at %s", config.output_terminal_path)


if __name__ == "__main__":
    main()
