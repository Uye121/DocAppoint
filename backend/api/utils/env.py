import environ
from pathlib import Path


def get_env():
    """Get environment variables, handling .env location automatically."""
    env = environ.Env()

    current_dir = Path(__file__).resolve().parents[3]

    env_file = current_dir / ".env"

    if env_file.exists():
        env.read_env(str(env_file))

    return env


env = get_env()
