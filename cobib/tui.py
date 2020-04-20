"""CoBib curses interface"""

import curses

from cobib import __version__
from cobib.commands import ListCommand


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

        # populate buffer with list of reference entries
        self.buffer = TUI.TextBuffer()
        ListCommand().execute(['--long'], out=self.buffer)

        # NOTE The +1 added onto the height accounts for some weird offset in the curses pad.
        self.viewport = curses.newpad(self.buffer.height+1, self.buffer.width)
        for row, line in enumerate(self.buffer.lines):
            self.viewport.addstr(row, 0, line)

        self.loop()

    def colors(self):  # pylint: disable=no-self-use
        """Initialize the color pairs for the curses TUI."""
        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_CYAN)

    def statusbar(self, bar, text, attr=0):
        """Update the text in the provided statusbar and refresh it."""
        bar.addstr(0, 0, text, attr)
        bar.refresh()

    class TextBuffer:  # pylint: disable=too-few-public-methods
        """TextBuffer class used as an auxiliary variable to redirect output into.

        This buffer class implements a `write` method which allows it to be used as a drop-in source
        for the `file` argument of the `print()` method. Thereby, its output can be gathered in this
        buffer for further usage (such as printing it into a curses pad).
        """
        def __init__(self):
            self.lines = []
            self.height = 0
            self.width = 0

        def write(self, string):
            """Writes a non-empty string into the buffer."""
            if string.strip():
                # only handle non-empty strings
                self.lines.append(string)
                self.height = len(self.lines)
                self.width = max(self.width, len(string))

    def loop(self):
        """The key-handling event loop."""
        k = 0
        view_lines = self.height-3
        current_line = 0
        top_line = 0
        left_edge = 0

        # Loop where k is the last character pressed
        while k != ord('q'):
            self.viewport.chgat(current_line, 0, curses.A_NORMAL)
            update = 0
            scroll = 0
            if k in (curses.KEY_DOWN, ord('j')):
                update = 1
            elif k in (curses.KEY_UP, ord('k')):
                update = -1
            elif k in (curses.KEY_LEFT, ord('h')):
                scroll = -1
            elif k in (curses.KEY_RIGHT, ord('l')):
                scroll = 1

            next_line = current_line + update

            if update == -1:
                if top_line > 0 and next_line < top_line:
                    top_line += update
                if next_line >= 0:
                    current_line = next_line
            elif update == 1:
                if next_line - top_line == view_lines and \
                        top_line + view_lines < self.buffer.height:
                    top_line += update
                if next_line < self.buffer.height:
                    current_line = next_line

            next_col = left_edge + scroll
            if 0 <= next_col <= self.buffer.width - self.width:
                left_edge = next_col

            self.viewport.chgat(current_line, 0, curses.color_pair(2))

            # Refresh the screen
            self.viewport.refresh(top_line, left_edge, 1, 0, view_lines, self.width-1)

            # Wait for next input
            k = self.stdscr.getch()


def tui():
    """Main executable for the curses-TUI."""
    curses.wrapper(TUI)


if __name__ == '__main__':
    tui()
