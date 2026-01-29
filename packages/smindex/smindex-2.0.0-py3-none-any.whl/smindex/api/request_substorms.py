from .get_url import get_substorm_url
import DateTimeTools as dtt
import requests
from .check_username import check_username
import csv


def request_substorms(start_date: int, end_date: int, list_type: str = "newell") -> list[dict]:
    """
    Request SMI index data for a specific date.

    Inputs
    ======
    start_date : int
        Start date in YYYYMMDD format.
    end_date : int
        End date in YYYYMMDD format.
    list_type : str, optional
        Type of substorm list to download. Default is "newell".

    Returns
    =======
    data: list of dict
        List of dictionaries containing the substorm data for the specified date range.
    """

    username = check_username()

    # check that the date difference is less than 25 years
    start_year, start_month, start_day = [x[0] for x in dtt.DateSplit(start_date)]
    end_year, end_month, end_day = [x[0] for x in dtt.DateSplit(end_date)]

    if end_year - start_year > 25:
        raise ValueError("Date range exceeds 25 years. Please request a smaller range.")

    url = get_substorm_url(username, [start_year, start_month, start_day], [end_year, end_month, end_day], list_type)
    response = requests.get(url)
    response.raise_for_status()

    csv_data = response.text

    return list(csv.DictReader(csv_data.splitlines()))
