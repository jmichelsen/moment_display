import wx
import time
import sys

import gettext

from .image import prep_image
from .feed import FeedManager

class ImagePanel(wx.Panel):
    def __init__(self, parent):
        self.feed_manager = FeedManager()
        wx.Panel.__init__(self, parent)
        self.update_count = 0
        self.bitmap1 = None

    def update_image(self, width, height):
        try:
            filename = self.feed_manager.get_random_photo()
            pil_image = prep_image(filename, width, height)
            self.update_count += 1

            outfile = '/tmp/SuperDPF-image.jpg'
            pil_image.save(outfile, optimize=False,
                           progressive=True, quality=100,
                           subsampling=0)

            bmp1 = wx.Image(outfile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()

            # image = wx.EmptyImage(*wx.DisplaySize())
            # image.SetData(pil_image.convert("RGB").tostring())
            # bmp1 = wx.BitmapFromImage(image)

            if self.bitmap1:
                old_bmp = self.bitmap1.GetBitmap()
                self.bitmap1.SetBitmap(bmp1)
                old_bmp.Destroy()
            else:
                self.bitmap1 = wx.StaticBitmap(self, -1, bmp1, (0, 0))
        except IOError as e:
            print e
            raise SystemExit
        except NotRegisteredError as reg_error:
            reg_error.code


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

        self.client = ImagePanel(self)
        self.client.SetFocus()

        self.ShowFullScreen(True, 0)
        # self.client.update_image(self.Size.width, self.Size.height)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        # A brief sleep allows ShowFullScreen to finish before displaying images
        self.timer.Start(500)

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

    def update(self, event):
        print "Updated: {}".format(time.ctime())
        self.timer.Stop()
        self.client.update_image(self.Size.width, self.Size.height)
        self.timer.Start(12000)

    def OnKeyUP(self, event):
        code = event.GetKeyCode()
        print "keypress: {}".format(code)
        if code == wx.WXK_ESCAPE:
            sys.exit(0)


def run_x():
    gettext.install("super_dpf")

    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, wx.ID_ANY, "")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
