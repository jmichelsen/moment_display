import os
import sys


def display_main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "moment_display.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
