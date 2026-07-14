from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import ProjectConfig, load_config


class ASCIIOptimizer:
    """Clean and center ASCII art for the terminal layout."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self.logger = logging.getLogger("ascii-optimizer")

    def load_lines(self, input_path: Path) -> List[str]:
        text = input_path.read_text(encoding="utf-8")
        return [line.rstrip("\n") for line in text.splitlines() if line.strip()]

    def remove_noisy_rows(self, lines: List[str]) -> List[str]:
        min_visible = 6 if self.config.density_mode == "dense" else 10 if self.config.density_mode == "sparse" else 8
        filtered = []
        for line in lines:
            visible_count = sum(1 for char in line if char not in {" ", "\t"})
            if visible_count >= min_visible:
                filtered.append(line)
        return filtered

    def trim_blank_columns(self, lines: List[str]) -> List[str]:
        if not lines:
            return []
        max_width = max(len(line) for line in lines)
        columns = list(range(max_width))
        visible_columns = []
        for column in columns:
            if any(line[column] != " " for line in lines if column < len(line)):
                visible_columns.append(column)
        if not visible_columns:
            return lines
        left = visible_columns[0]
        right = visible_columns[-1] + 1
        return [line[left:right].rstrip() for line in lines]

    def center_portrait(self, lines: List[str]) -> List[str]:
        target_width = self.config.ascii_width
        centered = []
        for line in lines:
            padding = max(0, target_width - len(line)) // 2
            centered.append(" " * padding + line[:target_width])
        return centered

    def normalize_spacing(self, lines: List[str]) -> List[str]:
        if not lines:
            return []
        width = max(len(line) for line in lines)
        return [line.ljust(width) for line in lines]

    def optimize(self, input_path: Path | None = None) -> Path:
        source_path = input_path or self.config.output_ascii_path
        lines = self.load_lines(source_path)
        lines = self.remove_noisy_rows(lines)
        lines = self.trim_blank_columns(lines)
        lines = self.normalize_spacing(lines)
        lines = self.center_portrait(lines)
        optimized_text = "\n".join(lines)
        output_path = self.config.output_ascii_path
        output_path.write_text(optimized_text, encoding="utf-8")
        self.logger.info("Optimized ASCII portrait written to %s", output_path)
        return output_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    optimizer = ASCIIOptimizer(load_config())
    optimizer.optimize()


if __name__ == "__main__":
    main()
