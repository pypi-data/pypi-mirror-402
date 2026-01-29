# py-ha-smn

Async Python client for the Servicio Meteorológico Nacional Argentina (SMN) API.

This library is designed for use with [Home Assistant](https://www.home-assistant.io/).

## Installation

```bash
pip install py-ha-smn
```

## Usage

```python
import aiohttp
from smn_argentina_api import SMNApiClient, SMNTokenManager

async def main():
    async with aiohttp.ClientSession() as session:
        # Create token manager and API client
        token_manager = SMNTokenManager(session)
        client = SMNApiClient(session, token_manager)

        # Get location ID from coordinates
        location = await client.async_get_location(-34.6037, -58.3816)
        location_id = str(location.get("id"))

        # Fetch current weather
        weather = await client.async_get_current_weather(location_id)
        print(f"Temperature: {weather.get('temperature')}°C")

        # Fetch forecast
        forecast = await client.async_get_forecast(location_id)
        print(f"Forecast days: {len(forecast.get('forecast', []))}")

        # Fetch alerts
        alerts = await client.async_get_alerts(location_id)
        print(f"Warnings: {len(alerts.get('warnings', []))}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## API Methods

### SMNApiClient

- `async_get_location(latitude, longitude)` - Get location ID from coordinates
- `async_get_current_weather(location_id)` - Fetch current weather data
- `async_get_forecast(location_id)` - Fetch weather forecast
- `async_get_alerts(location_id)` - Fetch weather alerts
- `async_get_shortterm_alerts(location_id)` - Fetch short-term severe weather alerts
- `async_get_heat_warnings(area_id)` - Fetch heat warnings

### SMNTokenManager

Handles JWT token authentication with the SMN API. Automatically refreshes tokens before expiration.

## Exceptions

- `SMNError` - Base exception for all SMN API errors
- `SMNConnectionError` - Connection to SMN API failed
- `SMNAuthenticationError` - Authentication with SMN API failed
- `SMNTokenError` - Token fetching or parsing failed

## License

Apache License 2.0
