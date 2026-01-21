"""
Streamlit Frontend for the Research Assistant.
"""

import streamlit as st
import requests

st.set_page_config(
    page_title="Research Assistant",
    page_icon="🔬",
    layout="wide"
)

# Minimal, clean CSS
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Clean typography */
    .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

    /* Search container */
    .search-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
    }

    .search-box h1 {
        color: white;
        font-size: 2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .search-box p {
        color: rgba(255,255,255,0.8);
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    /* Paper cards */
    .paper-card {
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: box-shadow 0.2s;
    }

    .paper-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    .paper-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 0.5rem;
        line-height: 1.4;
    }

    .paper-authors {
        font-size: 0.9rem;
        color: #718096;
        margin-bottom: 1rem;
    }

    .paper-summary {
        font-size: 0.95rem;
        color: #4a5568;
        line-height: 1.6;
        margin-bottom: 1rem;
    }

    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .score-high { background: #c6f6d5; color: #22543d; }
    .score-med { background: #fefcbf; color: #744210; }
    .score-low { background: #fed7d7; color: #742a2a; }

    /* Stats row */
    .stats-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat-box {
        background: #f7fafc;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        flex: 1;
    }

    .stat-number {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2d3748;
    }

    .stat-label {
        font-size: 0.85rem;
        color: #718096;
    }

    /* Button styling */
    .stButton > button {
        background: white;
        color: #667eea;
        border: none;
        font-weight: 600;
        padding: 0.75rem 2rem;
        border-radius: 8px;
    }

    .stButton > button:hover {
        background: #f7fafc;
    }

    /* Link button */
    .pdf-link {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: #667eea;
        text-decoration: none;
        font-weight: 500;
        font-size: 0.9rem;
    }

    .pdf-link:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000"


def get_papers(query: str) -> dict | None:
    """Fetch papers from API."""
    try:
        resp = requests.post(
            f"{API_URL}/api/research",
            json={"query": query},
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Start the backend server first.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def render_paper(paper: dict):
    """Render a single paper card."""
    score = paper.get("matching_score", 0)
    score_pct = int(score * 100) if score else 0

    if score_pct >= 75:
        score_class = "score-high"
    elif score_pct >= 50:
        score_class = "score-med"
    else:
        score_class = "score-low"

    st.markdown(f"""
    <div class="paper-card">
        <div class="paper-title">{paper.get('title', 'Untitled')}</div>
        <div class="paper-authors">{paper.get('authors', 'Unknown authors')}</div>
        <div class="paper-summary">{paper.get('summary', 'No summary available.')}</div>
        <span class="score-badge {score_class}">{score_pct}% match</span>
    </div>
    """, unsafe_allow_html=True)

    # PDF button outside the HTML for functionality
    pdf_link = paper.get("pdf_link", "")
    if pdf_link:
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            st.link_button("View PDF", pdf_link)


def main():
    # Header section
    st.markdown("""
    <div class="search-box">
        <h1>Research Assistant</h1>
        <p>Search academic papers with AI-powered relevance scoring</p>
    </div>
    """, unsafe_allow_html=True)

    # Search input
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(
            "query",
            placeholder="What would you like to research?",
            label_visibility="collapsed"
        )
    with col2:
        search = st.button("Search", use_container_width=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### Settings")
        max_results = st.select_slider(
            "Results",
            options=[5, 10, 15, 20],
            value=10
        )

        st.markdown("---")
        st.markdown("### How it works")
        st.markdown("""
        1. Enter a research topic
        2. AI agents search arXiv
        3. Papers are analyzed and scored
        4. Results ranked by relevance
        """)

        st.markdown("---")
        st.caption("Built with FastAPI + AutoGen")

    # Search results
    if search and query:
        with st.status("Searching papers...", expanded=True) as status:
            st.write("Querying arXiv database...")
            st.write("Analyzing relevance...")
            results = get_papers(query)
            status.update(label="Complete", state="complete")

        if results and results.get("papers"):
            papers = results["papers"]

            # Sort by relevance score (highest first)
            papers = sorted(papers, key=lambda p: p.get("matching_score", 0), reverse=True)

            # Stats
            avg_score = sum(p.get("matching_score", 0) for p in papers) / len(papers)

            st.markdown(f"""
            <div class="stats-container">
                <div class="stat-box">
                    <div class="stat-number">{len(papers)}</div>
                    <div class="stat-label">Papers found</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{int(avg_score * 100)}%</div>
                    <div class="stat-label">Avg. relevance</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"### Results for \"{query}\"")

            # Render papers
            for paper in papers:
                render_paper(paper)

        elif results:
            st.info("No papers found. Try different keywords.")

    elif search:
        st.warning("Enter a search query.")


if __name__ == "__main__":
    main()
