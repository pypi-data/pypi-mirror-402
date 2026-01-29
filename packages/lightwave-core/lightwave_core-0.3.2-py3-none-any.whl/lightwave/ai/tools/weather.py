"""Weather tools for Pydantic AI agents.

This module provides tools for getting location coordinates and weather information
that can be used by any agent that needs weather capabilities.

Adapted from https://ai.pydantic.dev/examples/weather-agent/
"""

from __future__ import annotations as _annotations

from typing import Any

import requests
from httpx import AsyncClient
from pydantic import BaseModel
from pydantic_ai.toolsets import FunctionToolset


class LatLng(BaseModel):
    """Latitude and longitude coordinates."""

    lat: float
    lng: float


async def get_lat_lng(location_description: str) -> LatLng | None:
    """Get the latitude and longitude of a location.

    Args:
        location_description: A description of a location.

    Returns:
        LatLng with coordinates if found, None if location not found or on error.
    """
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": location_description,
        "format": "json",
        "limit": 1,
    }
    headers = {
        "User-Agent": "LightWave/1.0 (https://lightwave-media.site; hello@lightwave-media.ltd)",
        "Referer": "https://lightwave-media.site/",
    }
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            first_result = data[0]
            if "lat" in first_result and "lon" in first_result:
                lat = float(first_result["lat"])
                lon = float(first_result["lon"])
                return LatLng(lat=lat, lng=lon)
    except (
        requests.RequestException,  # Network errors, timeouts, HTTP errors
        ValueError,  # JSON decode errors, float conversion errors
        KeyError,  # Missing keys (shouldn't happen with checks, but safety)
        TypeError,  # Unexpected data types
    ):
        pass
    return None


async def get_weather(lat: float, lng: float) -> dict[str, Any]:
    """Get the weather at a location using Open-Meteo API.

    Args:
        lat: Latitude of the location.
        lng: Longitude of the location.
    """
    params = [
        "temperature_2m",
        "precipitation_probability",
        "precipitation",
        "apparent_temperature",
        "weather_code",
        "cloud_cover",
        "rain",
        "showers",
        "visibility",
        "wind_speed_10m",
        "wind_direction_10m",
    ]
    async with AsyncClient() as client:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lng,
                "current": ",".join(params),
            },
        )
        response.raise_for_status()

        data = response.json()
        current = data.get("current", {})
        return current


weather_toolset = FunctionToolset(
    tools=[
        get_lat_lng,
        get_weather,
    ]
)
