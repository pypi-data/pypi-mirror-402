# -*- coding: utf-8 -*-
# Python version: 3.9
# @TianZhen

from __future__ import annotations
from typing import (Any, Optional, Union)

from . import _core
from .exceptions import CriticalException
from ._utils import (trace_exc, trace_stack, box_lines, _fmt_msg)


_EXC_FMT = r" [%(fileName)s->%(funcName)s(%(lineno)d)]"
_FRAME_GAP = 2


def _fmt_loc(loc: Union[bool, int], /):
    r"""
    Format the location trace.
    """
    if loc is False:
        return ""
    return trace_stack(max(0, loc) if isinstance(loc, int) else 1, fmt=_EXC_FMT)


def _fmt_exc(exc: Any, /, top_indent: int, frame_style: str, indent: int = 0, **pattern: Any):
    if exc is None:
        return ""

    with_border = bool(_core._TRACE_CONFIG.get("with_border", True))
    # exception message
    exc_msg = trace_exc(
        exc,
        exc_depth=_core._TRACE_CONFIG.get("exc_depth", -1),
        tb_depth=_core._TRACE_CONFIG.get("tb_depth", -1),
        exc_args_limit=_core._TRACE_CONFIG.get("exc_args_limit", -1),
        indent=3 if with_border else 4
    )
    # box lines
    if with_border:
        exc_msg = box_lines(
            exc_msg.splitlines()[1:],
            top_indent=top_indent + _FRAME_GAP,
            rest_indent=indent,
            frame_style=frame_style,
            **pattern
        )

    return exc_msg


def critical(msg: str = "", exc: Optional[Any] = None, /, throw: bool = True, loc: Union[bool, int] = True):
    r"""
    `CRITICAL` exception & `log` record (requires `log_init()`).

    NOTE: Used when the overall program is not running.

    Parameters
    ----------
        msg : str, default to `""`
            Description message.

        exc : Optional[Any], default to `None`
            An instance of raised exception. Used for outputting exception traceback.

        throw : bool, default to `True`
            Control whether to throw exception.
            - `True`: throw `CriticalException` exception;
            - `False`: output as `str`.

        loc : bool, default to `True`
            Control whether to display file function location information.
            - `True`: Display `CRITICAL` location as stack level `1`;
            - _int_: Display `CRITICAL` location according to stack level. i.e.: `0`: this function; `1`: the caller of this function; ...

    Returns
    -------
        str
            Formatted message.

    Raises
    ------
        `CriticalException`
    """
    _msg = _fmt_msg(msg)
    # main message
    main_msg = _core.cstr(f"CRITICAL-ERROR{_fmt_loc(loc)}: {_msg}", fg="w", bg="lr", styles={"bold"})
    # exception message
    exc_msg = _fmt_exc(exc, top_indent=len(main_msg), frame_style="double", fg="lr", styles={"bold", "blink"})
    # log
    if _core._FILE_HANDLER:
        _core._LOGGER.critical(str(_msg) + exc_msg, stack_info=True, stacklevel=2)

    final_msg = _core.cstr("\n", main_msg, " " * _FRAME_GAP, exc_msg)
    if throw:
        raise CriticalException(final_msg)

    return final_msg


def error(msg: str = "", exc: Optional[Any] = None, /, throw: bool = True, loc: Union[bool, int] = True):
    r"""
    `ERROR` exception & `log` record (requires `log_init()`).

    NOTE: Used when some functions are not running.

    Parameters
    ----------
        msg : str, default to `""`
            Description message.

        exc : Optional[Any], default to `None`
            An instance of raised exception. Used to output exception details.

        throw : bool, default to `True`
            Control whether to throw exception.
            - `True`: Print the `ERROR` exception;
            - `False`: Output as `str`.

        loc : bool, default to `True`
            Control whether to display file function location information.
            - `True`: Display `ERROR` location as stack level `1`;
            - _int_: Display `ERROR` location according to stack level. i.e.: `0`: this function; `1`: the caller of this function; ...

    Returns
    -------
        str
            Formatted message.
    """
    _msg = _fmt_msg(msg)
    # main message
    main_msg = _core.cstr(f"ERROR{_fmt_loc(loc)}: {_msg}", fg="d", bg="y", styles={"bold"})
    # exception message
    exc_msg = _fmt_exc(exc, top_indent=len(main_msg), frame_style="double", fg="y", styles={"bold", "blink"})
    # log
    if _core._FILE_HANDLER:
        _core._LOGGER.error(str(_msg) + exc_msg, stack_info=True, stacklevel=2)

    final_msg = _core.cstr(main_msg, " " * _FRAME_GAP, exc_msg)
    if throw:
        _core.display(final_msg)

    return final_msg


def warning(msg: str = "", exc: Optional[Any] = None, /, throw: bool = True, loc: Union[bool, int] = True, dim: bool = False):
    r"""
    `WARNING` exception & `log` record (requires `log_init()`).

    NOTE: Used when unexpected events occur, and the program can still run normally.

    Parameters
    ----------
        msg : str, default to `""`
            Description message.

        exc : Optional[Any], default to `None`
            An instance of raised exception. Used for outputting exception traceback.

        throw : bool, default to `True`
            Control whether to throw exception.
            - `True`: Print the `WARNING` exception;
            - `False`: Output as `str`.

        loc : bool, default to `True`
            Control whether to display file function location information.
            - `True`: Display `WARNING` location as stack level `1`;
            - _int_: Display `WARNING` location according to stack level. i.e.: `0`: this function; `1`: the caller of this function; ...

        dim : bool, default to `False`
            Control whether to dim the `WARNING` message.

    Returns
    -------
        str
            Formatted message.
    """
    _msg = _fmt_msg(msg)
    # main message
    main_msg = _core.cstr(f"WARNING{_fmt_loc(loc)}: {_msg}", fg="y", styles=None if dim else {"bold"})
    # exception message
    exc_msg = _fmt_exc(exc, top_indent=len(main_msg), frame_style="light", fg="y", styles={"dim"} if dim else {"bold"})
    # log
    if _core._FILE_HANDLER:
        _core._LOGGER.warning(str(_msg) + exc_msg, stacklevel=2)

    final_msg = _core.cstr(main_msg, " " * _FRAME_GAP, exc_msg)
    if throw:
        _core.display(final_msg)

    return final_msg


def info(msg: str = "", exc: Optional[Any] = None, /, indent: int = 0, throw: bool = True, loc: Union[bool, int] = False, outline: bool = False):
    r"""
    `INFO` exception & `log` record (requires `log_init()`).

    NOTE: Used to record key node information.

    Parameters
    ----------
        msg : str, default to `""`
            Description message.

        exc : Optional[Any], default to `None`
            An instance of raised exception. Used for outputting exception traceback.

        indent : int, default to `0`
            The indentation of the `INFO`.

        throw : bool, default to `True`
            Control whether to throw exception.
            - `True`: Print the `INFO` exception;
            - `False`: Output as `str`.

        loc : bool, default to `True`
            Control whether to display file function location information.
            - `True`: Display `INFO` location as stack level `1`;
            - _int_: Display `INFO` location according to stack level. i.e.: `0`: this function; `1`: the caller of this function; ...

        outline : bool, default to `False`
            Control whether to highlight the `INFO` message.

    Returns
    -------
        str
            Formatted message.
    """
    _msg = _fmt_msg(msg)
    # main message
    if outline:
        main_msg = _core.cstr(f"KEY-INFO{_fmt_loc(loc)}: {_msg}", fg="lb", styles={"bold"})
    else:
        main_msg = _core.cstr(f"INFO{_fmt_loc(loc)}: {_msg}", fg="lg", styles={"bold"})
    if indent > 0:
        main_msg = _core.cstr(" " * indent, main_msg)
    # exception message
    exc_msg = _fmt_exc(exc, top_indent=len(main_msg), indent=indent, frame_style="light", fg="lb" if outline else "g", styles={"bold"} if outline else None)
    # log
    if _core._FILE_HANDLER:
        _core._LOGGER.info(str(_msg) + exc_msg, stacklevel=2)

    final_msg = _core.cstr(main_msg, " " * _FRAME_GAP, exc_msg)
    if throw:
        _core.display(final_msg)

    return final_msg


def debug(*args: Any, **kwargs: Any):
    r"""
    `DEBUG` exception and `log` record (requires `log_init()`).

    NOTE: Used for debugging.
    """
    msg = ""
    for arg in args:
        msg += f"\n{arg}"
    for arg_name, arg_val in kwargs.items():
        msg += f"\n[{arg_name}]: {arg_val}"
    # log
    if _core._FILE_HANDLER and msg:
        _core._LOGGER.debug(msg, stacklevel=2)
