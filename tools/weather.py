import urllib.request 
import urllib.parse
import json

def get_weather(location:str) -> str:
    """Fetches the weather for a given location.
    Args:
        location (str): The city or location to fetch the weather for(eg,"New York","London","Tokyo")
    Returns:
        str: The weather for the given location
    """
    try:
        # Step 1: Geocoding (City name to Lat/Lon)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location)}&count=1&language=en&format=json"
        with urllib.request.urlopen(geo_url, timeout=10) as response:
            geo_data = json.loads(response.read().decode('utf-8'))
        
        if not geo_data.get('results'):
            return f"Location '{location}' not found."
        
        result = geo_data['results'][0]
        lat, lon = result['latitude'], result['longitude']
        city_name = result.get('name', location)

        # Step 2: Fetch Weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        with urllib.request.urlopen(weather_url, timeout=10) as response:
            weather_data = json.loads(response.read().decode('utf-8'))
        
        current = weather_data['current_weather']
        temp = current['temperature']
        windspeed = current['windspeed']
        
        return f"{city_name}: {temp}°C, Wind Speed: {windspeed} km/h"

    except Exception as e:
        return f"Error fetching weather for {location}: {e}"


