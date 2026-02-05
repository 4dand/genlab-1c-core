"""
CLI — интерфейс командной строки фреймворка
"""

from .commands import cmd_run, cmd_info, cmd_evaluate, cmd_report, cmd_stats, cmd_charts

__all__ = [
    "cmd_run",
    "cmd_info",
    "cmd_evaluate",
    "cmd_report",
    "cmd_stats",
    "cmd_charts",
]
