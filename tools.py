import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from livekit.agents import RunContext, function_tool

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

WEATHER_CODES = {
    0: "clear sky",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "severe thunderstorm with hail",
}


@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    """Get the current weather for a given city.

    Args:
        city: Name of the city to get the weather for.
    """
    try:
        geo_resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1},
            timeout=10,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"I couldn't find a city called {city}."

        loc = geo_data["results"][0]
        resolved_name = loc.get("name", city)
        country = loc.get("country", "")

        weather_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            },
            timeout=10,
        )
        weather_resp.raise_for_status()
        current = weather_resp.json().get("current", {})

        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        code = current.get("weather_code")
        condition = WEATHER_CODES.get(code, "unknown conditions")

        return (
            f"The weather in {resolved_name}, {country} right now is "
            f"{temp} degrees Celsius with {condition}. "
            f"Humidity is {humidity} percent and wind speed is {wind} kilometers per hour."
        )
    except requests.RequestException as e:
        return f"Sorry, I couldn't reach the weather service: {e}"
    except Exception as e:
        return f"Sorry, something went wrong getting the weather: {e}"


@function_tool()
async def send_email(context: RunContext, to_email: str, subject: str, body: str) -> str:
    """Send an email from the user's Gmail account.

    Args:
        to_email: The recipient's email address.
        subject: The subject line of the email.
        body: The main content/body of the email.
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return (
            "Email sending isn't configured yet. GMAIL_ADDRESS and "
            "GMAIL_APP_PASSWORD need to be set in the .env.local file."
        )

    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return f"Done. Email sent to {to_email} with subject '{subject}'."
    except smtplib.SMTPAuthenticationError:
        return (
            "Gmail rejected the login. Make sure GMAIL_APP_PASSWORD is a "
            "16-character App Password, not your normal Gmail password."
        )
    except Exception as e:
        return f"Sorry, I couldn't send the email: {e}"