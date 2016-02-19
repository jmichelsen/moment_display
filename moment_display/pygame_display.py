# http://bazaar.launchpad.net/~kdvolder/pypicslideshow/small-fixes-and-improvements/view/head:/pypicslideshow.py

import pygame
import logging
import traceback

from .image import prep_image
from .feed import FeedManager

log = logging.getLogger(__name__)


class Display:
    def __init__(self, **options):
        self.feed_manager = FeedManager()

        pygame.display.init()

        if options.get('testmode'):
            self.resolution = (1024, 768)
            self.main_surface = pygame.display.set_mode(self.resolution)
        else:
            self.resolution = pygame.display.list_modes()[0]
            pygame.mouse.set_visible(False)
            self.main_surface = pygame.display.set_mode(self.resolution,
                                                        pygame.FULLSCREEN)

        pygame.time.set_timer(pygame.USEREVENT + 1, 5000)

    def update_picture(self):
        try:
            filename = self.feed_manager.get_random_photo()
            pil_image = prep_image(filename, *self.resolution)

            outfile = '/tmp/SuperDPF-image.jpg'
            pil_image.save(outfile, optimize=False,
                           progressive=True, quality=100,
                           subsampling=0)
            image = pygame.image.load(outfile)
            self.main_surface.blit(image, (0,0))
        except Exception as e:
            log.error("Unexpected exception while updating image: "
                      "{}".format(e))
            traceback.print_exc()

    def run(self):
        self.update_picture()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                elif event.type == pygame.USEREVENT + 1:
                    self.update_picture()


def run(**options):
    window = Display(**options)
    window.run()
