"""
OLED animated face states using luma.oled.
Draws simple bitmap faces to reflect robot mood/state.
States: patrol | alert | happy | searching
"""
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from PIL import ImageDraw

_device = None


def setup(i2c_port=1, i2c_address=0x3C):
    global _device
    serial = i2c(port=i2c_port, address=i2c_address)
    _device = ssd1306(serial)


def _draw_eyes(draw, left_xy, right_xy, size=10, style="open"):
    """Helper — draw two eyes at given center coords."""
    lx, ly = left_xy
    rx, ry = right_xy
    if style == "open":
        draw.ellipse([lx - size, ly - size, lx + size, ly + size], outline=255, fill=255)
        draw.ellipse([rx - size, ry - size, rx + size, ry + size], outline=255, fill=255)
    elif style == "wide":
        s = size + 4
        draw.ellipse([lx - s, ly - s, lx + s, ly + s], outline=255, fill=255)
        draw.ellipse([rx - s, ry - s, rx + s, ry + s], outline=255, fill=255)
    elif style == "squint":
        draw.rectangle([lx - size, ly - 3, lx + size, ly + 3], fill=255)
        draw.rectangle([rx - size, ry - 3, rx + size, ry + 3], fill=255)
    elif style == "side":
        draw.ellipse([lx, ly - size, lx + size * 2, ly + size], outline=255, fill=255)
        draw.ellipse([rx, ry - size, rx + size * 2, ry + size], outline=255, fill=255)


def show_face(state="patrol"):
    if _device is None:
        return

    with canvas(_device) as draw:
        w, h = _device.width, _device.height
        cx = w // 2
        cy = h // 2

        if state == "patrol":
            # Normal forward eyes
            _draw_eyes(draw, (cx - 22, cy - 5), (cx + 22, cy - 5), size=10, style="open")
            draw.arc([cx - 12, cy + 5, cx + 12, cy + 18], start=0, end=180, fill=255)

        elif state == "alert":
            # Wide surprised eyes
            _draw_eyes(draw, (cx - 22, cy - 5), (cx + 22, cy - 5), size=10, style="wide")
            draw.ellipse([cx - 6, cy + 8, cx + 6, cy + 18], outline=255)

        elif state == "happy":
            # Squinting smiling eyes
            _draw_eyes(draw, (cx - 22, cy - 5), (cx + 22, cy - 5), size=10, style="squint")
            draw.arc([cx - 15, cy + 3, cx + 15, cy + 18], start=0, end=180, fill=255)

        elif state == "searching":
            # Side-glancing eyes
            _draw_eyes(draw, (cx - 32, cy - 5), (cx + 12, cy - 5), size=8, style="side")
            draw.line([cx - 15, cy + 12, cx + 15, cy + 12], fill=255)
