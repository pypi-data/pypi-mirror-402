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

class Loglevel(Enum):
    NONE = 0
    ERROR = 0.5
    INFO = 1
    WARNING = 1.5
    DEBUG = 2
    TRACE = 3
    TRACE2 = 4

def floor_loglevel(value: float) -> Loglevel:
    return max(
        (level for level in Loglevel if level.value <= value),
        key=lambda level: level.value,
        default=Loglevel.NONE
    )

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

def loglevel_colorize(loglevel: Loglevel, msg: str) -> str:
    return {
        Loglevel.INFO: colorize(f"<green>{msg}</green>"),
        Loglevel.ERROR: colorize(f"<red>{msg}</red>"),
        Loglevel.WARNING: colorize(f"<yellow>{msg}</yellow>"),
        Loglevel.DEBUG: colorize(f"<cyan>{msg}</cyan>"),
        Loglevel.TRACE: colorize(f"<back_cyan>{msg}</back_cyan>"),
        Loglevel.TRACE2: colorize(f"<magenta>{msg}</magenta>"),
    }[loglevel]

def loglevel_get_pre(loglevel: Loglevel, name: str) -> str:
    # TODO: use name and env variables for formatting
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    if name == "loggez":
        return {
            Loglevel.INFO: f"[{now} INFO] ",
            Loglevel.ERROR: f"[{now} ERROR] ",
            Loglevel.WARNING: f"[{now} WARNING] ",
            Loglevel.DEBUG: f"[{now} DEBUG] ",
            Loglevel.TRACE: f"[{now} TRACE] ",
            Loglevel.TRACE2: f"[{now} TRACE2] ",
        }[loglevel]
    else:
        return {
            Loglevel.INFO: f"[{now} {name}-INFO] ",
            Loglevel.ERROR: f"[{now} {name}-ERROR] ",
            Loglevel.WARNING: f"[{now} {name}-WARNING] ",
            Loglevel.DEBUG: f"[{now} {name}-DEBUG] ",
            Loglevel.TRACE: f"[{now} {name}-TRACE] ",
            Loglevel.TRACE2: f"[{now} {name}-TRACE2] ",
        }[loglevel]

def loglevel_get_post(name: str, caller_depth: int) -> str:
    # TODO: use name and env variables for formatting
    file_name, func_name, line_no = fast_log_context(caller_depth)
    return f" ({file_name}:{func_name}:{line_no})"

class Handler(ABC):
    def __init__(self, handler_log_level: Loglevel):
        self._handler_log_level = handler_log_level
        self.lock = threading.Lock()

    @property
    def handler_log_level(self) -> Loglevel:
        """The log level of this handler"""
        return self._handler_log_level

    @abstractmethod
    def log(self, message: str, user_log_level: Loglevel | float):
        """The logging function. Normally if user_log_level <= handler_log_level, message is displayed"""

class StdoutHandler(Handler):
    def log(self, message: str, user_log_level: Loglevel | float):
        user_log_level_value = user_log_level.value if isinstance(user_log_level, Loglevel) else user_log_level
        if user_log_level_value <= self.handler_log_level.value:
            with self.lock:
                sys.stdout.write(message)

class FileHandler(Handler):
    def __init__(self, file_path: str | Path, handler_log_level: Loglevel):
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

    def log(self, message: str, user_log_level: Loglevel | float):
        user_log_level_value = user_log_level.value if isinstance(user_log_level, Loglevel) else user_log_level

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
            Loglevel.INFO: float(os.getenv(f"{self.name}_INFO_FREQ_S", "2")),
            Loglevel.DEBUG: float(os.getenv(f"{self.name}_DEBUG_FREQ_S", "2")),
            Loglevel.TRACE: float(os.getenv(f"{self.name}_TRACE_FREQ_S", "2")),
        }

    def add_file_handler(self, path: str, handler_log_level: float=Loglevel.TRACE):
        """adds file handler"""
        self.handlers.append(FileHandler(path, handler_log_level))

    def get_file_handler(self) -> FileHandler | None:
        """Gets the first file handler. If not found, returns None"""
        for handler in self.handlers:
            if isinstance(handler, FileHandler):
                return handler
        return None

    def info(self, message: str, caller_depth: int=3):
        self.log(message, Loglevel.INFO, caller_depth=caller_depth)

    def debug(self, message: str, caller_depth: int=3):
        self.log(message, Loglevel.DEBUG, caller_depth=caller_depth)

    def debug2(self, message: str, caller_depth: int=3):
        self.log(message, Loglevel.TRACE, caller_depth=caller_depth)

    def trace(self, message: str, caller_depth: int=3):
        self.log(message, Loglevel.TRACE, caller_depth=caller_depth)

    def trace2(self, message: str, caller_depth: int=3):
        self.log(message, Loglevel.TRACE2, caller_depth=caller_depth)

    def error(self, message: str, caller_depth: int=3):
        self.log(message, Loglevel.ERROR, caller_depth=caller_depth)

    def warning(self, message: str, caller_depth: int=3):
        self.log(message, Loglevel.WARNING, caller_depth=caller_depth)

    def log(self, message: str, level: Loglevel, caller_depth: int=2):
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

    def log_every_s(self, message: str, level: Loglevel | str = "INFO"):
        """logs only once every {LOGLEVEL}_FREQ_S."""
        now = datetime.now()
        level = Loglevel(Loglevel._member_map_[level]) if isinstance(level, str) else level
        if (now - self._last_now).total_seconds() >= self._freq_s[level]:
            self.log(message, level, caller_depth=3)
            self._last_now = now

def make_logger(key: str, exists_ok: bool = False, log_file: Path | str | None = None) -> LoggezLogger:
    """creates a logger given a key name and optionally a log file"""
    def _loglevel_from_env(key: str, default: Loglevel) -> Loglevel:
        return floor_loglevel(float(os.environ[key]) if key in os.environ else default.value)

    global _EXISTING_LOGGERS
    assert not key in _EXISTING_LOGGERS or exists_ok, f"Logger '{key}' exists. Use exists_ok=True or different name"
    if key in _EXISTING_LOGGERS:
        if log_file is not None:
            assert _EXISTING_LOGGERS[key].get_file_handler() is not None
            assert (A := _EXISTING_LOGGERS[key].get_file_handler().file_path) == (B := Path(log_file)), (A, B)
        return _EXISTING_LOGGERS[key]

    log_level = Loglevel(_loglevel_from_env(f"{key}_LOGLEVEL", Loglevel.INFO))
    handlers = [StdoutHandler(handler_log_level=log_level)]
    if log_file is not None:
        file_log_level = Loglevel(_loglevel_from_env(f"{key}_FILE_LOGLEVEL", Loglevel.TRACE2))
        handlers.append(FileHandler(file_path=log_file, handler_log_level=file_log_level))

    _EXISTING_LOGGERS[key] = LoggezLogger(name=key, handlers=handlers)
    return _EXISTING_LOGGERS[key]

loggez_logger = make_logger("loggez")
