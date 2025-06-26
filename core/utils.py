import os


def require_env(var_name: str) -> str:
    """Retrieve the value of a required environment variable.

    Args:
        var_name (str): The name of the environment variable to retrieve.

    Returns:
        str: The value of the environment variable.

    Raises:
        OSError: If the environment variable is not set.
    """
    value = os.getenv(var_name)
    if not value:
        raise OSError(f"Missing required environment variable: {var_name}")
    return value
