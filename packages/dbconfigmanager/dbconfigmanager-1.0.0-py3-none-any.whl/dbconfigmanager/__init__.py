from .loader import load_environment, AppConfig
from .client import get_service_settings, _cache_lock, _cached_settings, _last_fetch_times
import json
from pathlib import Path
from typing import Dict

# Global configuration context
_global_config_context = {
    "service_name": "DEFAULT_SERVICE",
    "root_path": Path("."),
    "cache_file": ".env.json",
    "url": None  # Add URL to context
}


def init_service_env(
    service_name: str = "DEFAULT_SERVICE",
    root_path: Path = None,
    env_file: str = ".env",
    cache_file: str = ".env.json",
    url: str = None,                # <-- Accept URL here
    force_refresh: bool = False
) -> AppConfig:
    """
    Load environment for the given service and save configuration context globally.
    After initialization, reset_service_settings_cache() will automatically
    use the stored context.
    """
    if root_path is None:
        root_path = Path(__file__).resolve().parent

    _global_config_context.update({
        "service_name": service_name,
        "root_path": root_path,
        "cache_file": cache_file,
        "url": url  # store URL globally
    })

    load_environment(
        service_name=service_name,
        root_path=root_path,
        env_file=env_file,
        cache_file=cache_file,
        url=url,                     # <-- Pass URL here
        force_refresh=force_refresh
    )

    return AppConfig()


def reset_service_settings_cache() -> Dict[str, str]:
    """
    Reset cache (in-memory + file) and reload from remote
    using the globally stored context.
    """
    service_name = _global_config_context["service_name"]
    root_path = _global_config_context["root_path"]
    cache_file = _global_config_context["cache_file"]
    url = _global_config_context["url"]

    remote_env_cache_path = Path(root_path) / cache_file

    # 1️⃣ Clear in-memory cache
    with _cache_lock:
        _cached_settings.pop(service_name, None)
        _last_fetch_times.pop(service_name, None)

    # 2️⃣ Delete local file cache if exists
    if remote_env_cache_path.exists():
        try:
            remote_env_cache_path.unlink()
            print(f"🗑️ Removed cached file: {remote_env_cache_path}")
        except Exception as e:
            print(f"⚠️ Failed to delete remote cache file: {e}")

    # 3️⃣ Fetch fresh settings
    fresh_settings = get_service_settings(
        service_name=service_name,
        url=url,                    # <-- Pass URL here
        force_refresh=True
    )

    # 4️⃣ Save to cache file
    try:
        remote_env_cache_path.write_text(json.dumps(fresh_settings, indent=2))
        print(f"✅ Cached fresh settings to: {remote_env_cache_path}")
    except Exception as e:
        print(f"⚠️ Failed to write fresh cache to file: {e}")

    # 5️⃣ Re-load environment variables
    load_environment(
        service_name=service_name,
        root_path=root_path,
        env_file=".env",
        cache_file=cache_file,
        url=url,                    # <-- Pass URL here
        force_refresh=True
    )

    return fresh_settings
