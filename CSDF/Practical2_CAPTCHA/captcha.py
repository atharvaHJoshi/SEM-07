"""
Practical 2 : Generate and verify CAPTCHA image
Aim         : Create a CAPTCHA image with random characters and noise,
              then verify the text entered by the user.
Needs       : Pillow library (pip install pillow)
"""

import random
import string
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 250, 90
LENGTH = 5                        # number of characters in the CAPTCHA
OUTPUT = Path(__file__).parent / "captcha.png"


def load_font(size):
    """Use a normal font if it exists on the system, else Pillow's default font."""
    for path in ("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def generate_captcha(text):
    """Draw the given text on an image with random noise and save it."""
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    font = load_font(42)
    x = 15

    for char in text:
        # random dark colour and small random position for each character
        colour = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        y = random.randint(5, 30)
        draw.text((x, y), char, font=font, fill=colour)
        x += 45

    # noise: random lines and dots so that a bot cannot read the text easily
    for _ in range(6):
        draw.line((random.randint(0, WIDTH), random.randint(0, HEIGHT),
                   random.randint(0, WIDTH), random.randint(0, HEIGHT)),
                  fill=(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)),
                  width=2)
    for _ in range(300):
        draw.point((random.randint(0, WIDTH), random.randint(0, HEIGHT)),
                   fill=(random.randint(120, 200),) * 3)

    image.save(OUTPUT)
    print("CAPTCHA image saved as:", OUTPUT)


def verify(expected, answer):
    """Check the text typed by the user (ignore case and extra spaces)."""
    return answer.strip().upper() == expected.upper()


def main():
    text = "".join(random.choices(string.ascii_uppercase + string.digits, k=LENGTH))
    generate_captcha(text)

    for attempt in range(1, 4):
        answer = input(f"Attempt {attempt}/3 - enter the CAPTCHA text: ")
        if verify(text, answer):
            print("Verification successful! You are a human.")
            return
        print("Wrong CAPTCHA.")

    print("Verification failed. The correct text was:", text)


if __name__ == "__main__":
    main()
