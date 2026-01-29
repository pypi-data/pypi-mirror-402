from datetime import datetime
from typing import List


def get_index_url(username: str, start_time: datetime | List[int] | str, duration: int | float) -> str:
    """
    Construct the URL to download SMI indices from SuperMAG.

    Inputs
    ======
    username : str
        SuperMAG username.
    start_time : datetime | List[int] | str
        Start time as a datetime object, list of integers [year, month, day, hour, minute], or ISO format string.
    duration : int | float
        Duration in minutes for which to download data.

    Outputs
    =======
    url : str
        Constructed URL for downloading SMI indices.
    """

    if isinstance(start_time, list):
        start_time = datetime(*start_time)
    start = datetime.strftime(start_time, "%Y-%m-%dT%H:%M")

    url = "https://supermag.jhuapl.edu/services/indices.php?python&nohead"
    url += f"&start={start}&logon={username}&extent={duration:012d}"

    fields = [
        "sme",
        "sml",
        "smu",
        "num",
        "mlat",
        "mlt",
        "glat",
        "glon",
        "smer",
        "smlr",
        "smur",
        "numr",
        "mlatr",
        "mltr",
        "glatr",
        "glonr",
        "smr",
        "ltsmr",
        "ltnum",
        "nsmr"
    ]

    return url + "&indices=" + ",".join(fields)


def get_substorm_url(
    username: str,
    start_time: datetime | List[int] | str,
    end_time: datetime | List[int] | str,
    list_type: str = "newell"
) -> str:
    """
    Construct the URL to download substorm data from SuperMAG.

    Inputs
    ======
    username : str
        SuperMAG username.
    start_time : datetime | List[int] | str
        Start time as a datetime object, list of integers [year, month, day, hour, minute], or ISO format string.
    end_time : datetime | List[int] | str
        End time as a datetime object, list of integers [year, month, day, hour, minute], or ISO format string.
    list_type : str, optional
        Type of substorm list to download. Default is "newell".

    Outputs
    =======
    url : str
        Constructed URL for downloading substorm data.
    """

    valid_list_types = ["newell", "liou", "frey", "ohtani", "forsyth"]
    if list_type not in valid_list_types:
        raise ValueError(f"list_type must be one of {valid_list_types}")

    fmt = "csv"

    if isinstance(start_time, list):
        start_time = datetime(*start_time)
    start = datetime.strftime(start_time, "%Y-%m-%dT%H:%M:%S.000Z")

    if isinstance(end_time, list):
        end_time = datetime(*end_time)
    end = datetime.strftime(end_time, "%Y-%m-%dT%H:%M:%S.000Z")

    url = "https://supermag.jhuapl.edu/lib/services/?service=substorms"
    url += f"&downloadtype=substorm_list&user={username}&fmt={fmt}&start={start}&end={end}&list={list_type}"

    return url
