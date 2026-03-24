from pathlib import Path
import environ


def get_env():
    """Get environment variables, handling .env location automatically."""
    base_dir = Path(__file__).resolve().parents[2]

    env_path = base_dir.parent / ".env"

    env = environ.Env()
    environ.Env.read_env(env_path)

    return env


env = get_env()
