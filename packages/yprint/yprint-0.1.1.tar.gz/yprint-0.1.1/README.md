# yprint

yprint prefixes stdout/stderr lines with a colored call stack breadcrumb. It does this by preloading a small C shim that intercepts writes and lets the Python runtime update a per-thread prefix.

## Install

```bash
pip install yprint
```

## Usage

```bash
yprint -- python your_script.py
yprint -- bash -c 'python your_script.py'
```

### Options

- `--only PATH` (repeatable): Only show frames under the given path(s).
- `--prefix-width N`: Fixed width for the prefix column.

### Environment

- `YPRINT_ONLY`: Colon-separated list of allowed paths (same as `--only`).
- `YPRINT_PREFIX_WIDTH`: Fixed width for the prefix column.
- `YPRINT_COLOR`: `always` or `never` to force color on/off.
- `YPRINT_CACHE_DIR`: Override where the preload library is compiled.
- `YPRINT_ENABLE`: Set to `1` to auto-enable via `sitecustomize`.

yprint compiles the preload library on first run; a C compiler (`cc`) must be available.

## Dev / Release

```bash
pip install -e ".[dev]"
python -m build
python -m twine upload dist/*
```
