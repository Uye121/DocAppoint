import environ


def get_env():
    """Get environment variables, handling .env location automatically."""
    return environ.Env()


env = get_env()
