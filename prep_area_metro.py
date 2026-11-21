"""
prep_area_metro.py  --  derive ONE new field for the Metro Premium visualization.

For every DLD area in transactions.csv we compute the straight-line (haversine)
distance from the area's centre (area_lat, area_lon) to the NEAREST station of
dubai_metro_stations.geojson, and remember which station that is.

Why not use the column `nearest_metro_en`?
  - it has 56 different labels, but many are NOT stations of the geojson
    (tram / monorail stops such as "Harbour Tower", "Palm Jumeirah", old names
    such as "Damac Properties" or "Sharaf Dg Metro Station");
  - even for matching names, the area centre is often 4-7 km from the station
    named by DLD (e.g. "Rashidiya Metro Station" -> 6.6 km).
  So the DLD label is too inconsistent to measure distance. Computing our own
  distance from the official station coordinates is reproducible and comparable
  across all areas.

Usage:   python3 prep_area_metro.py            (downloads the files from GitHub)
         python3 prep_area_metro.py tx.csv stations.geojson   (local copies)
Output:  area_metro.json   (one record per area: area_id, km, station, station_code)
"""
import json
import sys

import numpy as np
import pandas as pd

BASE = "https://raw.githubusercontent.com/sharios/CS333/main/2026-27"
TX = sys.argv[1] if len(sys.argv) > 1 else BASE + "/Part%202/transactions.csv"
ST = sys.argv[2] if len(sys.argv) > 2 else BASE + "/Part%203/dubai_metro_stations.geojson"


# Current station names, keyed by STATION CODE (not by name, because names keep changing).
# Source: RTA "Dubai Rail Network" map, published 2026-09-25 (index "Find Your Destination").
# The course file gives names as of ~2020, so we keep both: `station` (2020, course file)
# and `station_now` (2026, RTA map). Capitalisation is normalised.
CURRENT_NAME = {
    # Red line
    "R11": "Centrepoint", "R12": "Emirates", "R13": "Airport Terminal 3",
    "R14": "Airport Terminal 1", "R15": "Al Garhoud", "R16": "City Centre Deira",
    "R17": "Al Rigga", "R18": "Union", "R19": "BurJuman", "R20": "ADCB",
    "R21": "Max", "R22": "World Trade Centre", "R23": "Emirates Towers",
    "R24": "Financial Centre", "R25": "Burj Khalifa/Dubai Mall", "R26": "Business Bay",
    "R29": "Garmin", "R31": "Equiti", "R32": "Mall of the Emirates",
    "R33": "Insurance Market", "R34": "Dubai Internet City", "R35": "Al Fardan Exchange",
    "R36": "Sobha Realty", "R37": "DMCC", "R38": "National Paints", "R39": "Ibn Battuta",
    "R40": "Energy", "R41": "Danube", "R42": "Life Pharmacy",
    # Route 2020 branch
    "R70": "The Gardens", "R71": "Discovery Gardens", "R72": "Al Furjan",
    "R73": "Jumeirah Golf Estates", "R74": "Dubai Investment Park",
    "E07": "Expo 2020",   # course file code E07 = R76 on the RTA map
    # Green line
    "G11": "e&", "G12": "Al Qusais", "G13": "Dubai Airport Free Zone", "G14": "Al Nahda",
    "G15": "Stadium", "G16": "Al Qiyadah", "G17": "Abu Hail", "G18": "Abu Baker Al Siddique",
    "G19": "Salah Al Din", "G20": "Union", "G21": "Baniyas Square", "G22": "Gold Souq",
    "G23": "Al Ras", "G24": "Al Ghubaiba", "G25": "Sharaf DG", "G26": "BurJuman",
    "G27": "Oud Metha", "G28": "Dubai Healthcare City", "G29": "Al Jadaf", "G30": "Creek",
}


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km (vectorised: lat2/lon2 may be arrays)."""
    p = np.pi / 180
    a = (np.sin((lat2 - lat1) * p / 2) ** 2
         + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * 6371 * np.arcsin(np.sqrt(a))


# 1) one row per area (all transactions of an area share the same point);
#    the 2 records without coordinates are dropped.
tx = pd.read_csv(TX, low_memory=False)
areas = (tx.dropna(subset=["area_lat", "area_lon"])
           .groupby("area_id", as_index=False)
           .agg(area_lat=("area_lat", "first"), area_lon=("area_lon", "first")))

# 2) the stations (Union and BurJuman appear on two lines -> keep one point each)
if ST.startswith("http"):
    import urllib.request
    gj = json.load(urllib.request.urlopen(ST))
else:
    gj = json.load(open(ST))
st = pd.DataFrame([f["properties"] for f in gj["features"]]).drop_duplicates("STATION_NAME")

# 3) nearest station for every area
D = np.array([haversine_km(r.area_lat, r.area_lon, st.LAT_STATION.values, st.LON_STATION.values)
              for r in areas.itertuples()])
areas["km"] = D.min(axis=1).round(3)
areas["station"] = st.STATION_NAME.values[D.argmin(axis=1)]
areas["station_code"] = st.STATION_NO.values[D.argmin(axis=1)]

# current name; stations without a passenger stop on the 2026 map (R75) fall back to the 2020 name
areas["station_now"] = [CURRENT_NAME.get(c, s) for c, s in zip(areas.station_code, areas.station)]

out = areas[["area_id", "km", "station", "station_now", "station_code"]].to_dict(orient="records")
json.dump(out, open("area_metro.json", "w"), separators=(",", ":"))
print(f"{len(out)} areas written to area_metro.json")
print(areas.km.describe().round(2).to_string())
