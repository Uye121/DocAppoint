import os
from pathlib import Path
import environ


def get_env():
    """Get environment variables, handling .env location automatically."""
    env = environ.Env()
    settings_module = os.environ.get(
        "DJANGO_SETTINGS_MODULE", "api.settings.development"
    ).lower()

    if "development" in settings_module:
        base_dir = Path(__file__).resolve().parents[2]
        env_path = base_dir.parent / ".env"

        if env_path.exists():
            environ.Env.read_env(env_path)
            print(f"[DEV] loaded .env from {env_path}")
        else:
            print(f"[DEV] .env not found at {env_path}")
    elif "production" in settings_module:
        print("[PROD] using system environment variables")

    return env


env = get_env()
