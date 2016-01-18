from time import time
import wx
from PIL import Image, ImageFilter


def scale_display_size(display_tuple, factor):
    x, y = display_tuple
    return (int(x * factor), int(y * factor))


def prep_image(filename, width, height):
    with open(filename) as imagefile:
        # Copy the image in memory to avoid closed file errors later
        img = Image.open(imagefile)
        if img.size == wx.DisplaySize():
            print "No prep for {}".format(filename)
            return img.copy()
        background = img.copy()
    w, h = img.size

    print "prep_image({}) {} -> {}".format(filename,
                                           img.size,
                                           wx.DisplaySize())

    background = background.resize(scale_display_size(wx.DisplaySize(), 0.1),
                                   Image.ANTIALIAS)
    background = background.filter(ImageFilter.GaussianBlur(radius=5))
    background = background.resize(wx.DisplaySize(),
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
        return img.resize(wx.DisplaySize(), Image.ANTIALIAS)
