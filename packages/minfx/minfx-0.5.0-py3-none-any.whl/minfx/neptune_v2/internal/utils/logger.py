from __future__ import annotations
__all__ = ['NEPTUNE_LOGGER_NAME', 'get_disabled_logger', 'get_logger']
import logging
import os
import re
import sys
import time
from typing import TYPE_CHECKING
BACKEND_PATTERN = re.compile('^\\[backend (\\d+)\\] ')
NEPTUNE_LOGGER_NAME = 'minfx'
NEPTUNE_NO_PREFIX_LOGGER_NAME = 'minfx_no_prefix'
NEPTUNE_NOOP_LOGGER_NAME = 'minfx_noop'
LOG_FORMAT = '%(asctime)s.%(msecs)03.0f [%(levelname)s] [%(name)s] %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
NO_PREFIX_FORMAT = '%(message)s'

class AnsiColors:
    RESET = '\x1b[0m'
    BOLD = '\x1b[1m'
    DIM = '\x1b[2m'
    BLACK = '\x1b[30m'
    RED = '\x1b[31m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    BLUE = '\x1b[34m'
    MAGENTA = '\x1b[35m'
    CYAN = '\x1b[36m'
    WHITE = '\x1b[37m'
    BRIGHT_RED = '\x1b[91m'
    BRIGHT_GREEN = '\x1b[92m'
    BRIGHT_YELLOW = '\x1b[93m'
    BRIGHT_BLUE = '\x1b[94m'
    BRIGHT_MAGENTA = '\x1b[95m'
    BRIGHT_CYAN = '\x1b[96m'

def _should_use_colors():
    color_env = os.environ.get('MINFX_LOG_COLOR', '').lower()
    if color_env in ('1', 'true', 'yes', 'on'):
        return True
    if color_env in ('0', 'false', 'no', 'off'):
        return False
    if os.environ.get('NO_COLOR') is not None:
        return False
    try:
        return sys.stderr.isatty()
    except Exception:
        return False

class CustomFormatter(logging.Formatter):
    converter = time.gmtime
    LEVEL_COLORS = {logging.DEBUG: AnsiColors.BRIGHT_BLUE, logging.INFO: AnsiColors.BRIGHT_GREEN, logging.WARNING: AnsiColors.BRIGHT_YELLOW, logging.ERROR: AnsiColors.BRIGHT_RED, logging.CRITICAL: AnsiColors.BOLD + AnsiColors.BRIGHT_RED}

    def __init__(self, use_colors=None):
        super().__init__()
        self._use_colors = use_colors

    def format(self, record):
        record.levelname = record.levelname.lower()
        use_colors = self._use_colors if self._use_colors is not None else _should_use_colors()
        if use_colors:
            return self._format_colored(record)
        return self._format_plain(record)

    def _format_plain(self, record):
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
        formatter.converter = time.gmtime
        return formatter.format(record)

    def _format_colored(self, record):
        level_color = self.LEVEL_COLORS.get(record.levelno, AnsiColors.RESET)
        timestamp = time.strftime(LOG_DATE_FORMAT, time.gmtime(record.created))
        msecs = f'{record.msecs:03.0f}'
        colored_timestamp = f'{AnsiColors.DIM}{AnsiColors.CYAN}{timestamp}.{msecs}{AnsiColors.RESET}'
        colored_level = f'{level_color}[{record.levelname}]{AnsiColors.RESET}'
        colored_name = f'{AnsiColors.DIM}{AnsiColors.MAGENTA}[{record.name}]{AnsiColors.RESET}'
        message = self._colorize_backend_id(record.getMessage())
        return f'{colored_timestamp} {colored_level} {colored_name} {message}'

    def _colorize_backend_id(self, message):
        match = BACKEND_PATTERN.match(message)
        if match:
            backend_num = match.group(1)
            colored_backend = f'{AnsiColors.BRIGHT_CYAN}[backend {backend_num}]{AnsiColors.RESET}'
            return colored_backend + ' ' + message[match.end():]
        return message

class GrabbableStderrHandler(logging.StreamHandler):

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)

    @property
    def stream(self):
        return sys.stderr

    def emit(self, record):
        try:
            super().emit(record)
            self.flush()
        except BrokenPipeError:
            self._emit_to_tty(record)

    def _emit_to_tty(self, record):
        try:
            with open('/dev/tty', 'w') as tty:
                msg = self.format(record)
                tty.write(msg + self.terminator)
                tty.flush()
        except Exception:
            pass

def get_logger(with_prefix=True):
    name = NEPTUNE_LOGGER_NAME if with_prefix else NEPTUNE_NO_PREFIX_LOGGER_NAME
    return logging.getLogger(name)

def get_disabled_logger():
    return logging.getLogger(NEPTUNE_NOOP_LOGGER_NAME)

def _set_up_logging():
    neptune_logger = logging.getLogger(NEPTUNE_LOGGER_NAME)
    neptune_logger.propagate = False
    stderr_handler = GrabbableStderrHandler()
    stderr_handler.setFormatter(CustomFormatter())
    neptune_logger.addHandler(stderr_handler)
    neptune_logger.setLevel(logging.INFO)

def _set_up_no_prefix_logging():
    neptune_logger = logging.getLogger(NEPTUNE_NO_PREFIX_LOGGER_NAME)
    neptune_logger.propagate = False
    stderr_handler = GrabbableStderrHandler()
    stderr_handler.setFormatter(logging.Formatter(NO_PREFIX_FORMAT))
    neptune_logger.addHandler(stderr_handler)
    neptune_logger.setLevel(logging.INFO)

def _set_up_disabled_logging():
    neptune_logger = logging.getLogger(NEPTUNE_NOOP_LOGGER_NAME)
    neptune_logger.setLevel(logging.CRITICAL)
_set_up_logging()
_set_up_no_prefix_logging()
_set_up_disabled_logging()