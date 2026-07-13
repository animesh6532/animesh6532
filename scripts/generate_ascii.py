from PIL import Image, ImageOps, ImageEnhance
import os

# ==============================
# Configuration
# ==============================

INPUT_IMAGE = "../assets/profile.jpg"
OUTPUT_TEXT = "../assets/ascii.txt"

# Width of ASCII portrait
WIDTH = 90

# Dark → Light characters
ASCII_CHARS = "@%#*+=-:. "

# ==============================
# Resize image
# ==============================

def resize_image(image, new_width=WIDTH):
    width, height = image.size
    aspect_ratio = height / width

    # Character height correction
    new_height = int(aspect_ratio * new_width * 0.55)

    return image.resize((new_width, new_height))


# ==============================
# Convert to grayscale
# ==============================

def grayscale(image):
    return ImageOps.grayscale(image)


# ==============================
# Improve contrast
# ==============================

def enhance(image):
    contrast = ImageEnhance.Contrast(image)
    image = contrast.enhance(2.0)

    sharp = ImageEnhance.Sharpness(image)
    image = sharp.enhance(1.4)

    return image


# ==============================
# Pixels -> ASCII
# ==============================

def pixels_to_ascii(image):
    pixels = image.getdata()

    ascii_str = ""

    for pixel in pixels:
        ascii_str += ASCII_CHARS[pixel * (len(ASCII_CHARS)-1) // 255]

    return ascii_str


# ==============================
# Main
# ==============================

def main():

    if not os.path.exists(INPUT_IMAGE):
        print("Image not found:", INPUT_IMAGE)
        return

    image = Image.open(INPUT_IMAGE)

    image = resize_image(image)

    image = grayscale(image)

    image = enhance(image)

    ascii_data = pixels_to_ascii(image)

    width = image.width

    ascii_image = "\n".join(
        ascii_data[i:i+width]
        for i in range(0, len(ascii_data), width)
    )

    with open(OUTPUT_TEXT, "w", encoding="utf-8") as f:
        f.write(ascii_image)

    print("ASCII portrait saved to", OUTPUT_TEXT)


if __name__ == "__main__":
    main()
