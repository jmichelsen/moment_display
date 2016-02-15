import logging
import traceback

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
# import gtk

from .image import prep_image
from .feed import FeedManager

log = logging.getLogger(__name__)


class MomentGtk:
    def __init__(self):
        self.feed_manager = FeedManager()
        self.window = Gtk.Window()
        self.image = Gtk.Image()
        self.window.add(self.image)
        self.window.show_all()
        self.window.fullscreen()
        self.window.connect('delete-event', Gtk.main_quit)
        self.window.connect('key-release-event', self.on_key_release)

        GLib.timeout_add_seconds(25, self.on_tick)
        GLib.timeout_add(350, self.on_tick, False)

    def on_tick(self, continue_tick=True):
        # if not self.image.context:
        #     return True
        try:
            filename = self.feed_manager.get_random_photo()
            rect = self.image.get_allocation()
            size = self.window.get_size()
            pil_image = prep_image(filename, *size)
            outfile = '/tmp/SuperDPF-gtk-image.jpg'
            pil_image.save(outfile, optimize=False,
                   progressive=True, quality=100,
                   subsampling=0)
            self.image.set_from_file(outfile)
        except Exception as e:
            traceback.print_exc()
            log.error("Problem updating image: {} - {}".format(filename, e))
        return continue_tick

    def on_key_release(self, widget, ev, data=None):
        if ev.keyval == 65307:  # Escape key
            Gtk.main_quit()


def run_x():
    win = MomentGtk()
    Gtk.main()
