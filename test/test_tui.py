"""Tests for CoBib's TUI."""
# pylint: disable=unused-argument, redefined-outer-name

import curses
import os
import select
from pathlib import Path

import pyte
import pytest
from cobib import __version__ as version
from cobib.config import CONFIG
from cobib.database import read_database
from cobib.tui import TUI


@pytest.fixture
def setup():
    """Setup."""
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))
    read_database()


def assert_normal_startup(screen):
    """Asserts the normal startup of the TUI."""
    # the top statusline contains the version info and number of entries
    assert f"CoBib v{version} - 3 Entries" in screen.display[0]
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


@pytest.mark.parametrize(['key', 'assertion'], [
        ['q', assert_normal_startup],
        ['?', assert_help_screen],
    ])
def test_tui(setup, key, assertion):
    """Test TUI.

    Args:
        setup: runs pytest fixture.
        key (str): key to be send to the CoBib TUI.
        assertion (Callable): function to run the assertions for the key to be tested.
    """
    # create pseudo-terminal
    pid, f_d = os.forkpty()
    if pid == 0:
        # child process spawns TUI
        curses.wrapper(TUI)
    else:
        # parent process sets up virtual screen of identical size
        screen = pyte.Screen(80, 24)
        stream = pyte.ByteStream(screen)
        # set correct encoding with Unicode chars
        stream.select_other_charset('@')
        # send single key to be tested to TUI
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
        print(*screen.display, "\n")
        assertion(screen)
