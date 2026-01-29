import os
import json
from .database import SMIDatabase

# try and find the SMINDEX_PATH variable - this is where data will be stored
module_path = os.path.dirname(__file__)

data_path = os.getenv("SMINDEX_PATH")
if data_path is None:
    data_path = f"{os.getenv("HOME")}/.smindex"
    if not os.path.isdir(data_path):
        print(
            f"SMINDEX_PATH environment variable not set - using default path {data_path}"
        )
        os.makedirs(data_path)

config_file = f"{data_path}/config.json"
if os.path.isfile(config_file):
    warn = False
    with open(config_file, "r") as f:
        config = json.load(f)
else:
    config = {}
    with open(config_file, "w") as f:
        json.dump(config, f)

dbfile = f"{data_path}/smindex.db"
db = SMIDatabase(dbfile)

# if this is successful - now check whether the subdirectories exist
dlddir = f"{data_path}/download"
bindir = f"{data_path}/binary"
tmpdir = f"{data_path}/temp"
subdir = f"{data_path}/substorms"
if not os.path.isdir(dlddir):
    os.system("mkdir -pv " + dlddir)
if not os.path.isdir(bindir):
    os.system("mkdir -pv " + bindir)
if not os.path.isdir(tmpdir):
    os.system("mkdir -pv " + tmpdir)
if not os.path.isdir(subdir):
    os.system("mkdir -pv " + subdir)

# this is the data type for the recarray which will store the indices
# The regional SME,SMU,SML indices are centred on a 3-hour MLT range
smi_dtype = [
    ("date", "i4"),             # date in YYYYMMDD format
    ("ut", "f4"),               # time in hours since start of day
    ("timestamp", "f8"),        # timestamp (Unix time)
    ("SME", "f4"),              # SuperMAG Electrojet (SME) index
    ("SML", "f4"),              # SuperMAG Lower (SML) index
    ("SMLmlat", "f4"),          # SML magnetic latitude
    ("SMLmlt", "f4"),           # SML magnetic local time
    ("SMLglat", "f4"),          # SML geographic latitude
    ("SMLglon", "f4"),          # SML geographic longitude
    ("SMU", "f4"),              # SuperMAG Upper (SMU) index
    ("SMUmlat", "f4"),          # SMU magnetic latitude
    ("SMUmlt", "f4"),           # SMU magnetic local time
    ("SMUglat", "f4"),          # SMU geographic latitude
    ("SMUglon", "f4"),          # SMU geographic longitude
    ("SMEnum", "i4"),           # Number of stations used for SME
    ("SMEr", "f4", (24,)),      # SME regional values (24 MLT sectors)
    ("SMLr", "f4", (24,)),      # SML regional values (24 MLT sectors)
    ("SMLrmlat", "f4", (24,)),  # SML regional magnetic latitudes
    ("SMLrmlt", "f4", (24,)),   # SML regional magnetic local times
    ("SMLrglat", "f4", (24,)),  # SML regional geographic latitudes
    ("SMLrglon", "f4", (24,)),  # SML regional geographic longitudes
    ("SMUr", "f4", (24,)),      # SMU regional values (24 MLT sectors)
    ("SMUrmlat", "f4", (24,)),  # SMU regional magnetic latitudes
    ("SMUrmlt", "f4", (24,)),   # SMU regional magnetic local times
    ("SMUrglat", "f4", (24,)),  # SMU regional geographic latitudes
    ("SMUrglon", "f4", (24,)),  # SMU regional geographic longitudes
    ("SMErnum", "i4", (24,)),   # Number of stations per MLT sector
    ("SMR", "f4"),              # SuperMAG Ring current (SMR) index
    ("SMRnum00", "i4"),         # Number of stations for SMR at 00 MLT
    ("SMRnum06", "i4"),         # Number of stations for SMR at 06 MLT
    ("SMRnum12", "i4"),         # Number of stations for SMR at 12 MLT
    ("SMRnum18", "i4")          # Number of stations for SMR at 18 MLT
]


# this dtype is to store the substorm lists
substorm_dtype = [
    ("date", "int32"),         # Date in the format yyyymmdd
    ("ut", "float32"),         # Time in hours since the start of the day
    ("timestamp", "float64"),  # Continuous time since 1950 (in hours)
    ("mlt", "float32"),        # Magnetic Local Time
    ("mlat", "float32"),       # Mag latitude
    ("glon", "float32"),       # Geo Longitude
    ("glat", "float32"),       # Geo Latitude
    ("source", "U7"),          # Substorm list it came from:
]

# this is where the substorm list will be stored in memory
substorms = None
