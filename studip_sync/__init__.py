"""Stud.IP file synchronization tool.

A command line tool that keeps track of new files on Stud.IP and downloads them to your computer.
"""

__license__ = "Unlicense"
__version__ = "2.0.0"
__author__ = __maintainer__ = "Wolfgang Popp"
__email__ = "mail@wolfgang-popp.de"


def _get_config_path():
    import os
    prefix = os.environ.get("XDG_CONFIG_HOME") or "~/.config"
    path = os.path.join(prefix, "studip-sync/")
    return os.path.expanduser(path)


def get_config_file():
    import os
    from studip_sync.arg_parser import ARGS
    from studip_sync.constants import CONFIG_FILENAME

    if ARGS.config:
        return ARGS.config
    else:
        return os.path.join(CONFIG_PATH, CONFIG_FILENAME)


CONFIG_PATH = _get_config_path()
