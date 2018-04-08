"""Stud.IP file synchronization tool.

A command line tool that keeps track of new files on Stud.IP and downloads them to your computer.
"""

__license__ = "Unlicense"
__version__ = "0.4.0"
__author__ = __maintainer__ = "Wolfgang Popp"
__email__ = "mail@wolfgang-popp.de"


def _get_config_path():
    import os
    prefix = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    path = os.path.join(prefix, "studip-sync/config.json")
    return os.path.expanduser(path)


CONFIG_PATH = _get_config_path()
