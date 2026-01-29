from .get_url import get_index_url
from .._globals import config
from ..update_config import set_username
import DateTimeTools as dtt
import requests


def request_indices(date: int) -> dict:
    """
    Request SMI index data for a specific date.

    Inputs
    ======
    date : int
        Date in YYYYMMDD format.

    Returns
    =======
    data: json
        JSON response containing the SMI index data for the specified date.
    """

    username = config.get('username', None)
    if username is None:
        username = set_username()

    if not username:
        raise ValueError("A SuperMAG username is required to request data. Please set it in the configuration.")

    year, month, day = dtt.DateSplit(date)

    url = get_index_url(username, [year[0], month[0], day[0]], 86400)

    response = requests.get(url)
    response.raise_for_status()

    json_data = response.json()
    return json_data
