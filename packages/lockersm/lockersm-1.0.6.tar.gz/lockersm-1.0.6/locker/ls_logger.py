import os
import re
import sys
import six
import traceback
import logging


LOCKER_LOG = os.environ.get("LOCKER_LOG")

logger = logging.getLogger("locker")


def logfmt(props):
    def fmt(key, val):
        # Handle case where val is a bytes or bytesarray
        if hasattr(val, "decode"):
            val = val.decode("utf-8")
        # Check if val is already a string to avoid re-encoding into
        # ascii. Since the code is sent through 2to3, we can't just
        # use unicode(val, encoding='utf8') since it will be
        # translated incorrectly.
        if not isinstance(val, six.string_types):
            val = six.text_type(val)
        if re.search(r"\s", val):
            val = repr(val)
        # key should already be a string
        if re.search(r"\s", key):
            key = repr(key)
        return u"{key}={val}".format(key=key, val=val)

    return u" ".join([fmt(key, val) for key, val in sorted(props.items())])


def _console_log_level(log_level):
    if log_level in ["debug", "info", "warning", "error"]:
        return log_level
    elif LOCKER_LOG in ["debug", "info", "warning", "error"]:
        return LOCKER_LOG
    else:
        return None


def log_debug(message, **params):
    msg = logfmt(dict(message=message, **params))
    # if _console_log_level() == "debug":
    #     print(msg, file=sys.stderr)
    logger.debug(msg)


def log_info(message, **params):
    msg = logfmt(dict(message=message, **params))
    # if _console_log_level() in ["debug", "info"]:
    #     print(msg, file=sys.stderr)
    logger.info(msg)


def log_warning(message, **params):
    msg = logfmt(dict(message=message, **params))
    # if _console_log_level() in ["debug", "info"]:
    #     print(msg, file=sys.stderr)
    logger.warning(msg)


def log_error(message, **params):
    if not message:
        tb = traceback.format_exc()
        message = 'Something was wrong' if tb is None else tb
    msg = logfmt(dict(message=message, **params))
    logger.error(msg)
