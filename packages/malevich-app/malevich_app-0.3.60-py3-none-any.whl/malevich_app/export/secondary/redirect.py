import sys
import contextvars
import builtins
import threading
from io import StringIO
from contextlib import AbstractContextManager
from malevich_app.export.secondary.LoggingWrapper import LoggingWrapper

async_current_buffer = contextvars.ContextVar("async_current_buffer")
thread_current_buffer = threading.local()
_base_print = builtins.print

def _override_print(*args, **kwargs):
    if buf := async_current_buffer.get(None):
        buf.write(" ".join(str(a) for a in args) + "\n")
    elif buf := getattr(thread_current_buffer, "buffer", None):
        buf.write(" ".join(str(a) for a in args) + "\n")
    else:
        _base_print(*args, **kwargs)

builtins.print = _override_print


class _DualStreamRedirect(AbstractContextManager):
    def __init__(self, buffer: StringIO):
        self.buffer = buffer
        self._old_stdout = []
        self._old_stderr = []
        self.__token = None

    def __enter__(self):
        logger_wrapper = LoggingWrapper(self.buffer, sys.stdout)
        self.__token = async_current_buffer.set(logger_wrapper)
        thread_current_buffer.buffer = logger_wrapper
        self._old_stdout.append(sys.stdout)
        sys.stdout = logger_wrapper
        self._old_stderr.append(sys.stderr)
        sys.stderr = LoggingWrapper(self.buffer, sys.stderr, "stderr: ")
        return self.buffer

    def __exit__(self, exctype, excinst, exctb):
        sys.stderr = self._old_stderr.pop()
        sys.stdout = self._old_stdout.pop()
        thread_current_buffer.buffer = None
        async_current_buffer.reset(self.__token)


def redirect_out(buffer: StringIO):
    return _DualStreamRedirect(buffer)
