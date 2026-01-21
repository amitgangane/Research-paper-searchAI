"""
Tools for the Research Assistant.

Contains utility functions for searching and fetching research papers.
"""

import logging

import arxiv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_arxiv_query(query: str) -> str:
    """
    Build an optimized arXiv search query.

    Handles both natural language queries and paper title searches.

    Args:
        query: User's search query

    Returns:
        Optimized query string for arXiv API
    """
    query = query.strip().lower()

    # Common conversational phrases to strip out
    noise_phrases = [
        "show me papers on", "show me papers about",
        "find papers on", "find papers about",
        "search for papers on", "search for papers about",
        "search for", "find me", "show me",
        "papers on", "papers about",
        "research on", "research about",
        "i want to find", "i want to see",
        "can you find", "can you show",
        "looking for", "look for",
    ]

    # Remove noise phrases
    clean_query = query
    for phrase in noise_phrases:
        clean_query = clean_query.replace(phrase, "")
    clean_query = clean_query.strip()

    # If nothing left after cleaning, use original
    if not clean_query:
        clean_query = query

    # Check if it looks like a specific paper title (has unusual structure)
    # Paper titles often have colons, specific patterns
    words = clean_query.split()
    is_likely_title = (
        ":" in clean_query or  # Titles often have colons
        (len(words) >= 5 and not any(w in clean_query for w in ["how", "what", "why", "which"]))
    )

    if is_likely_title:
        return f'ti:"{clean_query}" OR abs:"{clean_query}"'

    # Topic search - search in title and abstract
    return f'ti:{clean_query} OR abs:{clean_query}'


def search_arxiv(query: str, max_results: int = 10) -> list[dict]:
    """
    Search arXiv for papers matching the given query.

    Args:
        query: The search query string - can be a topic, keywords, or paper title.
        max_results: Maximum number of papers to return. Defaults to 10.

    Returns:
        A list of dictionaries containing paper data with keys:
            - title: Paper title
            - pdf_link: URL to the PDF
            - authors: Comma-separated author names
            - summary: Paper abstract
            - published: Publication date as ISO string
            - arxiv_id: The arXiv identifier

    Raises:
        ValueError: If query is empty or max_results is invalid.

    Example:
        >>> papers = search_arxiv("retrieval augmented generation", max_results=5)
        >>> print(papers[0]["title"])
        "Retrieval-Augmented Generation for..."
    """
    # Input validation
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    if max_results < 1:
        raise ValueError("max_results must be at least 1")

    if max_results > 100:
        logger.warning(f"max_results={max_results} is high, limiting to 100")
        max_results = 100

    papers: list[dict] = []

    try:
        # Build smart query for arXiv
        search_query = build_arxiv_query(query)
        logger.info(f"Searching arXiv for: '{search_query}' (max_results={max_results})")

        # Create search client with relevance sorting
        search = arxiv.Search(
            query=search_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )

        # Create client for fetching results
        client = arxiv.Client()

        # Fetch and process results
        for result in client.results(search):
            paper_data = {
                "title": result.title,
                "pdf_link": result.pdf_url,
                "authors": ", ".join(author.name for author in result.authors),
                "summary": result.summary,
                "published": result.published.isoformat() if result.published else None,
                "arxiv_id": result.entry_id.split("/")[-1]
            }
            papers.append(paper_data)

        logger.info(f"Found {len(papers)} papers for query: '{query}'")

    except arxiv.HTTPError as e:
        logger.error(f"arXiv API HTTP error: {e}")
        raise RuntimeError(f"Failed to fetch papers from arXiv: HTTP error - {e}")

    except arxiv.UnexpectedEmptyPageError as e:
        logger.error(f"arXiv returned empty page: {e}")
        raise RuntimeError(f"arXiv returned unexpected empty response: {e}")

    except Exception as e:
        logger.error(f"Unexpected error searching arXiv: {e}")
        raise RuntimeError(f"Failed to search arXiv: {e}")

    return papers


def format_papers_for_display(papers: list[dict]) -> str:
    """
    Format a list of papers for human-readable display.

    Args:
        papers: List of paper dictionaries from search_arxiv().

    Returns:
        Formatted string representation of the papers.
    """
    if not papers:
        return "No papers found."

    output_lines = []
    for i, paper in enumerate(papers, 1):
        output_lines.append(f"\n{'='*60}")
        output_lines.append(f"Paper {i}: {paper['title']}")
        output_lines.append(f"Authors: {paper['authors']}")
        output_lines.append(f"PDF: {paper['pdf_link']}")
        output_lines.append(f"Summary: {paper['summary'][:300]}...")

    return "\n".join(output_lines)


if __name__ == "__main__":
    # Quick test of the search function
    test_query = "retrieval augmented generation"
    print(f"Testing search for: {test_query}")

    try:
        results = search_arxiv(test_query, max_results=3)
        print(format_papers_for_display(results))
    except Exception as e:
        print(f"Error: {e}")
