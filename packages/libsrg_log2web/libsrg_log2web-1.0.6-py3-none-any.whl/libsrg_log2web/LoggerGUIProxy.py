# libsrg (Code and Documentation) is published under an MIT License
# Copyright (c) 2023,2024 Steven Goncalo
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# 2024 Steven Goncalo
import logging
from enum import Enum


class LogOps(Enum):
    NEW_THREAD = 1
    THREAD_EXIT = 2
    FG_COLOR = 3
    BG_COLOR = 4


LOG_OP_FMT_STRING = "LOG_OP_FMT_STRING %s"


def _send_log_op(op: LogOps, *args, logr=None):
    fmt = LOG_OP_FMT_STRING
    fmt += " %s" * len(args)
    if not logr:
        logr = logging.getLogger("LoggerGUIProxy")
    # print(f"send op {op=} {args=} {fmt=}")
    stacklevel = 2
    logr.info(fmt, op, stacklevel=stacklevel, *args)


class LoggerGUIProxy:
    """
    LoggerGUIProxy provides several methods to control the LoggerGUI via calls to logging.
    """

    @classmethod
    def gui_new_line(cls, logr=None):
        """
        Schedule the GUI line item for this thread to be deleted and disassociate it with this thread.
        If subsequent logging occurs from the same thread, a new GUI line is created.
        """
        _send_log_op(LogOps.NEW_THREAD, logr=logr)

    @classmethod
    def gui_freeze_line(cls, logr=None):
        """
        Freeze the current contents of the GUI line for this thread.
        Do not schedule the GUI line item for this thread to be deleted but disassociate it with this thread.
        If subsequent logging occurs from the same thread, a new GUI line is created.
        """
        _send_log_op(LogOps.THREAD_EXIT, logr=logr)

    @classmethod
    def gui_end_line(cls, logr=None):
        """
        Freeze the current contents of the GUI line for this thread.
        Do not schedule the GUI line item for this thread to be deleted but disassociate it with this thread.
        If subsequent logging occurs from the same thread, a new GUI line is created.
        """
        _send_log_op(LogOps.THREAD_EXIT, logr=logr)

    @classmethod
    def gui_configure(cls, logr=None, **kwargs):
        """
        Send one or more logs to set configuration values for the GUI line associated with this thread.
        Each log sent is a single name/value pair.
        """
        if "background" in kwargs:
            _send_log_op(LogOps.BG_COLOR, kwargs["background"], logr=logr)
        if "foreground" in kwargs:
            _send_log_op(LogOps.FG_COLOR, kwargs["foreground"], logr=logr)

    @classmethod
    def gui_set_colors(cls, logr=None, foreground=None, background=None, ):
        if foreground:
            _send_log_op(LogOps.FG_COLOR, foreground, logr=logr)
        if background:
            _send_log_op(LogOps.BG_COLOR, background, logr=logr)
