import argparse
import importlib.resources as resources
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .terminal import default_prefix_width


def _project_root() -> str:
    return os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir))


def _cache_dir() -> str:
    override = os.environ.get("YPRINT_CACHE_DIR")
    if override:
        return os.path.expanduser(override)
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Caches/yprint")
    base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    return os.path.join(base, "yprint")


def _preload_source_path():
    try:
        src = resources.files(__package__).joinpath("yprint_preload.c")
        return resources.as_file(src)
    except AttributeError:
        return resources.path(__package__, "yprint_preload.c")


def _ensure_preload() -> str:
    cache_dir = _cache_dir()
    os.makedirs(cache_dir, exist_ok=True)
    so_path = os.path.join(cache_dir, "yprint_preload.so")

    with _preload_source_path() as src_path:
        src_path = Path(src_path)
        needs_build = True
        if os.path.exists(so_path):
            needs_build = os.path.getmtime(so_path) < src_path.stat().st_mtime

        if needs_build:
            compiler = shutil.which("cc")
            if not compiler:
                raise RuntimeError("cc compiler not found; cannot build yprint preload")
            if sys.platform == "darwin":
                cmd = [
                    compiler,
                    "-dynamiclib",
                    "-O2",
                    "-o",
                    so_path,
                    str(src_path),
                    "-pthread",
                ]
            else:
                cmd = [
                    compiler,
                    "-shared",
                    "-fPIC",
                    "-O2",
                    "-o",
                    so_path,
                    str(src_path),
                    "-ldl",
                    "-pthread",
                ]
            subprocess.check_call(cmd)
    return so_path


def _parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="yprint", add_help=True)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Only show frames under this path (can be repeated)",
    )
    parser.add_argument(
        "--prefix-width",
        type=int,
        default=None,
        help="Fixed width for the prefix column",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("yprint: missing command; use -- to separate command args", file=sys.stderr)
        return 2

    preload_path = _ensure_preload()

    env = os.environ.copy()
    env["YPRINT_ENABLE"] = "1"
    env["YPRINT_LIB"] = preload_path

    if args.only:
        only_paths = [os.path.realpath(os.path.abspath(path)) for path in args.only]
        env["YPRINT_ONLY"] = os.pathsep.join(only_paths)

    prefix_width = args.prefix_width if args.prefix_width else default_prefix_width()
    env["YPRINT_PREFIX_WIDTH"] = str(prefix_width)

    root = _project_root()
    pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = root + (os.pathsep + pythonpath if pythonpath else "")

    if sys.platform == "darwin":
        preload_var = "DYLD_INSERT_LIBRARIES"
        env["DYLD_FORCE_FLAT_NAMESPACE"] = "1"
    else:
        preload_var = "LD_PRELOAD"

    existing_preload = env.get(preload_var, "")
    if existing_preload:
        env[preload_var] = preload_path + os.pathsep + existing_preload
    else:
        env[preload_var] = preload_path

    os.execvpe(command[0], command, env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
