from django.core.management.base import BaseCommand

from moment_display import feed

display_types = [
    'wxPython',
    'gtk',
]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--toolkit',
                            dest='toolkit',
                            choices=display_types,
                            default='gtk')
        parser.add_argument('--disable-threads',
                            action='store_true',
                            dest='disable_threads',
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
        else:
            print "Unknown toolkit type: {}".format(toolkit)
