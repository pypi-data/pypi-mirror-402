from .core import parse, strip_tags
from .utils import timestamp
from .styles import ANSI

import builtins
import datetime
import os
import sys
import traceback
import inspect
import json
import logging


class Console:
    LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,
        "FAILURE": 25,
        "WARN": 30,
        "ERROR": 40,
    }

    LOGGING_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARN",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "ERROR",
    }

    def __init__(self):
        self.show_timestamp = True
        self.time_format = "%H:%M:%S"
        self.level = self.LEVELS["INFO"]

        self.out_file = None
        self.err_file = None
        self.rotate_logs = False
        self.json_logs = False

        self._logging_bound = False
        self._exclusive_logging = False

    # =========================
    # CONFIG
    # =========================

    def set_level(self, level):
        level = level.upper()
        if level not in self.LEVELS:
            raise ValueError(f"Nível inválido: {level}")
        self.level = self.LEVELS[level]

    def set_log_rotation(self, rotate: bool):
        self.rotate_logs = bool(rotate)

    def enable_json_logs(self, enable=True):
        self.json_logs = bool(enable)

    def set_log_files(self, out=None, err=None):
        if self.out_file:
            self.out_file.close()
        if self.err_file:
            self.err_file.close()

        mode = "w" if self.rotate_logs else "a"

        if out is None and err is None:
            if os.path.exists("out.log") or os.path.exists("err.log"):
                out, err = "out.log", "err.log"
            elif os.path.exists("saida.log") or os.path.exists("erro.log"):
                out, err = "saida.log", "erro.log"
            else:
                out, err = "out.log", "err.log"

        self.out_file = open(out, mode) if out else None
        self.err_file = open(err, mode) if err else None

    # =========================
    # INTERNALS
    # =========================

    def _allowed(self, level):
        return self.LEVELS[level] >= self.level

    def _prefix(self, level, color, show_timestamp):
        if not show_timestamp:
            return f"{ANSI[color]}{ANSI['bold']}{level}{ANSI['reset']} "

        time = timestamp(self.time_format)
        return (
            f"{ANSI['grey']}{time}{ANSI['reset']} "
            f"{ANSI[color]}{ANSI['bold']}{level}{ANSI['reset']} "
        )

    def _get_context(self):
        for frame in inspect.stack():
            if "consolepy" in frame.filename:
                continue
            return {
                "file": os.path.basename(frame.filename),
                "line": frame.lineno,
                "function": frame.function,
            }
        return None

    def _write_file(self, level, message, context=None, exc=None):
        if not self.out_file and not self.err_file:
            return

        time = datetime.datetime.now().isoformat()
        clean = strip_tags(message)

        if self.json_logs:
            data = {
                "time": time,
                "level": level,
                "message": clean,
            }
            if context:
                data.update(context)
            if exc:
                data["traceback"] = exc
            line = json.dumps(data, ensure_ascii=False) + "\n"
        else:
            ctx = ""
            if context:
                ctx = f"{context['file']}:{context['line']} {context['function']} "
            line = f"{time} {level} {ctx}{clean}\n"

        target = self.err_file if level in ("WARN", "ERROR") else self.out_file
        if target:
            target.write(line)
            target.flush()

    def _format_exception_terminal(self):
        exc_type, exc_value, exc_tb = sys.exc_info()
        return "".join(
            f"{ANSI['red']}{l}{ANSI['reset']}"
            for l in traceback.format_exception(exc_type, exc_value, exc_tb)
        )

    def _format_exception_file(self):
        exc_type, exc_value, exc_tb = sys.exc_info()
        return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    # =========================
    # OUTPUT API
    # =========================

    def print(self, text):
        builtins.print(parse(str(text)))

    def success(self, text, context=False, show_timestamp=False):
        if self._exclusive_logging:
            return
        if not self._allowed("SUCCESS"):
            return
        ctx = self._get_context() if context else None
        builtins.print(self._prefix("SUCCESS", "green", show_timestamp) + parse(str(text)))
        self._write_file("SUCCESS", text, ctx)

    def failure(self, text, context=False, show_timestamp=False):
        if self._exclusive_logging:
            return
        if not self._allowed("FAILURE"):
            return
        ctx = self._get_context() if context else None
        builtins.print(self._prefix("FAILURE", "red", show_timestamp) + parse(str(text)))
        self._write_file("FAILURE", text, ctx)

    def debug(self, text, context=False, show_timestamp=True):
        if self._exclusive_logging:
            return
        if not self._allowed("DEBUG"):
            return
        ctx = self._get_context() if context else None
        builtins.print(self._prefix("DEBUG", "grey", show_timestamp) + parse(str(text)))
        self._write_file("DEBUG", text, ctx)

    def info(self, text, context=False, show_timestamp=True):
        if self._exclusive_logging:
            return
        if not self._allowed("INFO"):
            return
        ctx = self._get_context() if context else None
        builtins.print(self._prefix("INFO", "cyan", show_timestamp) + parse(str(text)))
        self._write_file("INFO", text, ctx)

    def warn(self, text, context=False, show_timestamp=True):
        if self._exclusive_logging:
            return
        if not self._allowed("WARN"):
            return
        ctx = self._get_context() if context else None
        builtins.print(self._prefix("WARN", "yellow", show_timestamp) + parse(str(text)))
        self._write_file("WARN", text, ctx)

    def error(self, text, context=False, show_timestamp=True):
        if self._exclusive_logging:
            return
        if not self._allowed("ERROR"):
            return
        ctx = self._get_context() if context else None
        builtins.print(self._prefix("ERROR", "red", show_timestamp) + parse(str(text)))
        self._write_file("ERROR", text, ctx)

    def exception(self, text="Unhandled exception", context=False, show_timestamp=True):
        if self._exclusive_logging:
            return
        if not self._allowed("ERROR"):
            return
        builtins.print(self._prefix("ERROR", "red", show_timestamp) + parse(str(text)))
        builtins.print(self._format_exception_terminal(), end="")
        self._write_file("ERROR", text, None, self._format_exception_file())

    # =========================
    # LOGGING INTEGRATION
    # =========================

    def bind_logging(self, exclusive=False):
        if self._logging_bound:
            return

        self._exclusive_logging = bool(exclusive)

        class ConsoleHandler(logging.Handler):
            def emit(handler_self, record):
                level = Console.LOGGING_MAP.get(record.levelno)
                if not level:
                    return

                msg = record.getMessage()

                if level == "DEBUG":
                    self._emit_from_logging("DEBUG", msg)
                elif level == "INFO":
                    self._emit_from_logging("INFO", msg)
                elif level == "WARN":
                    self._emit_from_logging("WARN", msg)
                else:
                    self._emit_from_logging("ERROR", msg)

        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(ConsoleHandler())
        root.setLevel(logging.DEBUG)

        self._logging_bound = True

    def _emit_from_logging(self, level, text):
        if not self._allowed(level):
            return
        builtins.print(self._prefix(level, {
            "DEBUG": "grey",
            "INFO": "cyan",
            "WARN": "yellow",
            "ERROR": "red"
        }[level]) + parse(str(text)))
        self._write_file(level, text)


console = Console()
