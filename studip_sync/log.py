import logging
import os
import sys

LOGGER_NAME = "studip_sync"
_LOGGING_CONFIGURED = False
_USE_COLOR = False

_RESET = "\033[0m"
_COLORS = {
    "red": "\033[31m",
    "yellow": "\033[33m",
    "green": "\033[32m",
    "cyan": "\033[36m",
    "blue": "\033[34m",
    "bold": "\033[1m"
}


def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()


def colorize(text, color):
    if not _USE_COLOR:
        return text

    code = _COLORS.get(color)
    if not code:
        return text

    return "{}{}{}".format(code, text, _RESET)


class CliFormatter(logging.Formatter):
    def format(self, record):
        message = super(CliFormatter, self).format(record)

        if record.levelno >= logging.ERROR:
            return colorize("ERROR:", "red") + " " + message
        if record.levelno >= logging.WARNING:
            return colorize("WARN:", "yellow") + " " + message
        if record.levelno == logging.DEBUG:
            return colorize("DEBUG:", "cyan") + " " + message
        return message


def configure_logging(verbose=False):
    global _LOGGING_CONFIGURED, _USE_COLOR
    if _LOGGING_CONFIGURED:
        return

    _USE_COLOR = _supports_color()

    root_logger = logging.getLogger()
    root_logger.handlers = []

    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler()
    handler.setFormatter(CliFormatter("%(message)s"))

    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Avoid clutter from dependencies in normal CLI usage.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    _LOGGING_CONFIGURED = True


def get_logger(module_name=None):
    if not module_name:
        return logging.getLogger(LOGGER_NAME)

    return logging.getLogger("{}.{}".format(LOGGER_NAME, module_name))
