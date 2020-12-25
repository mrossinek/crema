"""CoBib's TUI viewport."""

import curses
import logging

from cobib.config import CONFIG
from .buffer import TextBuffer

LOGGER = logging.getLogger(__name__)


class Frame:
    """Frame class used to integrate a `TextBuffer` and `curses.pad` tightly with each other.

    This helper class is mainly used to implement the main 'viewport' of the TUI. It is a stateful
    object which handles a session-persistent history of the viewport to enable seamless level
    navigation.
    """

    def __init__(self, max_height, max_width):
        """Initializes the Frame object."""
        LOGGER.debug("Initializing frame's buffer")
        self.buffer = TextBuffer()
        LOGGER.debug("Initializing frame's pad")
        self.pad = curses.newpad(1, 1)
        # Also store a history of buffer contents and state (such as the current line, etc.)
        self.history = []

        self.visible = max_height
        self.width = max_width
        self.list_mode = -1  # -1: list mode active, >=0: previously selected line
        self.current_line = 0
        self.top_line = 0
        self.left_edge = 0

    def scroll_y(self, update):
        """Scroll vertically.

        Args:
            update (int or str): the offset specifying the scrolling height.
        """
        scrolloff = CONFIG.config['TUI'].getint('scroll_offset', 3)
        overlap = scrolloff >= self.visible - scrolloff
        scroll_lock = overlap and self.current_line - self.top_line == self.visible // 2
        # jump to top
        if update == 'g':
            LOGGER.debug('Jump to top of viewport.')
            self.top_line = 0
            self.current_line = 0
        # jump to bottom
        elif update == 'G':
            LOGGER.debug('Jump to bottom of viewport.')
            self.top_line = max(self.buffer.height - self.visible, 0)
            self.current_line = self.buffer.height-1
        # scroll up
        elif update < 0:
            LOGGER.debug('Scroll viewport up by %d lines.', update)
            next_line = self.current_line + update
            if self.top_line > 0 and next_line < self.top_line + scrolloff:
                if scroll_lock or not overlap:
                    self.top_line += update
                elif overlap and \
                        self.current_line - self.top_line > self.visible // 2 and \
                        next_line - self.top_line < self.visible // 2:
                    self.top_line = next_line - self.visible // 2
            self.current_line = max(next_line, 0)
        # scroll down
        elif update > 0:
            LOGGER.debug('Scroll viewport down by %d lines.', update)
            next_line = self.current_line + update
            if next_line >= self.top_line + self.visible - scrolloff and \
                    self.buffer.height > self.top_line + self.visible:
                if scroll_lock or not overlap:
                    self.top_line += update
                elif overlap and \
                        self.current_line - self.top_line < self.visible // 2 and \
                        next_line - self.top_line > self.visible // 2:
                    self.top_line = next_line - self.visible // 2
            if next_line < self.buffer.height:
                self.current_line = next_line
            else:
                self.top_line = self.buffer.height - self.visible
                self.current_line = self.buffer.height - 1

    def scroll_x(self, update):
        """Scroll horizontally.

        Args:
            update (int or str): the offset specifying the scrolling width.
        """
        # jump to beginning
        if update == 0:
            LOGGER.debug('Jump to first column of viewport.')
            self.left_edge = 0
        # jump to end
        elif update == '$':
            LOGGER.debug('Jump to end of viewport.')
            self.left_edge = self.buffer.width - self.width
        else:
            LOGGER.debug('Scroll viewport horizontally by %d columns.', update)
            next_col = self.left_edge + update
            # limit column such that no empty columns can appear on left or right
            if 0 <= next_col <= self.buffer.width - self.width:
                self.left_edge = next_col

    def wrap(self):
        """Toggles wrapping of the text currently displayed."""
        LOGGER.debug('Wrap command triggered.')
        # first, ensure left_edge is set to 0
        self.left_edge = 0
        # then, wrap the buffer
        self.buffer.wrap(self.width)
        self.buffer.view(self.pad, self.visible, self.width-1)
        # if cursor line is below buffer height, move it one line back up
        if self.buffer.height and self.current_line >= self.buffer.height:
            self.current_line -= 1
