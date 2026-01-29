import os
import time
from contextlib import contextmanager

global _has_log
_has_log = False


def log(text: str):
    global _has_log
    output_file = "output.txt"
    if not _has_log:
        if os.path.exists(output_file):
            os.remove(output_file)
        _has_log = True
    with open(output_file, "a+") as f:
        f.write(text + "\n")


@contextmanager
def timed(name: str):
    start_time = time.perf_counter()
    yield
    end_time = time.perf_counter()
    log(f"{name}: {end_time - start_time}")
