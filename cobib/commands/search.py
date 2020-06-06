"""CoBib search command."""

import argparse
import sys

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command


class SearchCommand(Command):
    """Search Command."""

    name = 'search'

    def execute(self, args, out=sys.stdout):
        """Search database.

        Searches the database recursively (i.e. including any associated files) for a query string.

        Args: See base class.
        """
        parser = ArgumentParser(prog="search", description="Search subcommand parser.")
        parser.add_argument("query", type=str, help="text to search for")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        output = []
        for label, entry in CONFIG.config['BIB_DATA'].items():
            matches = entry.search(largs.query)
            if not matches:
                continue

            output.append(label)
            if out == sys.stdout:
                output[-1] = '\033[1;34m' + output[-1] + '\033[0m'

            if out == sys.stdout:
                for line in matches:
                    line = line.replace(largs.query, '\033[31m' + largs.query + '\033[0m')
                    output.append(line)
            else:
                output.extend(matches)

        print('\n'.join(output), file=out)

    @staticmethod
    def tui(tui):
        """See base class."""
