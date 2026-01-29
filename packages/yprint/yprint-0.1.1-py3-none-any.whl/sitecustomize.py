import os

if os.environ.get("YPRINT_ENABLE") == "1" or os.environ.get("PWATCH_ENABLE") == "1":
    try:
        from yprint.auto import enable

        enable()
    except Exception:
        pass
