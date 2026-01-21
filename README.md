# Research Assistant

A multi-agent system for searching and analyzing academic papers from arXiv. Built with FastAPI, Microsoft AutoGen, and Streamlit.

## How It Works

1. User enters a research query
2. **Researcher Agent** searches arXiv for relevant papers
3. **Analyst Agent** summarizes each paper and assigns relevance scores
4. Results are displayed in a clean web interface

## Project Structure

```
Research_paper_AI_search/
├── backend/
│   ├── main.py          # FastAPI server with caching
│   ├── agents.py        # AutoGen agent configuration
│   ├── tools.py         # arXiv search tool
│   └── schemas.py       # Pydantic data models
├── frontend/
│   └── app.py           # Streamlit UI
├── requirements.txt
├── .env                 # API keys (create from .env.example)
└── README.md
```

## Setup

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd Research_paper_AI_search

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

## Running the Application

You need **two terminals** - one for the backend, one for the frontend.

### Terminal 1: Start Backend

```bash
cd Research_paper_AI_search/backend
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Terminal 2: Start Frontend

```bash
cd Research_paper_AI_search/frontend
streamlit run app.py
```

The UI will open at `http://localhost:8501`

## Usage

1. Open `http://localhost:8501` in your browser
2. Enter a research topic (e.g., "transformer architecture", "retrieval augmented generation")
3. Click Search
4. View papers sorted by relevance score

### Search Tips

- **Topic search:** "machine learning", "neural networks"
- **Paper title:** "attention is all you need"
- **Natural language:** "show me papers on transformers"

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Detailed status with cache stats |
| POST | `/api/research` | Search papers (body: `{"query": "..."}`) |
| DELETE | `/api/cache` | Clear cached results |

## Features

- Multi-agent collaboration (Researcher + Analyst)
- In-memory caching with 1-hour TTL
- Relevance scoring (0-100%)
- PDF links for each paper
- Responsive web interface

## Tech Stack

- **Backend:** FastAPI, Python 3.11+
- **Agents:** Microsoft AutoGen 0.4+
- **Frontend:** Streamlit
- **Data Source:** arXiv API
- **LLM:** OpenAI GPT-4o-mini (configurable)
