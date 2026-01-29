"""
Utility functions to support the operation of the UIS Sprint Report tool. Includes functions to verify
GitLab credentials, check the availability of the Ollama model, and manage local cache files.

These functions enhance the robustness of the tool by ensuring all configurations and dependencies
are correctly set up before performing main operations.
"""
import os
import ollama
from rich import print
from get_gitlab_issues import check_access
from .config import CACHE_FILE


def check_gitlab_credentials(token, url):
    """
    Validates GitLab API credentials by attempting an access check.

    Parameters:
        token (str): The GitLab access token.
        url (str): The GitLab API URL.

    Raises:
        Exception: If the credentials are not valid.
    """
    if not check_access(token, url):
        print(f"[red]Invalid GitLab credentials[/red]")
        raise Exception("Invalid GitLab credentials")
    print("[green]GitLab credentials are valid[/green]")


def check_ollama(model=None):
    """
    Verifies if a specified Ollama model is available and running.

    Parameters:
        model (str, optional): The name of the model to check. Defaults to None.

    Raises:
        Exception: If the Ollama model is not valid or the Ollama service is not running.
    """
    try:
        models = ollama.list()['models']
        if models and not any(m['name'] == model for m in models):
            print(f"[red]Invalid Ollama model[/red]")
            raise Exception("Invalid Ollama model")
    except Exception as e:
        print(f"[red]Ollama is not running. Error: {e}[/red]")
        raise Exception("Ollama is not running")
    print("[green]Ollama model is valid[/green]")


def manage_cache_file(create=False, content=None):
    """
    Manages a local cache file for storing or clearing temporary data.

    Parameters:
        create (bool): If True, creates a new cache file with the provided content. If False,
                       deletes the existing cache file.
        content (str, optional): Data to write to the file when creating. Defaults to None.
    """
    if create:
        with open(CACHE_FILE, 'w') as f:
            f.write(content)
    else:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)