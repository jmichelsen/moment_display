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
        if not options['disable_threads']:
            rt = feed.RefreshFeedThread()
            rt.start()
            dt = feed.DownloadThread()
            dt.start()
        toolkit = options['toolkit']
        print "Window toolkit: {}".format(toolkit)

        if toolkit == 'gtk':
            from moment_display import xgtk
            xgtk.run_x()
        elif toolkit == 'wxPython':
            from moment_display import xdisplay
            xdisplay.run_x()
        elif toolkit == 'pygame':
            from moment_display import pygame_display
            pygame_display.run(**options)
        else:
            print "Unknown toolkit type: {}".format(toolkit)
