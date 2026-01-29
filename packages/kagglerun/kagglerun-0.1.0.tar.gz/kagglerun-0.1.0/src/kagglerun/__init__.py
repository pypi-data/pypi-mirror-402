"""
KaggleRun - Execute Python on Kaggle's FREE H100 GPUs from your terminal.

No browser needed. Perfect for AI agents like Claude Code.
"""

__version__ = "0.1.0"
__author__ = "KaggleRun Contributors"

from .executor import KaggleExecutor
from .cli import main as cli_main

__all__ = ["KaggleExecutor", "cli_main", "__version__"]
