"""CoBib's TUI state."""

import logging

from cobib.config import CONFIG

LOGGER = logging.getLogger(__name__)


class State:
    """State class to track the stateful parameters of CoBib's TUI.

    State objects are used to store all stateful parameters of CoBib's TUI and simplify the handling
    of these parameters across the TUI and Frame objects.
    """

    def __init__(self):
        """Initializes the State object."""
        LOGGER.debug('Initializing the State')
        self.current_line = 0
        self.top_line = 0
        self.left_edge = 0
        self.selection = set()
        self.list_mode = -1
        self.inactive_commands = []
        self.list_args = []

    def initialize(self):
        """Initialize configuration-dependent settings."""
        self.list_args = CONFIG.config['TUI'].get('default_list_args').split(' ')
        if CONFIG.config['TUI'].getboolean('reverse_order', True):
            self.list_args += ['-r']


STATE = State()
