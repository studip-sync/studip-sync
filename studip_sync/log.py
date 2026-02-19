import logging

LOGGER_NAME = "studip_sync"
_LOGGING_CONFIGURED = False


def configure_logging(verbose=False):
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")
    _LOGGING_CONFIGURED = True


def get_logger(module_name=None):
    if not module_name:
        return logging.getLogger(LOGGER_NAME)

    return logging.getLogger("{}.{}".format(LOGGER_NAME, module_name))
