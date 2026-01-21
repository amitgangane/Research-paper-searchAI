"""
Pydantic schemas for the Research Assistant API.

Defines data models for papers and API responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Paper(BaseModel):
    """
    Represents a research paper from arXiv.

    Attributes:
        title: The title of the paper.
        pdf_link: URL to the PDF version of the paper.
        authors: Comma-separated list of author names.
        summary: Abstract or AI-generated summary of the paper.
        matching_score: Relevance score (0.0 to 1.0) based on the query.
    """
    title: str = Field(..., description="Title of the research paper")
    pdf_link: str = Field(..., description="URL to the PDF version")
    authors: str = Field(..., description="Comma-separated list of authors")
    summary: str = Field(..., description="Abstract or summary of the paper")
    matching_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance score from 0.0 to 1.0"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                "pdf_link": "https://arxiv.org/pdf/2005.11401.pdf",
                "authors": "Patrick Lewis, Ethan Perez, Aleksandra Piktus",
                "summary": "This paper introduces RAG, combining retrieval with generation...",
                "matching_score": 0.95
            }
        }


class ResearchResponse(BaseModel):
    """
    API response containing a list of research papers.

    Attributes:
        query: The original search query.
        total_results: Number of papers returned.
        papers: List of Paper objects.
    """
    query: str = Field(..., description="The original search query")
    total_results: int = Field(..., description="Number of papers returned")
    papers: list[Paper] = Field(default_factory=list, description="List of papers")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "RAG systems",
                "total_results": 10,
                "papers": []
            }
        }
