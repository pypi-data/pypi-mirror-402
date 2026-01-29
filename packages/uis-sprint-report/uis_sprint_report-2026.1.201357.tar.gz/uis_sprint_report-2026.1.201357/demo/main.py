"""
This module defines the command-line interface for the UIS Sprint Report tool. It allows users to generate sprint
reports, create PowerPoint presentations based on sprint activities, and interact with the sprint data
via a chat interface.
The tool integrates with GitLab to fetch issues and uses the Ollama model for processing data.

The module sets up the CLI with various options to specify details like API base URL, access token, commands,
and other necessary parameters to control the behavior of the report generation and interaction processes.
"""
import click
from .utils import check_gitlab_credentials, check_ollama
from .embeddings import generate_embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from .demo import execute_command
from .config import (
    DEFAULT_API_BASE,
    DEFAULT_COMMAND,
    DEFAULT_GROUP_ID,
    DEFAULT_ITERATION_ID,
    DEFAULT_LABELS,
    DEFAULT_MODEL,
    DEFAULT_PPTX_FILE_NAME,
    CACHE_FILE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MAX_TOKENS,
    MAX_ATTEMPTS
)


@click.command()
@click.option("--api-base",     default=DEFAULT_API_BASE,       metavar="BASE_URL")
@click.option("--access-token", default=None,                   metavar="ACCESS_TOKEN")
@click.option("--command",      default=DEFAULT_COMMAND,        metavar="COMMAND")
@click.option("--group-id",     default=DEFAULT_GROUP_ID,       metavar="GROUP_ID")
@click.option("--iteration-id", default=DEFAULT_ITERATION_ID,   metavar="ITERATION_ID")
@click.option("--labels",       default=DEFAULT_LABELS,         metavar="LABELS")
@click.option("--model",        default=DEFAULT_MODEL,          metavar="MODEL")
@click.option("--cache-file",   default=CACHE_FILE,             metavar="CACHE_FILE")
@click.option("--chunk-size",   default=CHUNK_SIZE,             metavar="CHUNK_SIZE")
@click.option("--chunk-overlap",default=CHUNK_OVERLAP,          metavar="CHUNK_OVERLAP")
@click.option("--max-tokens",   default=MAX_TOKENS,             metavar="MAX_TOKENS")
@click.option("--sprint-goals", default="",                     metavar="SPRINT_GOALS")
@click.option("--pptx-file",    default=DEFAULT_PPTX_FILE_NAME, metavar="PPTX_FILE")
@click.option("--max-attempts", default=MAX_ATTEMPTS,           metavar="MAX_ATTEMPTS")
def demo(
        api_base: str,
        access_token: str,
        model: str,
        command: str,
        labels: str,
        iteration_id: int,
        group_id: int,
        cache_file: str,
        chunk_size: int,
        chunk_overlap: int,
        max_tokens: int,
        sprint_goals: str,
        pptx_file: str,
        max_attempts: int
):
    """
    Executes the specified command with the provided parameters to interact with GitLab issues, generate reports,
    and manage sprint activities.

    :param api_base: The base URL for the GitLab API.
    :param access_token: The access token for GitLab API authentication.
    :param model: The name of the Ollama model to use.
    :param command: The command to execute ('report', 'pptx', 'chat').
    :param labels: Labels used to filter issues in GitLab.
    :param iteration_id: Specific iteration ID for issue retrieval.
    :param group_id: GitLab group ID from which to retrieve issues.
    :param cache_file: Path to cache file for storing retrieved data.
    :param chunk_size: Size of text chunks for processing.
    :param chunk_overlap: Overlap between text chunks.
    :param max_tokens: Max number of tokens the model can handle.
    :param sprint_goals: Goals of the sprint to be included in the report.
    :param pptx_file: Path to save the generated PowerPoint file.
    :param max_attempts: Max attempts for generating outputs.
    """
    check_gitlab_credentials(access_token, api_base)
    check_ollama(model)
    embedding_model = HuggingFaceEmbeddings()
    embeddings = generate_embeddings(
        api_base,
        access_token,
        labels,
        group_id,
        iteration_id,
        cache_file,
        chunk_size,
        chunk_overlap,
        embedding_model,
        sprint_goals
    )
    execute_command(command, embeddings, model, max_tokens, max_attempts, sprint_goals, pptx_file)


if __name__ == "__main__":
    demo()
