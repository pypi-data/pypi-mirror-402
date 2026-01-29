"""Generate the test images used in the test suite so you can view them."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

output_dir = Path(__file__).parent / "test_images"
output_dir.mkdir(exist_ok=True)


def create_sample_image():
    """The basic sample_image fixture - white with blue square."""
    img = Image.new("RGB", (100, 100), color="white")
    for x in range(20, 80):
        for y in range(20, 80):
            img.putpixel((x, y), (0, 100, 200))
    return img


def create_sample_image_modified():
    """The modified version - white with orange square, shifted position."""
    img = Image.new("RGB", (100, 100), color="white")
    for x in range(30, 90):
        for y in range(30, 90):
            img.putpixel((x, y), (200, 100, 0))
    return img


def create_real_webpage_image():
    """A more realistic webpage-like test image."""
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header (dark blue)
    draw.rectangle([0, 0, 800, 60], fill=(30, 60, 114))

    # Header text
    draw.text((20, 20), "Example Website", fill=(255, 255, 255))

    # Sidebar (light gray)
    draw.rectangle([0, 60, 200, 600], fill=(245, 245, 245))

    # Sidebar menu items
    for i, item in enumerate(["Home", "Products", "About", "Contact"]):
        y = 80 + i * 40
        draw.text((20, y), item, fill=(100, 100, 100))

    # Main content area
    draw.text((220, 80), "Welcome to Our Site", fill=(30, 30, 30))

    # A blue button
    draw.rectangle([220, 120, 350, 160], fill=(59, 130, 246))
    draw.text((240, 130), "Click Me", fill=(255, 255, 255))

    # Some content boxes
    draw.rectangle([220, 180, 500, 280], outline=(200, 200, 200), width=1)
    draw.text((230, 190), "Feature 1", fill=(50, 50, 50))

    draw.rectangle([520, 180, 780, 280], outline=(200, 200, 200), width=1)
    draw.text((530, 190), "Feature 2", fill=(50, 50, 50))

    return img


def create_real_webpage_modified():
    """Modified version of the webpage - button color changed, text updated."""
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Header (dark blue) - same
    draw.rectangle([0, 0, 800, 60], fill=(30, 60, 114))
    draw.text((20, 20), "Example Website", fill=(255, 255, 255))

    # Sidebar - same
    draw.rectangle([0, 60, 200, 600], fill=(245, 245, 245))
    for i, item in enumerate(["Home", "Products", "About", "Contact"]):
        y = 80 + i * 40
        draw.text((20, y), item, fill=(100, 100, 100))

    # Main content area - CHANGED title
    draw.text((220, 80), "Welcome to Our NEW Site", fill=(30, 30, 30))

    # CHANGED: Green button instead of blue
    draw.rectangle([220, 120, 350, 160], fill=(34, 197, 94))
    draw.text((235, 130), "Buy Now", fill=(255, 255, 255))

    # Content boxes - same
    draw.rectangle([220, 180, 500, 280], outline=(200, 200, 200), width=1)
    draw.text((230, 190), "Feature 1", fill=(50, 50, 50))

    draw.rectangle([520, 180, 780, 280], outline=(200, 200, 200), width=1)
    draw.text((530, 190), "Feature 2", fill=(50, 50, 50))

    # ADDED: New banner
    draw.rectangle([220, 300, 780, 350], fill=(254, 243, 199))
    draw.text((230, 315), "NEW! Check out our summer sale!", fill=(180, 100, 0))

    return img


if __name__ == "__main__":
    # Generate and save all test images

    print("Generating test images...")

    # Simple test images
    img1 = create_sample_image()
    img1.save(output_dir / "01_sample_baseline.png")
    print(f"Saved: {output_dir / '01_sample_baseline.png'}")

    img2 = create_sample_image_modified()
    img2.save(output_dir / "02_sample_modified.png")
    print(f"Saved: {output_dir / '02_sample_modified.png'}")

    # Realistic webpage images
    img3 = create_real_webpage_image()
    img3.save(output_dir / "03_webpage_baseline.png")
    print(f"Saved: {output_dir / '03_webpage_baseline.png'}")

    img4 = create_real_webpage_modified()
    img4.save(output_dir / "04_webpage_modified.png")
    print(f"Saved: {output_dir / '04_webpage_modified.png'}")

    print(f"\nAll images saved to: {output_dir}")
    print("\nChanges between webpage versions:")
    print("  - Title: 'Welcome to Our Site' → 'Welcome to Our NEW Site'")
    print("  - Button: Blue 'Click Me' → Green 'Buy Now'")
    print("  - Added: Yellow summer sale banner")
