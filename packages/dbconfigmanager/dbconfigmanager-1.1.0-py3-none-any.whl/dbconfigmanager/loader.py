import os
import json
from pathlib import Path
from dotenv import load_dotenv
from .client import get_service_settings


class AppConfig:
    """Dynamic access to all environment variables."""

    def __getitem__(self, key: str):
        return os.getenv(key)

    def __getattr__(self, key: str):
        value = os.getenv(key)
        if value is None:
            raise AttributeError(f"Environment variable '{key}' not found")
        return value

    def all(self) -> dict:
        return dict(os.environ)


def load_environment(
    service_name: str = "DEFAULT_SERVICE",
    root_path: Path = None,
    url: str = None,
    env_file: str = ".env",
    cache_file: str = "remote_env.json",
    force_refresh: bool = False
):
    """Load environment variables from .env, cache, or remote API."""
    root = root_path or Path.cwd()
    base_env = root / env_file
    remote_cache = root / cache_file

    # 1️⃣ Load .env if exists
    if base_env.exists():
        load_dotenv(dotenv_path=base_env, override=False)
        print("✅ Loaded local .env file. Skipping remote fetch.")
        return

    # 2️⃣ Load cache
    if remote_cache.exists() and not force_refresh:
        try:
            cached = json.loads(remote_cache.read_text())
            for k, v in cached.items():
                os.environ[k] = str(v)
            print(
                f"✅ Loaded {len(cached)} cached remote settings from {remote_cache}.")
            return
        except Exception as e:
            print(f"⚠️ Failed to read remote cache: {e}. Refetching...")

    # 3️⃣ Fetch remote
    if not url:
        raise ValueError("URL must be provided to fetch remote settings")
    print(f"🌐 Fetching remote settings for {service_name}...")
    settings = get_service_settings(
        service_name=service_name, url=url, force_refresh=force_refresh)
    if settings:
        for k, v in settings.items():
            os.environ[k] = str(v)
        remote_cache.write_text(json.dumps(settings, indent=2))
        print(f"✅ Loaded {len(settings)} remote settings and cached.")
