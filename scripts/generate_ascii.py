from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import ProjectConfig, load_config


class ASCIIImageGenerator:
    """Generate an ASCII portrait from an input image."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self.logger = logging.getLogger("ascii-generator")

    def load_image(self, image_path: Path) -> Image.Image:
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        return Image.open(image_path).convert("RGB")

    def resize_image(self, image: Image.Image) -> Image.Image:
        width, height = image.size
        aspect_ratio = height / max(width, 1)
        target_width = self.config.ascii_width
        compression_factor = (self.config.ascii_char_width_ratio * self.config.ascii_font_size) / self.config.ascii_line_height
        target_height = max(8, int(aspect_ratio * target_width * compression_factor))
        self.logger.info("Resizing image from %s to %s (compression factor: %.4f)", (width, height), (target_width, target_height), compression_factor)
        return image.resize((target_width, target_height))

    def enhance_image(self, image: Image.Image) -> Image.Image:
        grayscale = ImageOps.grayscale(image)
        grayscale = ImageOps.autocontrast(grayscale, cutoff=1)
        grayscale = ImageEnhance.Contrast(grayscale).enhance(1.45)
        grayscale = ImageEnhance.Sharpness(grayscale).enhance(1.2)
        grayscale = ImageEnhance.Brightness(grayscale).enhance(1.05)
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        edge_array = np.array(edges, dtype=np.float32)
        gray_array = np.array(grayscale, dtype=np.float32)
        combined = np.clip(gray_array * 0.75 + edge_array * 0.25, 0, 255).astype(np.uint8)
        return Image.fromarray(combined, mode="L")

    def normalize_brightness(self, image: Image.Image) -> Image.Image:
        array = np.array(image, dtype=np.float32)
        if array.max() <= array.min():
            return image
        normalized = (array - array.min()) / (array.max() - array.min())
        normalized = np.clip(normalized * 255.0, 0, 255).astype(np.uint8)
        return Image.fromarray(normalized, mode="L")

    def to_ascii(self, image: Image.Image) -> str:
        pixels = list(image.getdata())
        rows: List[str] = []
        for row_index in range(0, len(pixels), image.width):
            row_pixels = pixels[row_index : row_index + image.width]
            ascii_row = "".join(self._pixel_to_char(pixel) for pixel in row_pixels)
            rows.append(ascii_row)
        return "\n".join(rows)

    def _pixel_to_char(self, pixel: int) -> str:
        if pixel < 25:
            return self.config.ascii_chars[0]
        index = int((pixel / 255.0) * (len(self.config.ascii_chars) - 1))
        return self.config.ascii_chars[index]

    def save_ascii(self, ascii_art: str, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(ascii_art, encoding="utf-8")
        return output_path

    def generate(self, image_path: Path | None = None) -> Path:
        source_path = Path(image_path or self.config.image_path)
        if not source_path.is_absolute():
            source_path = self.config.project_root / source_path
        image = self.load_image(source_path)
        resized = self.resize_image(image)
        enhanced = self.enhance_image(resized)
        normalized = self.normalize_brightness(enhanced)
        ascii_art = self.to_ascii(normalized)
        output_path = self.config.output_ascii_path
        self.save_ascii(ascii_art, output_path)
        self.logger.info("ASCII portrait saved to %s", output_path)
        return output_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generator = ASCIIImageGenerator(load_config())
    generator.generate()


if __name__ == "__main__":
    main()
