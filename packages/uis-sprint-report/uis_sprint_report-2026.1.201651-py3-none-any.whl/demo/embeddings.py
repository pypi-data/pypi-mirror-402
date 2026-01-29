"""
This module handles the retrieval of issues from GitLab and generates embeddings from the issue
descriptions for sprint reporting. It uses the langchain library to create vector embeddings that
can be used to retrieve similar texts or perform further analysis.
"""
from rich import print
from .utils import manage_cache_file
from get_gitlab_issues import get_gitlab_issues, get_gitlab_issue

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS


def generate_embeddings(
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
):
    """
    Retrieves issues from GitLab and generates text embeddings.

    This function fetches issues based on provided filters, extracts text, and uses the specified
    embedding model to generate vector embeddings that can be used for text retrieval.

    Parameters:
        api_base (str): The base URL for the GitLab API.
        access_token (str): Token for API authentication.
        labels (str): Labels to filter the issues.
        group_id (int): GitLab group ID to fetch issues from.
        iteration_id (int): Specific iteration ID for issue retrieval.
        cache_file (str): Path to the cache file for storing and retrieving issue data.
        chunk_size (int): Size of text chunks for processing.
        chunk_overlap (int): Overlap between consecutive text chunks.
        embedding_model (any): Model used to generate embeddings.
        sprint_goals (str): Description of sprint goals to include in the cache.

    Returns:
        FAISS.Retriever: A retriever object that can be used to fetch similar text based on the
        embeddings generated.
    """
    print("[green]Recieveing issues from GitLab...[/green]")
    issues = get_gitlab_issues(access_token, api_base, group_id, labels, iteration_id)
    board = []
    for issue in issues:
        issue = issue.attributes
        board.append(issue)

    print("[green]✅ Issues received[/green]")
    manage_cache_file(create=True, content=sprint_goals+"\n "+str(board))

    print("[green]Generate embeddings...[/green]")
    loader = TextLoader(cache_file)
    documents = loader.load()
    splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = splitter.split_documents(documents)

    embedding = embedding_model
    vector_store = FAISS.from_documents(texts, embedding)
    retriever = vector_store.as_retriever()
    manage_cache_file(content="")
    print("[green]✅ Embeddings generated[/green]")
    return retriever