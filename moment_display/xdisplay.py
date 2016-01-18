import wx
import time
import sys
import os

import gettext

from .image import prep_image


class ImagePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        image_path = os.path.join(os.getcwd(), 'testimages')
        self.image_files = [os.path.join(image_path, f) for f in
                            os.listdir(image_path)]
        self.update_count = 0
        self.bitmap1 = None
        self.update_image()

    def update_image(self):
        try:
            image_index = self.update_count % len(self.image_files)
            filename = self.image_files[image_index]
            pil_image = prep_image(filename,
                                    *wx.DisplaySize())
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


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)

        self.width, self.height = wx.DisplaySize()
        print "Targeting images for {}x{}".format(self.width, self.height)

        self.client = ImagePanel(self)
        self.client.SetFocus()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.timer.Start(2000)

        self.ShowFullScreen(True, 0)

        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

    def update(self, event):
        print "Updated: {}".format(time.ctime())
        self.timer.Stop()
        self.client.update_image()
        self.timer.Start(2000)

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
