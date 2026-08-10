import googlemaps
import pandas as pd
import os
from datetime import datetime

API_KEY = os.environ["GMAPS_API_KEY"]
CSV_FILE = "transit_data.csv"

gmaps = googlemaps.Client(key=API_KEY)

routes = [
  ("KMUTT Bangkok", "ใต้ทางด่วน กม.9"),
  ("ใต้ทางด่วน กม.9", "KMUTT Bangkok"),
  ("ใต้ทางด่วน กม.9", "Mo Chit BTS Station"),
  ("ใต้ทางด่วน กม.9", "Siam Paragon"),
  ("KMUTT Bangkok", "The Mall Life Store BangKae"),
  ("KMUTT Bangkok", "Opposite Bangpakok Market"),
  ("วัดแค บางปลากด", "KMUTT Bangkok"),
]

def log_transit_data(origin, destination):
    now = datetime.now()
    result = gmaps.directions(origin=origin, destination=destination,
                               mode="transit", departure_time=now)
    if not result:
        print(f"No route found: {origin} -> {destination}")
        return None

    leg = result[0]['legs'][0]
    duration_min = leg.get('duration_in_traffic', leg['duration'])['value'] / 60
    distance_km = leg['distance']['value'] / 1000

    return {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "hour": now.hour,
        "origin": origin,
        "destination": destination,
        "duration_min": round(duration_min, 1),
        "distance_km": round(distance_km, 2),
        "departure": leg.get('departure_time', {}).get('text', 'N/A'),
        "arrival": leg.get('arrival_time', {}).get('text', 'N/A'),
    }

rows = [log_transit_data(o, d) for o, d in routes]
rows = [r for r in rows if r]

file_exists = os.path.exists(CSV_FILE)
pd.DataFrame(rows).to_csv(CSV_FILE, mode='a', header=not file_exists, index=False)
print(f"Logged {len(rows)} rows")
