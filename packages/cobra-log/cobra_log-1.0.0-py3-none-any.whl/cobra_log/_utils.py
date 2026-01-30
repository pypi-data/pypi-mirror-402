# -*- coding: utf-8 -*-
# Python version: 3.9
# @TianZhen

import inspect
import os
import traceback
import warnings
from typing import (Any, Tuple, List, Optional, Union, Sequence)

from ._core import cstr, _TRACE_CONFIG


_TRACE_FMT = r"%(fileName)s->%(funcName)s(%(lineno)d)"

_END_SYMBOLS = (".", "!", "?", "。", "！", "？")
_FINAL_STYLES = {"bold", "selected"}

_TB_STR = "traceback"
_EXC_ARROW_STR = cstr("\u25B6 ", styles={"bold"})
# traceback braces
_BRACE = {"upper": "\u250E", "middle": "\u2520", "lower": "\u2516"}
_SHORT_LINE = "\u2574"

_FRAME = {
    "light": {
        "top_left": "\u256D",
        "top_right": "\u256E",
        "bottom_left": "\u2570",
        "bottom_right": "\u256F",
        "horizontal": "\u2500",
        "vertical": "\u2502"
    },
    "double": {
        "top_left": "\u2554",
        "top_right": "\u2557",
        "bottom_left": "\u255A",
        "bottom_right": "\u255D",
        "horizontal": "\u2550",
        "vertical": "\u2551"
    },
    "heavy": {
        "top_left": "\u250F",
        "top_right": "\u2513",
        "bottom_left": "\u2517",
        "bottom_right": "\u251B",
        "horizontal": "\u2501",
        "vertical": "\u2503"
    }
}


def box_lines(lines: Sequence[str], top_indent: int = 0, rest_indent: int = 0, frame_style: str = "light", **pattern: Any) -> str:
    frame = _FRAME[frame_style]
    rest_indent = max(0, rest_indent)
    # width
    width = max(len(line) for line in lines) + 1
    if width == 1:
        return ""
    width = max(_TRACE_CONFIG.get("min_width", 50), width)
    # top line
    top_line_items: List[str] = []
    top_indent = max(0, top_indent)
    if top_indent == 0:
        top_line_items.append(frame["top_left"])
    top_remain_len = width + rest_indent + 1 - top_indent
    if top_remain_len > 0:
        top_line_items.append(frame["horizontal"] * top_remain_len)
    if top_remain_len > -1:
        top_line_items.append(frame["top_right"])
    boxed_lines = [cstr(*top_line_items, **pattern)]
    # middle lines
    vert_line = cstr(frame["vertical"], **pattern)
    for line in lines:
        boxed_lines.append(cstr(" " * rest_indent, vert_line, line, " " * (width - len(line)), vert_line))
    # bottom line
    boxed_lines.append(cstr(
        " " * rest_indent,
        frame["bottom_left"],
        frame["horizontal"] * width,
        frame["bottom_right"],
        **pattern
    ))
    return cstr(*boxed_lines, sep="\n")


def trace_stack(stack_level: int = 1, /, fmt: str = _TRACE_FMT) -> str:
    r"""
    Trace the stack information of the function call.

    Parameters
    ----------
        stack_level : int, default to `1`
            The stack level of the function call.
            - `0`: this function;
            - `1`: the caller of this function;
            - ...

        fmt : str, default to TRACE_FMT
            The format string, `TRACE_FMT` is defined as `r"%(fileName)s->%(funcName)s(%(lineno)d)"`.
            Includes:
            - `%(stackDepth)d`: stack depth;
            - `%(funcName)s`: function name;
            - `%(filePath)s`: file path;
            - `%(fileName)s`: file name;
            - `%(lineno)d`: line number;
            - `%(funcLineno)d`: function start line number.

    Returns
    -------
        str
            Formatted stack information.
    """
    try:
        total_stack = inspect.stack()
        frame_info = total_stack[stack_level][0]
        total_depth = len(total_stack)  # total stack depth

        stackDepth = total_depth - stack_level  # current stack depth
        funcName = frame_info.f_code.co_name  # current function name
        filePath = frame_info.f_code.co_filename  # current file path
        fileName = os.path.basename(filePath)  # current file name
        lineno = int(frame_info.f_lineno)  # current line number
        funcLineno = frame_info.f_code.co_firstlineno  # function start line number

        return fmt % {"stackDepth": stackDepth, "funcName": funcName, "filePath": filePath, "fileName": fileName, "lineno": lineno, "funcLineno": funcLineno}

    except Exception as e:
        warnings.warn(
            f"Trace Stack By Format {fmt!r} Error, Got <{e.__class__.__name__}> {e}",
            category=UserWarning,
            stacklevel=3,
        )
        return ""


def trace_exc(
    exception: Any,
    /,
    exc_depth: int = -1,
    tb_depth: Optional[int] = -1,
    exc_args_limit: int = -1,
    indent: int = 4
) -> str:
    r"""
    Trace the exception chain and format it as a string.

    Parameters
    ----------
        exception : Any
            The exception instance to trace.

        exc_depth : int, default to `-1`
            The maximum depth of exception chain to trace.
            - `< 1`: Trace all exceptions in the chain;
            - `>= 1`: Trace the last `exc_depth` exceptions in the chain, omitting earlier exceptions.

        tb_depth : Optional[int], default to `-1`
            The maximum depth of traceback frames to trace for each exception.
            - `None`: Without traceback frames;
            - `< 1`: Trace all traceback frames;
            - `>= 1`: Trace the last `tb_depth` traceback frames, omitting earlier frames.

        exc_args_limit : int, default to `-1`
            The maximum number of exception arguments to display for each exception.
            - `< 1`: Display all exception arguments;
            - `>= 1`: Display the first `exc_args_limit` exception arguments, omitting later arguments.

        indent : int, default to `4`
            The number of spaces to indent for each level of exception in the chain.

    Returns
    -------
        str
            Formatted string.
    """
    if not isinstance(exception, Exception):
        # non-exception type
        return _add_indent(indent) + _EXC_ARROW_STR +\
            cstr(_fmt_msg(exception), styles=_FINAL_STYLES)
    # exception type
    # build exception chain
    exc_list: List[Union[Exception, int]] = []
    exc = exception
    while exc is not None:
        exc_list.append(exc)
        exc = exc.__cause__ or exc.__context__
    if 0 < exc_depth < len(exc_list):
        _e_omit_num = len(exc_list) - exc_depth
        exc_list = exc_list[-exc_depth:]
        exc_list.insert(0, cstr(f"... Omitted {_e_omit_num} Exception(s) ...", styles={"dim"}))
    # format exception chain
    trace_lines: List[str] = []
    for exc_idx, exc in enumerate(exc_list):
        # for exception chain
        _base_indent = _add_indent(indent)
        if isinstance(exc, str):
            # omitted exceptions
            trace_lines.extend([_base_indent, exc])
            continue
        # actual exception
        indent_arrow = cstr(_base_indent, f"({len(exc_list)-exc_idx})", _EXC_ARROW_STR)
        trace_lines.append(indent_arrow)
        is_final = exc_idx == len(exc_list) - 1
        # exception name
        exc_name = cstr(
            exc.__class__.__name__,
            fg=None if is_final else "c",
            bg="lr" if is_final else None,
            styles={"dim"} if is_final else {"bold"}
        )
        # traceback
        _tb_indent = _add_indent(len(indent_arrow) - 1)
        tb_stack = list(traceback.extract_tb(exc.__traceback__))
        if not tb_depth or len(tb_stack) == 1:
            # only one traceback frame
            tb_stack = tb_stack[-1:]
            _name_width = len(exc_name)
        else:
            if 0 < tb_depth < len(tb_stack):
                _tb_omit_num = len(tb_stack) - tb_depth
                tb_stack = tb_stack[-tb_depth:]
                _tb_len = len(tb_stack)
                tb_stack.insert(0, cstr(f"... Omitted {_tb_omit_num} Traceback Frame(s) ...", styles={"dim"}))
            _tb_len = len(tb_stack)
            tb_idx_width = len(str(_tb_len))
            _name_width = max(len(_TB_STR) + tb_idx_width + 1, len(exc_name))
        for tb_idx, tb in enumerate(tb_stack):
            # for each traceback frame
            if isinstance(tb, str):
                # omitted traceback frames
                trace_lines.extend([f"{_BRACE['upper']} ", tb])
                continue
            # traceback detail
            _tb_detail = cstr(f"{tb.filename}({tb.lineno})", styles={"udl"})
            if tb_idx == len(tb_stack) - 1:
                # final traceback (exception raised here)
                tb_prefix = _BRACE["lower"] if len(tb_stack) > 1 else ""
                _tb_name = exc_name
                _tb_styles = _FINAL_STYLES if is_final else set()
                # exception args
                _e_args = _fmt_exc_args(exc.args, is_final)
                if 0 < exc_args_limit < len(_e_args):
                    _arg_omit_num = len(_e_args) - exc_args_limit
                    _e_args = _e_args[:exc_args_limit]
                    _e_args.append(
                        cstr(f" ... Omitted {_arg_omit_num} Argument(s) ...", styles={"dim"})
                    )
                _e_args_indent = _add_indent(
                    len(_tb_indent) + _name_width + len(_tb_detail) + len(tb_prefix) + 4)
                arg_lines = []
                for e_arg_idx, e_arg in enumerate(_e_args):
                    # for each exception argument
                    if e_arg_idx == 0:
                        # first exception argument
                        _prefix = f" {_BRACE['upper']}" if len(_e_args) > 1 else " "
                        arg_lines.append(cstr(_prefix, e_arg, styles=[(None, _tb_styles)]))
                    else:
                        # non-first exception argument
                        _prefix = _BRACE["lower"] if e_arg_idx == len(_e_args) - 1 else _BRACE["middle"]
                        arg_lines.extend([_e_args_indent, _prefix, e_arg])
            else:
                # non-final traceback
                tb_prefix = _BRACE["upper"] if tb_idx == 0 else _BRACE["middle"]
                _tb_name = cstr(
                    f"{_TB_STR}-{str(len(tb_stack) - tb_idx - 1).zfill(tb_idx_width)}",
                    fg="lg",
                    styles={"bold"}
                )
                _tb_styles = {"dim"}
                arg_lines = [cstr(" >>> ", fg="ly", styles={"bold", *_tb_styles}),
                             cstr(tb.line, styles=_tb_styles)]
            tb_indent = "" if tb_idx == 0 else _tb_indent
            # traceback head
            tb_head = cstr("<", _tb_name.center(_name_width), ": ", _tb_detail,
                           ">", styles=[(None, {"italic", *_tb_styles})])
            # assemble
            trace_lines.extend([tb_indent, tb_prefix, tb_head, *arg_lines])
        # update
        indent += 4

    return cstr(*trace_lines)


def _fmt_msg(msg: Any, /, limit: Optional[int] = None) -> str:
    r"""Format message."""
    msg = msg if isinstance(msg, str) else str(msg)
    if limit is not None and len(msg) > limit:
        msg = msg[:limit] + ".."
    if msg and not msg.endswith(_END_SYMBOLS):
        msg += "."
    return msg


def _add_indent(indent: int, /) -> str:
    r"""Create indentation."""
    return cstr("\n" + " " * indent, styles={"disappear"})


def _fmt_exc_args(e_args: Tuple[Any, ...], /, is_final: bool, is_top=True) -> List[str]:
    r"""Format exception arguments."""
    fmt_args: List[str] = []
    for m in e_args:
        if isinstance(m, Tuple):
            fmt_args.extend(_fmt_exc_args(m, is_final, is_top=is_top))
        elif isinstance(m, Exception):
            # exception head
            exc_name = cstr(m.__class__.__name__, fg="r" if is_final else "c")
            e_msg = cstr("<", exc_name, "> ", styles={"italic"})
            # exception args
            sub_args = _fmt_exc_args(m.args, is_final, is_top=False)
            if len(sub_args) > 1:
                rest_msgs = [f", {_fmt_msg(arg, 12)}" for arg in sub_args[1:]]
                e_msg += cstr("( ", styles={"dim"}) + sub_args[0] +\
                    cstr(*rest_msgs, " )", styles={"dim"})
            else:
                e_msg += sub_args[0]
            fmt_args.append(e_msg)
        else:
            prefix = _SHORT_LINE if is_top and len(e_args) > 1 else ""
            fmt_args.append(prefix + _fmt_msg(m))

    return fmt_args
