# http://bazaar.launchpad.net/~kdvolder/pypicslideshow/small-fixes-and-improvements/view/head:/pypicslideshow.py

import pygame
import logging
import traceback
import time

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

        pygame.time.set_timer(pygame.USEREVENT + 1, 25000)

    def update_picture(self):
        filename = None
        try:
            file_buffer = self.feed_manager.get_random_photo(*self.resolution)
            image = pygame.image.load(file_buffer)
            self.main_surface.blit(image, (0,0))
            pygame.display.update()
        except Exception as e:
            if filename:
                log.error("Error processing file: {}".format(filename))
                self.feed_manager.reject_file(filename)
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
            time.sleep(.1)


def run(**options):
    window = Display(**options)
    window.run()
