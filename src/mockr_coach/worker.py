"""Executed only inside an OS sandbox; stdin contains source and one case's args."""

import contextlib
import json
import os
import resource
import sys


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16384, 16384))
    resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
    if sys.platform == "linux":
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    payload = json.load(sys.stdin)
    try:
        namespace = {"__name__": "candidate"}
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            exec(compile(payload["code"], "<candidate>", "exec"), namespace)
            result = namespace["solve"](*payload["args"])
        encoded = json.dumps({"result": result}, allow_nan=False)
        if len(encoded.encode()) > 8192:
            raise ValueError("Result too large")
        print(encoded)
    except BaseException:
        print('{"error":"runtime-error"}')


if __name__ == "__main__":
    main()
