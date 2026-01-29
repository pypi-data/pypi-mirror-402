import pytest
from unittest.mock import patch, MagicMock
from demo.embeddings import generate_embeddings
from langchain_huggingface import HuggingFaceEmbeddings


def test_generate_embeddings_integration():
    embedding_model = HuggingFaceEmbeddings()
    with patch("demo.embeddings.get_gitlab_issues") as mock_get_gitlab_issues, \
            patch("demo.utils.manage_cache_file") as mock_manage_cache, \
            patch("langchain_community.document_loaders.TextLoader") as mock_text_loader, \
            patch("langchain_text_splitters.CharacterTextSplitter") as mock_splitter:
        mock_issue = MagicMock(attributes={'title': 'Bug Fix', 'description': 'Fix a critical bug'})
        mock_get_gitlab_issues.return_value = [mock_issue]
        mock_text_loader.return_value.load.return_value = "Bug Fix Fix a critical bug"
        mock_splitter.return_value.split_documents.return_value = ["Bug Fix", "Fix a critical bug"]

        result = generate_embeddings(
            api_base="http://api.gitlab.com",
            access_token="valid_token",
            labels="bug",
            group_id=123,
            iteration_id=456,
            cache_file=".cache",
            chunk_size=100,
            chunk_overlap=20,
            embedding_model=embedding_model,
            sprint_goals="Complete all tasks"
        )

        mock_get_gitlab_issues.assert_called_once_with("valid_token", "http://api.gitlab.com", 123, "bug", 456)
        assert result is not None