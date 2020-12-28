"""CoBib undo command."""

import argparse
import logging
import os
import subprocess
import sys

from cobib.config import CONFIG
from .base_command import ArgumentParser, Command

LOGGER = logging.getLogger(__name__)


class UndoCommand(Command):
    """Undo Command."""

    name = 'undo'

    def execute(self, args, out=sys.stdout):
        """Undo last change.

        Undoes the last change to the database file. By default, only auto-commited changes by CoBib
        will be undone. Use `--force` to undo other changes, too.

        Args: See base class.
        """
        conf_database = CONFIG.config['DATABASE']
        git_tracked = conf_database.getboolean('git')
        if not git_tracked:
            msg = "You must enable CoBib's git-tracking in order to use the `Undo` command. " + \
                "Please refer to the man-page for more information on how to do so."
            print(msg, file=sys.stderr)
            LOGGER.error(msg)
            return

        file = os.path.realpath(os.path.expanduser(conf_database['file']))
        root = os.path.dirname(file)
        if not os.path.exists(os.path.join(root, '.git')):
            msg = "You have configured, but not initialized CoBib's git-tracking. " + \
                "Please consult `cobib init --help` for more information on how to do so."
            print(msg, file=sys.stderr)
            LOGGER.error(msg)
            return

        LOGGER.debug('Starting Undo command.')
        parser = ArgumentParser(prog="undo", description="Undo subcommand parser.")
        parser.add_argument("-f", "--force", action='store_true',
                            help="allow undoing non auto-commited changes")

        try:
            largs = parser.parse_args(args)
        except argparse.ArgumentError as exc:
            print("{}: {}".format(exc.argument_name, exc.message), file=sys.stderr)
            return

        LOGGER.debug('Obtaining git log.')
        lines = subprocess.check_output([
            "git", "--no-pager", "-C", f"{root}", "log", "--oneline", "--no-decorate", "--no-abbrev"
        ])
        reverted_shas = set()
        for commit in lines.decode().strip().split('\n'):
            LOGGER.debug('Processing commit %s', commit)
            sha, *message = commit.split()
            if message[0] == 'Revert':
                # revertion commits are produced by the `Undo` command and we don't want to undo
                # and undo (that's what `Redo` is for)
                LOGGER.debug('Revertion commits are not undone.')
                msg = subprocess.Popen([
                    "git", "--no-pager", "-C", f"{root}", "log", "--pretty=%B", "--max-count",
                    "1", f"{sha}"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                reverted_shas.add(
                    msg.stdout.read().decode().strip().split('\n')[-1].strip('.').split()[-1]
                )
                continue
            if sha in reverted_shas:
                LOGGER.info('Skipping %s as it was already reverted', sha)
                continue
            if largs.force or (message[0] == 'Auto-commit:' and message[-1] != 'InitCommand'):
                # we undo a commit iff:
                #  - the `force` argument is specified OR
                #  - the commit is an `auto-commited` change which is NOT from `InitCommand`
                LOGGER.debug('Attempting to undo %s.', sha)
                undo = subprocess.Popen([
                    "git", "-C", f"{root}", "revert", "--no-gpg-sign", "--no-edit", f"{sha}"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                undo.communicate()
                if undo.returncode != 0:
                    LOGGER.error('Undo was unsuccessful. Please consult the logs and git history of'
                                 ' your database for more information.')
                break
        else:
            msg = "Could not find a commit to undo. Please commit something first!"
            print(msg, file=sys.stderr)
            LOGGER.warning(msg)
            sys.exit(1)
