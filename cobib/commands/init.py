"""Cobib init command."""

import argparse
import logging
import os
import sys
import warnings

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class InitCommand(Command):
    """Init Command."""

    name = 'init'

    def execute(self, args, out=sys.stdout):
        """Initialize database.

        Initializes the yaml database file at the configured location.

        Args: See base class.
        """
        LOGGER.debug('Starting Init command.')
        parser = ArgumentParser(prog="init", description="Init subcommand parser.")
        parser.add_argument('-g', '--git', action='store_true',
                            help="initialize git repository")
        parser.add_argument('-f', '--force', action='store_true',
                            help="DEPRECATED! This argument will be removed in v2.6")

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        if largs.force:
            msg = 'The "force" argument has been deprecated and is in the process of being removed.'
            warnings.warn(msg, DeprecationWarning)
            LOGGER.warning(msg)

        conf_database = CONFIG.config['DATABASE']
        file = os.path.realpath(os.path.expanduser(conf_database['file']))
        root = os.path.dirname(file)

        file_exists = os.path.exists(file)
        git_tracked = os.path.exists(os.path.join(root, '.git'))

        if file_exists:
            if git_tracked:
                msg = 'Database file already exists and is being tracked by git. ' + \
                      'There is nothing else to do.'
                print(msg, file=sys.stderr)
                LOGGER.info(msg)
                return

            if not git_tracked and not largs.git:
                msg = 'Database file already exists! Use --git to start tracking it with git.'
                print(msg, file=sys.stderr)
                LOGGER.warning(msg)
                return

        else:
            LOGGER.debug('Creating path for database file: "%s"', root)
            os.makedirs(root, exist_ok=True)

            LOGGER.debug('Creating empty database file: "%s"', file)
            open(file, 'w').close()

        if largs.git:
            if not conf_database.getboolean('git'):
                msg = 'You are about to initialize the git tracking of your database, but this ' + \
                      'will only have effect if you also enable the DATABASE/git setting in ' + \
                      'your configuration file!'
                print(msg, file=sys.stderr)
                LOGGER.warning(msg)
            LOGGER.debug('Initializing git repository in "%s"', root)
            os.system(f'git init {root}')
            self.git(force=True)
