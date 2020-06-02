"""Tests for CoBib's TUI."""
# pylint: disable=unused-argument, redefined-outer-name

import curses
import os
import select
from pathlib import Path

import pyte
import pytest
from cobib import __version__ as version
from cobib.commands import AddCommand, DeleteCommand
from cobib.config import CONFIG
from cobib.database import read_database
from cobib.tui import TUI


@pytest.fixture
def setup():
    """Setup."""
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    read_database()
    AddCommand().execute(['-b', './test/dummy_scrolling_entry.bib'])
    yield setup
    DeleteCommand().execute(['dummy_entry_for_scroll_testing'])


def assert_normal_view(screen):
    """Asserts the normal view of the TUI."""
    # the top statusline contains the version info and number of entries
    assert f"CoBib v{version} - 4 Entries" in screen.display[0]
    # current line should be first line below top statusbar
    assert screen.display[1][-4:] == "@@@@"  # testing mode indicator for current line
    # the entries per line
    assert "einstein" in screen.display[1]
    assert "latexcompanion" in screen.display[2]
    assert "knuthwebsite" in screen.display[3]
    # the prompt line should be empty
    assert screen.display[-1].strip() == ""


def assert_help_screen(screen):
    """Asserts the contents of the Help screen."""
    assert "CoBib TUI Help" in screen.display[2]
    for cmd, desc in TUI.HELP_DICT.items():
        assert any("{:<8} {}".format(cmd+':', desc) in line for line in screen.display[4:21])


def assert_scroll(screen, update, direction):
    """Asserts cursor-line position after scrolling.

    Attention: The values of update *strongly* depend on the contents of the dummy scrolling entry.
    """
    if direction == 'y' or update == 0:
        assert screen.display[1 + update][-4:] == "@@@@"
    elif direction == 'x':
        assert screen.display[1][-4 - update:-update] == "@@@@"


def assert_delete(screen):
    """Asserts entry is deleted.

    This also ensures it is added again after successful deletion.
    """
    assert f"CoBib v{version} - 3 Entries" in screen.display[0]
    assert not any("dummy_entry_for_scroll_testing" in line for line in screen.display[4:21])
    AddCommand().execute(['-b', './test/dummy_scrolling_entry.bib'])


def assert_editor(screen):
    """Asserts the editor opens."""
    assert False


@pytest.mark.parametrize(['keys', 'assertion', 'assertion_kwargs'], [
        ['', assert_normal_view, {}],
        ['?', assert_help_screen, {}],
        ['?q', assert_normal_view, {}],  # also checks the quit command
        ['j', assert_scroll, {'update': 1, 'direction': 'y'}],
        ['jjk', assert_scroll, {'update': 1, 'direction': 'y'}],
        ['G', assert_scroll, {'update': 3, 'direction': 'y'}],
        ['Gg', assert_scroll, {'update': 0, 'direction': 'y'}],
        ['l', assert_scroll, {'update': 1, 'direction': 'x'}],
        ['llh', assert_scroll, {'update': 1, 'direction': 'x'}],
        ['$', assert_scroll, {'update': 23, 'direction': 'x'}],
        ['$0', assert_scroll, {'update': 0, 'direction': 'x'}],
        ['w', lambda _: None, {}],
        ['a', lambda _: None, {}],
        ['Gd', assert_delete, {}],
        ['e', assert_editor, {}],
        ['f', lambda _: None, {}],
        ['s', lambda _: None, {}],
        ['o', lambda _: None, {}],
        ['x', lambda _: None, {}],
        ['/', lambda _: None, {}],  # TODO unittest Search command
        ['v', lambda _: None, {}],  # TODO unittest Select command
    ])
def test_tui(setup, keys, assertion, assertion_kwargs):
    """Test TUI.

    Args:
        setup: runs pytest fixture.
        keys (str): keys to be send to the CoBib TUI.
        assertion (Callable): function to run the assertions for the key to be tested.
        assertion_kwargs (dict): additional keyword arguments for assertion function.
    """
    # create pseudo-terminal
    pid, f_d = os.forkpty()
    if pid == 0:
        # child process spawns TUI
        curses.wrapper(TUI, test=True)
    else:
        # parent process sets up virtual screen of identical size
        screen = pyte.Screen(80, 24)
        stream = pyte.ByteStream(screen)
        # send keys char-wise to TUI
        for key in keys:
            os.write(f_d, str.encode(key))
        # scrape pseudo-terminal's screen
        while True:
            try:
                [f_d], _, _ = select.select([f_d], [], [], 1)
            except (KeyboardInterrupt, ValueError):
                # either test was interrupted or file descriptor of child process provides nothing
                # to be read
                break
            else:
                try:
                    # scrape screen of child process
                    data = os.read(f_d, 1024)
                    stream.feed(data)
                except OSError:
                    # reading empty
                    break
        for line in screen.display:
            print(line)
        assertion(screen, **assertion_kwargs)
