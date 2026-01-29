"""SRM-HGA public package.

The main entrypoints are:
- :class:`srmhga.stack.SRMHGA` (sync)
- :class:`srmhga.stack.AsyncSRMHGA` (async wrapper)
"""

from .core.config import Config
from .stack import SRMHGA, AsyncSRMHGA

__all__ = ["Config", "SRMHGA", "AsyncSRMHGA"]

__version__ = "1.0.0"
