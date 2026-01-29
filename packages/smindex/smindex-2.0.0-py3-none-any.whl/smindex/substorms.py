from ._globals import db, substorm_dtype
import numpy as np
from typing import Optional


def substorms(
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
    list_type: Optional[str] = None,
) -> np.ndarray:
    """
    Retrieve substorm data for a specified date range.

    Inputs
    ======
    start_date : int
        Start date in YYYYMMDD format.
    end_date : int
        End date in YYYYMMDD format.
    list_type : str, optional
        Type of substorm list to filter by (e.g., "newell", "forsyth", "othani",
        "frey", "liou"). If None, retrieves all types.

    Returns
    =======
    data : np.ndarray
        Structured array containing substorm data within the specified date range.
    """

    records = db.read_substorms(start_date, end_date)

    if list_type is not None:
        records = [rec for rec in records if rec[8] == list_type]

    if not records:
        return np.recarray(0, dtype=substorm_dtype)

    data = np.recarray(len(records), dtype=substorm_dtype)
    for i, record in enumerate(records):
        data.date[i] = record[1]
        data.ut[i] = record[2]
        data.timestamp[i] = record[3]
        data.mlt[i] = record[4]
        data.mlat[i] = record[5]
        data.glon[i] = record[6]
        data.glat[i] = record[7]
        data.source[i] = record[8]
    return data
