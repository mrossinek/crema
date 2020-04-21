"""CoBib show command"""

import argparse
import sys

from cobib import __version__
from .base_command import Command


class ShowCommand(Command):
    """Show Command"""

    name = 'show'

    def execute(self, args, out=sys.stdout):
        """show entry

        Prints the details of a selected entry in bibtex format to stdout.
        """
        parser = argparse.ArgumentParser(prog="show", description="Show subcommand parser.")
        parser.add_argument("label", type=str, help="label of the entry")
        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)
        largs = parser.parse_args(args)
        bib_data = self._read_database()
        try:
            entry = bib_data[largs.label]
            entry_str = entry.to_bibtex()
            print(entry_str, file=out)
        except KeyError:
            print("Error: No entry with the label '{}' could be found.".format(largs.label))

    def tui(self, tui):
        """TUI command interface"""
        # get current label
        label, prev_current = tui.get_current_label()
        # populate buffer with entry data
        tui.buffer.clear()
        self.execute([label], out=tui.buffer)
        tui.buffer.split()
        tui.buffer.view(tui.viewport, tui.visible, tui.width-1)

        # store previously selected line
        tui.current_line = 0
        # update top statusbar
        tui.topstatus = "CoBib v{} - {}".format(__version__, label)
        tui.statusbar(tui.topbar, tui.topstatus)
        # enter show menu
        tui.inactive_commands = ['Add', 'Filter', 'Search', 'Show', 'Sort']
        tui.loop()

        # restore selected line and list view
        tui.inactive_commands = []
        tui.update_database_list()
        tui.current_line = min(prev_current, tui.buffer.height-1)
