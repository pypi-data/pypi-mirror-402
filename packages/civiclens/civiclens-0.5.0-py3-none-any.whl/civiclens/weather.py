import json
import httpx
import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def print_response(response: str):
    """
    Prints a formatted panel containing the response.

    Args:
        response (str): The formatted response to print.
    """
    console.print(
        Panel(
            Markdown(response),
            title="🤖 Response",
            border_style="cyan",
            padding=(1, 2),
        )
    )


async def get_weather_async(location: str = ""):
    async with httpx.AsyncClient(headers={"User-Agent": "curl"}) as client:
        r = await client.get(
            f"https://wttr.in/{location}",
            params={"format": "j1"},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()


def get_weather(
    location: str = "",
    *,
    format: str = "j1",
    timeout: int = 30
) -> dict:
    """
    Fetch weather data from wttr.in.

    :param location: City, country, or coordinates (e.g. "Accra", "London", "37.77,-122.42")
    :param format: Output format ("j1" = JSON, "3" = short text, "4" = emoji)
    :return: Parsed JSON weather data
    """
    url = f"https://wttr.in/{location}"
    params = {"format": format}

    response = requests.get(
        url,
        params=params,
        headers={"User-Agent": "curl"},  # important for wttr.in
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()

def extract_lat_lon(data: dict) -> tuple[float | None, float | None]:
    """
    Extract latitude and longitude from weather data.

    :param data: Parsed JSON weather data
    :return: A tuple of (latitude, longitude) or (None, None) if extraction fails
    """
    
    try:
        area = data["nearest_area"][0]
        return float(area["latitude"]), float(area["longitude"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None, None


def print_weather(args) -> None:
    """
    Print weather information in a human-readable format.

    :param data: Weather data dictionary
    """
    # location
    location = str(args.location)

    # data
    data = get_weather(location=location)
    # print(json.dumps(data, indent=4))
    # print(data)
    
    current = data["current_condition"][0]
    temp_f = current["temp_F"]
    humidity = current["humidity"]
    description = current["weatherDesc"][0]["value"]
    
    response_md = f"""
        ### 🌤️ Current Weather

        Location: {location}  
        Temperature: {temp_f}°F  
        Humidity: {humidity}%  
        Condition: {description}
        (Latitude, Longitude): {extract_lat_lon(data)}
        """
    print_response(response_md.strip())

    


def add_weather_cmd(subparsers):
    """
    Adds the get command to the CLI.

    The get command asks a question to the model.

    The available arguments are:
    - weather: The question to ask the model
    - --location: The location to query
    - --humidity: The humidity to query
    - --description: The description to query

    Usage: civiclens get <question> --location <location> --humidity <humidity> --description <description>
    """
    query = subparsers.add_parser(
        "get",
        help="get the weather")

    query.add_argument(
        "weather", 
        type=str,
        help="Get the weather"
    )

    query.add_argument(
        "--location",
        "-l",
        default="Dallas, TX",
        type=str,
        help="The location to query"
    )
    
    query.add_argument(
        "--humidity",
        action="store_true",
        help="Include humidity in the weather output"
    )

    query.add_argument(
        "--description",
        action="store_true",
        help="Include weather condition in the output"
    )

    query.set_defaults(func=print_weather)