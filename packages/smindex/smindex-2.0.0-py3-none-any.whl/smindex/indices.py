from ._globals import db, smi_dtype
from .download_indices import download_indices
import numpy as np
import datetime
import DateTimeTools as dtt
from tqdm import tqdm


def _normalize_date_input(
    date_input: datetime.date | datetime.datetime | np.datetime64 | int | tuple[int, float]
) -> tuple[int, float, bool]:
    """
    Normalize various date input types to a standard format.

    Inputs
    ======
    date_input : datetime.date | datetime.datetime | np.datetime64 | int | tuple[int, float]
        Input date in various possible formats. If a tuple is provided, it should be
        (date: int YYYYMMDD, ut: float hours).

    Outputs
    =======
    date : int
        Date in YYYYMMDD format.
    timestamp : float
        Corresponding Unix timestamp.
    has_time : bool
        Indicates whether the input included a specific time component.
    """

    has_time = False
    if isinstance(date_input, tuple):
        date, ut = date_input
        timestamp = dtt.UnixTime(date, ut)[0]
    elif isinstance(date_input, int):
        date = date_input
        ut = 0.0
        timestamp = dtt.UnixTime(date, ut)[0]
    elif isinstance(date_input, datetime.datetime):
        date = int(date_input.strftime("%Y%m%d"))
        timestamp = date_input.timestamp()
        has_time = True
    elif isinstance(date_input, np.datetime64):
        dt = date_input.astype('datetime64[us]').item()
        date = int(dt.strftime("%Y%m%d"))
        timestamp = dt.timestamp()
        has_time = True
    elif isinstance(date_input, datetime.date):
        date = int(date_input.strftime("%Y%m%d"))
        ut = 0.0
        timestamp = dtt.UnixTime(date, ut)[0]
    else:
        raise ValueError("Invalid input type for date")

    return date, timestamp, has_time


def indices(
    start: datetime.date | datetime.datetime | np.datetime64 | int | tuple[int, float],
    end: datetime.date | datetime.datetime | np.datetime64 | int | tuple[int, float] = None,
    overwrite: bool = False
) -> np.recarray:
    """
    Retrieve SMI index data for a specified date or date range.

    Inputs
    ======
    start : datetime.date | datetime.datetime | np.datetime64 | int | tuple[int, float]
        Start date in various formats. If a tuple is provided, it should be (date: int YYYYMMDD, ut: float hours).
    end : datetime.date | datetime.datetime | np.datetime64 | int | tuple[int, float], optional
        End date in various formats. If None, retrieves data for a single day.
    overwrite : bool, optional
        If True, forces re-download of data even if it already exists locally.

    Returns
    =======
    data : np.recarray
        Structured array containing SMI index data within the specified date range.
    """

    # normalize inputs
    start_date, start_ts, start_has_time = _normalize_date_input(start)
    limit_time = False
    if end is not None:
        end_date, end_ts, end_has_time = _normalize_date_input(end)
        print(start_has_time, end_has_time)
        dates = dtt.ListDates(start_date, end_date)
        if start_has_time or end_has_time:
            limit_time = True
    else:
        dates = [start_date]

    # check which dates need to be downloaded
    existing_dates = db.check_existing_dates(dates)
    print(existing_dates)
    dates_to_download = [d for d in dates if (d not in existing_dates) or overwrite]

    if len(dates_to_download) > 0:
        for date in tqdm(dates_to_download, desc="Downloading SMI indices"):
            download_indices(date, overwrite=overwrite, quiet=False)

    # read in data
    all_data = []
    n = 0
    for date in dates:
        path = db.get_date(date)
        data = np.load(path)
        all_data.append(data)
        n += data.size

    data = np.recarray((n,), dtype=smi_dtype)
    pos = 0
    for day_data in all_data:
        data[pos:pos + day_data.size] = day_data
        pos += day_data.size

    if limit_time:
        print(start_ts, end_ts)
        mask = (data.timestamp >= start_ts) & (data.timestamp <= end_ts)
        data = data[mask]

    return data
