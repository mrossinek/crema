"""An example configuration file for CoBib.

Since version 3.0 CoBib is configured through a Python file.
For documentation purposes this example configuration file lists all possible settings with
explanations and their default settings.

For anyone who knows a little bit of Python, here are some insights on how this configuration works.
Internally, CoBib's configuration is nothing but a (nested) Python dictionary. However, for ease of
usage all of its fields are also exposed as attributes. This means, that the following two lines are
equivalent:
    config['database']['git'] = True
    config.database.git = True
"""

# Generally, you won't need these, but the default configuration relies on them.
import os
import sys

# To get started you must import CoBib's configuration.
from cobib.config import config
# Now, you are all set to apply your own settings.


# COMMANDS
# These settings affect some command specific behavior.

# You can specify the default bibtex entry type via the following setting:
config.commands.edit.default_entry_type = 'article'

# You can specify a custom command which will be used to `open` files associated with your entries.
config.commands.open.command = 'xdg-open' if sys.platform.lower() == 'linux' else 'open'

# You can specify a custom grep tool which will be used to search through your database and any
# associated files. The default tool (`grep`) will not provide results for attached PDFs but other
# tools such as [ripgrep-all](https://github.com/phiresky/ripgrep-all) will.
config.commands.search.grep = 'grep'

# You can specify whether searches should be performed case-insensitive. By default, this is off.
config.commands.search.ignore_case = False


# DATABASE
# These settings affect the database in general.

# You can specify the path to the database YAML file by changing the following setting.
# You can use a `~` to represent your `$HOME` directory.
config.database.file = os.path.expanduser('~/.local/share/cobib/literature.yaml')

# CoBib can integrate with `git` in order to automatically track the history of your database.
# However, by default, this option is disabled. If you want to enable it, simply change the
# following setting to `True` and initialize your database with `cobib init --git`.
# Warning: Before enabling this setting you must ensure that you have set up git properly by setting
# your name and email address.
config.database.git = False

# DATABASE.FORMAT
# You can also specify some aspects about the format of the database (currently only one but there
# will be more in the future).

# You can specify the type of the `month` field. It can be either `int` or `str` and will be
# converted automatically. I.e. '8' will become 'aug' if you set this to `str`.
config.database.format.month = int


# PARSERS
# These settings affect some parser specific behavior.

# You can specify whether the bibtex-parser should ignore non-standard bibtex entry types.
config.parsers.bibtex.ignore_non_standard_types = False


# TUI
# These settings affect the functionality and look of the TUI.

# You can specify a list of default arguments for the default list view.
config.tui.default_list_args = ['-l']

# You can disable the prompt before quitting CoBib by turning off the following setting:
config.tui.prompt_before_quit = True

# You can specify whether the list view of the TUI should be reversed. By default, this is enabled,
# because this will place the most recently entries at the top of the TUI.
config.tui.reverse_order = True

# You can specify a scroll offset. This corresponds to the number of lines which will be kept
# visible above or below the cursor line while scrolling the buffer. If you set this number to
# something very large (e.g. 99) you can pin the cursor line to the center of the window during
# scrolling.
config.tui.scroll_offset = 3

# TUI.COLORS
# With the following color settings you can change the look of the TUI. Each of these settings
# accepts any of the following color names: `black`, `red`, `green`, `yellow`, `blue`, `magenta`,
# `cyan` and `white`.
config.tui.colors.cursor_line_fg = 'white'
config.tui.colors.cursor_line_bg = 'cyan'
config.tui.colors.top_statusbar_fg = 'black'
config.tui.colors.top_statusbar_bg = 'yellow'
config.tui.colors.bottom_statusbar_fg = 'black'
config.tui.colors.bottom_statusbar_bg = 'yellow'
config.tui.colors.search_label_fg = 'blue'
config.tui.colors.search_label_bg = 'black'
config.tui.colors.search_query_fg = 'red'
config.tui.colors.search_query_bg = 'black'
config.tui.colors.popup_help_fg = 'white'
config.tui.colors.popup_help_bg = 'green'
config.tui.colors.popup_stdout_fg = 'white'
config.tui.colors.popup_stdout_bg = 'blue'
config.tui.colors.popup_stderr_fg = 'white'
config.tui.colors.popup_stderr_bg = 'red'
config.tui.colors.selection_fg = 'white'
config.tui.colors.selection_bg = 'magenta'

# Note, if your terminal supports it, you can even try to override the color specifications right
# from within CoBib. The check relies on the `curses.can_change_color()` function, which is more or
# less documented [here](https://docs.python.org/3/library/curses.html#curses.can_change_color).
# You can attempt to get this to work by overwriting the named colors with a `#RRGGBB` value like
# so:
#     config.tui.colors.black = `#222222`
# , which changes the black definition into a more mallow gray.

# TUI.KEY_BINDINGS
# You can also change the default key bindings of the TUI by overwriting any of the following
# settings with a different key.
config.tui.key_bindings.prompt = ':'
config.tui.key_bindings.search = '/'
config.tui.key_bindings.help = '?'
config.tui.key_bindings.add = 'a'
config.tui.key_bindings.delete = 'd'
config.tui.key_bindings.edit = 'e'
config.tui.key_bindings.filter = 'f'
config.tui.key_bindings.modify = 'm'
config.tui.key_bindings.open = 'o'
config.tui.key_bindings.quit = 'q'
config.tui.key_bindings.redo = 'r'
config.tui.key_bindings.sort = 's'
config.tui.key_bindings.undo = 'u'
config.tui.key_bindings.select = 'v'
config.tui.key_bindings.wrap = 'w'
config.tui.key_bindings.export = 'x'
config.tui.key_bindings.show = 'ENTER'
# Note, the exception of this last key which is set to the custom `ENTER` string. When CoBib
# encounters this string it will automatically map to the ASCII codes 10 and 13 (corresponding with
# the `line feed` and `carriage return`, respectively). Any other string is interpreted a single
# character whose ASCII value is used as the trigger.
