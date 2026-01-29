"""
Python logger settings.
Uses ENV variables to control the log level:
from loggez import make_logger
my_logger = make_logger("MY_KEY")
my_logger.trace2("message")
run with:
MY_KEY=4 python blabla.py
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from io import IOBase
import os
from datetime import datetime
from enum import Enum
import sys
from pathlib import Path
from colorama import Fore, Back, Style
import threading

_EXISTING_LOGGERS: dict[str, LoggezLogger] = {}

class LogLevel(Enum):
    NONE = 0
    ERROR = 0.25
    WARNING = 0.5
    INFO = 1
    DEBUG = 2
    TRACE = 3
    TRACE2 = 4

def fast_log_context(depth: int) -> tuple[str, str, int]:
    try:
        # 0 is current, 1 is caller, 2 is caller's caller etc.
        f = sys._getframe(depth)
        filename = os.path.basename(f.f_code.co_filename)
        func_name = f.f_code.co_name
        lineno = f.f_lineno
        return filename, func_name, lineno
    except ValueError:
        return "???", "???", 0

def colorize(msg: str) -> str:
    _colors = {
        "cyan": Fore.CYAN,
        "magenta": Fore.MAGENTA,
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "back_red": Back.RED,
        "back_cyan": Back.CYAN,
    }

    def _get_next(msg: str, replacements: dict[str, str]) -> str:
        for replacement in replacements.keys():
            if msg[0: len(replacement)] == replacement:
                return replacement
        raise RuntimeError(f"Found no next color in {msg} out of {list(replacements)}")

    active_color = None
    new_message = []
    i = 0
    while i < len(msg):
        if msg[i] == "<" and msg[i+1:i+8] != "module>": # can happen in 'post'
            assert active_color is None or msg[i + 1] == "/", f"Use </color> before starting a new color: {msg}"
            _color = _get_next(msg[i + 2:], _colors) if active_color else _get_next(msg[i + 1:], _colors)
            assert active_color is None or _color == active_color, f"Active color: {active_color}. Got: {_color}"
            skip = len(_color) + 1 + (active_color is not None)
            assert msg[i + skip] == ">", f"Expected <color>(ch {i}), got: {msg}"
            new_message.append((_colors[_color] if active_color is None else Style.RESET_ALL))
            active_color = None if active_color is not None else _color
            i += skip + 1
        else:
            new_message.append(msg[i])
            i += 1
    return "".join(new_message)

def loglevel_colorize(loglevel: LogLevel, msg: str) -> str:
    return {
        LogLevel.INFO: colorize(f"<green>{msg}</green>"),
        LogLevel.ERROR: colorize(f"<red>{msg}</red>"),
        LogLevel.WARNING: colorize(f"<yellow>{msg}</yellow>"),
        LogLevel.DEBUG: colorize(f"<cyan>{msg}</cyan>"),
        LogLevel.TRACE: colorize(f"<back_cyan>{msg}</back_cyan>"),
        LogLevel.TRACE2: colorize(f"<magenta>{msg}</magenta>"),
    }[loglevel]

def loglevel_get_pre(loglevel: LogLevel, name: str) -> str:
    # TODO: use name and env variables for formatting
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if name == "loggez":
        return {
            LogLevel.INFO: f"[{now} INFO] ",
            LogLevel.ERROR: f"[{now} ERROR] ",
            LogLevel.WARNING: f"[{now} WARNING] ",
            LogLevel.DEBUG: f"[{now} DEBUG] ",
            LogLevel.TRACE: f"[{now} TRACE] ",
            LogLevel.TRACE2: f"[{now} TRACE2] ",
        }[loglevel]
    else:
        return {
            LogLevel.INFO: f"[{now} {name}-INFO] ",
            LogLevel.ERROR: f"[{now} {name}-ERROR] ",
            LogLevel.WARNING: f"[{now} {name}-WARNING] ",
            LogLevel.DEBUG: f"[{now} {name}-DEBUG] ",
            LogLevel.TRACE: f"[{now} {name}-TRACE] ",
            LogLevel.TRACE2: f"[{now} {name}-TRACE2] ",
        }[loglevel]

def loglevel_get_post(name: str, caller_depth: int) -> str:
    # TODO: use name and env variables for formatting
    file_name, func_name, line_no = fast_log_context(caller_depth)
    return f" ({file_name}:{func_name}:{line_no})"

class Handler(ABC):
    def __init__(self, handler_log_level: LogLevel):
        self._handler_log_level = handler_log_level
        self.lock = threading.Lock()

    @property
    def handler_log_level(self) -> LogLevel:
        """The log level of this handler"""
        return self._handler_log_level

    @abstractmethod
    def log(self, message: str, user_log_level: LogLevel | float):
        """The logging function. Normally if user_log_level <= handler_log_level, message is displayed"""

class StdoutHandler(Handler):
    def log(self, message: str, user_log_level: LogLevel | float):
        user_log_level_value = user_log_level.value if isinstance(user_log_level, LogLevel) else user_log_level
        if user_log_level_value <= self.handler_log_level.value:
            with self.lock:
                sys.stdout.write(message)

class FileHandler(Handler):
    def __init__(self, file_path: str | Path, handler_log_level: LogLevel):
        super().__init__(handler_log_level=handler_log_level)
        self.file_path = Path(file_path)
        self._fp = None
        assert not self.file_path.exists(), f"File: '{file_path}' exists already. Delete first."

    @property
    def fp(self) -> IOBase:
        """the file descriptor of this file handler. Lazily created."""
        if self._fp is None:
            Path(self.file_path).parent.mkdir(exist_ok=True, parents=True)
            self._fp = open(self.file_path, "w", encoding="utf-8")
        return self._fp

    def log(self, message: str, user_log_level: LogLevel | float):
        user_log_level_value = user_log_level.value if isinstance(user_log_level, LogLevel) else user_log_level

        if user_log_level_value <= self.handler_log_level.value:
            with self.lock:
                self.fp.write(message)

class LoggezLogger:
    """small interface-like class on top of the default logger for the extra methods"""
    def __init__(self, name: str, handlers: list[Handler]):
        assert len(handlers) > 0, "at least one handler required"
        self.name = name
        self.handlers = handlers

        self._last_now: datetime = datetime(1900, 1, 1)
        self._freq_s = {
            LogLevel.INFO: float(os.getenv(f"{self.name}_INFO_FREQ_S", "2")),
            LogLevel.DEBUG: float(os.getenv(f"{self.name}_DEBUG_FREQ_S", "2")),
            LogLevel.TRACE: float(os.getenv(f"{self.name}_TRACE_FREQ_S", "2")),
        }

    def add_file_handler(self, path: str, handler_log_level: float):
        """adds file handler"""
        self.handlers.append(FileHandler(path, handler_log_level))

    def get_file_handler(self) -> FileHandler | None:
        """Gets the first file handler. If not found, returns None"""
        for handler in self.handlers:
            if isinstance(handler, FileHandler):
                return handler
        return None

    def info(self, message: str, caller_depth: int=3):
        self.log(message, LogLevel.INFO, caller_depth=caller_depth)

    def debug(self, message: str, caller_depth: int=3):
        self.log(message, LogLevel.DEBUG, caller_depth=caller_depth)

    def trace(self, message: str, caller_depth: int=3):
        self.log(message, LogLevel.TRACE, caller_depth=caller_depth)

    def trace2(self, message: str, caller_depth: int=3):
        self.log(message, LogLevel.TRACE2, caller_depth=caller_depth)

    def error(self, message: str, caller_depth: int=3):
        self.log(message, LogLevel.ERROR, caller_depth=caller_depth)

    def warning(self, message: str, caller_depth: int=3):
        self.log(message, LogLevel.WARNING, caller_depth=caller_depth)

    def log(self, message: str, level: LogLevel, caller_depth: int=2):
        pre = loglevel_get_pre(loglevel=level, name=self.name) # TODO: colorize if any handler supports
        post = loglevel_get_post(name=self.name, caller_depth=caller_depth + 1) # TODO: same
        message_regular = f"{pre}{message}{post}\n"
        message_colored = None

        for handler in self.handlers:
            if isinstance(handler, StdoutHandler):
                if message_colored is None:
                    pre_colored = colorize(loglevel_colorize(level, pre))
                    post_colored = colorize(f"<yellow>{post}</yellow>")
                    message_colored = f"{pre_colored}{message}{post_colored}\n"
                handler.log(message_colored, level)
            else:
                handler.log(message_regular, level)

    def log_every_s(self, message: str, level: LogLevel = LogLevel.INFO):
        """logs only once every {LOGLEVEL}_FREQ_S."""
        now = datetime.now()
        if (now - self._last_now).total_seconds() >= self._freq_s[level]:
            self.log(message, level, caller_depth=3)
            self._last_now = now

def make_logger(key: str, exists_ok: bool = False, log_file: Path | str | None = None) -> LoggezLogger:
    """creates a logger given a key name and optionally a log file"""
    def _getenv(key, default):
        return float(os.environ[key]) if key in os.environ else default

    global _EXISTING_LOGGERS
    assert not key in _EXISTING_LOGGERS or exists_ok, f"Logger '{key}' exists. Use exists_ok=True or different name"
    if key in _EXISTING_LOGGERS:
        if log_file is not None:
            assert _EXISTING_LOGGERS[key].get_file_handler() is not None
            assert (A := _EXISTING_LOGGERS[key].get_file_handler().file_path) == (B := Path(log_file)), (A, B)
        return _EXISTING_LOGGERS[key]

    log_level = LogLevel(_getenv(f"{key}_LOGLEVEL", LogLevel.INFO))
    handlers = [StdoutHandler(handler_log_level=log_level)]
    if log_file is not None:
        file_log_level = LogLevel(_getenv(f"{key}_FILE_LOGLEVEL", LogLevel.TRACE2))
        handlers.append(FileHandler(file_path=log_file, handler_log_level=file_log_level))

    _EXISTING_LOGGERS[key] = LoggezLogger(name=key, handlers=handlers)
    return _EXISTING_LOGGERS[key]

loggez_logger = make_logger("loggez")
