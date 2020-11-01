"""CoBib open command."""

import argparse
import logging
import os
import subprocess
import sys
from collections import defaultdict
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

        errors = []
        for label in largs.labels:
            things_to_open = defaultdict(list)
            count = 0
            # first: find all possible things to open
            try:
                entry = CONFIG.config['BIB_DATA'][label]
                for field in ('file', 'url'):
                    if field in entry.data.keys() and entry.data[field]:
                        for val in entry.data[field].split(','):
                            LOGGER.debug('Parsing "%s" for URLs.', val)
                            things_to_open[field] += [urlparse(val)]
                            count += 1
            except KeyError:
                msg = "Error: No entry with the label '{}' could be found.".format(label)
                LOGGER.error(msg)
                continue

            # if there are none, skip current label
            if not things_to_open:
                msg = "Warning: This entry has no actionable field associated with it."
                LOGGER.warning(msg)
                if out is None:
                    errors.append(msg)
                continue

            if count == 1:
                # we found a single url to open
                err = self._open_url(list(things_to_open.values()))[0]
                if err:
                    errors.append(err)
            else:
                # we query the user what to do
                idx = 1
                url_list = []
                for field, urls in things_to_open.items():
                    for url in urls:
                        print(f"{idx:3}: [{field}] {url.geturl()}")
                        url_list.append(url)
                        idx += 1
                while True:
                    choice = input("Entry to open [Type 'help' for more info]: ")
                    if not choice:
                        msg = 'User aborted open command.'
                        LOGGER.warning(msg)
                        print(msg, file=sys.stderr)
                        return None
                    if choice == 'help':
                        LOGGER.debug('User requested help.')
                        help = "\nYou can specify one of the following options:" + \
                               "\n  1. a url number" + \
                               "\n  2. a field name provided in '[...]'" + \
                               "\n  3. or simply 'all'"
                        print(help)
                    elif choice == 'all':
                        LOGGER.debug('User selected all urls.')
                        for url in url_list:
                            err = self._open_url(url)
                            if err:
                                errors.append(err)
                        break
                    elif choice in things_to_open.keys():
                        LOGGER.debug('User selected the %s set of urls.', choice)
                        for url in things_to_open[choice]:
                            err = self._open_url(url)
                            if err:
                                errors.append(err)
                        break
                    elif choice.isdigit() and int(choice) > 0 and int(choice) <= count:
                        LOGGER.debug('User selected url %s', choice)
                        err = self._open_url(url_list[int(choice)-1])
                        if err:
                            errors.append(err)
                        break


        return '\n'.join(errors)

    @staticmethod
    def _open_url(url):
        """Opens a url."""
        opener = CONFIG.config['DATABASE'].get('open', None)
        try:
            url = url.geturl() if url.scheme else os.path.abspath(url.geturl())
            LOGGER.debug('Opening "%s" with %s.', url, opener)
            with open(os.devnull, 'w') as devnull:
                subprocess.Popen([opener, url], stdout=devnull, stderr=devnull,
                                 stdin=devnull, close_fds=True)
        except FileNotFoundError as err:
            LOGGER.error(err)
            return str(err)
        return ''

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
