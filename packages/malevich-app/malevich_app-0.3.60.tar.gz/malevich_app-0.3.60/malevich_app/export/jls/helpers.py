import asyncio
import importlib
import io
import traceback
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Tuple, Optional, Callable, Dict
from mypy_extensions import VarArg
from starlette.concurrency import run_in_threadpool
from malevich_app.export.jls.EntityType import EntityType
from malevich_app.export.jls.df import JDF
from malevich_app.export.secondary.collection.Collection import Collection
from malevich_app.export.jls.WrapperMode import InputWrapper
from malevich_app.export.secondary.const import DOC_SCHEME_PREFIX, DOCS_SCHEME_PREFIX, LIBS
from malevich_app.export.secondary.redirect import redirect_out

_process_executor = ProcessPoolExecutor(max_workers=8)
_thread_executor = ThreadPoolExecutor(max_workers=8)


async def get_schemes_info(julius_app, collections: List[Tuple[Collection, ...]]) -> Tuple[List[Tuple[Callable[[VarArg(pd.DataFrame)], JDF], Optional[Tuple[Optional[str], ...]], bool]], Optional[int]]:
    schemes_info, ret_type, sink_index = await julius_app.get_schemes_info()
    if julius_app.get_operation() == EntityType.INPUT and julius_app.get_input_mode() == InputWrapper.INPUT_DOC:
        assert ret_type is None or ret_type == "bool", f"wrong function return type={ret_type} (app id={julius_app.app_id})"

    if len(schemes_info) != len(collections) and sink_index is None:
        schemes_names = [x[1] for x in schemes_info]
        if not (julius_app.get_operation() == EntityType.OUTPUT and len(schemes_names) == 1 and schemes_names[0] is not None and len(schemes_names[0]) == 1 and schemes_names[0][0] is not None and schemes_names[0][0].endswith("*")):
            raise Exception(f"wrong function type, schemes={schemes_names}, collections={[tuple([subcollection.get() for subcollection in subcollections]) for subcollections in collections]}."
                            f" wrong count arguments: {len(schemes_names)} != {len(collections)} (app id={julius_app.app_id})")
    return schemes_info, sink_index


def get_params_names(fun: callable):
    return list(getattr(fun, "__annotations", fun.__annotations__).keys())


def is_async(fun: callable):
    return fun.__code__.co_flags & (1 << 7) != 0


async def run_func_in_threadpool(f: callable, *args, **kwargs):
    if is_async(f):
        return await run_in_threadpool(lambda: asyncio.run(f(*args, **kwargs)))
    else:
        return await run_in_threadpool(f, *args, **kwargs)


def _with_logs_buffer(func_module: str, func_name: str, exist_schemes: Optional[set[str]], *args):
    from malevich_app.export.secondary.creator import update_dummy_scheme
    from malevich_app.jls_lib.utils import Context

    if exist_schemes is not None:
        for scheme_name in exist_schemes:
            update_dummy_scheme(scheme_name)
    for lib in LIBS:
        importlib.reload(importlib.import_module(lib))
    module = importlib.import_module(func_module)
    f = getattr(module, func_name)

    if isinstance(arg := args[0], Context):
        arg._fix_app_cfg()
    elif isinstance(arg := args[-1], Context):
        arg._fix_app_cfg()

    logs_buffer = io.StringIO()
    with redirect_out(logs_buffer):
        try:
            res = f(*args)
            return res, logs_buffer.getvalue()
        except BaseException as ex:
            traceback.print_exc(file=logs_buffer)
            return ex, logs_buffer.getvalue()


def _with_logs_buffer_log(f: callable, logs_buffer, *args):
    with redirect_out(logs_buffer):
        try:
            res = f(*args)
            return res
        except BaseException as ex:
            traceback.print_exc(file=logs_buffer)
            return ex


async def run_func(f: callable, *args, cpu_bound: bool = False, logs_buffer: Optional[io.StringIO] = None, exist_schemes: Optional[set[str]] = None):
    if is_async(f):
        return await f(*args)
    else:
        loop = asyncio.get_running_loop()
        if cpu_bound:
            if len(args) > 0:
                from malevich_app.jls_lib.utils import Context
                if isinstance(arg := args[0], Context):
                    if not isinstance(arg.app_cfg, Dict):
                        arg.app_cfg = arg.app_cfg.dict()
                elif isinstance(arg := args[-1], Context):
                    if not isinstance(arg.app_cfg, Dict):
                        arg.app_cfg = arg.app_cfg.dict()
            res, logs = await loop.run_in_executor(_process_executor, _with_logs_buffer, f.__module__, f.__name__, exist_schemes, *args)
            logs_buffer.write(logs)
            if isinstance(res, BaseException):
                raise res from None
            return res
        else:
            res = await loop.run_in_executor(_thread_executor, _with_logs_buffer_log, f, logs_buffer, *args)
            if isinstance(res, BaseException):
                raise res from None
            return res


class Object(object):
    pass


class PreContext:
    def __int__(self):
        self.common = None

    def _logs(self, *args, **kwargs):
        return ""


def is_docs_scheme(scheme: Optional[str]) -> bool:
    return scheme is not None and (scheme.startswith(DOC_SCHEME_PREFIX) or scheme.startswith(DOCS_SCHEME_PREFIX))
