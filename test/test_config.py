"""Tests for CoBib's config validation."""
# pylint: disable=unused-argument, redefined-outer-name

import os
from pathlib import Path

import pytest
from cobib.config import CONFIG


@pytest.fixture
def setup():
    """Setup."""
    # ensure configuration is empty
    CONFIG.config = {}
    root = os.path.abspath(os.path.dirname(__file__))
    CONFIG.set_config(Path(root + '/../cobib/docs/debug.ini'))


def test_base_config(setup):
    """Test the initial configuration passes all validation checks."""
    CONFIG.validate()


@pytest.mark.parametrize(['section'], [
        ['DATABASE'],
        ['FORMAT'],
        ['TUI'],
        ['KEY_BINDINGS'],
        ['COLORS'],
    ])
def test_missing_section(setup, section):
    """Test raised RuntimeError for missing configuration section."""
    with pytest.raises(RuntimeError) as exc_info:
        del CONFIG.config[section]
        CONFIG.validate()
    assert section in str(exc_info.value)


@pytest.mark.parametrize(['section', 'field'], [
        ['DATABASE', 'file'],
        ['DATABASE', 'open'],
        ['DATABASE', 'grep'],
        ['FORMAT', 'month'],
        ['FORMAT', 'ignore_non_standard_types'],
        ['TUI', 'default_list_args'],
        ['TUI', 'prompt_before_quit'],
        ['TUI', 'reverse_order'],
        ['TUI', 'scroll_offset'],
    ])
def test_database_section(setup, section, field):
    """Test raised RuntimeError for invalid config fields."""
    with pytest.raises(RuntimeError) as exc_info:
        del CONFIG.config.get(section, {})[field]
        CONFIG.validate()
    assert f'{section}/{field}' in str(exc_info.value)
