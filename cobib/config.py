"""CoBib configuration module."""

import copy
import importlib.util
import io
import logging
import os
import sys

LOGGER = logging.getLogger(__name__)

ANSI_COLORS = [
    'black',
    'red',
    'green',
    'yellow',
    'blue',
    'magenta',
    'cyan',
    'white',
]

XDG_CONFIG_FILE = '~/.config/cobib/config.py'


class Config(dict):
    """CoBib's configuration object.

    Source: https://stackoverflow.com/a/3031270
    """

    MARKER = object()

    # pylint: disable=super-init-not-called
    def __init__(self, value=None):
        if value is None:
            pass
        elif isinstance(value, dict):
            for key in value:
                self.__setitem__(key, value[key])
        else:
            raise TypeError('expected dict')

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, Config):
            value = Config(value)
        super().__setitem__(key, value)

    def __getitem__(self, key):
        found = self.get(key, Config.MARKER)
        if found is Config.MARKER:
            found = Config()
            super().__setitem__(key, found)
        return found

    __setattr__, __getattr__ = __setitem__, __getitem__

    @staticmethod
    def load(configpath=None):
        """TODO"""
        if configpath is not None:
            if isinstance(configpath, io.TextIOWrapper):
                configpath = configpath.name
            LOGGER.info('Loading configuration from %s', configpath)
        elif os.path.exists(os.path.expanduser(XDG_CONFIG_FILE)):
            LOGGER.info('Loading configuration from default location: %s',
                        os.path.expanduser(XDG_CONFIG_FILE))
            configpath = os.path.expanduser(XDG_CONFIG_FILE)
        else:
            return
        spec = importlib.util.spec_from_file_location("config", configpath)
        cfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cfg)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            self[key] = copy.deepcopy(value)

    def get_ansi_color(self, name):
        """Returns an ANSI color code for the named color.

        Args:
            name (str): a named color as specified in the configuration *excluding* the `_fg` or
                        `_bg` suffix.

        Returns:
            A string representing the foreground and background ANSI color code.
        """
        fg_color = 30 + ANSI_COLORS.index(self.tui.colors.get(name + '_fg'))
        bg_color = 40 + ANSI_COLORS.index(self.tui.colors.get(name + '_bg'))

        return f'\x1b[{fg_color};{bg_color}m'

    DEFAULTS = {
        'database': {
            'file': os.path.expanduser('~/.local/share/cobib/literature.yaml'),
            'git': False,
            'open': 'xdg-open' if sys.platform.lower() == 'linux' else 'open',
            'grep': 'grep',
            'search_ignore_case': False,
        },
        'format': {
            'month': int,
            'ignore_non_standard_types': False,
            'default_entry_type': 'article',
        },
        'tui': {
            'default_list_args': '-l',
            'prompt_before_quit': True,
            'reverse_order': True,
            'scroll_offset': 3,
            'colors': {
                'cursor_line_fg': 'white',
                'cursor_line_bg': 'cyan',
                'top_statusbar_fg': 'black',
                'top_statusbar_bg': 'yellow',
                'bottom_statusbar_fg': 'black',
                'bottom_statusbar_bg': 'yellow',
                'search_label_fg': 'blue',
                'search_label_bg': 'black',
                'search_query_fg': 'red',
                'search_query_bg': 'black',
                'popup_help_fg': 'white',
                'popup_help_bg': 'green',
                'popup_stdout_fg': 'white',
                'popup_stdout_bg': 'blue',
                'popup_stderr_fg': 'white',
                'popup_stderr_bg': 'red',
                'selection_fg': 'white',
                'selection_bg': 'magenta',
            },
            'key_bindings': {
                'prompt': ':',
                'search': '/',
                'help': '?',
                'add': 'a',
                'delete': 'd',
                'edit': 'e',
                'filter': 'f',
                'modify': 'm',
                'open': 'o',
                'quit': 'q',
                'redo': 'r',
                'sort': 's',
                'undo': 'u',
                'select': 'v',
                'wrap': 'w',
                'export': 'x',
                'show': 'ENTER',
            },
        },
    }

    def defaults(self):
        """TODO"""
        try:
            del self.database
        except AttributeError:
            pass
        self.database.update(**self.DEFAULTS['database'])

        try:
            del self.format
        except AttributeError:
            pass
        self.format.update(**self.DEFAULTS['format'])

        try:
            del self.tui
        except AttributeError:
            pass
        self.tui.update(**self.DEFAULTS['tui'])

    def validate(self):
        """Validates the configuration at runtime."""
        LOGGER.info('Validating the runtime configuration.')

        # DATABASE section
        LOGGER.debug('Validating the DATABASE configuration section.')
        self._assert(self.database, "Missing config.database section!")
        self._assert(isinstance(self.database.file, str),
                     "config.database.file should be a string.")
        self._assert(isinstance(self.database.git, bool),
                     "config.database.git should be a boolean.")
        self._assert(isinstance(self.database.open, str),
                     "config.database.open should be a string.")
        self._assert(isinstance(self.database.grep, str),
                     "config.database.grep should be a string.")
        self._assert(isinstance(self.database.search_ignore_case, bool),
                     "config.database.search_ignore_case should be a boolean.")

        # FORMAT section
        LOGGER.debug('Validating the FORMAT configuration section.')
        self._assert(self.format, "Missing config.format section!")
        self._assert(self.format.month in (int, str),
                     "config.format.month should be either the `int` or `str` Python type.")
        self._assert(isinstance(self.format.ignore_non_standard_types, bool),
                     "config.format.ignore_non_standard_types should be a boolean.")
        self._assert(isinstance(self.format.default_entry_type, str),
                     "config.format.default_entry_type should be a string.")

        # TUI section
        LOGGER.debug('Validating the TUI configuration section.')
        self._assert(self.tui, "Missing config.tui section!")
        self._assert(isinstance(self.tui.default_list_args, str),
                     "config.tui.default_list_args should be a string.")
        self._assert(isinstance(self.tui.prompt_before_quit, bool),
                     "config.tui.prompt_before_quit should be a boolean.")
        self._assert(isinstance(self.tui.reverse_order, bool),
                     "config.tui.reverse_order should be a boolean.")
        self._assert(isinstance(self.tui.scroll_offset, int),
                     "config.tui.scroll_offset should be an integer.")

        # TUI.COLORS section
        self._assert(self.tui.colors, "Missing config.tui.colors section!")
        for name in self.DEFAULTS['tui']['colors'].keys():
            self._assert(name in self.tui.colors.keys(),
                         f"Missing config.tui.colors.{name} specification!")

        for name, color in self.tui.colors.items():
            if name not in self.DEFAULTS['tui']['colors'].keys() and name not in ANSI_COLORS:
                LOGGER.warning('Ignoring unkonwn TUI color: %s.', name)
            self._assert(color in ANSI_COLORS or
                         (len(color.strip('#')) == 6 and
                          tuple(int(color.strip('#')[i:i+2], 16) for i in (0, 2, 4))),
                         f"Unknown color specification: {color}")

        # TUI.KEY_BINDINGS section
        self._assert(self.tui.key_bindings, "Missing config.tui.key_bindings section!")
        for command in self.DEFAULTS['tui']['key_bindings'].keys():
            self._assert(command in self.tui.key_bindings.keys(),
                         f"Missing config.tui.key_bindings.{command} key binding!")
        for command, key in self.DEFAULTS['tui']['key_bindings'].items():
            self._assert(isinstance(key, str),
                         f"config.tui.key_bindings.{command} should be a string.")

    @staticmethod
    def _assert(expression, error):
        """Asserts the expression is True.

        Raises:
            RuntimeError with the specified error string.
        """
        if not expression:
            raise RuntimeError(error)


config = Config()
config.defaults()
