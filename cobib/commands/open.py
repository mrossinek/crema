"""CoBib open command."""

import argparse
import logging
import os
import subprocess
import sys
from urllib.parse import urlparse

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class OpenCommand(Command):
    """Open Command."""

    name = 'open'

    def execute(self, args, out=sys.stderr):
        """Open file from entries.

        Opens the associated file of the entries with xdg-open.

        Args: See base class.
        """
        LOGGER.debug('Starting Open command.')
        parser = ArgumentParser(prog="open", description="Open subcommand parser.")
        parser.add_argument("labels", type=str, nargs='+', help="labels of the entries")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return None

        opener = CONFIG.config['DATABASE'].get('open', None)

        errors = []
        for label in largs.labels:
            things_to_open = {}
            # first: find all possible things to open
            try:
                entry = CONFIG.config['BIB_DATA'][label]
                if 'file' in entry.data.keys() and entry.data['file']:
                    LOGGER.debug('Parsing "%s" for URLs.', entry.data['file'])
                    things_to_open['file'] = urlparse(entry.data['file'])
            except KeyError:
                msg = "Error: No entry with the label '{}' could be found.".format(label)
                LOGGER.error(msg)
                continue

            # if there are none, skip current label
            if not things_to_open:
                msg = "Error: There is no file associated with this entry."
                LOGGER.error(msg)
                if out is None:
                    errors.append(msg)
                continue

            try:
                # TODO instead of simply opening all we should prompt the user what to do here
                # - if a single entry exists, simply open it
                # - if multiple exist, print a menu for the user to choose from
                # - the choices should be either a single entry given by index, or a group of values
                # given by their field, or all of them
                # now try to open them
                for url in things_to_open.values():
                    if url.scheme:
                        # actual URL
                        url = url.geturl()
                    else:
                        # assume we are talking about a file and thus get its absolute path
                        url = os.path.abspath(url.geturl())
                    LOGGER.debug('Opening "%s" with %s.', url, opener)
                    with open(os.devnull, 'w') as devnull:
                        subprocess.Popen([opener, url], stdout=devnull, stderr=devnull,
                                         stdin=devnull, close_fds=True)
            except FileNotFoundError as err:
                LOGGER.error(err)
                errors.append(str(err))

        return '\n'.join(errors)

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Open command triggered from TUI.')
        if tui.selection:
            # use selection for command
            labels = list(tui.selection)
        else:
            # get current label
            label, _ = tui.get_current_label()
            labels = [label]
        # populate buffer with entry data
        error = OpenCommand().execute(labels, out=None)
        if error:
            tui.prompt_print(error)
