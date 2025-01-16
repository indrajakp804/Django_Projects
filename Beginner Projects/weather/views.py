import requests
from django.shortcuts import render


def index(request):
    city = request.GET.get("city", "New York")  # default city
    api_key = "7cf57d8f6e4c6f2f408ed7b9faccd7a1"  # replace with your OpenWeatherMap API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        weather_data = {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
        }
    except Exception as e:
        weather_data = None

    return render(request, "weather/weather.html", {"weather_data": weather_data})
