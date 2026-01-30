# src/cobra_log/__init__.py
"""
cobra-log
===========

A lightweight and easy-to-use logging library for Python.

Modules
-------
- :mod:`exceptions`: Custom exception classes for cobra-log.
Functions
---------
- :func:`log_init()`: Initialize the logging system.
- :func:`enable_color()`: Enable or disable colored output (need :pkg:`cobra-color`).
- :func:`set_trace()`: Configure global trace display settings.
- :func:`critical()`: Log a critical error message.
- :func:`error()`: Log an error message.
- :func:`warning()`: Log a warning message.
- :func:`info()`: Log an informational message.
- :func:`debug()`: Log a debug message.
- :func:`trace_stack()`: Trace the stack information of the function call.

Examples
--------

```python
from cobra_log import (log_init, info, warning)

# Initialize the log system
log_init("log_save_path", display_type="style")

try:
    try:
        1 / 0  # This will raise a ZeroDivisionError
    except Exception as e1:
        raise RuntimeError("This is the main exception")
except Exception as e:
    warning("A warning occurred.", e)
    info("Continuing execution after warning.")
```
"""

from . import exceptions

from ._core import (log_init, enable_color, set_trace)
from ._log_levels import (critical, error, warning, info, debug)
from ._utils import trace_stack


__author__ = "Zhen Tian"
__version__ = "1.0.0"

__all__ = [
    "exceptions",  # module
    "log_init",
    "enable_color",
    "set_trace",
    "critical",
    "error",
    "warning",
    "info",
    "debug",
    "trace_stack"
]
