"""CoBib ZSH Helper."""

import inspect

from cobib import commands
from cobib.config import config
from cobib.database import read_database


def list_commands():
    """Lists all available subcommands."""
    return [cls.name for _, cls in inspect.getmembers(commands) if inspect.isclass(cls)]


def list_tags():
    """List all available tags in the database."""
    read_database()
    tags = list(config.bib_data.keys())
    return tags


def list_filters():
    """Lists all field names available for filtering."""
    read_database()
    filters = set()
    for entry in config.bib_data.values():
        filters.update(entry.data.keys())
    return filters
