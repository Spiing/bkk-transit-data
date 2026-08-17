
import googlemaps
import pandas as pd
import os
import requests
from datetime import datetime
 
GMAPS_API_KEY = os.environ["GMAPS_API_KEY"]
OWM_API_KEY = os.environ["OWM_API_KEY"]
CSV_FILE = "transit_data.csv"
 
gmaps = googlemaps.Client(key=GMAPS_API_KEY)
 
routes = [
    ("KMUTT Bangkok", "ใต้ทางด่วน กม.9"),
    ("ใต้ทางด่วน กม.9", "KMUTT Bangkok"),
    ("ใต้ทางด่วน กม.9", "Mo Chit BTS Station"),
    ("ใต้ทางด่วน กม.9", "Siam Paragon"),
    ("KMUTT Bangkok", "The Mall Life Store BangKae"),
    ("KMUTT Bangkok", "Opposite Bangpakok Market"),
    ("วัดแค บางปลากด", "KMUTT Bangkok"),
]
 
# พิกัดกรุงเทพฯ สำหรับดึงสภาพอากาศ (จุดกลางเมือง เพียงพอสำหรับภาพรวมทั้ง 7 route)
BKK_LAT = 13.7563
BKK_LON = 100.5018
 
 
def get_weather(lat=BKK_LAT, lon=BKK_LON):
    """ดึงสภาพอากาศปัจจุบันจาก OpenWeatherMap"""
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric"
        )
        r = requests.get(url, timeout=10).json()
        rain_mm = r.get("rain", {}).get("1h", 0)
        return {
            "rain_mm": rain_mm,
            "is_raining": 1 if rain_mm > 0 else 0,
            "temp_c": r.get("main", {}).get("temp"),
            "humidity": r.get("main", {}).get("humidity"),
            "weather_desc": r.get("weather", [{}])[0].get("description", "N/A"),
        }
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        return {
            "rain_mm": None,
            "is_raining": None,
            "temp_c": None,
            "humidity": None,
            "weather_desc": "N/A",
        }
 
 
def log_transit_data(origin, destination, weather):
    now = datetime.now()
    result = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="transit",
        departure_time=now,
    )
 
    if not result:
        print(f"No route found: {origin} -> {destination}")
        return None
 
    leg = result[0]["legs"][0]
    if "duration_in_traffic" in leg:
        duration_min = leg["duration_in_traffic"]["value"] / 60
    else:
        duration_min = leg["duration"]["value"] / 60
    distance_km = leg["distance"]["value"] / 1000
 
    return {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "hour": now.hour,
        "origin": origin,
        "destination": destination,
        "duration_min": round(duration_min, 1),
        "distance_km": round(distance_km, 2),
        "departure": leg.get("departure_time", {}).get("text", "N/A"),
        "arrival": leg.get("arrival_time", {}).get("text", "N/A"),
        # ตัวแปรสภาพอากาศ ดึงครั้งเดียวต่อรอบรัน ใช้ร่วมกันทุก route ในรอบนั้น
        "rain_mm": weather["rain_mm"],
        "is_raining": weather["is_raining"],
        "temp_c": weather["temp_c"],
        "humidity": weather["humidity"],
        "weather_desc": weather["weather_desc"],
    }
 
 
# ดึงสภาพอากาศครั้งเดียวต่อรอบรัน (ประหยัด API call แทนที่จะดึงซ้ำทุก route)
weather_now = get_weather()
 
rows = [log_transit_data(o, d, weather_now) for o, d in routes]
rows = [r for r in rows if r]
 
file_exists = os.path.exists(CSV_FILE)
pd.DataFrame(rows).to_csv(CSV_FILE, mode="a", header=not file_exists, index=False)
print(f"Logged {len(rows)} rows (rain_mm={weather_now['rain_mm']}, temp={weather_now['temp_c']})")
