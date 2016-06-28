import threading
import time

from django.core.management.base import BaseCommand

from moment_display import feed

display_types = [
    'wxPython',
    'gtk',
    'pygame',
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--toolkit',
                            dest='toolkit',
                            choices=display_types,
                            default='pygame')
        parser.add_argument('--disable-threads',
                            action='store_true',
                            dest='disable_threads',
                            default=False)
        parser.add_argument('--testmode',
                            action='store_true',
                            dest='testmode',
                            default=False)

    def handle(self, *args, **options):
        threads = list()
        toolkit = options['toolkit']
        print "Window toolkit: {}".format(toolkit)

        if toolkit == 'gtk':
            threads.append(ThreadEntry(GtkThread, list(), dict(),
                                       auto_restart=False))
        elif toolkit == 'wxPython':
            threads.append(ThreadEntry(WxPythonThread, list(), dict(),
                                       auto_restart=False))
        elif toolkit == 'pygame':
            threads.append(ThreadEntry(PyGameThread, [options], dict(),
                                       auto_restart=False))
        else:
            print "Unknown toolkit type: {}".format(toolkit)
            return

        if not options['disable_threads']:
            threads.append(ThreadEntry(feed.RefreshFeedThread, list(), dict()))
            threads.append(ThreadEntry(feed.DownloadThread, list(), dict()))

        try:
            while True:
                for thread in threads:
                    thread.insure_running()
                time.sleep(2)
        except thread.ThreadShutdown:
            pass


class ThreadEntry(object):
    class ThreadShutdown(Exception):
        pass

    def __init__(self, t_class, t_args, t_kwargs, auto_restart=True):
        self.t_class = t_class
        self.t_args = t_args
        self.t_kwargs = t_kwargs
        self.instance = None
        self.auto_restart = auto_restart

    def insure_running(self):
        if self.instance is None:
            self._start_instance()
        elif not self.instance.is_alive():
            if self.auto_restart:
                print "Restarting instance of {}".format(
                    self.t_class.__name__
                )
                self._start_instance()
            else:
                raise self.ThreadShutdown()

    def _start_instance(self):
        self.instance = self.t_class(*self.t_args, **self.t_kwargs)
        self.instance.start()
        time.sleep(.05)


class GtkThread(threading.Thread):
    def run(self):
        from moment_display import xgtk
        xgtk.run_x()


class WxPythonThread(threading.Thread):
    def run(self):
        from moment_display import xdisplay
        xdisplay.run_x()


class PyGameThread(threading.Thread):
    def __init__(self, options, *args, **kwargs):
        super(PyGameThread, self).__init__(*args, **kwargs)
        self.options = options

    def run(self):
        from moment_display import pygame_display
        pygame_display.run(**self.options)
