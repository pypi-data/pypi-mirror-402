import pytest
from unittest.mock import patch
from demo.utils import check_gitlab_credentials, check_ollama

def test_check_gitlab_credentials_valid():
    with patch("demo.utils.check_access", return_value=True), patch("demo.utils.print") as mock_print:
        check_gitlab_credentials("valid_token", "http://gitlab.com")
        mock_print.assert_called_with("[green]GitLab credentials are valid[/green]")

def test_check_gitlab_credentials_invalid():
    with patch("demo.utils.check_access", return_value=False), patch("demo.utils.print") as mock_print:
        with pytest.raises(Exception) as exc_info:
            check_gitlab_credentials("invalid_token", "http://gitlab.com")
        assert str(exc_info.value) == "Invalid GitLab credentials"
        mock_print.assert_called_with("[red]Invalid GitLab credentials[/red]")

def test_check_ollama_valid_model():
    with patch("ollama.list", return_value={'models': [{'name': 'test_model'}]}), patch("demo.utils.print") as mock_print:
        check_ollama(model="test_model")
        mock_print.assert_called_with("[green]Ollama model is valid[/green]")

def test_check_ollama_invalid_model():
    with patch("ollama.list", return_value={'models': [{'name': 'test_model'}]}), patch("demo.utils.print") as mock_print:
        with pytest.raises(Exception) as exc_info:
            check_ollama(model="invalid_model")
        assert str(exc_info.value) == "Ollama is not running"

def test_check_ollama_service_down():
    with patch("ollama.list", side_effect=Exception("Service Down")), patch("demo.utils.print") as mock_print:
        with pytest.raises(Exception) as exc_info:
            check_ollama()
        assert str(exc_info.value) == "Ollama is not running"
        mock_print.assert_called_with("[red]Ollama is not running. Error: Service Down[/red]")