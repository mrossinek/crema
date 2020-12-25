"""CoBib's TUI viewport."""

import curses
import logging
import re

from cobib import __version__
from cobib.commands import ListCommand
from cobib.config import CONFIG
from .buffer import TextBuffer
from .state import STATE

LOGGER = logging.getLogger(__name__)


class Frame:
    """Frame class used to integrate a `TextBuffer` and `curses.pad` tightly with each other.

    This helper class is mainly used to implement the main 'viewport' of the TUI. It is a stateful
    object which handles a session-persistent history of the viewport to enable seamless level
    navigation.
    """

    def __init__(self, tui, max_height, max_width):
        """Initializes the Frame object."""
        LOGGER.debug("Initializing frame's buffer")
        self.buffer = TextBuffer()
        LOGGER.debug("Initializing frame's pad")
        self.pad = curses.newpad(1, 1)
        # Also store a history of buffer contents and state (such as the current line, etc.)
        self.history = []

        # store TUI reference
        self.tui = tui
        self.visible = max_height
        self.width = max_width

    def scroll_y(self, update):
        """Scroll vertically.

        Args:
            update (int or str): the offset specifying the scrolling height.
        """
        scrolloff = CONFIG.config['TUI'].getint('scroll_offset', 3)
        overlap = scrolloff >= self.visible - scrolloff
        scroll_lock = overlap and STATE.current_line - STATE.top_line == self.visible // 2
        # jump to top
        if update == 'g':
            LOGGER.debug('Jump to top of viewport.')
            STATE.top_line = 0
            STATE.current_line = 0
        # jump to bottom
        elif update == 'G':
            LOGGER.debug('Jump to bottom of viewport.')
            STATE.top_line = max(self.buffer.height - self.visible, 0)
            STATE.current_line = self.buffer.height-1
        # scroll up
        elif update < 0:
            LOGGER.debug('Scroll viewport up by %d lines.', update)
            next_line = STATE.current_line + update
            if STATE.top_line > 0 and next_line < STATE.top_line + scrolloff:
                if scroll_lock or not overlap:
                    STATE.top_line += update
                elif overlap and \
                        STATE.current_line - STATE.top_line > self.visible // 2 and \
                        next_line - STATE.top_line < self.visible // 2:
                    STATE.top_line = next_line - self.visible // 2
            STATE.current_line = max(next_line, 0)
        # scroll down
        elif update > 0:
            LOGGER.debug('Scroll viewport down by %d lines.', update)
            next_line = STATE.current_line + update
            if next_line >= STATE.top_line + self.visible - scrolloff and \
                    self.buffer.height > STATE.top_line + self.visible:
                if scroll_lock or not overlap:
                    STATE.top_line += update
                elif overlap and \
                        STATE.current_line - STATE.top_line < self.visible // 2 and \
                        next_line - STATE.top_line > self.visible // 2:
                    STATE.top_line = next_line - self.visible // 2
            if next_line < self.buffer.height:
                STATE.current_line = next_line
            else:
                STATE.top_line = self.buffer.height - self.visible
                STATE.current_line = self.buffer.height - 1

    def scroll_x(self, update):
        """Scroll horizontally.

        Args:
            update (int or str): the offset specifying the scrolling width.
        """
        # jump to beginning
        if update == 0:
            LOGGER.debug('Jump to first column of viewport.')
            STATE.left_edge = 0
        # jump to end
        elif update == '$':
            LOGGER.debug('Jump to end of viewport.')
            STATE.left_edge = self.buffer.width - self.width
        else:
            LOGGER.debug('Scroll viewport horizontally by %d columns.', update)
            next_col = STATE.left_edge + update
            # limit column such that no empty columns can appear on left or right
            if 0 <= next_col <= self.buffer.width - self.width:
                STATE.left_edge = next_col

    def wrap(self):
        """Toggles wrapping of the text currently displayed."""
        LOGGER.debug('Wrap command triggered.')
        # first, ensure left_edge is set to 0
        STATE.left_edge = 0
        # then, wrap the buffer
        self.buffer.wrap(self.width)
        self.buffer.view(self.pad, self.visible, self.width-1)
        # if cursor line is below buffer height, move it one line back up
        if self.buffer.height and STATE.current_line >= self.buffer.height:
            STATE.current_line -= 1

    def get_current_label(self):
        """Returns the label and y position of the currently selected entry."""
        LOGGER.debug('Obtaining current label "under" cursor.')
        cur_y, _ = self.pad.getyx()
        # Two cases are possible: the list and the show mode
        if STATE.list_mode == -1:
            # In the list mode, the label can be found in the current line
            # or in one of the previous lines if we are on a wrapped line
            while chr(self.pad.inch(cur_y, 0)) == TextBuffer.INDENT[0]:
                cur_y -= 1
            label = self.pad.instr(cur_y, 0).decode('utf-8').split(' ')[0]
        elif re.match(r'\d+ hit',
                      '-'.join(self.tui.topbar.instr(0, 0).decode('utf-8').split('-')[1:]).strip()):
            while chr(self.pad.inch(cur_y, 0)) in ('[', TextBuffer.INDENT[0]):
                cur_y -= 1
            label = self.pad.instr(cur_y, 0).decode('utf-8').split(' ')[0]
        else:
            # In any other mode, the label can be found in the top statusbar
            label = '-'.join(self.tui.topbar.instr(0, 0).decode('utf-8').split('-')[1:]).strip()
            # We also set cur_y to 0 for the select command to find it
            cur_y = 0
        LOGGER.debug('Current label at "%s" is "%s".', str(cur_y), label)
        return label, cur_y

    def update_list(self):
        """Updates the default list view."""
        LOGGER.debug('Re-populating the viewport with the list command.')
        self.buffer.clear()
        labels = ListCommand().execute(STATE.list_args, out=self.buffer)
        labels = labels or []  # convert to empty list if labels is None
        # populate buffer with the list
        if STATE.list_mode >= 0:
            STATE.current_line = STATE.list_mode
            STATE.list_mode = -1
        # reset viewport
        STATE.top_line = 0
        STATE.left_edge = 0
        STATE.inactive_commands = []
        # highlight current selection
        for label in STATE.selection:
            # Note: the two spaces are explained in the `select()` method.
            # Also: this step may become a performance bottleneck because we replace inside the
            # whole buffer for each selected label!
            self.buffer.replace(range(self.buffer.height), label + '  ',
                                CONFIG.get_ansi_color('selection') + label + '\x1b[0m  ')
        # display buffer in viewport
        self.buffer.view(self.pad, self.visible, self.width-1, ansi_map=self.tui.ANSI_MAP)
        # update top statusbar
        self.tui.topstatus = "CoBib v{} - {} Entries".format(__version__, len(labels))
        self.tui.statusbar(self.tui.topbar, self.tui.topstatus)
        # if cursor position is out-of-view (due to e.g. top-line reset in Show command), reset the
        # top-line such that the current line becomes visible again
        if STATE.current_line > STATE.top_line + self.visible:
            STATE.top_line = min(STATE.current_line, self.buffer.height - self.visible)
