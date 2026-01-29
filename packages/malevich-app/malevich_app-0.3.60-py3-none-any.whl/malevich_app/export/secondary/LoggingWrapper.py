from io import StringIO
import threading


class LoggingWrapper:
    def __init__(self, buffer: StringIO, raw_stream, prefix: str = None):
        self.buffer = buffer
        self.prefix = prefix or ""
        self.__raw_stream = raw_stream
        self.__in_write = threading.local()

    def write(self, message):
        if not message.strip():
            return

        if getattr(self.__in_write, 'active', False):
            self.__raw_stream.write(message)
            return

        self.__in_write.active = True
        try:
            self.buffer.write(f"{self.prefix}{message}\n")
        finally:
            self.__in_write.active = False

    def flush(self):
        if hasattr(self.buffer, 'flush'):
            self.buffer.flush()
