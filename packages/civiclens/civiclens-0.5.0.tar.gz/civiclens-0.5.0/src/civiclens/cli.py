import argparse
import os
from enum import Enum
from civiclens.data import add_data_cmd
from civiclens.weather import add_weather_cmd
from civiclens.utils import add_ingest_cmd, add_query_cmd, add_info_cmd
from civiclens import __version__
from civiclens.llm import add_prompt_cmd
from civiclens.demo import PromptCommand

class Audience(str, Enum):
    youth = "youth"
    executive = "executive"
    child = "child"

def positive_int(value):
    """
    Converts a string to a positive integer.

    Args:
        value (str): The string to convert to an integer

    Returns:
        int: The converted integer

    Raises:
        argparse.ArgumentTypeError: If the value is not a positive integer
    """
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("Value must be > 0")
    return ivalue



EPILOG = """
Examples:
==================================
Ingest documents from an S3 bucket:
  civiclens ingest \\
      --source s3 \\
      --path s3://eo-archive \\
      --chunk-size 1200

Query the system with audience adaptation:
  civiclens query "How does this EO affect education?" --audience teen

Query with retrieval depth and source transparency:
  civiclens query "How does this executive order affect education?" \\
      --audience teen \\
      --top-k 5 \\
      --show-sources

Evaluate RAG system performance using benchmark data:
  civiclens eval \\
      --dataset benchmarks/eo_questions.json \\
      --metrics faithfulness answer_relevance context_recall context_precision \\
      --top-k 5 \\
      --save-results
      
Copyright © 2026 CivicLens AI
"""


def main():
    
    """
    Main function for the CivicLens AI CLI.

    This function parses command line arguments using argparse and calls
    the appropriate sub-command function based on the value of the
    'command' argument.

    The available sub-commands are ingest, query, and eval.

    The ingest command ingests documents into the vector database.

    The query command generates a civic summary for a given set of
    documents.

    The eval command evaluates the performance of the model on a
    given set of documents.

    """
    parser = argparse.ArgumentParser(
        prog="civiclens",
        epilog=EPILOG,
        description="CivicLens AI – Document analysis and civic summarization CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to YAML or JSON config file"
    )

    parser.add_argument(
        "--openai-key",
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key",
        required=False
    )
    
    parser.add_argument(
        "--audience",
        "-a",
        choices=[a.value for a in Audience],
        default=Audience.youth.value
    )
    
    parser.add_argument(
        "--top-k", 
        "-k",
        type=positive_int, 
        default=5
    )
    
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version number and exit"
    )

    subparsers = parser.add_subparsers(
        title="Available Commands",
        dest="command",
        required=True
    )

    # add commands
    add_ingest_cmd(subparsers)
    add_query_cmd(subparsers)
    add_info_cmd(subparsers)
    add_prompt_cmd(subparsers)
    add_data_cmd(subparsers)
    add_weather_cmd(subparsers)

    # PromptCommand.add_to_subparsers(subparsers)


    try:
        args = parser.parse_args()
        args.func(args)
    except SystemExit:
        print("Use --help to see available commands.")
        raise


if __name__ == "__main__":
    main()
