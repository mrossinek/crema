"""CoBib curses interface"""

import curses
from signal import signal, SIGWINCH

from cobib import __version__
from cobib import commands
from .buffer import TextBuffer


class TUI:  # pylint: disable=too-many-instance-attributes
    """CoBib's curses-based TUI.

    The TUI is implemented as a class to simplify management of different windows/pads and keep a
    synchronized state most consistently.
    """

    # available command dictionary
    COMMANDS = {
        'Add': lambda _: None,  # TODO add command
        'Delete': commands.DeleteCommand.tui,
        'Edit': commands.EditCommand.tui,
        'Export': lambda _: None,  # TODO export command
        'Filter': lambda _: None,  # TODO filter command
        'Help': lambda _: None,  # TODO help command
        'Open': commands.OpenCommand.tui,
        'Prompt': lambda _: None,  # TODO command prompt
        'Quit': lambda self: self.quit(),
        'Search': lambda _: None,  # TODO search command
        'Select': lambda _: None,  # TODO select command
        'Show': commands.ShowCommand.tui,
        'Sort': lambda _: None,  # TODO sort command
        'Wrap': lambda self: self.wrap(),
        'down': lambda self: self.scroll_y(1),
        'left': lambda self: self.scroll_x(-1),
        'right': lambda self: self.scroll_x(1),
        'up': lambda self: self.scroll_y(-1),
    }
    # standard key bindings
    KEYDICT = {
        10: 'Show',  # line feed = ENTER
        13: 'Show',  # carriage return = ENTER
        curses.KEY_DOWN: 'down',
        curses.KEY_LEFT: 'left',
        curses.KEY_RIGHT: 'right',
        curses.KEY_UP: 'up',
        ord('/'): 'Search',
        ord(':'): 'Prompt',
        ord('?'): 'Help',
        ord('a'): 'Add',
        ord('d'): 'Delete',
        ord('e'): 'Edit',
        ord('f'): 'Filter',
        ord('h'): 'left',
        ord('j'): 'down',
        ord('k'): 'up',
        ord('l'): 'right',
        ord('o'): 'Open',
        ord('q'): 'Quit',
        ord('s'): 'Sort',
        ord('v'): 'Select',
        ord('w'): 'Wrap',
        ord('x'): 'Export',
    }

    def __init__(self, stdscr):
        self.stdscr = stdscr

        # register resize handler
        signal(SIGWINCH, self.resize_handler)

        # Clear and refresh the screen for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # Initialize layout
        curses.curs_set(0)
        self.height, self.width = self.stdscr.getmaxyx()
        self.visible = self.height-3
        # and colors
        TUI.colors()
        # and inactive commands
        self.inactive_commands = []

        # Initialize top status bar
        self.topbar = curses.newwin(1, self.width, 0, 0)
        self.topbar.bkgd(' ', curses.color_pair(1))

        # Initialize bottom status bar
        # NOTE: -2 leaves an additional empty line for the command prompt
        self.botbar = curses.newwin(1, self.width, self.height-2, 0)
        self.botbar.bkgd(' ', curses.color_pair(1))
        self.statusbar(self.botbar, self.infoline)

        # Initialize command prompt and viewport
        self.prompt = curses.newwin(1, self.width, self.height-1, 0)
        self.viewport = curses.newpad(1, 1)

        # populate buffer with list of reference entries
        self.buffer = TextBuffer()
        self.update_list()

        # prepare and start key event loop
        self.current_line = 0
        self.list_mode = -1  # -1: list mode active, >=0: previously selected line
        self.top_line = 0
        self.left_edge = 0
        self.loop()

    def resize_handler(self, signum, frame):  # pylint: disable=unused-argument
        """Handles terminal window resize events."""
        # stop curses window
        curses.endwin()
        # clear and refresh for a blank canvas
        self.stdscr.clear()
        self.stdscr.refresh()
        # update total dimension data
        self.height, self.width = self.stdscr.getmaxyx()
        self.visible = self.height-3
        # update top statusbar
        self.topbar.resize(1, self.width)
        self.statusbar(self.topbar, self.topstatus)
        self.topbar.refresh()
        # update bottom statusbar
        self.botbar.resize(1, self.width)
        self.botbar.mvwin(self.height-2, 0)
        self.statusbar(self.botbar, self.infoline)
        self.botbar.refresh()
        # update prompt
        self.prompt.resize(1, self.width)
        self.prompt.mvwin(self.height-1, 0)
        # update viewport
        self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

    def quit(self):
        """Break the key event loop."""
        if self.list_mode == -1:
            raise StopIteration
        self.current_line = self.list_mode
        self.update_list()

    @staticmethod
    def colors():
        """Initialize the color pairs for the curses TUI."""
        # Start colors in curses
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_CYAN)

    @staticmethod
    def statusbar(statusline, text, attr=0):
        """Update the text in the provided status bar and refresh it."""
        statusline.erase()
        _, max_x = statusline.getmaxyx()
        statusline.addnstr(0, 0, text, max_x-1, attr)
        statusline.refresh()

    @property
    def infoline(self):
        """Lists available key bindings."""
        cmds = ["Quit", "Help", "", "Show", "Open", "Wrap", "", "Add", "Edit", "Delete", "",
                "Search", "Filter", "Sort", "Select", "", "Export"]
        infoline = ''
        for cmd in cmds:
            if cmd:
                # get associated key for this command
                for key, command in TUI.KEYDICT.items():
                    if cmd == command:
                        key = 'ENTER' if key in (10, 13) else chr(key)
                        infoline += " {}:{}".format(key, cmd)
                        break
            else:
                infoline += "  "
        return infoline.strip()

    def loop(self):
        """The key-handling event loop."""
        key = 0
        # key is the last character pressed
        while True:
            # reset highlight of current line
            self.viewport.chgat(self.current_line, 0, curses.A_NORMAL)

            # handle possible keys
            try:
                if key in TUI.KEYDICT.keys():
                    cmd = TUI.KEYDICT[key]
                    if cmd not in self.inactive_commands:
                        TUI.COMMANDS[cmd](self)
                elif key == curses.KEY_RESIZE:
                    self.resize_handler(None, None)
            except StopIteration:
                # raised by quit command
                break

            # highlight current line
            self.viewport.chgat(self.current_line, 0, curses.color_pair(2))

            # Refresh the screen
            self.viewport.refresh(self.top_line, self.left_edge, 1, 0, self.visible, self.width-1)

            # Wait for next input
            key = self.stdscr.getch()

    def scroll_y(self, update):
        """Scroll viewport vertically."""
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

    def scroll_x(self, update):
        """Scroll viewport horizontally."""
        next_col = self.left_edge + update
        # limit column such that no empty columns can appear on left or right
        if 0 <= next_col <= self.buffer.width - self.width:
            self.left_edge = next_col

    def wrap(self):
        """Toggles wrapping of the text currently displayed in the viewport."""
        # first, ensure left_edge is set to 0
        self.left_edge = 0
        # then, wrap the buffer
        self.buffer.wrap(self.width)
        self.buffer.view(self.viewport, self.visible, self.width-1)

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

        # TODO return prompt string

    def get_current_label(self):
        """Obtain label of currently selected entry."""
        # Two cases are possible: the list and the show mode
        if self.list_mode == -1:
            # In the list mode, the label can be found in the current line
            # or in one of the previous lines if we are on a wrapped line
            cur_y, _ = self.viewport.getyx()
            while chr(self.viewport.inch(cur_y, 0)) == TextBuffer.INDENT[0]:
                cur_y -= 1
            label = self.viewport.instr(cur_y, 0).decode('utf-8').split(' ')[0]
            self.list_mode = cur_y
        else:
            # In any other mode, the label can be found in the top statusbar
            label = '-'.join(self.topbar.instr(0, 0).decode('utf-8').split('-')[1:]).strip()
        return label

    def update_list(self):
        """Updates the default list view."""
        self.buffer.clear()
        labels = commands.ListCommand().execute(['--long'], out=self.buffer)
        # populate buffer with the list
        self.list_mode = -1
        self.inactive_commands = []
        self.buffer.view(self.viewport, self.visible, self.width-1)
        # update top statusbar
        self.topstatus = "CoBib v{} - {} Entries".format(__version__, len(labels))
        self.statusbar(self.topbar, self.topstatus)
