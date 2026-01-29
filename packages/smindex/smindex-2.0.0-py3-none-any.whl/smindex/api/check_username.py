from .._globals import config
from ..update_config import set_username


def check_username() -> str:
    """
    Check if a SuperMAG username is set in the configuration. If not, prompt the user to set one.

    Returns
    =======
    username : str
        The SuperMAG username.
    """

    username = config.get('username', None)
    if username is None:
        username = set_username()

    if not username:
        raise ValueError("A SuperMAG username is required to request data. Please set it in the configuration.")
    return username
