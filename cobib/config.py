"""CoBib configuration module."""

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

    def validate(self):
        """Validates the configuration at runtime."""
        LOGGER.info('Validating the runtime configuration.')
        # TODO

    @staticmethod
    def _assert(expression, error):
        """Asserts the expression is True.

        Raises:
            RuntimeError with the specified error string.
        """
        if not expression:
            raise RuntimeError(error)

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

    def defaults(self):
        """TODO"""
        self.database.file = os.path.expanduser('~/.local/share/cobib/literature.yaml')
        self.database.git = False
        self.database.open = 'xdg-open' if sys.platform.lower() == 'linux' else 'open'
        self.database.grep = 'grep'
        self.database.search_ignore_case = False

        self.format.month = int
        self.format.ignore_non_standard_types = False
        self.format.default_entry_type = 'article'

        self.tui.default_list_args = '-l'
        self.tui.prompt_before_quit = True
        self.tui.reverse_order = True
        self.tui.scroll_offset = 3

        self.tui.colors.cursor_line_fg = 'white'
        self.tui.colors.cursor_line_bg = 'cyan'
        self.tui.colors.top_statusbar_fg = 'black'
        self.tui.colors.top_statusbar_bg = 'yellow'
        self.tui.colors.bottom_statusbar_fg = 'black'
        self.tui.colors.bottom_statusbar_bg = 'yellow'
        self.tui.colors.search_label_fg = 'blue'
        self.tui.colors.search_label_bg = 'black'
        self.tui.colors.search_query_fg = 'red'
        self.tui.colors.search_query_bg = 'black'
        self.tui.colors.popup_help_fg = 'white'
        self.tui.colors.popup_help_bg = 'green'
        self.tui.colors.popup_stdout_fg = 'white'
        self.tui.colors.popup_stdout_bg = 'blue'
        self.tui.colors.popup_stderr_fg = 'white'
        self.tui.colors.popup_stderr_bg = 'red'
        self.tui.colors.selection_fg = 'white'
        self.tui.colors.selection_bg = 'magenta'

        self.tui.key_bindings.prompt = ':'
        self.tui.key_bindings.search = '/'
        self.tui.key_bindings.help = '?'
        self.tui.key_bindings.add = 'a'
        self.tui.key_bindings.delete = 'd'
        self.tui.key_bindings.edit = 'e'
        self.tui.key_bindings.filter = 'f'
        self.tui.key_bindings.modify = 'm'
        self.tui.key_bindings.open = 'o'
        self.tui.key_bindings.quit = 'q'
        self.tui.key_bindings.redo = 'r'
        self.tui.key_bindings.sort = 's'
        self.tui.key_bindings.undo = 'u'
        self.tui.key_bindings.select = 'v'
        self.tui.key_bindings.wrap = 'w'
        self.tui.key_bindings.export = 'x'
        self.tui.key_bindings.show = 'ENTER'


config = Config()
config.defaults()
