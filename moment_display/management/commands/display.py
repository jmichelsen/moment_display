import time

from django.core.management.base import BaseCommand

from moment_display import feed, xdisplay


class Command(BaseCommand):
    def handle(self, *args, **options):
        rt = feed.RefreshFeedThread()
        rt.start()
        dt = feed.DownloadThread()
        dt.start()
        print "Started download thread"
        xdisplay.run_x()
