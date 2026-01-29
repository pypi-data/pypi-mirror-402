import ctypes
import os
import sys
import threading
from typing import Callable, List, Optional, Tuple

from .prefix import format_prefix


_YPRINT_ROOT = os.path.realpath(os.path.dirname(__file__))
_SITE_CUSTOMIZE = os.path.realpath(os.path.join(_YPRINT_ROOT, os.pardir, "sitecustomize.py"))

_tls = threading.local()
_enabled = False
_prior_profile = None
_set_prefix: Optional[Callable[[bytes, bytes], None]] = None


def _env(primary: str, legacy: str) -> Optional[str]:
    value = os.environ.get(primary)
    if value:
        return value
    return os.environ.get(legacy)


def _resolve_set_prefix(lib) -> Optional[Callable[[bytes, bytes], None]]:
    for name in ("yprint_set_prefix", "pwatch_set_prefix"):
        try:
            return getattr(lib, name)
        except AttributeError:
            continue
    return None


def _load_set_prefix() -> Optional[Callable[[bytes, bytes], None]]:
    lib = ctypes.CDLL(None)
    func = _resolve_set_prefix(lib)
    if func is None:
        lib_path = _env("YPRINT_LIB", "PWATCH_LIB")
        if not lib_path:
            return None
        lib = ctypes.CDLL(lib_path, mode=ctypes.RTLD_GLOBAL)
        func = _resolve_set_prefix(lib)
        if func is None:
            return None
    func.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    func.restype = None
    return func


def _is_internal(filename: Optional[str]) -> bool:
    if not filename or filename.startswith("<"):
        return False
    real = os.path.realpath(filename)
    if real == _SITE_CUSTOMIZE:
        return True
    return real == _YPRINT_ROOT or real.startswith(_YPRINT_ROOT + os.sep)


def _collect_frames(frame) -> List[Tuple[str, Optional[str]]]:
    frames: List[Tuple[str, Optional[str]]] = []
    current = frame
    while current:
        code = current.f_code
        filename = code.co_filename
        if not _is_internal(filename):
            func = code.co_name or "<unknown>"
            if func == "<module>":
                func = "main"
            frames.append((func, filename))
        current = current.f_back
    frames.reverse()
    return frames


def _update_prefix(frame) -> None:
    if _set_prefix is None:
        return
    frames = _collect_frames(frame) if frame else []
    plain, colored = format_prefix(frames)
    _set_prefix(plain.encode("utf-8", "replace"), colored.encode("utf-8", "replace"))


def _profile(frame, event, arg):
    if getattr(_tls, "busy", False):
        if _prior_profile:
            _prior_profile(frame, event, arg)
        return
    if event not in ("call", "return"):
        if _prior_profile:
            _prior_profile(frame, event, arg)
        return

    _tls.busy = True
    try:
        target = frame if event == "call" else frame.f_back
        _update_prefix(target)
    finally:
        _tls.busy = False

    if _prior_profile:
        _prior_profile(frame, event, arg)


def enable() -> None:
    global _enabled
    global _prior_profile
    global _set_prefix

    if _enabled:
        return
    if os.environ.get("YPRINT_ENABLE") != "1" and os.environ.get("PWATCH_ENABLE") != "1":
        return

    _set_prefix = _load_set_prefix()
    if _set_prefix is None:
        return

    _prior_profile = sys.getprofile()
    sys.setprofile(_profile)
    threading.setprofile(_profile)

    _update_prefix(sys._getframe())
    _enabled = True
