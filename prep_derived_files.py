"""
prep_derived_files.py  --  makes the four derived data files used by the visualization.

  area_metro.json      one record per DLD area: nearest metro station, straight-line distance (km)
                       from the area centre, and the station's coordinates
  stations.json        the metro stations (one point per station) with current names
  station_venues.json  recorded venues within 1 km of their nearest station
  area_venues.json     recorded venues within 1.5 km of the centre of every area that is more
                       than 2 km from its nearest station

Why our own distance instead of the column `nearest_metro_en`?
  It has 56 labels, many of which are not stations of the metro file (tram / monorail stops,
  old names), and even for matching names the area centre is often 4-7 km from the station
  DLD names. Distances computed from the official station coordinates are reproducible and
  comparable across all areas.

Usage:
  python3 prep_derived_files.py transactions.csv dubai_metro_stations.geojson venues.csv
  (the three input files are in the course repository; the venues file is the Foursquare file)

Notes
  - Distances are straight lines (haversine), not walking or driving distances.
  - The venue category -> six-group lookup table is written out below (GROUP_CATEGORIES);
    a category that is not listed falls into "Other".
  - A venue appears in station_venues.json once, next to its NEAREST station, and only if
    that station is within 1 km.
"""
import json
import sys

import numpy as np
import pandas as pd

TX, ST, VEN = sys.argv[1], sys.argv[2], sys.argv[3]

# Current station names, keyed by STATION CODE (names keep changing).
# Source: RTA "Dubai Rail Network" map, published 2026-09-25 ("Find Your Destination" index).
# The course file gives names as of about 2020, so we keep both: `station` (course file)
# and `station_now` (RTA map). Stations that are not on the 2026 map keep their 2020 name.
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


GROUP_CATEGORIES = {
    'Restaurants': [
        'Afghan Restaurant',
        'African Restaurant',
        'American Restaurant',
        'Asian Restaurant',
        'Australian Restaurant',
        'BBQ Joint',
        'Bakery',
        'Belgian Restaurant',
        'Bistro',
        'Brazilian Restaurant',
        'Breakfast Spot',
        'Buffet',
        'Burger Joint',
        'Burrito Place',
        'Cajun / Creole Restaurant',
        'Chinese Restaurant',
        'Churrascaria',
        'Comfort Food Restaurant',
        'Dim Sum Restaurant',
        'Diner',
        'Eastern European Restaurant',
        'Egyptian Restaurant',
        'Ethiopian Restaurant',
        'Falafel Restaurant',
        'Fast Food Restaurant',
        'Filipino Restaurant',
        'Food Court',
        'French Restaurant',
        'Fried Chicken Joint',
        'Greek Restaurant',
        'Hong Kong Restaurant',
        'Hot Dog Joint',
        'Indian Restaurant',
        'Indonesian Restaurant',
        'Iraqi Restaurant',
        'Italian Restaurant',
        'Japanese Restaurant',
        'Korean Restaurant',
        'Kurdish Restaurant',
        'Latin American Restaurant',
        'Lebanese Restaurant',
        'Mediterranean Restaurant',
        'Mexican Restaurant',
        'Middle Eastern Restaurant',
        'Modern European Restaurant',
        'Molecular Gastronomy Restaurant',
        'Moroccan Restaurant',
        'New American Restaurant',
        'Noodle House',
        'North Indian Restaurant',
        'Pakistani Restaurant',
        'Persian Restaurant',
        'Peruvian Restaurant',
        'Pizza Place',
        'Restaurant',
        'Russian Restaurant',
        'Salad Place',
        'Sandwich Place',
        'Scandinavian Restaurant',
        'Seafood Restaurant',
        'Snack Place',
        'South American Restaurant',
        'South Indian Restaurant',
        'Spanish Restaurant',
        'Steakhouse',
        'Sushi Restaurant',
        'Syrian Restaurant',
        'Tapas Restaurant',
        'Tex-Mex Restaurant',
        'Thai Restaurant',
        'Theme Restaurant',
        'Turkish Restaurant',
        'Vegetarian / Vegan Restaurant',
        'Vietnamese Restaurant',
        'Yemeni Restaurant',
    ],
    'Cafés and coffee': [
        'Café',
        'Coffee Shop',
        'Tea Room',
    ],
    'Hotels': [
        'Bed & Breakfast',
        'Hotel',
        'Motel',
        'Resort',
    ],
    'Shops': [
        'Accessories Store',
        'Arts & Crafts Store',
        'Bookstore',
        'Boutique',
        'Bridal Shop',
        'Camera Store',
        'Chocolate Shop',
        'Clothing Store',
        'Convenience Store',
        'Cosmetics Shop',
        'Cupcake Shop',
        'Department Store',
        'Dessert Shop',
        'Donut Shop',
        'Duty-free Shop',
        'Electronics Store',
        'Farmers Market',
        'Fish Market',
        'Flea Market',
        'Flower Shop',
        'Food & Drink Shop',
        'Frozen Yogurt Shop',
        'Furniture / Home Store',
        'Gift Shop',
        'Grocery Store',
        'Ice Cream Shop',
        'Jewelry Store',
        'Kids Store',
        'Lingerie Store',
        'Market',
        "Men's Store",
        'Miscellaneous Shop',
        'Mobile Phone Shop',
        'Mobility Store',
        'Motorcycle Shop',
        'Music Store',
        'Organic Grocery',
        'Perfume Shop',
        'Pet Store',
        'Pharmacy',
        'Record Shop',
        'Salon / Barbershop',
        'Shoe Store',
        'Shopping Mall',
        'Shopping Plaza',
        'Smoke Shop',
        'Sporting Goods Shop',
        'Supermarket',
        'Tailor Shop',
        'Toy / Game Store',
        "Women's Store",
    ],
    'Beach and leisure': [
        'Amphitheater',
        'Art Gallery',
        'Art Museum',
        'Athletics & Sports',
        'Bar',
        'Beach',
        'Cocktail Bar',
        'Garden',
        'Garden Center',
        'Golf Course',
        'Gym',
        'Gym / Fitness Center',
        'History Museum',
        'Hookah Bar',
        'Hotel Bar',
        'Hotel Pool',
        'Juice Bar',
        'Karaoke Bar',
        'Mini Golf',
        'Movie Theater',
        'Museum',
        'Nightclub',
        'Park',
        'Pool',
        'Pool Hall',
        'Sports Bar',
        'Sports Club',
        'Stadium',
        'Tennis Stadium',
        'Theme Park',
        'Theme Park Ride / Attraction',
        'Water Park',
        'Waterfront',
        'Wine Bar',
        'Zoo',
    ],
    'Other': [
        'Airport',
        'Airport Lounge',
        'Airport Service',
        'Arcade',
        'Bank',
        'Basketball Court',
        'Bowling Alley',
        'Business Service',
        'Canal',
        'Comedy Club',
        'Concert Hall',
        'Cycle Studio',
        'Deli / Bodega',
        'Gastropub',
        'General Entertainment',
        'Health & Beauty Service',
        'Historic Site',
        'Irish Pub',
        'Lounge',
        'Monument / Landmark',
        'Multiplex',
        'Music Venue',
        'Nail Salon',
        'Office',
        'Opera House',
        'Performing Arts Venue',
        'Pilates Studio',
        'Plaza',
        'Post Office',
        'Pub',
        'Public Art',
        'Residential Building (Apartment / Condo)',
        'Roof Deck',
        'Scenic Lookout',
        'Skating Rink',
        'Ski Area',
        'Soccer Field',
        'Spa',
        'Tourist Information Center',
        'Track',
        'Tram Station',
        'University',
        'Yoga Studio',
    ],
}

GROUP_OF = {c: g for g, cs in GROUP_CATEGORIES.items() for c in cs}


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km (lat2/lon2 may be arrays)."""
    p = np.pi / 180
    a = (np.sin((lat2 - lat1) * p / 2) ** 2
         + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def write(name, records):
    json.dump(records, open(name, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(records):5d} records -> {name}")


# 1) one row per area (all transactions of an area share the same point); rows without
#    coordinates are dropped
tx = pd.read_csv(TX, low_memory=False)
areas = (tx.dropna(subset=["area_lat", "area_lon"])
           .groupby("area_id", as_index=False)
           .agg(area_lat=("area_lat", "first"), area_lon=("area_lon", "first")))

# 2) the stations (Union and BurJuman appear on two lines -> keep one point each)
gj = json.load(open(ST, encoding="utf-8"))
st = pd.DataFrame([f["properties"] for f in gj["features"]]).drop_duplicates("STATION_NAME")
st = st.reset_index(drop=True)
st["station_now"] = [CURRENT_NAME.get(c, n) for c, n in zip(st.STATION_NO, st.STATION_NAME)]

# 3) nearest station for every area -> area_metro.json
D = np.array([haversine_km(r.area_lat, r.area_lon, st.LAT_STATION.values, st.LON_STATION.values)
              for r in areas.itertuples()])
j = D.argmin(axis=1)
areas["km"] = D.min(axis=1).round(3)
areas["station"] = st.STATION_NAME.values[j]
areas["station_now"] = st.station_now.values[j]
areas["station_code"] = st.STATION_NO.values[j]
areas["station_lat"] = st.LAT_STATION.values[j]
areas["station_lon"] = st.LON_STATION.values[j]
write("area_metro.json", areas[["area_id", "km", "station", "station_now", "station_code",
                                "station_lat", "station_lon"]].to_dict(orient="records"))

# 4) stations.json
write("stations.json", st[["STATION_NO", "LAT_STATION", "LON_STATION", "station_now"]]
      .to_dict(orient="records"))

# 5) venues (unique by venue id) with their group
ven = pd.read_csv(VEN).drop_duplicates("Venue Id").reset_index(drop=True)
ven["group"] = ven["Venue Category"].map(GROUP_OF).fillna("Other")

# 5a) station_venues.json: each venue next to its nearest station, kept if within 1 km
rows = []
for v in ven.itertuples(index=False):
    d = haversine_km(v[7], v[8], st.LAT_STATION.values, st.LON_STATION.values)
    k = int(d.argmin())
    if d[k] <= 1.0:
        rows.append({"id": v[5], "name": v[6], "category": v[9], "lat": float(v[7]), "lon": float(v[8]),
                     "station_code": st.STATION_NO.values[k], "distance_km": float(d[k]),
                     "group": v[-1]})
write("station_venues.json", rows)

# 5b) area_venues.json: venues within 1.5 km of the centre of areas more than 2 km from a station
rows = []
for a in areas[areas.km > 2].itertuples():
    d = haversine_km(a.area_lat, a.area_lon, ven["Venue Latitude"].values, ven["Venue Longitude"].values)
    for i in np.where(d <= 1.5)[0]:
        v = ven.iloc[i]
        rows.append({"area_id": int(a.area_id), "id": v["Venue Id"], "name": v["Venue"],
                     "category": v["Venue Category"], "lat": float(v["Venue Latitude"]),
                     "lon": float(v["Venue Longitude"]), "distance_km": round(float(d[i]), 3),
                     "group": v["group"]})
write("area_venues.json", rows)
