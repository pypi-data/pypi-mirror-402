# -*- coding: utf-8 -*-
# Python version: 3.9
# @TianZhen

from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
import warnings
import os
from typing import (Any, Optional)

from .types import LogLevelName


_LOG_FMT = r"%(asctime)s - <%(levelname)s> - <%(filename)s(%(funcName)s)-%(lineno)d> - %(message)s"
_DATE_FMT = r"%y-%m-%d %H:%M:%S"

# Logger instance
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_FILE_HANDLER = None
# cstr & smart_print
try:
    from cobra_color import (cstr as t_cstr, safe_print as t_safe_print)  # type: ignore
    _COLOR_AVAIL = True
except ImportError:
    warnings.warn(
        "Missing Color Library <cobra-color>, <cobra-log> Using `Stable Plain` Display Instead.",
        category=UserWarning,
        stacklevel=3,
    )
    _COLOR_AVAIL = False

_USE_COLOR: bool = _COLOR_AVAIL


def cstr(*objects: Any, sep: str = "", **kwargs):
    if _USE_COLOR:
        return t_cstr(*objects, sep=sep, **kwargs)
    return sep.join(objects)


def display(*args, **kwargs):
    if _COLOR_AVAIL:
        return t_safe_print(*args, **kwargs)
    print(*args, **kwargs)


def enable_color(flag: bool = True, /):
    r"""
    Enable or disable colored terminal output.
    """
    global _USE_COLOR
    _USE_COLOR = flag and _COLOR_AVAIL


# trace display
_TRACE_CONFIG = {
    "with_border": True,
    "exc_depth": -1,
    "tb_depth": -1,
    "exc_args_limit": -1,
    "min_width": 50
}


def set_trace(**kwargs: Any):
    r"""
    Set the global trace display configuration.

    Parameters
    ----------
        **kwargs : Any
            The trace display configuration to be updated. Including:
            - `with_border`: bool
            - `exc_depth`: int
            - `tb_depth`: Optional[int]
            - `exc_args_limit`: int
    """
    global _TRACE_CONFIG
    _TRACE_CONFIG.update(kwargs)


def log_init(
    log_save_path: Optional[str] = None,
    log_level: LogLevelName = "debug",
    log_fmt: str = _LOG_FMT,
    date_fmt: str = _DATE_FMT,
    cover: bool = True,
    backup_count: int = 0,
    use_color: bool = True
):
    r"""
    Initialize the log storage configuration.

    NOTE: The log storage configuration can be set multiple times, and only the latest log storage configuration instance is retained.

    Parameters
    ----------
        log_save_path : Optional[str], default to `None`
            The log file storage address. If invalid, no log file output stream is created.

        log_level : LogLevelName, default to `"debug"`
            The lowest level of log file storage, `LogLevelName` includes `"debug"`, `"info"`, `"warning"`, `"error"` and `"critical"`.

        log_fmt : str, default to LOG_FMT
            The log storage format, `LOG_FMT` is defined as `r"%(asctime)s - <%(levelname)s> - <%(filename)s(%(funcName)s)-%(lineno)d> - %(message)s"`.
            Includes:
            - `%(levelno)s`: log level value;
            - `%(levelname)s`: log level name;
            - `%(pathname)s`: the path of the current executable program, i.e., sys.argv[0];
            - `%(filename)s`: the name of the current executable program;
            - `%(funcName)s`: the current function of the log;
            - `%(lineno)d`: the current line number of the log;
            - `%(asctime)s`: the time of the log;
            - `%(thread)d`: thread ID;
            - `%(threadName)s`: thread name;
            - `%(process)d`: process ID;
            - `%(message)s`: log information;
            - `%(name)s`: log handler name, default to root.

        date_fmt : _type_, default to DATE_FMT
            The time storage format in the log, `DATE_FMT` is defined as `r"%y-%m-%d %H:%M:%S"`.

        cover : bool, default to `True`
            Control whether to cover the latest storage configuration instance.

        backup_count : int, default to `0`
            The number of log file backups.
            - `>0`: rolling log;
            - `<=0`: no backup, all logs are stored in one file.

        use_color : bool, default to `True`
            Control whether to enable colored terminal output.
    """
    # log level
    if log_level == "critical":
        level = logging.CRITICAL
    elif log_level == "error":
        level = logging.ERROR
    elif log_level == "warning":
        level = logging.WARNING
    elif log_level == "info":
        level = logging.INFO
    else:
        level = logging.DEBUG
    # set logger handler
    global _FILE_HANDLER
    if _FILE_HANDLER and cover:
        _LOGGER.removeHandler(_FILE_HANDLER)

    if log_save_path is not None and log_save_path.endswith(".log"):
        # create log directory
        log_dir = os.path.dirname(log_save_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        # file handler
        _FILE_HANDLER = RotatingFileHandler(
            filename=log_save_path,
            mode="a",
            backupCount=backup_count,
            maxBytes=100*1024,
            delay=True
        )
        _LOGGER.addHandler(_FILE_HANDLER)
        _FILE_HANDLER.setFormatter(logging.Formatter(
            fmt=log_fmt,
            datefmt=date_fmt
        ))
        _FILE_HANDLER.setLevel(level)

    # enable color
    enable_color(use_color)
