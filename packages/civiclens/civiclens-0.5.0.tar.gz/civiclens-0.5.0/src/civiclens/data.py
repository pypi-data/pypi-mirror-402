import requests
import json
import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def print_llm_response(response: str):
    """
    Prints a formatted panel containing the LLM response.

    Args:
        response (str): The LLM response to print.
    """
    console.print(
        Panel(
            Markdown(response),
            title="🤖 LLM Response",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def fetch_ip_data(args):
    """
    Fetch IP data from a provided URL.

    Args:
        args: A parsed argparse object containing the URL to fetch IP data from.

    Returns:
        dict: A JSON object containing IP data.
    """
    url = args.url
    ip = args.ip
    response = requests.get(url).json()

    if response["status"] == "success":
        return print_llm_response(json.dumps(response["query"], indent=4))
    else:
        return print_llm_response(json.dumps(response, indent=4))


def add_data_cmd(subparsers):
    """
    Adds the data command to the CLI.

    The data command asks a data question and prints the response.

    The available arguments are:
    - location: The location to get the data for.
    - --url: The URL to query (default: http://ip-api.com/json/)
    """
    query = subparsers.add_parser(
        "show",
        help="Ask a data question")

    query.add_argument(
        "data", 
        type=str,
        help="Get the data"
    )

    query.add_argument(
        "--ip",
        action="store_true",
        help="The IP address to query"
    )
    
    query.add_argument(
        "--url",
        "-u",
        type=str,
        default="http://ip-api.com/json/",
        help="The URL to query (default: http://ip-api.com/json/)"
    )

    query.set_defaults(func=fetch_ip_data)