from __future__ import annotations

import os
from typing import Any, Callable

from dotenv import load_dotenv

load_dotenv()


class EnvError(RuntimeError):
    pass


_TRUE = {"true", "1", "yes"}
_FALSE = {"false", "0", "no"}


def _cast_bool(raw: str, *, key: str) -> bool:
    v = raw.strip().lower()
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    raise EnvError(
        f"Invalid value for environment variable {key!r}: {raw!r}. "
        f"Expected one of: true/false, 1/0, yes/no."
    )


def _cast_value(raw: str, *, key: str, cast: Callable[[str], Any]) -> Any:
    try:
        if cast is bool:
            return _cast_bool(raw, key=key)
        return cast(raw)
    except EnvError:
        raise
    except Exception:
        cast_name = getattr(cast, "__name__", repr(cast))
        raise EnvError(
            f"Invalid value for environment variable {key!r}: {raw!r}. "
            f"Could not cast using {cast_name}."
        ) from None


def env(key: str, default: Any = None, cast: Callable[[str], Any] = str, required: bool = True) -> Any:
    raw = os.getenv(key)

    missing = raw is None or raw.strip() == ""
    if missing:
        if default is not None:
            if cast in (str, int, float, bool):
                return _cast_value(str(default), key=key, cast=cast)
            return default
        if required:
            raise EnvError(
                f"Missing required environment variable {key!r}. "
                f"Set it in your environment or add it to a .env file."
            )
        return default

    return _cast_value(raw, key=key, cast=cast)

