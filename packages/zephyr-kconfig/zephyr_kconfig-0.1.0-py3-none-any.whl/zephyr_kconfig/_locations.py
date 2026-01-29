import os
from pathlib import Path
from typing import Final

from xdg_base_dirs import xdg_cache_home, xdg_data_home

_ZKC_DATA_HOME_ENV_VAR: Final[str] = "ZKC_DATA_HOME"


def _get_data_home() -> Path:
    env_zkc_data = os.getenv(_ZKC_DATA_HOME_ENV_VAR, None)
    if env_zkc_data:
        return Path(env_zkc_data).expanduser().resolve()
    return xdg_data_home()


def _get_cache_home() -> Path:
    env_zkc_data = os.getenv(_ZKC_DATA_HOME_ENV_VAR, None)
    if env_zkc_data:
        return Path(env_zkc_data).joinpath("cache").expanduser().resolve()
    return xdg_cache_home()


def _zkc_directory(root: Path) -> Path:
    directory = root / "zkc"
    directory.mkdir(exist_ok=True, parents=True)
    return directory


def data_directory() -> Path:
    """Return (possibly creating) the application data directory."""
    return _zkc_directory(_get_data_home())


def cache_directory() -> Path:
    return _zkc_directory(_get_cache_home())
