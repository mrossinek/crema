"""CoBib curses interface"""

import curses
import textwrap

from cobib import __version__
from cobib.commands import ListCommand, ShowCommand, DeleteCommand


class TUI:  # pylint: disable=too-many-instance-attributes
    """CoBib's curses-based TUI.

    The TUI is implemented as a class to simplify management of different windows/pads and keep a
    synchronized state most consistently.
    """

    def __init__(self, stdscr):
        self.stdscr = stdscr

        # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # Initialize layout
        curses.curs_set(0)
        self.height, self.width = self.stdscr.getmaxyx()
        # and colors
        self.colors()

        # Initialize top status bar
        self.topbar = curses.newwin(1, self.width, 0, 0)
        self.topbar.bkgd(' ', curses.color_pair(1))
        self.statusbar(self.topbar, "CoBib v{}".format(__version__))

        # Initialize bottom status bar
        # NOTE: -2 leaves an additional empty line for the command prompt
        self.botbar = curses.newwin(1, self.width, self.height-2, 0)
        self.botbar.bkgd(' ', curses.color_pair(1))
        self.statusbar(self.botbar, "q:Quit")

        # Initialize command prompt
        self.prompt = curses.newwin(1, self.width, self.height-1, 0)

        # populate buffer with list of reference entries
        self.initial_list = TUI.TextBuffer()
        ListCommand().execute(['--long'], out=self.initial_list)

        self.buffer = self.initial_list.copy()

        # NOTE The +1 added onto the height accounts for some weird offset in the curses pad.
        self.viewport = curses.newpad(self.buffer.height+1, self.buffer.width)
        for row, line in enumerate(self.buffer.lines):
            self.viewport.addstr(row, 0, line)

        # prepare and start key event loop
        self.current_line = 0
        self.visible = self.height-3
        self.top_line = 0
        self.left_edge = 0
        self.loop()

    def colors(self):  # pylint: disable=no-self-use
        """Initialize the color pairs for the curses TUI."""
        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_CYAN)

    def statusbar(self, statusline, text, attr=0):  # pylint: disable=no-self-use
        """Update the text in the provided status bar and refresh it."""
        statusline.addstr(0, 0, text, attr)
        statusline.refresh()

    class TextBuffer:
        """TextBuffer class used as an auxiliary variable to redirect output into.

        This buffer class implements a `write` method which allows it to be used as a drop-in source
        for the `file` argument of the `print()` method. Thereby, its output can be gathered in this
        buffer for further usage (such as printing it into a curses pad).
        """
        def __init__(self):
            self.lines = []
            self.height = 0
            self.width = 0

        def copy(self):
            """Copy."""
            clone = TUI.TextBuffer()
            clone.lines = self.lines.copy()
            clone.height = self.height
            clone.width = self.width
            return clone

        def write(self, string):
            """Writes a non-empty string into the buffer."""
            if string.strip():
                # only handle non-empty strings
                self.lines.append(string)
                self.height = len(self.lines)
                self.width = max(self.width, len(string))

        def clear(self):
            """Clears the buffer."""
            self.lines = []
            self.height = 0
            self.width = 0

        def split(self):
            """Split lines at line breaks."""
            copy = self.lines.copy()
            self.lines = []
            self.width = 0
            for line in copy:
                for string in line.split('\n'):
                    self.lines.append(string)
                    self.width = max(self.width, len(string))
            self.height = len(self.lines)

        def wrap(self, width):
            """Wrap text in buffer to given width."""
            copy = self.lines.copy()
            self.lines = []
            for line in copy:
                for string in textwrap.wrap(line, width=width-1, subsequent_indent="↪ "):
                    self.lines.append(string)
            self.width = width
            self.height = len(self.lines)

        def view(self, pad, visible_height, visible_width):
            """View buffer in provided curses pad."""
            # first clear pad
            pad.erase()
            pad.refresh(0, 0, 1, 0, visible_height, visible_width)
            # then resize
            pad.resize(self.height+1, max(self.width, visible_width+1))
            # and populate
            for row, line in enumerate(self.lines):
                pad.addstr(row, 0, line)
            pad.refresh(0, 0, 1, 0, visible_height, visible_width)

    def loop(self, disabled=None):  # pylint: disable=too-many-branches
        """The key-handling event loop."""
        key = 0
        # key is the last character pressed
        while key != ord('q'):
            # reset highlight of current line
            self.viewport.chgat(self.current_line, 0, curses.A_NORMAL)

            # handle possible keys
            if disabled and key in disabled:
                pass
            elif key in (curses.KEY_DOWN, ord('j')):
                self._scroll_y(1)
            elif key in (curses.KEY_UP, ord('k')):
                self._scroll_y(-1)
            elif key in (curses.KEY_LEFT, ord('h')):
                self._scroll_x(-1)
            elif key in (curses.KEY_RIGHT, ord('l')):
                self._scroll_x(1)
            elif key in (10, 13):
                # ENTER key
                self._run_command(ShowCommand)
            elif key == ord(':'):
                self._prompt()
            elif key == ord('/'):
                # TODO searching
                pass
            elif key == ord('?'):
                # TODO help
                pass
            elif key == ord('a'):
                self._prompt('add')
            elif key == ord('d'):
                self._run_command(DeleteCommand)
            elif key == ord('e'):
                # TODO edit command
                pass
            elif key == ord('o'):
                # TODO open command
                pass
            elif key == ord('s'):
                # TODO sorting
                pass
            elif key == ord('w'):
                # first, ensure left_edge is set to 0
                self.left_edge = 0
                # then, wrap the buffer
                self.buffer.wrap(self.width)
                self.buffer.view(self.viewport, self.visible, self.width-1)
            elif key == ord('x'):
                # TODO export command
                pass

            # highlight current line
            self.viewport.chgat(self.current_line, 0, curses.color_pair(2))

            # Refresh the screen
            self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

            # Wait for next input
            key = self.stdscr.getch()

    def _scroll_y(self, update):
        next_line = self.current_line + update
        # scroll up
        if update == -1:
            if self.top_line > 0 and next_line < self.top_line:
                self.top_line += update
            if next_line >= 0:
                self.current_line = next_line
        # scroll down
        elif update == 1:
            if next_line - self.top_line == self.visible and \
                    self.top_line + self.visible < self.buffer.height:
                self.top_line += update
            if next_line < self.buffer.height:
                self.current_line = next_line

    def _scroll_x(self, update):
        next_col = self.left_edge + update
        # limit column such that no empty columns can appear on left or right
        if 0 <= next_col <= self.buffer.width - self.width:
            self.left_edge = next_col

    def _prompt(self, command=None):
        # enter echo mode and make cursor visible
        curses.echo()
        curses.curs_set(1)

        # populate prompt line and place cursor
        prompt = ":" if command is None else f":{command} "
        self.prompt.addstr(0, 0, prompt)
        self.prompt.move(0, len(prompt))
        self.prompt.refresh()

        key = 0
        # handle special keys
        while key != 27:  # exit on ESC
            if key == 127:  # BACKSPACE
                cur_y, cur_x = self.prompt.getyx()
                # replace last three characters with spaces (2 characters from BACKSPACE key)
                self.prompt.addstr(cur_y, cur_x - 3, '   ')
                self.prompt.move(cur_y, cur_x - 3)
            elif key in (10, 13):  # ENTER
                # TODO handle command
                break
            key = self.prompt.getch()

        # leave echo mode and make cursor invisible
        curses.noecho()
        curses.curs_set(0)

        # clear prompt line
        self.prompt.clear()
        self.prompt.refresh()

    def _run_command(self, cmd):
        # get current label
        cur_y, _ = self.viewport.getyx()
        label = ''
        char = ''
        cur_x = 0
        while char != ' ':
            label += char
            char = chr(self.viewport.inch(cur_y, cur_x))
            cur_x += 1

        # populate buffer
        self.buffer.clear()
        cmd().execute([label], out=self.buffer)
        if self.buffer.lines:
            self.buffer.split()
            self.buffer.view(self.viewport, self.visible, self.width-1)

            # fall into nested key event loop
            prev_current = self.current_line
            self.current_line = 0
            self.loop(disabled=[ord('a'), 10, 13])
            self.current_line = prev_current
        else:
            # something changed in the database
            self.initial_list.clear()
            ListCommand().execute(['--long'], out=self.initial_list)

        # populate buffer with list of reference entries
        self.buffer = self.initial_list.copy()
        self.buffer.view(self.viewport, self.visible, self.width-1)


def tui():
    """Main executable for the curses-TUI."""
    curses.wrapper(TUI)


if __name__ == '__main__':
    tui()
