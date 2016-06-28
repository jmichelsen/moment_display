import os
import logging

from PIL import Image, ImageFilter, ImageDraw, ImageFont

log = logging.getLogger(__name__)


def scale_display_size(display_tuple, factor):
    x, y = display_tuple
    return (int(x * factor), int(y * factor))


def prep_image(filename, width, height):
    with open(filename) as imagefile:
        # Copy the image in memory to avoid closed file errors later
        img = Image.open(imagefile).convert('RGB')
        if img.size == (width, height):
            log.debug("No prep for {}".format(filename))
            return img.copy()
        background = img.copy()
    w, h = img.size

    log.debug("prep_image({}) {} -> {}".format(filename,
                                               img.size,
                                               (width, height)))

    background = background.resize(scale_display_size((width, height), 0.1),
                                   Image.ANTIALIAS)
    background = background.filter(ImageFilter.GaussianBlur(radius=5))
    background = background.resize((width, height),
                                   Image.ANTIALIAS)

    new_height = width * h / w
    if new_height > height:
        new_width = height * w / h
        margin = (width - new_width) / 2
        new_image = img.resize((new_width, height), Image.ANTIALIAS)
        background.paste(new_image, (margin, 0))
        return background
    elif new_height < height:
        new_image = img.resize((width, new_height), Image.ANTIALIAS)
        top_margin = (height - new_height) / 2
        background.paste(new_image, (0, top_margin))
        return background
    else:
        return img.resize((width, height), Image.ANTIALIAS)


def draw_image_message_file(filename, message):
    image = Image.new("RGBA", (4800, 2800), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font_file = os.path.join(os.path.dirname(__file__), 'FreeSans.ttf')
    font = ImageFont.truetype(font_file, 75)
    for num, line in enumerate(message.split('\n')):
        draw.text((10, 70*num), line, (0, 0, 0), font=font)
    image.save(filename)
