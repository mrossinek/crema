"""CoBib modify command."""

import argparse
import logging
import os
import sys

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command
from .list import ListCommand

LOGGER = logging.getLogger(__name__)


class ModifyCommand(Command):
    """Modify Command."""

    name = 'modify'

    @staticmethod
    def field_value_pair(string):
        """Utility method to assert the field-value pair argument type.

        Args:
            string (str): the argument string to check.
        """
        # try splitting the string into field and value, any errors will be handled by argparse
        field, value = string.split(':')
        return (field, value)

    def execute(self, args, out=sys.stdout):
        """Modify entries.

        Allows bulk modification of entries.

        Args: See base class.
        """
        LOGGER.debug('Starting Modify command.')
        parser = ArgumentParser(prog="modify", description="Modify subcommand parser.")
        parser.add_argument("modification", type=self.field_value_pair,
                            help="Modification to apply to the specified entries."
                            "\nThis argument must be a string formatted as <field>:<value> where "
                            "field can be any field of the entries and value can be any string "
                            "which should be placed in that field. Be sure to escape this "
                            "field-value pair properly, especially if the value contains spaces."
                            )
        parser.add_argument("-a", "--append", action="store_true",
                            help="Appends to the modified field rather than overwriting it.")
        parser.add_argument("-s", "--selection", action="store_true",
                            help="Interprets `list_arg` as the list of selected entries.")
        parser.add_argument('list_arg', nargs='+',
                            help="Any arguments for the List subcommand."
                            "Use this to add filters to specify a subset of modified entries."
                            "You can should a '--' before the List arguments to ensure separation."
                            "See also `list --help` for more information on the List arguments."
                            "Note: when a selection has been made inside the TUI, this list is "
                            "interpreted as the list of entry labels to be modified. This also "
                            "requires the --selection argument to be set which you can exploit "
                            "on the command-line to achieve a similar effect.")

        if not args:
            parser.print_usage(sys.stderr)
            sys.exit(1)

        try:
            largs = parser.parse_intermixed_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        out = open(os.devnull, 'w')
        if largs.selection:
            LOGGER.info('Selection given. Interpreting `list_arg` as a list of labels')
            labels = largs.list_arg
        else:
            LOGGER.debug('Gathering filtered list of entries to be modified.')
            labels = ListCommand().execute(largs.list_arg, out=out)

        field, value = largs.modification

        if largs.append:
            msg = 'The append-mode of the `modify` command has not been implemented yet.'
            print(msg)
            LOGGER.warning(msg)
            sys.exit(1)

        for label in labels:
            try:
                entry = CONFIG.config['BIB_DATA'][label]
                entry.data[field] = value

                conf_database = CONFIG.config['DATABASE']
                file = os.path.expanduser(conf_database['file'])
                with open(file, 'r') as bib:
                    lines = bib.readlines()
                entry_to_be_replaced = False
                with open(file, 'w') as bib:
                    for line in lines:
                        if line.startswith(label + ':'):
                            LOGGER.debug('Entry "%s" found. Starting to replace lines.', label)
                            entry_to_be_replaced = True
                            continue
                        if entry_to_be_replaced and line.startswith('...'):
                            LOGGER.debug('Reached end of entry "%s".', label)
                            entry_to_be_replaced = False
                            bib.writelines('\n'.join(entry.to_yaml().split('\n')[1:]))
                            continue
                        if not entry_to_be_replaced:
                            bib.write(line)

                msg = f"'{label}' was modified."
                print(msg)
                LOGGER.info(msg)
            except KeyError:
                print("Error: No entry with the label '{}' could be found.".format(label))

        self.git(args=vars(largs))

    @staticmethod
    def tui(tui):
        """See base class."""
        LOGGER.debug('Modify command triggered from TUI.')
        # handle input via prompt
        if tui.selection:
            tui.execute_command('modify -s', pass_selection=True)
        else:
            tui.execute_command('modify')
