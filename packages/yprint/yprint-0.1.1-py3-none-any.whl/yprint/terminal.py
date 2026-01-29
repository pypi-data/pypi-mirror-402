import os
import sys


def detect_columns():
    for stream in (sys.stdout, sys.stderr):
        try:
            if stream and stream.isatty():
                return os.get_terminal_size(stream.fileno()).columns
        except OSError:
            continue
    return None


def default_prefix_width():
    columns = detect_columns()
    if columns and columns > 0:
        return max(1, columns // 3)
    return 40
