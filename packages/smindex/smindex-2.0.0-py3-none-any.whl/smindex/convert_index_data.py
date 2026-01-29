import numpy as np
import DateTimeTools as dtt
from . import _globals
from typing import List


def convert_index_data(json_data: List[dict]) -> np.recarray:
    """
    Convert JSON data of indices into a structured numpy recarray.

    Inputs
    ======
    json_data : List[dict]
        List of dictionaries containing index data.

    Outputs
    =======
    data : np.recarray
        Structured numpy recarray with fields defined in _globals.smi_dtype.
    """

    n = len(json_data)
    data = np.recarray(n, dtype=_globals.smi_dtype)

    fieldmap = {
        "SMR": "smr",
        "SMRnum00": "smrnum00",
        "SMRnum06": "smrnum06",
        "SMRnum12": "smrnum12",
        "SMRnum18": "smrnum18",
        "timestamp": "tval"
    }

    for i, entry in enumerate(json_data):
        for field in _globals.smi_dtype:
            new_field_name = field[0]
            field_name = fieldmap.get(new_field_name, new_field_name)
            if new_field_name not in ["date", "ut"]:
                try:
                    data[i][new_field_name] = entry.get(field_name, np.nan)
                except Exception:
                    print(f"Error processing field {field_name} for entry {i}")
                    print(entry)
                    raise

    # Convert timestamp to date and ut
    data.date, data.ut = dtt.UnixTimetoDate(data.timestamp)

    return data
