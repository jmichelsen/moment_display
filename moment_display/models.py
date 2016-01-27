import os

from django.db import models


class FeedManager(models.Manager):
    def available_photos(self):
        return self.filter(downloaded=True, revoked=False)

    def download_queue(self):
        return self.filter(downloaded=False, revoked=False)


class Feed(models.Model):
    moment_id = models.CharField(max_length=100)
    provider_name = models.CharField(max_length=50)
    album_pk = models.IntegerField()
    feeditem_pk = models.IntegerField()
    url = models.TextField()
    views = models.IntegerField(default=0)
    downloaded = models.BooleanField(default=False)
    revoked = models.BooleanField(default=False)

    objects = FeedManager()

    @property
    def local_filename(self):
        url = self.url.split('?')[0]
        file, ext = os.path.splitext(url)
        return os.path.join(
            '{}.{}'.format(self.provider_name, self.album_pk),
            str(self.feeditem_pk)+ext,
        )

    class Meta:
        unique_together = ('provider_name', 'feeditem_pk')