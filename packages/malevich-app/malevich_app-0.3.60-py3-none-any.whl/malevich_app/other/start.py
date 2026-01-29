import importlib.util
import os
import subprocess
from pathlib import Path
import uvicorn
import asyncio

EXIST_PKG_MODE = "info" # info, remove, assert


def not_exist_pkg_check():
    global EXIST_PKG_MODE
    if EXIST_PKG_MODE == "info":
        return

    spec = importlib.util.find_spec("malevich_app")
    if spec is None or not spec.origin:
        return

    origin = Path(spec.origin)
    if "site-packages" in str(origin):
        if EXIST_PKG_MODE == "remove":
            subprocess.check_call(['pip', 'uninstall', "malevich_app", '-y'])
            # after remove check
            EXIST_PKG_MODE = "assert"
            not_exist_pkg_check()
        elif EXIST_PKG_MODE == "assert":
            raise Exception("`malevich_app` pkg should not exist, please remove it")
        else:
            raise Exception("unknown EXIST_PKG_MODE")

def not_exist_pkg_check_info(buf):
    global EXIST_PKG_MODE
    if EXIST_PKG_MODE != "info":
        return

    spec = importlib.util.find_spec("malevich_app")
    if spec is None or not spec.origin:
        return

    origin = Path(spec.origin)
    if "site-packages" in str(origin):
        buf.write("`malevich_app` pkg is installed, there may be a conflict with the base image\n")

def start():
    import malevich_app.export.secondary.const as C
    from malevich_app.export.processes.main import logs_streaming_restart
    from malevich_app.export.secondary.logger import logfile

    C.IS_LOCAL = False
    if C.IS_EXTERNAL:
        os.makedirs(C.MOUNT_PATH, exist_ok=True)
        os.makedirs(C.MOUNT_PATH_OBJ, exist_ok=True)
    if C.LOGS_STREAMING:
        asyncio.run(logs_streaming_restart(wait=False))
    else:
        open(logfile, 'a').close()
    uvicorn.run("malevich_app.export.api.api:app", host="0.0.0.0", port=int(os.environ["PORT"]), loop="asyncio", reload=False, workers=1)


if __name__ == "__main__":
    not_exist_pkg_check()
    start()
