import json
import requests
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown


class LLMConsoleRenderer:
    """Handles rendering LLM output to the terminal using Rich."""

    def __init__(self):
        self.console = Console()

    def print_response(self, response: str) -> None:
        """
        Prints a formatted panel containing the LLM response.
        """
        self.console.print(
            Panel(
                Markdown(response),
                title="🤖 LLM Response",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def stream_response(self, chunks) -> None:
        """
        Streams a sequence of chunks from an LLM response.
        """
        self.console.print("\n🤖 LLM Response\n", style="bold cyan")
        with self.console.status("Thinking...", spinner="dots"):
            for chunk in chunks:
                self.console.print(chunk, end="", style="green")


class LLMClient:
    """Client for querying a local or remote LLM endpoint."""

    def __init__(
        self,
        url: str = "http://localhost:11434/api/chat",
        model: str = "gpt-oss:20b",
        temperature: float = 0.0,
        max_tokens: int = 2048,
        renderer: LLMConsoleRenderer | None = None,
        timeout: int = 60,
    ):
        self.url = url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.renderer = renderer or LLMConsoleRenderer()

    def query(self, prompt: str) -> str:
        """
        Query the model and return the full response text.
        """
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt.strip(),
                }
            ],
            "options": {
                "seed": 123,
                "temperature": self.temperature,
                "num_ctx": self.max_tokens,
            },
        }

        response_text = ""

        with requests.post(
            self.url,
            json=payload,
            stream=True,
            timeout=self.timeout,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue

                data = json.loads(line)
                if "message" in data:
                    response_text += data["message"]["content"]

        return response_text

    def query_and_render(self, prompt: str) -> None:
        """
        Query the model and print the formatted response.
        """
        response = self.query(prompt)
        self.renderer.print_response(response)


class PromptCommand:
    """CLI command registration and handler."""

    @staticmethod
    def add_to_subparsers(subparsers):
        """
        Adds the `prompt` command to the CLI.
        """
        parser = subparsers.add_parser(
            "prompt",
            help="Ask a question to the model",
        )

        parser.add_argument(
            "question",
            type=str,
            default="Hello, how can I help you?",
            help="The question to ask the model",
        )

        parser.add_argument(
            "--temperature",
            "-t",
            type=float,
            default=0.0,
            help="The temperature value for the model (default: 0.0)",
        )

        parser.add_argument(
            "--max-tokens",
            "-m",
            type=int,
            default=2048,
            help="The maximum number of tokens to generate (default: 2048)",
        )

        parser.add_argument(
            "--model",
            type=str,
            default="gpt-oss:20b",
            help="The model to query (default: gpt-oss:20b)",
        )

        parser.add_argument(
            "--url",
            "-u",
            type=str,
            default="http://localhost:11434/api/chat",
            help="The URL of the model to query",
        )

        parser.set_defaults(func=PromptCommand.run)

    @staticmethod
    def run(args):
        """
        CLI entrypoint for the prompt command.
        """
        client = LLMClient(
            url=args.url,
            model=args.model,
            temperature=float(args.temperature),
            max_tokens=int(args.max_tokens),
        )

        client.query_and_render(args.question)
