"""
Trip Mate AI — AI Travel Planner
==========================================
Streamlit frontend ONLY. All intelligence lives in backend.py.

This file must never import LangGraph, PostgreSQL, agents, or tools directly.
The only backend contract used here is:

    result = run_travel_agent(user_input=..., thread_id=...)

    result = {
        "thread_id": str,
        "answer": str,
        "flight_results": str,
        "hotel_results": str,
        "itinerary": str,
        "llm_calls": int,
    }
"""

import io
import re
import time
import uuid
from datetime import datetime
from typing import Optional

import streamlit as st

from backend import run_travel_agent

# ReportLab is optional — PDF download degrades gracefully if unavailable.
try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        HRFlowable,
    )
    from reportlab.lib import colors as rl_colors

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Trip Mate AI — Plan Your Perfect Journey",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# CONSTANTS
# ==========================================================

HERO_IMAGE_URL = "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=1600&auto=format&fit=crop"

DESTINATIONS = [
    {
        "name": "Japan",
        "emoji": "🗾",
        "image": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?q=80&w=800&auto=format&fit=crop",
        "budget": "$1,800 – $3,000",
        "season": "Mar – May",
        "duration": "7 Days",
        "prompt": "Plan a complete 7 day trip to Japan from Delhi including flights and hotels",
    },
    {
        "name": "Paris",
        "emoji": "🗼",
        "image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?q=80&w=800&auto=format&fit=crop",
        "budget": "$1,500 – $2,500",
        "season": "Apr – Jun",
        "duration": "5 Days",
        "prompt": "Plan a complete 5 day trip to Paris from Delhi including flights and hotels",
    },
    {
        "name": "Dubai",
        "emoji": "🏙️",
        "image": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?q=80&w=800&auto=format&fit=crop",
        "budget": "$1,200 – $2,200",
        "season": "Nov – Mar",
        "duration": "4 Days",
        "prompt": "Plan a complete 4 day trip to Dubai from Delhi including flights and hotels",
    },
    {
        "name": "Goa",
        "emoji": "🏖️",
        "image": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?q=80&w=800&auto=format&fit=crop",
        "budget": "$400 – $900",
        "season": "Nov – Feb",
        "duration": "4 Days",
        "prompt": "Plan a complete 4 day trip to Goa from Delhi including flights and hotels",
    },
    {
        "name": "Bali",
        "emoji": "🌴",
        "image": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?q=80&w=800&auto=format&fit=crop",
        "budget": "$900 – $1,800",
        "season": "Apr – Oct",
        "duration": "6 Days",
        "prompt": "Plan a complete 6 day trip to Bali from Delhi including flights and hotels",
    },
    {
        "name": "Switzerland",
        "emoji": "🏔️",
        "image": "https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99?q=80&w=800&auto=format&fit=crop",
        "budget": "$2,500 – $4,000",
        "season": "Jun – Sep",
        "duration": "8 Days",
        "prompt": "Plan a complete 8 day trip to Switzerland from Delhi including flights and hotels",
    },
]

CAPABILITY_CARDS = [
    ("🛫", "Flights","Live flight search"),
    ("🏨", "Hotels", "AI hotel recommendations"),
    ("🗓️", "Itinerary", "Personalized travel plans"),
    ("🧠", "AI Planner", "Powered by LangGraph"),
 
]

PIPELINE_STEPS = [
    ("✈️", "Flight Agent", "Searching Flights"),
    ("🏨", "Hotel Agent", "Searching Hotels"),
    ("🗓️", "Itinerary Agent", "Creating Itinerary"),
    ("🧠", "Final Agent", "Generating Final Response"),
]


# ==========================================================
# CSS — PREMIUM DARK BLUE GLASSMORPHISM
# ==========================================================

def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --bg-primary: #0B1220;
            --bg-secondary: #111827;
            --bg-sidebar: #081018;
            --card-bg: rgba(17,24,39,0.88);
            --accent-primary: #2563EB;
            --accent-secondary: #38BDF8;
            --success: #22C55E;
            --warning: #F59E0B;
            --error: #EF4444;
            --text-primary: #F8FAFC;
            --text-secondary: #CBD5E1;
            --border-color: rgba(255,255,255,0.08);
            --radius: 18px;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {background: transparent;}
        .stDeployButton {display: none;}

        .stApp {
            background: radial-gradient(circle at 15% 0%, #101c33 0%, var(--bg-primary) 45%, #060a13 100%);
            color: var(--text-primary);
        }

        section[data-testid="stSidebar"] {
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        /* Fade-in animation */
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(14px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in { animation: fadeInUp 0.5s ease both; }

        /* Hero */
        .hero-banner {
            position: relative;
            border-radius: var(--radius);
            overflow: hidden;
            height: 320px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            text-align: center;
            margin-bottom: 1.75rem;
            border: 1px solid var(--border-color);
            box-shadow: 0 20px 60px rgba(0,0,0,0.45);
        }
        .hero-banner::before {
            content: "";
            position: absolute;
            inset: 0;
            background-image: linear-gradient(180deg, rgba(11,18,32,0.35) 0%, rgba(11,18,32,0.92) 100%), url('__HERO_IMG__');
            background-size: cover;
            background-position: center;
            filter: saturate(1.05);
        }
        .hero-banner h1 {
            position: relative;
            font-size: 3rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(90deg, #F8FAFC, var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }
        .hero-banner p {
            position: relative;
            color: var(--text-secondary);
            font-size: 1.15rem;
            margin-top: 0.6rem;
        }
        .hero-badge {
            position: relative;
            display: inline-block;
            margin-top: 1rem;
            padding: 0.35rem 1rem;
            border-radius: 999px;
            background: rgba(37,99,235,0.18);
            border: 1px solid rgba(56,189,248,0.35);
            color: var(--accent-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }

        /* Generic glass card */
        .glass-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 1.25rem 1.4rem;
            backdrop-filter: blur(14px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.28);
            transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
        }
        .glass-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 16px 40px rgba(37,99,235,0.22);
            border-color: rgba(56,189,248,0.35);
        }

        /* Capability chips */
        .capability-card {
            text-align: center;
            padding: 1rem 0.5rem;
        }
        .capability-card .icon { font-size: 1.6rem; }
        .capability-card .title { font-weight: 700; margin-top: 0.35rem; font-size: 0.95rem; }
        .capability-card .subtitle { color: var(--text-secondary); font-size: 0.78rem; margin-top: 0.1rem; }

        /* Destination cards */
        .destination-card {
            border-radius: var(--radius);
            overflow: hidden;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            margin-bottom: 0.6rem;
        }
        .destination-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 18px 45px rgba(37,99,235,0.28);
        }
        .destination-card .dest-image {
            height: 130px;
            background-size: cover;
            background-position: center;
            position: relative;
        }
        .destination-card .dest-image::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, rgba(11,18,32,0) 40%, rgba(11,18,32,0.9) 100%);
        }
        .destination-card .dest-name {
            position: absolute;
            bottom: 8px;
            left: 14px;
            font-weight: 800;
            font-size: 1.15rem;
            z-index: 2;
        }
        .destination-card .dest-body {
            padding: 0.85rem 1rem 0.3rem 1rem;
            font-size: 0.82rem;
            color: var(--text-secondary);
        }
        .destination-card .dest-body div { margin-bottom: 0.3rem; }

        /* Metric cards */
        .metric-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: var(--radius);
            padding: 1rem 1.1rem;
            text-align: center;
            box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        }
        .metric-card .metric-value {
            font-size: 1.6rem;
            font-weight: 800;
            background: linear-gradient(90deg, var(--accent-secondary), var(--accent-primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .metric-card .metric-label {
            color: var(--text-secondary);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-top: 0.15rem;
        }

        /* Pipeline */
        .pipeline-step {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            padding: 0.7rem 1rem;
            border-radius: 14px;
            border: 1px solid var(--border-color);
            background: rgba(17,24,39,0.6);
            margin-bottom: 0.5rem;
            animation: fadeInUp 0.4s ease both;
        }
        .pipeline-step .step-icon {
            font-size: 1.3rem;
            width: 38px;
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            background: rgba(37,99,235,0.18);
        }
        .pipeline-step .step-title { font-weight: 700; font-size: 0.95rem; }
        .pipeline-step .step-sub { color: var(--text-secondary); font-size: 0.78rem; }
        .pipeline-step .step-status {
            margin-left: auto;
            color: var(--success);
            font-weight: 700;
            font-size: 0.82rem;
        }

        /* Flight & Hotel cards */
        .info-card {
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            border-radius: 14px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.75rem;
        }
        .info-card .info-title {
            font-weight: 700;
            font-size: 1.02rem;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.5rem 1rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        .info-grid b { color: var(--text-primary); }
        .status-pill {
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        .status-active { background: rgba(34,197,94,0.18); color: var(--success); }
        .status-delayed { background: rgba(245,158,11,0.18); color: var(--warning); }
        .status-cancelled { background: rgba(239,68,68,0.18); color: var(--error); }
        .status-unknown { background: rgba(148,163,184,0.18); color: var(--text-secondary); }

        /* Chat bubbles */
        div[data-testid="stChatMessage"] {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 0.4rem 0.2rem;
            margin-bottom: 0.6rem;
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            padding: 0.55rem 1.1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            box-shadow: 0 8px 20px rgba(37,99,235,0.25);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(37,99,235,0.4);
        }

        .stDownloadButton > button {
            background: rgba(17,24,39,0.9);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            font-weight: 600;
        }
        .stDownloadButton > button:hover {
            border-color: var(--accent-secondary);
        }

        /* Error card */
        .error-card {
            border: 1px solid rgba(239,68,68,0.4);
            background: rgba(239,68,68,0.08);
            border-radius: 14px;
            padding: 1rem 1.2rem;
            color: #FCA5A5;
        }

        /* Section headers */
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin: 1.2rem 0 0.6rem 0;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        hr.soft-divider {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 1.1rem 0;
        }

        .footer-note {
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.82rem;
            padding: 1.5rem 0 0.5rem 0;
        }

        .badge-pill {
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            background: rgba(56,189,248,0.12);
            border: 1px solid rgba(56,189,248,0.3);
            color: var(--accent-secondary);
            font-size: 0.72rem;
            font-weight: 600;
            margin: 0.15rem 0.25rem 0.15rem 0;
        }
        </style>
        """.replace("__HERO_IMG__", HERO_IMAGE_URL),
        unsafe_allow_html=True,
    )


# ==========================================================
# SESSION STATE
# ==========================================================

def init_session_state() -> None:
    defaults = {
        "messages": [],
        "thread_id": f"user_{uuid.uuid4().hex}",
        "llm_calls": 0,
        "response_time": 0.0,
        "conversation_count": 0,
        "last_result": None,
        "pending_prompt": None,
        "backend_status": "unknown",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def start_new_chat() -> None:
    st.session_state.messages = []
    st.session_state.thread_id = f"user_{uuid.uuid4().hex}"
    st.session_state.llm_calls = 0
    st.session_state.response_time = 0.0
    st.session_state.conversation_count = 0
    st.session_state.last_result = None
    st.session_state.pending_prompt = None


def short_thread_id(thread_id: str) -> str:
    cleaned = thread_id.replace("user_", "")
    if len(cleaned) <= 10:
        return cleaned
    return f"{cleaned[:6]}…{cleaned[-4:]}"


# ==========================================================
# BACKEND HEALTH CHECK
# ==========================================================

def check_backend_status() -> str:
    """
    Best-effort detection of backend availability.
    We avoid calling run_travel_agent() itself (that would trigger a full
    agent pipeline run), so we simply confirm the import succeeded.
    """
    try:
        if callable(run_travel_agent):
            return "connected"
        return "unavailable"
    except Exception:
        return "unavailable"


# ==========================================================
# PARSERS — turn raw backend text into structured cards
# ==========================================================

def parse_flight_results(raw: str):
    """
    Parses the text produced by tools/flight_tool.py's format_flight().
    Returns (route_info, [flight_dicts]) or (None, None) if not parseable.
    """
    if not raw or not raw.strip():
        return None, []

    if raw.strip().lower().startswith(("flight api error", "flight api request failed",
                                        "flight api returned invalid json", "no live flight data")):
        return raw.strip(), []

    blocks = [b.strip() for b in raw.split("\n\n---\n\n")]
    if not blocks:
        return None, []

    route_info = None
    flight_blocks = blocks

    if not blocks[0].lower().startswith("airline:"):
        route_info = blocks[0].split("\n\n")[0].strip()
        # If the route line and first flight got merged in the same block
        remainder = blocks[0][len(route_info):].strip()
        flight_blocks = ([remainder] if remainder else []) + blocks[1:]

    flights = []
    field_pattern = re.compile(r"^-\s*([^:]+):\s*(.*)$")

    for block in flight_blocks:
        if not block.strip():
            continue
        flight = {
            "airline": "Unknown airline",
            "flight_number": "Unknown",
            "status": "Unknown",
            "dep_airport": "Unknown", "dep_iata": "Unknown",
            "dep_terminal": "N/A", "dep_gate": "N/A",
            "dep_scheduled": "Unknown", "dep_delay": "N/A",
            "arr_airport": "Unknown", "arr_iata": "Unknown",
            "arr_terminal": "N/A", "arr_gate": "N/A",
            "arr_scheduled": "Unknown", "arr_delay": "N/A",
        }
        section = None
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("airline:"):
                flight["airline"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("flight:"):
                flight["flight_number"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("status:"):
                flight["status"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("departure:"):
                section = "dep"
            elif line.lower().startswith("arrival:"):
                section = "arr"
            else:
                m = field_pattern.match(line)
                if m and section:
                    label, value = m.group(1).strip().lower(), m.group(2).strip()
                    key_map = {
                        "airport": f"{section}_airport",
                        "iata": f"{section}_iata",
                        "terminal": f"{section}_terminal",
                        "gate": f"{section}_gate",
                        "scheduled": f"{section}_scheduled",
                        "delay": f"{section}_delay",
                    }
                    if label in key_map:
                        flight[key_map[label]] = value
        flights.append(flight)

    return route_info, flights


def parse_hotel_results(raw: str):
    """
    Parses the text produced by tools/tavily_tool.py's tavily_search().
    Each entry looks like:
        1. **Title**
           https://url
           snippet...
    Returns a list of dicts: {index, title, url, snippet}
    """
    if not raw or not raw.strip():
        return []

    entries = []
    pattern = re.compile(
        r"(\d+)\.\s*\*\*(.+?)\*\*\s*\n\s*(\S+)\s*\n\s*(.*?)(?=\n\d+\.\s*\*\*|\Z)",
        re.DOTALL,
    )
    for match in pattern.finditer(raw):
        idx, title, url, snippet = match.groups()
        entries.append({
            "index": idx,
            "title": title.strip(),
            "url": url.strip(),
            "snippet": " ".join(snippet.split()).strip(),
        })
    return entries


def status_pill_class(status: str) -> str:
    status_lower = (status or "").lower()
    if "active" in status_lower or "landed" in status_lower or "scheduled" in status_lower:
        return "status-active"
    if "delay" in status_lower:
        return "status-delayed"
    if "cancel" in status_lower or "diverted" in status_lower:
        return "status-cancelled"
    return "status-unknown"


# ==========================================================
# UI FRAGMENTS
# ==========================================================

def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-banner fade-in">
            <div class="hero-badge">✈ AI-Powered Travel Planning</div>
            <h1>Trip Mate AI</h1>
            <p>Plan your perfect journey with AI — flights, hotels & itineraries in seconds</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_capability_cards() -> None:
    cols = st.columns(len(CAPABILITY_CARDS))
    for col, (icon, title, subtitle) in zip(cols, CAPABILITY_CARDS):
        with col:
            st.markdown(
                f"""
                <div class="glass-card capability-card fade-in">
                    <div class="icon">{icon}</div>
                    <div class="title">{title}</div>
                    <div class="subtitle">{subtitle}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_destination_cards() -> Optional[str]:
    st.markdown('<div class="section-title">🌍 Suggested Trips</div>', unsafe_allow_html=True)
    clicked_prompt = None
    cols = st.columns(3)
    for i, dest in enumerate(DESTINATIONS):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="destination-card fade-in">
                    <div class="dest-image" style="background-image:url('{dest['image']}')">
                        <div class="dest-name">{dest['emoji']} {dest['name']}</div>
                    </div>
                    <div class="dest-body">
                        <div>💰 <b>{dest['budget']}</b></div>
                        <div>🗓️ Best season: <b>{dest['season']}</b></div>
                        <div>⏱️ Duration: <b>{dest['duration']}</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Plan {dest['name']} trip", key=f"dest_{dest['name']}", use_container_width=True):
                clicked_prompt = dest["prompt"]
    return clicked_prompt


def render_metrics() -> None:
    metrics = [
        ("Agents Executed", "4" if st.session_state.conversation_count > 0 else "0"),
        ("LLM Calls", str(st.session_state.llm_calls)),
        ("Conversations", str(st.session_state.conversation_count)),
        ("Response Time", f"{st.session_state.response_time:.1f}s" if st.session_state.response_time else "—"),
        ("Thread", short_thread_id(st.session_state.thread_id)),
    ]
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card fade-in">
                    <div class="metric-value">{value}</div>
                    <div class="metric-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_pipeline() -> None:
    st.markdown('<div class="section-title">🧬 Live Agent Pipeline</div>', unsafe_allow_html=True)
    for icon, title, sub in PIPELINE_STEPS:
        st.markdown(
            f"""
            <div class="pipeline-step">
                <div class="step-icon">{icon}</div>
                <div>
                    <div class="step-title">{title}</div>
                    <div class="step-sub">{sub}</div>
                </div>
                <div class="step-status">✓ Complete</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_flight_section(raw: str) -> None:
    if not raw or not raw.strip():
        return
    route_info, flights = parse_flight_results(raw)

    if not flights:
        with st.expander("✈️ Flight Details", expanded=True):
            st.markdown(f'<div class="glass-card">{route_info or raw}</div>', unsafe_allow_html=True)
        return

    with st.expander(f"✈️ Flight Details ({len(flights)} found)", expanded=True):
        if route_info:
            st.caption(route_info)
        for f in flights:
            pill_class = status_pill_class(f["status"])
            st.markdown(
                f"""
                <div class="info-card fade-in">
                    <div class="info-title">
                        🛫 {f['airline']} · {f['flight_number']}
                        <span class="status-pill {pill_class}">{f['status']}</span>
                    </div>
                    <div class="info-grid">
                        <div>🛫 Departure<br><b>{f['dep_airport']} ({f['dep_iata']})</b></div>
                        <div>🛬 Arrival<br><b>{f['arr_airport']} ({f['arr_iata']})</b></div>
                        <div>🕐 Dep. Time<br><b>{f['dep_scheduled']}</b></div>
                        <div>🕑 Arr. Time<br><b>{f['arr_scheduled']}</b></div>
                        <div>🚪 Terminal / Gate<br><b>{f['dep_terminal']} / {f['dep_gate']}</b></div>
                        <div>🚪 Terminal / Gate<br><b>{f['arr_terminal']} / {f['arr_gate']}</b></div>
                        <div>⏱️ Dep. Delay<br><b>{f['dep_delay']}</b></div>
                        <div>⏱️ Arr. Delay<br><b>{f['arr_delay']}</b></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.caption("ℹ️ Live flight status data — ticket prices are not provided by this API.")


def render_hotel_section(raw: str) -> None:
    if not raw or not raw.strip():
        return
    hotels = parse_hotel_results(raw)

    with st.expander(f"🏨 Hotel Suggestions ({len(hotels) if hotels else 0} found)", expanded=True):
        if not hotels:
            st.markdown(f'<div class="glass-card">{raw}</div>', unsafe_allow_html=True)
            return
        cols = st.columns(2)
        for i, hotel in enumerate(hotels):
            with cols[i % 2]:
                st.markdown(
                    f"""
                    <div class="info-card fade-in">
                        <div class="info-title">🏨 {hotel['title']}</div>
                        <div style="color:var(--text-secondary); font-size:0.85rem; margin-bottom:0.5rem;">
                            {hotel['snippet']}
                        </div>
                        <a href="{hotel['url']}" target="_blank" style="color:var(--accent-secondary); font-size:0.82rem; text-decoration:none;">
                            🔗 View source
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_itinerary_section(raw: str) -> None:
    if not raw or not raw.strip():
        return
    with st.expander("🗓️ Generated Itinerary", expanded=True):
        st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(raw)
        st.markdown("</div>", unsafe_allow_html=True)


def render_future_ready_placeholders(result: dict) -> None:
    """Weather / Maps — only render if backend actually returns this data."""
    weather = result.get("weather_results") if isinstance(result, dict) else None
    maps = result.get("map_results") if isinstance(result, dict) else None

    if weather:
        with st.expander("🌦️ Weather", expanded=False):
            st.markdown(f'<div class="glass-card">{weather}</div>', unsafe_allow_html=True)

    if maps:
        with st.expander("🗺️ Maps", expanded=False):
            st.markdown(f'<div class="glass-card">{maps}</div>', unsafe_allow_html=True)


# ==========================================================
# DOWNLOAD HELPERS
# ==========================================================

def build_txt_export(answer: str) -> bytes:
    return answer.encode("utf-8")

def build_markdown_export(answer: str) -> bytes: 
    header = f"# Trip Mate AI — Travel Plan\n\n_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n---\n\n" 
    return (header + answer).encode("utf-8")

def build_pdf_export(answer: str) -> Optional[bytes]:
    if not REPORTLAB_AVAILABLE:
        return None
    
    # Convert currency symbols for better PDF compatibility
    answer = (
        answer.replace("₹", "INR ")
              .replace("$", "USD ")
              .replace("€", "EUR ")
              .replace("£", "GBP ")
              .replace("¥", "JPY ")
    )

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=22,
        alignment=1,
        spaceAfter=6,
    )

    heading = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=5,
    )

    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=11,
        leading=18,
        spaceAfter=6,
    )

    story = []

    story.append(Paragraph("<b>✈ Trip Mate AI</b>", title))
    story.append(
        Paragraph(
            "<i>Personalized Travel Itinerary</i>",
            styles["Italic"],
        )
    )

    story.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%d %b %Y | %I:%M %p')}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 12))

    headings = {
        "Trip Summary",
        "Flight Information",
        "Hotel Suggestions",
        "Day-by-Day Itinerary",
        "Estimated Budget",
        "Final Recommendations",
    }

    for line in answer.replace("**", "").split("\n"):

        line = line.strip()

        if not line:
            story.append(Spacer(1, 5))
            continue

        if line in headings:
            story.append(Spacer(1, 8))
            story.append(Paragraph(f"<b>{line.upper()}</b>", heading))
        else:
            story.append(Paragraph(line, body))

    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf

# ==========================================================
# SIDEBAR
# ==========================================================

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
                <div style="font-size:1.6rem; font-weight:800;">✈ Trip Mate AI</div>
                <div style="color:var(--text-secondary); font-size:0.85rem;">AI Travel Planner</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

        status = st.session_state.backend_status
        status_color = "#22C55E" if status == "connected" else "#EF4444"
        status_label = "Connected" if status == "connected" else "Unavailable"
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.9rem;">
                <span style="width:9px; height:9px; border-radius:50%; background:{status_color}; display:inline-block;"></span>
                <span style="font-weight:600; font-size:0.9rem;">Backend Status</span>
            </div>
            <div style="color:{status_color}; font-weight:700; font-size:0.85rem; margin-top:-0.6rem; margin-bottom:0.9rem;">
                {status_label}
            </div>
            """,
            unsafe_allow_html=True,
        )

        sidebar_info = [
            ("🌍 Default Location", "Delhi"),
            ("🧠 Model", "Groq Llama 3.3 70B"),
            ("💾 Database", "PostgreSQL"),
            ("🧩 Memory", "LangGraph Checkpointer"),
        ]
        for label, value in sidebar_info:
            st.markdown(
                f"""
                <div style="margin-bottom:0.7rem;">
                    <div style="color:var(--text-secondary); font-size:0.78rem;">{label}</div>
                    <div style="font-weight:600; font-size:0.9rem;">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

        session_info = [
            ("Current Thread", short_thread_id(st.session_state.thread_id)),
            ("Conversation Count", str(st.session_state.conversation_count)),
            ("LLM Calls", str(st.session_state.llm_calls)),
            ("Response Time", f"{st.session_state.response_time:.2f}s" if st.session_state.response_time else "—"),
        ]
        for label, value in session_info:
            st.markdown(
                f"""
                <div style="margin-bottom:0.7rem;">
                    <div style="color:var(--text-secondary); font-size:0.78rem;">{label}</div>
                    <div style="font-weight:600; font-size:0.9rem;">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

        if st.button("➕ New Chat", use_container_width=True):
            start_new_chat()
            st.rerun()

        st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

        st.markdown(
            """
            <div style="color:var(--text-secondary); font-size:0.78rem; margin-bottom:0.5rem;">Powered By</div>
            <div>
                <span class="badge-pill">LangGraph</span>
                <span class="badge-pill">Groq</span>
                <span class="badge-pill">PostgreSQL</span>
                <span class="badge-pill">AviationStack</span>
                <span class="badge-pill">Tavily</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================================
# CHAT EXECUTION
# ==========================================================

def run_agent_turn(user_prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    with st.chat_message("assistant", avatar="✈️"):
        pipeline_placeholder = st.empty()
        with pipeline_placeholder.container():
            with st.spinner("✈ Planning your perfect journey..."):
                start_time = time.time()
                try:
                    result = run_travel_agent(
                        user_input=user_prompt,
                        thread_id=st.session_state.thread_id,
                    )
                    error = None
                except Exception as exc:  # noqa: BLE001
                    result = None
                    error = str(exc)
                elapsed = time.time() - start_time

        pipeline_placeholder.empty()

        if error or not result:
            st.markdown(
                f"""
                <div class="error-card fade-in">
                    <b>⚠️ Something went wrong while planning your trip.</b><br/>
                    {error or "The backend returned no result."}
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": "⚠️ I couldn't complete this request. Please try again.",
                "result": None,
            })
            return

        st.session_state.response_time = elapsed
        st.session_state.llm_calls = result.get("llm_calls", st.session_state.llm_calls)
        st.session_state.conversation_count += 1
        st.session_state.thread_id = result.get("thread_id", st.session_state.thread_id)
        st.session_state.last_result = result

        render_pipeline()
        st.markdown(f'<div class="glass-card fade-in">', unsafe_allow_html=True)
        st.markdown(result.get("answer", ""))
        st.markdown("</div>", unsafe_allow_html=True)

        render_flight_section(result.get("flight_results", ""))
        render_hotel_section(result.get("hotel_results", ""))
        render_itinerary_section(result.get("itinerary", ""))
        render_future_ready_placeholders(result)

        render_download_and_copy(result)

        st.session_state.messages.append({
            "role": "assistant",
            "content": result.get("answer", ""),
            "result": result,
        })


def render_download_and_copy(result: dict) -> None:
    answer = result.get("answer", "") or ""
    if not answer.strip():
        return

    st.markdown(
        '<div class="section-title">📥 Export Your Plan</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(3)

    # TXT Download
    with cols[0]:
        st.download_button(
            "⬇️ TXT",
            data=build_txt_export(answer),
            file_name=f"tripmate_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
            key=f"txt_{st.session_state.thread_id}",
        )

    # PDF Download
    with cols[1]:
        pdf_bytes = build_pdf_export(answer)
        if pdf_bytes:
            st.download_button(
                "⬇️ PDF",
                data=pdf_bytes,
                file_name=f"tripmate_plan_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"pdf_{st.session_state.thread_id}",
            )
        else:
            st.button(
                "⬇️ PDF (Unavailable)",
                disabled=True,
                use_container_width=True,
                key="pdf_unavailable",
            )

    # Copy
    with cols[2]:
        with st.popover("📋 Copy Plan", use_container_width=True):
            st.code(answer, language=None)
            st.caption("Select the text above and copy it.")


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:
    init_session_state()
    inject_css()
    st.session_state.backend_status = check_backend_status()

    render_sidebar()

    is_first_visit = len(st.session_state.messages) == 0

    if is_first_visit:
        render_hero()
        render_capability_cards()
        clicked_prompt = render_destination_cards()
        if clicked_prompt:
            st.session_state.pending_prompt = clicked_prompt
            st.rerun()
    else:
        render_metrics()
        st.markdown('<hr class="soft-divider">', unsafe_allow_html=True)

    # Replay conversation history
    for msg in st.session_state.messages:
        avatar = "👤" if msg["role"] == "user" else "✈️"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            result = msg.get("result")
            if result and msg["role"] == "assistant":
                render_flight_section(result.get("flight_results", ""))
                render_hotel_section(result.get("hotel_results", ""))
                render_itinerary_section(result.get("itinerary", ""))
                render_future_ready_placeholders(result)
                render_download_and_copy(result)

    # Chat input
    user_prompt = st.chat_input("Ask Trip Mate AI to plan your next trip...")

    if st.session_state.pending_prompt:
        prompt_to_run = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        run_agent_turn(prompt_to_run)
    elif user_prompt:
        run_agent_turn(user_prompt)

    st.markdown(
        """
        <div class="footer-note">
            Powered by <b>LangGraph</b> · <b>Groq</b> · <b>PostgreSQL</b> · <b>AviationStack</b> · <b>Tavily</b><br/>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()