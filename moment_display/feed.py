import os
import json
import requests

MOMENT_HOME = os.environ.get("MOMENT_HOME", os.path.expanduser('~/.MomentHome'))


_CONFIG_DEFAULTS = (
    ('base_url', 'http://localhost:8000'),
    ('moment_token', None),
    ('registration_code', None)
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
                print e

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


class FeedManager(object):
    def __init__(self):
        self.config = MomentConfig()

    def begin_registration(self):
        reg = requests.put(self.config.registration_url)
        reg_info = reg.json()
        self.config.moment_token = reg_info.get('token')
        self.config.registration_code = reg_info.get('registration_code')
        self.config.save()

    @property
    def is_registered(self):
        if not self.config.moment_token:
            self.begin_registration()
            return False

        reg = requests.get(self.config.registration_url,
                           params={'device_token': self.config.moment_token})
        registration_status = reg.json()
        return registration_status.get('registered', False)

    def get_photo_feed(self):
        res = requests.get(self.config.feed_url,
                           params={'device_token': self.config.moment_token})
        feed_data = res.json()
        return feed_data.get('images', list())
