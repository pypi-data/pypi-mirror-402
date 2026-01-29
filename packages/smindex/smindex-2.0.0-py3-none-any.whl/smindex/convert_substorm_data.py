import numpy as np
import datetime
from typing import List
from ._globals import substorm_dtype


def convert_substorm_data(csv_data: List[dict], source: str) -> np.recarray:
    """
    Convert CSV data of substorms into a structured numpy recarray.

    Inputs
    ======
    csv_data : List[dict]
        List of dictionaries containing substorm data.
    source : str
        Source identifier for the substorm list.

    Outputs
    =======
    data : np.recarray
        Structured numpy recarray with fields defined in substorm_dtype.
    """

    n = len(csv_data)
    data = np.recarray(n, dtype=substorm_dtype)

    for i, row in enumerate(csv_data):
        for key, val in row.items():
            new_key = key.lower()
            if new_key == "date_utc":
                dt = datetime.datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                data.date[i] = int(dt.strftime("%Y%m%d"))
                data.ut[i] = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
                data.timestamp[i] = dt.timestamp()
            else:
                data[new_key][i] = val
        data.source[i] = source

    return data
