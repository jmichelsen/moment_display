import os
import json
import hashlib
import random

import requests

from .image import draw_image_message_file

MOMENT_HOME = os.environ.get("MOMENT_HOME", os.path.expanduser('~/.MomentHome'))

_CONFIG_DEFAULTS = (
    ('base_url', 'http://localhost:8000'),
    ('moment_token', None),
    ('registration_code', None),
    ('photo_display_seconds', 15),
)


class MomentConfig(object):
    def __init__(self):
        self.cfg_file = os.path.join(MOMENT_HOME, 'moment.cfg')
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
                print "Error loading config: {}".format(e)

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
        dir_name = os.path.join(MOMENT_HOME, 'image_cache')
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)
        return dir_name

    @property
    def registration_image_filename(self):
        return os.path.join(MOMENT_HOME, 'registration-code.png')

    @property
    def empty_feed_image_filename(self):
        return os.path.join(MOMENT_HOME, 'empty-feed.png')


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

    def get_photo_feed(self):
        res = requests.get(self.config.feed_url,
                           params={'device_token': self.config.moment_token})
        feed_data = res.json()
        return feed_data.get('images', list())

    def fetch_photos(self):
        image_list = self.get_photo_feed()
        last_photo = None
        for img_file in image_list:
            base, ext = os.path.splitext(img_file)
            if ext in ['.gif']:
                continue
            filename_hash = hashlib.sha1()
            filename_hash.update(base)
            cache_filename = os.path.join(self.config.image_dir,
                                          filename_hash.hexdigest()+ext)
            if not os.path.isfile(cache_filename):
                r = requests.get(img_file)
                with open(cache_filename, 'wb') as cache_file:
                    for chunk in r.iter_content(chunk_size=512*1024):
                        cache_file.write(chunk)

            last_photo = cache_filename
        return last_photo

    def get_random_photo(self):
        image_list = [os.path.join(self.config.image_dir, f) for f in
                      os.listdir(self.config.image_dir)]

        if not self.is_registered:
            return self.config.registration_image_filename

        if not image_list:
            last_photo = self.fetch_photos()
            if not last_photo:
                if not os.path.isfile(self.config.empty_feed_image_filename):
                    draw_image_message_file(
                        self.config.empty_feed_image_filename,
                        "No images found in feed"
                    )
                return self.config.empty_feed_image_filename
            return last_photo

        return random.choice(image_list)

    @property
    def next_sleep(self):
        # Returns milliseconds
        if self._last_registration_status:
            return self.config.photo_display_seconds * 1000
        else:
            return 2500
