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

def stream_llm_response(chunks):
    """
    Stream a sequence of chunks from an LLM response to the console.

    :param chunks: An iterable of strings, where each string is a chunk of the LLM response.
    """
    console.print("\n🤖 LLM Response\n", style="bold cyan")
    with console.status("Thinking...", spinner="dots"):
        for chunk in chunks:
            console.print(chunk, end="", style="green")
            
            

def query_model(args):
    # Create the data payload as a dictionary
 
    """
    Query a model using the provided prompt and parameters.

    Parameters:
    prompt (str): The input to the model.
    stream (bool, optional): Whether to stream the response. Defaults to True.
    model (str, optional): The model to query. Defaults to "gpt-oss:20b".
    temperature (float, optional): The temperature value for the model. Defaults to 0.0.
    max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 2048.
    url (str, optional): The URL of the model to query. Defaults to "http://localhost:11434/api/chat".

    Returns:
    str: The output of the model.

    """
    url = args.url
    prompt = args.question.strip()
    model = args.model
    temperature = float(args.temperature)
    max_tokens = int(args.max_tokens)

    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "options": {     # Settings below are required for deterministic responses
            "seed": 123,
            "temperature": temperature,
            "num_ctx": max_tokens
        }
    }

    # Send the POST request
    with requests.post(url, json=data, stream=True, timeout=60) as r:
        r.raise_for_status()
        response_data = ""
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            response_json = json.loads(line)
            if "message" in response_json:
                response_data += response_json["message"]["content"]

    # Print the LLM response
    # if stream:
    #     stream_llm_response(response_data)
    # else:
    print_llm_response(response=response_data)


def add_prompt_cmd(subparsers):
    """
    Adds the query command to the CLI.

    The query command asks a question to the model.

    The available arguments are:
    - question: The question to ask the model
    - --temperature or -t: The temperature value for the model (default: 0.0)
    - --max-tokens or -m: The maximum number of tokens to generate (default: 2048)
    """
    query = subparsers.add_parser(
        "prompt",
        help="Ask a question to the model")

    query.add_argument(
        "question", 
        type=str,
        default="Hello, how can I help you?",
        help="The question to ask the model"
    )

    query.add_argument(
        "--temperature",
        "-t",
        type=float,
        default=0.0,
        help="The temperature value for the model (default: 0.0)"
    )

    query.add_argument(
        "--max-tokens",
        "-m",
        type=int,
        default=2048,
        help="The maximum number of tokens to generate (default: 2048)"
    )
    
    query.add_argument(
        "--model",
        type=str,
        default="gpt-oss:20b",
        help="The model to query (default: gpt-oss:20b)"
    )
    
    query.add_argument(
        "--url",
        "-u",
        type=str,
        default="http://localhost:11434/api/chat",
        help="The URL of the model to query (default: http://localhost:11434/api/chat)"
    )
    
    # query.add_argument(
    #     "--port",
    #     "-p",
    #     type=str,
    #     default="11434:11434",
    #     help="Port mapping for the model server (default: 11434:11434)"
    # )

    query.set_defaults(func=query_model)
    
    