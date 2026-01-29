import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Union, Dict, List, Any
from pydantic import BaseModel


class CollectBuffer:
    def __init__(self, base_path: Union[str, Path], flush_interval: float = 1.0, buffer_limit: int = 10):
        self.__base_path = Path(base_path)
        self.__base_path.mkdir(parents=True, exist_ok=True)
        self.__flush_interval = flush_interval
        self.__buffer_limit = buffer_limit
        self.__buffers: dict[str, list[dict]] = {}
        self.__timers: dict[str, threading.Timer] = {}
        self.__locks: dict[str, threading.Lock] = {}

    def _serialize_payload(self, payload):
        if isinstance(payload, BaseModel):
            return payload.model_dump()
        if isinstance(payload, (dict, list, str)) or payload is None:
            return payload
        return str(payload)

    def __get_lock(self, key: str) -> threading.Lock:
        lock = self.__locks.get(key)
        if lock is None:
            lock = threading.Lock()
            self.__locks[key] = lock
        return lock

    def collect(self, key: str, payload: Union[BaseModel, Dict, List, str]):
        ts = datetime.now().isoformat()
        record = {"timestamp": ts, "payload": self._serialize_payload(payload)}

        with self.__get_lock(key):
            buf = self.__buffers.get(key)
            if buf is None:
                buf = []
                self.__buffers[key] = buf
            buf.append(record)

            if len(buf) >= self.__buffer_limit:
                self.flush(key)
                return

            if key not in self.__timers:
                timer = threading.Timer(self.__flush_interval, lambda: self.flush(key))
                self.__timers[key] = timer
                timer.start()

    def flush(self, key: str):
        with self.__get_lock(key):
            buf = self.__buffers.pop(key, None)
            if (timer := self.__timers.pop(key, None)) is not None:
                timer.cancel()
            if buf is None:
                return

            file_path = self.__base_path / f"{key}.jsonl"
            with file_path.open("a", encoding="utf-8") as f:
                for record in buf:
                    json.dump(record, f, ensure_ascii=False)
                    f.write("\n")


class JournalEntry:
    def __init__(self, key: str, buffer: CollectBuffer):
        self.__key = key
        self.__buffer = buffer

    def append(self, data):
        self.__buffer.collect(self.__key, data)


class JournalProxy:
    def __init__(self, buffer: CollectBuffer):
        self.__buffer = buffer

    def __getitem__(self, key: str) -> JournalEntry:
        return JournalEntry(key, self.__buffer)


class StateProxy:
    def __init__(self):
        self._data = {}

    def __setitem__(self, key: str, value: Any):
        self._data[key] = value

    def __getitem__(self, key):
        return self._data.get(key)
