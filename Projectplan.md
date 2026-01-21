The Architecture Plan:

Architecture: Client-Server (REST API).

Backend: FastAPI (Python) + AutoGen (Agent Orchestration).

Frontend: Streamlit (for a clean, professional data-dashboard UI).

Logic:

    Tool: search_arxiv (Python function).

    Agent A (Researcher): Calls the tool to fetch raw data.

    Agent B (Analyst): Summarizes, scores relevance, and enforces JSON output.


Phase 1: Context & Core Utilities (The Foundation)

Goal: Set up the project structure, Pydantic data models, and the arXiv tool.

Copy/Paste this into Claude:

I am building a professional-grade Multi-Agent Research Assistant. Tech Stack: Python 3.11, FastAPI, Microsoft AutoGen, arXiv library. Goal: A user inputs a query (e.g., "RAG systems"), and the system returns a structured list of the top 10 papers with summaries and relevance scores.

Task - Phase 1: Please write the code for schemas.py and tools.py.

schemas.py: Define Pydantic models for the output. I need a Paper model (title, pdf_link, authors, summary, matching_score) and a ResearchResponse model (list of Papers).

tools.py: Write a robust function search_arxiv(query: str, max_results: int = 10) using the arxiv python library.

It must return a list of dictionaries containing the raw paper data.

Include error handling (try/except) for API failures.

Include type hinting and docstrings.



Phase 2: The Agent Logic (AutoGen Configuration)

Goal: Configure the agents to communicate and use the tool.


Great. Now let's move to Phase 2: Agent Configuration. Please create a file named agents.py.

Requirements:

Initialize the LLM config (assume config_list is loaded from environment variables).

Register the search_arxiv function (from Phase 1) as a tool.

Define two agents:

Researcher (AssistantAgent): Its system message should instruct it to use the search_arxiv tool to find papers relevant to the user's request.

Analyst (AssistantAgent): Its system message should instruct it to take the raw data from the Researcher, summarize each paper (2-3 sentences), assign a 'matching_score' (0-100) based on relevance, and strictly output valid JSON matching the ResearchResponse schema from Phase 1.

Create a UserProxyAgent configured for function execution (so it can execute the tool calls made by the Researcher).

Create a function run_research_workflow(query: str) that initiates the chat between the user_proxy and the agents and returns the final JSON string.



Phase 3: The API Layer (FastAPI)

Goal: Wrap the logic in a professional web server.


Excellent. Now Phase 3: The API. Create a file named main.py using FastAPI.

Requirements:

Setup a standard FastAPI app with CORS middleware (allow all origins for now).

Create a POST endpoint /api/research.

It should accept a JSON body with a query string.

Inside the endpoint, call the run_research_workflow function from Phase 2.

Critical: The agents might output text wrapping the JSON. Ensure the endpoint parses the final response to extract only the JSON list before returning it to the client. If parsing fails, return a 500 error with details.

Use python-dotenv to load API keys at startup.




Phase 4: The Frontend (Streamlit)

Goal: A professional UI to visualize the results.


Finally, Phase 4: The Frontend. Create a frontend/app.py using Streamlit.

Requirements:

A clean, modern UI layout. Title: "AutoGen Research Assistant".

A text input box for the user query and a "Search" button.

When the button is clicked:

Show a loading spinner.

Send a POST request to http://localhost:8000/api/research.

Display Logic:

If the request is successful, iterate through the returned list of papers.

Use st.expander for each paper. The expander label should be "Title (Score: X/100)".

Inside the expander, show the Authors, the Summary, and a clear button/link to "Open PDF".

Add a Sidebar with "Configuration" (like Max Papers selector) that passes parameters to the backend if applicable.




I want to improve the performance of my FastAPI backend by adding a Caching Layer.

Current Context: I have a main.py with a POST endpoint /api/research that calls a slow function run_research_workflow(query).

Your Task: Please modify main.py to implement Async In-Memory Caching.

Requirements:

Create a simple caching mechanism (using a Python dictionary or async-lru) to store results.

Key: The user's query string (normalized to lowercase) should be the cache key.

Value: The final JSON list returned by the agents.

Logic:

When a request comes in, check if the query exists in the cache.

If HIT: Return the stored JSON immediately and print "🚀 CACHE HIT" to the console.

If MISS: Run the slow agent workflow, store the result in the cache, and print "🐢 CACHE MISS" to the console.

TTL (Optional): If possible, make the cache expire after 1 hour so data doesn't get too stale.

Please provide the full updated code for main.py.