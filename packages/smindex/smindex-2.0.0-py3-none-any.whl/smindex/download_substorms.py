import numpy as np
import datetime
from .convert_substorm_data import convert_substorm_data
from .api.request_substorms import request_substorms
from tqdm import tqdm
from ._globals import db, substorm_dtype


substorm_ranges = {
    "newell": (1970, "present"),
    "forsyth": (1970, "present"),
    "liou": (1995, 2010),
    "frey": (2000, 2005),
    "ohtani": (1970, "present")
}


def get_date_range(list_type: str) -> tuple[int, int]:
    """
    Return the start and end dates for a given substorm list type.

    Inputs
    ======
    list_type : str
        Type of substorm list. Must be one of the keys in substorm_ranges.

    Outputs
    =======
    start_date : int
        Start date in YYYYMMDD format.
    end_date : int
        End date in YYYYMMDD format.
    """

    if list_type not in substorm_ranges:
        raise ValueError(f"list_type must be one of {list(substorm_ranges.keys())}")

    start_date = substorm_ranges[list_type][0]*10000 + 101  # January 1st of start year
    end_year = substorm_ranges[list_type][1]

    if end_year == "present":
        today = datetime.date.today()
        end_date = today.year*10000 + today.month*100 + today.day
    else:
        end_date = end_year*10000 + 1231  # December 31st of end year

    return start_date, end_date


def get_range_batches(start_date: int, end_date: int, batch_years: int = 25) -> list[tuple[int, int]]:
    """
    Split a date range into batches of specified number of years.

    Inputs
    ======
    start_date : int
        Start date in YYYYMMDD format.
    end_date : int
        End date in YYYYMMDD format.
    batch_years : int, optional
        Number of years per batch. Default is 25.

    Outputs
    =======
    batches : list of tuple[int, int]
        List of (start_date, end_date) tuples for each batch.
    """

    start_year = start_date // 10000
    end_year = end_date // 10000

    batches = []
    for year in range(start_year, end_year + 1, batch_years):
        batch_start = max(start_date, year * 10000 + 101)
        batch_end = min(end_date, (year + batch_years - 1) * 10000 + 1231)
        batches.append((batch_start, batch_end))

    return batches


def get_all_download_batches() -> list[dict]:
    """
    Get all download batches for all substorm list types.

    Outputs
    =======
    all_batches : list of dict
        List of dictionaries containing 'list_type', 'start_date', and 'end_date' for each batch.
    """

    all_batches = []
    for list_type in substorm_ranges.keys():
        start_date, end_date = get_date_range(list_type)
        batches = get_range_batches(start_date, end_date)
        all_batches.extend([{
            "list_type": list_type,
            "start_date": batch[0],
            "end_date": batch[1]
            } for batch in batches
        ])
    return all_batches


def process_batch(batch: dict) -> np.recarray:
    """
    Process a single batch of substorm data.

    Inputs
    ======
    batch : dict
        Dictionary containing 'list_type', 'start_date', and 'end_date'.

    Outputs
    =======
    data : np.recarray
        Structured numpy recarray containing the substorm data for the batch.
    """

    list_type = batch["list_type"]
    start_date = batch["start_date"]
    end_date = batch["end_date"]

    csv_data = request_substorms(start_date, end_date, list_type=list_type)
    data = convert_substorm_data(csv_data, source=list_type)

    return data


def download_substorms() -> np.recarray:
    """
    Download all substorm data in batches.

    Outputs
    =======
    all_data : np.recarray
        Structured numpy recarray containing all downloaded substorm data.
    """

    all_batches = get_all_download_batches()
    data_list = []

    n = 0
    for batch in tqdm(all_batches, desc="Downloading substorm lists"):
        batch_data = process_batch(batch)
        data_list.append(batch_data)
        n += batch_data.size

    all_data = np.recarray((n,), dtype=substorm_dtype)
    pos = 0
    for batch_data in data_list:
        all_data[pos:pos + batch_data.size] = batch_data
        pos += batch_data.size

    srt = np.argsort(all_data.timestamp)
    all_data = all_data[srt]

    db.insert_substorms(all_data)

    return all_data
