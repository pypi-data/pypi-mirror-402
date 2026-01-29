import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from demo.main import demo


@pytest.fixture
def runner():
    return CliRunner()


def test_valid_command_execution(runner):
    with patch("demo.main.check_gitlab_credentials") as mock_check_gitlab_credentials, \
         patch("demo.main.check_ollama") as mock_check_ollama, \
         patch("demo.main.generate_embeddings") as mock_generate_embeddings, \
         patch("demo.main.execute_command") as mock_execute_command, \
         patch("demo.main.HuggingFaceEmbeddings") as mock_hugging_face_embeddings:

        mock_hugging_face_embeddings.return_value = MagicMock()
        mock_generate_embeddings.return_value = "mock_embeddings"

        result = runner.invoke(demo, [
            "--api-base", "http://api.gitlab.com",
            "--access-token", "valid_token",
            "--command", "report",
            "--model", "test_model",
            "--group-id", "123",
            "--iteration-id", "456",
            "--labels", "bug",
            "--sprint-goals", "Complete all tasks"
        ])

        assert result.exit_code == 0
        mock_check_gitlab_credentials.assert_called_once_with("valid_token", "http://api.gitlab.com")
        mock_check_ollama.assert_called_once_with("test_model")
        mock_generate_embeddings.assert_called_once()
        mock_execute_command.assert_called_once()


def test_error_handling_invalid_credentials(runner):
    with patch("demo.main.check_gitlab_credentials", side_effect=Exception("Invalid credentials")), \
         patch("demo.main.print") as mock_print:

        result = runner.invoke(demo, [
            "--api-base", "http://api.gitlab.com",
            "--access-token", "invalid_token"
        ])

        assert result.exit_code != 0