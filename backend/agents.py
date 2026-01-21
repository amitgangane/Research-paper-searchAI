"""
AutoGen Agent Configuration for the Research Assistant.

Defines the multi-agent workflow for searching and analyzing research papers.
Uses AutoGen 0.4+ async API.
"""

import asyncio
import json
import logging
import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

from tools import search_arxiv
from schemas import ResearchResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_model_client() -> OpenAIChatCompletionClient:
    """
    Create OpenAI model client from environment variables.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    return OpenAIChatCompletionClient(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
    )


# Wrap search_arxiv as a FunctionTool
search_tool = FunctionTool(
    search_arxiv,
    description="Search arXiv for academic papers. Returns a list of paper dictionaries with title, pdf_link, authors, summary, published date, and arxiv_id.",
)


# System prompts for agents
RESEARCHER_SYSTEM_MESSAGE = """You are a Research Assistant specialized in finding academic papers.

Your role:
1. When given a research query, use the search_arxiv tool to find relevant papers.
2. Call the tool with the user's query to retrieve papers.
3. After receiving results, present them and say "RESEARCH_COMPLETE" to signal you're done.

Always use the search_arxiv tool - do not make up paper information."""

ANALYST_SYSTEM_MESSAGE = """You are a Research Analyst specialized in evaluating academic papers.

Your role:
1. Wait for the Researcher to complete their search (indicated by "RESEARCH_COMPLETE").
2. For each paper found, create a concise summary (2-3 sentences) based on the abstract.
3. Assign a matching_score (0.0 to 1.0) based on relevance to the original query:
   - 0.9-1.0: Directly addresses the query topic
   - 0.7-0.8: Highly relevant, closely related
   - 0.5-0.6: Moderately relevant
   - 0.3-0.4: Tangentially related
   - 0.0-0.2: Minimally relevant

4. Output ONLY valid JSON matching this exact schema:
{
    "query": "<original query>",
    "total_results": <number>,
    "papers": [
        {
            "title": "<paper title>",
            "pdf_link": "<pdf url>",
            "authors": "<comma-separated authors>",
            "summary": "<your 2-3 sentence summary>",
            "matching_score": <0.0-1.0>
        }
    ]
}

5. After outputting the JSON, say "TERMINATE" to end the conversation.

IMPORTANT: Your final response must contain valid JSON."""


async def run_research_workflow(query: str) -> str:
    """
    Execute the full research workflow for a given query.

    Args:
        query: The research topic to search for (e.g., "RAG systems")

    Returns:
        JSON string matching the ResearchResponse schema
    """
    logger.info(f"Starting research workflow for query: '{query}'")

    model_client = get_model_client()

    # Create the Researcher agent with the search tool
    researcher = AssistantAgent(
        name="Researcher",
        system_message=RESEARCHER_SYSTEM_MESSAGE,
        model_client=model_client,
        tools=[search_tool],
    )

    # Create the Analyst agent
    analyst = AssistantAgent(
        name="Analyst",
        system_message=ANALYST_SYSTEM_MESSAGE,
        model_client=model_client,
    )

    # Termination condition - stop when TERMINATE is mentioned
    termination = TextMentionTermination("TERMINATE")

    # Create a team with round-robin communication
    team = RoundRobinGroupChat(
        participants=[researcher, analyst],
        termination_condition=termination,
        max_turns=10,
    )

    # Run the team with the user's query
    task = f"Please search for academic papers about: {query}"

    result = await team.run(task=task)

    # Extract the final response containing JSON
    final_output = ""
    for message in reversed(result.messages):
        content = message.content if hasattr(message, 'content') else str(message)
        if isinstance(content, str) and "{" in content and "papers" in content:
            final_output = content
            break

    # Clean up and validate the output
    try:
        # Extract JSON from the response
        clean_output = final_output.strip()

        # Remove TERMINATE if present
        clean_output = clean_output.replace("TERMINATE", "").strip()

        # Find JSON in the response
        start_idx = clean_output.find("{")
        end_idx = clean_output.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            clean_output = clean_output[start_idx:end_idx]

        # Validate against our schema
        parsed = json.loads(clean_output)
        response = ResearchResponse(**parsed)
        return response.model_dump_json(indent=2)
    except Exception as e:
        logger.warning(f"Could not validate output against schema: {e}")
        return final_output


def run_research_sync(query: str) -> str:
    """
    Synchronous wrapper for run_research_workflow.

    Args:
        query: The research topic to search for

    Returns:
        JSON string matching the ResearchResponse schema
    """
    return asyncio.run(run_research_workflow(query))


if __name__ == "__main__":
    # Test the workflow
    test_query = "retrieval augmented generation"
    print(f"Testing research workflow for: {test_query}")
    print("=" * 60)

    try:
        result = run_research_sync(test_query)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
