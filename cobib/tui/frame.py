"""CoBib's TUI viewport."""

import curses
import logging

from .buffer import TextBuffer

LOGGER = logging.getLogger(__name__)


class Frame:
    """Frame class used to integrate a `TextBuffer` and `curses.pad` tightly with each other.

    This helper class is mainly used to implement the main 'viewport' of the TUI. It is a stateful
    object which handles a session-persistent history of the viewport to enable seamless level
    navigation.
    """

    def __init__(self):
        """Initializes the Frame object."""
        LOGGER.debug("Initializing frame's buffer")
        self.buffer = TextBuffer()
        LOGGER.debug("Initializing frame's pad")
        self.pad = curses.newpad(1, 1)
        # Also store a history of buffer contents and state (such as the current line, etc.)
        self.history = []
