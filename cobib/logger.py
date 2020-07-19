"""CoBib logging module."""

import logging

LOGGER = logging.getLogger('cobib')


def switch_to_stream_handler():
    """Switches the logger to a stream handler."""
    for handler in LOGGER.handlers:
        LOGGER.removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('{levelname:8s} {name} {message}', style='{'))
    LOGGER.addHandler(handler)


def switch_to_file_handler():
    """Switches the logger to a file handler."""
    for handler in LOGGER.handlers:
        LOGGER.removeHandler(handler)
    handler = logging.FileHandler(filename='/tmp/cobib.log', mode='a')
    handler.setFormatter(logging.Formatter('{asctime} {levelname:8s} {name} {message}', style='{'))
    LOGGER.addHandler(handler)


# initialize stream logger
switch_to_stream_handler()
