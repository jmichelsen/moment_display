import os
import json
import random
import time
import threading
import logging

import requests

from django.conf import settings

from .image import draw_image_message_file
from .models import Feed

log = logging.getLogger(__name__)

_CONFIG_DEFAULTS = (
    ('base_url', 'http://localhost:8000'),
    ('moment_token', None),
    ('registration_code', None),
    ('photo_display_seconds', 15),
)


class MomentConfig(object):
    def __init__(self):
        self.cfg_file = os.path.join(settings.MOMENT_HOME, 'moment.cfg')
        self.load()

        try:
            with open('/sys/class/net/eth0/address') as macfile:
                self.mac_address = macfile.read()[0:17].upper()
        except IOError as e:
            self.mac_address = '00:00:00:00:00:00'

    def load(self):
        self.cfg_dict = dict()
        if os.path.isfile(self.cfg_file):
            try:
                with open(self.cfg_file) as cfg:
                    self.cfg_dict = json.loads(cfg.read())
            except Exception as e:
                log.error("Error loading config: {}".format(e))

        for key, default in _CONFIG_DEFAULTS:
            setattr(self, key, self.cfg_dict.get(key, default))

    def save(self):
        cfg_dict = dict()
        for key, default in _CONFIG_DEFAULTS:
            cfg_dict[key] = getattr(self, key)
        with open(self.cfg_file, 'w') as cfg:
            json.dump(cfg_dict, cfg, indent=3)

    @property
    def registration_url(self):
        return "{}/api/v1/device/registration/{}".format(self.base_url,
                                                         self.mac_address)

    @property
    def feed_url(self):
        return "{}/api/v1/feed/master".format(self.base_url)

    @property
    def image_dir(self):
        dir_name = os.path.join(settings.MOMENT_HOME, 'image_cache')
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)
        return dir_name

    @property
    def registration_image_filename(self):
        return os.path.join(settings.MOMENT_HOME, 'registration-code.png')

    @property
    def empty_feed_image_filename(self):
        return os.path.join(settings.MOMENT_HOME, 'empty-feed.png')


class FeedManager(object):
    def __init__(self):
        self.config = MomentConfig()
        self._last_registration_status = False

    def begin_registration(self):
        reg = requests.put(self.config.registration_url)
        reg_info = reg.json()
        self.config.moment_token = reg_info.get('token')
        self.config.registration_code = reg_info.get('registration_code')

        filename = self.config.registration_image_filename
        msg = "Registration Code: {}\n" \
              "Register at /accounts/devices/register".format(
            self.config.registration_code)
        draw_image_message_file(filename, msg)

        self.config.save()

    @property
    def is_registered(self):
        self._last_registration_status = self.update_registration_status()
        return self._last_registration_status

    def update_registration_status(self):
        if not self.config.moment_token:
            self.begin_registration()
            return False

        reg = requests.get(self.config.registration_url,
                           params={'device_token': self.config.moment_token})
        status = reg.json()
        if not status.get('registered') and \
            not status.get('pending_registration'):
            self.begin_registration()
            return False
        return status.get('registered', False)

    def get_random_photo(self):
        image_qs = Feed.objects.available_photos()

        if not self.is_registered:
            return self.config.registration_image_filename

        if not image_qs:
            qs = Feed.objects.download_queue()
            # Block getting a limited set to make sure something is available
            refresh_feed(self.config, limit=1)

            # We probably just got registered so start a full feed refresh
            OneTimeRefreshThread().start()
            if qs:
                logging.info("Downloading first image")
                image = qs.first()
                download_feed_item(image)
                return self._image_filename(image)
            else:
                if not os.path.isfile(self.config.empty_feed_image_filename):
                    draw_image_message_file(
                        self.config.empty_feed_image_filename,
                        "No images found in feed"
                    )
                return self.config.empty_feed_image_filename

        return self._image_filename(random.choice(image_qs))

    def _image_filename(self, image_rec):
        return os.path.join(self.config.image_dir, image_rec.local_filename)

    @property
    def next_sleep(self):
        # Returns milliseconds
        if self._last_registration_status:
            return self.config.photo_display_seconds * 1000
        else:
            return 2500


def download_feed_item(item, config=None):
    if not config:
        config = MomentConfig()
    result = requests.get(item.url)
    filename = os.path.join(config.image_dir,
                            item.local_filename)
    dirname = os.path.dirname(filename)
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    with open(filename, 'wb') as cache_file:
        for chunk in result.iter_content(chunk_size=512*1024):
            cache_file.write(chunk)

    item.downloaded = True
    item.save()


class DownloadThread(threading.Thread):
    daemon = True

    def run(self):
        fm = FeedManager()
        # Sleep initially to give RefreshFeedThread time to run
        time.sleep(30)
        while True:
            qs = Feed.objects.download_queue()
            try:
                for item in qs:
                    log.info("Downloading image: {}"
                             .format(item.local_filename))
                    download_feed_item(item, fm.config)
                    time.sleep(10)
            except Exception as e:
                log.error("Error downloading feed image: {}".format(str(e)))

            log.debug("DownloadThread sleeping...")
            time.sleep(300)


def refresh_feed(config, limit=None):
    res = requests.get(config.feed_url,
               params={'device_token': config.moment_token})
    feed_data = res.json()
    created = 0
    for item in feed_data.get('images', list()):
        try:
            rec = Feed.objects.get(provider_name=item['provider_name'],
                             feeditem_pk=item['feeditem_pk'])
            if rec.revoked:
                rec.revoked = False
                rec.save()
        except Feed.DoesNotExist:
            rec = Feed.objects.create(**item)
            created += 1
            log.debug("Added file: {}".format(rec.local_filename))
            if limit and created >= limit:
                break

    feed_albums = feed_data.get('albums', dict())
    for provider, albums in feed_albums.items():
        revoke_qs = Feed.objects.filter(provider_name=provider, revoked=False)\
            .exclude(album_pk__in=albums)
        count = revoke_qs.count()
        if count:
            log.info("Revoking {} {} feed items".format(count, provider))
            revoke_qs.update(revoked=True)
    revoke_qs = Feed.objects.exclude(provider_name__in=feed_albums.keys())
    provider_list = sorted(set(revoke_qs.values_list('provider_name',
                                                     flat=True)))
    if provider_list:
        log.info("Revoking {} items from {}".format(revoke_qs.count(),
                                                    provider_list))
        revoke_qs.update(revoked=True)


class RefreshFeedThread(threading.Thread):
    daemon = True

    def run(self):
        fm = FeedManager()
        while True:
            refresh_feed(fm.config)

            log.debug("Feed refresh sleeping...")
            time.sleep(600)


class OneTimeRefreshThread(threading.Thread):
    daemon = True

    def run(self):
        log.info("Starting one time refresh...")
        fm = FeedManager()
        # Get enough images to display while the full feed downloads
        refresh_feed(fm.config, limit=20)

        # Limit queryset in case another feed refresh expanded it
        for item in Feed.objects.download_queue()[:20]:
            log.info("Downloading image: {}".format(item.local_filename))
            download_feed_item(item, fm.config)
        log.info("Initial download in one time refresh completed...")

        # Get everything from feed, but leave for the normal download thread
        refresh_feed(fm.config)
        log.info("Finishing one time refresh...")
