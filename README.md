# ✈️ Trip Mate AI

**Trip Mate AI** is an AI-powered travel planning assistant that helps users plan personalized trips by combining **live flight search**, **hotel recommendations**, and **AI-generated itineraries**. The application leverages a **LangGraph multi-agent architecture**, **Groq LLMs**, and **persistent conversation memory** with PostgreSQL to provide an interactive travel planning experience.

🌐 **Live Demo:** https://tripmate-ai-wqhh.onrender.com/
> **Note:** Since the application is hosted on Render's free tier, the first request may take some time while the server wakes up.

---

## 🚀 Features

- 🤖 AI-powered personalized travel planning
- ✈️ Live flight search using AviationStack API
- 🏨 Hotel recommendations using Tavily Search
- 🗺️ Day-by-day itinerary generation
- 🧠 Persistent conversation memory with LangGraph + PostgreSQL
- 💬 Multi-turn conversations with thread-based memory
- 📄 Export travel plans as PDF and TXT
- 📋 Copy itinerary with one click
- 🌙 Modern responsive Streamlit interface
- 📊 LangSmith tracing and monitoring
- 🐳 Docker support for containerized deployment

---

## 🏗️ Architecture

```text
                 User
                   │
                   ▼
          Streamlit Frontend
                   │
                   ▼
         LangGraph Workflow (Orchestrates the workflow)
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
 Flight Search  Hotel Search  AI Planner
      │            │            │
      ▼            ▼            ▼
 AviationStack   Tavily API   Groq LLM
           └────────┬────────┘
                    ▼
      PostgreSQL Memory (Render)
                    │
                    ▼
      Personalized Travel Plan

```


---

## 🛠️ Tech Stack

| Category | Technology |
|-----------|------------|
| Language | Python |
| Frontend | Streamlit |
| AI Framework | LangGraph |
| LLM | Groq (Llama 3.3 70B Versatile) |
| Memory | PostgreSQL |
| Database Hosting | Render PostgreSQL |
| Search | Tavily API |
| Flight API | AviationStack API |
| Observability | LangSmith |
| Containerization | Docker |
| Package Manager | uv |
| Deployment | Render |

---

## 📂 Project Structure

```text
Tripmate-AI/
│
├── app.py                 # Streamlit frontend
├── backend.py             # LangGraph workflow
├── tools/
│   ├── flight_tool.py
│   └── tavily_tool.py
│
├── Dockerfile
├── .dockerignore
├── pyproject.toml
├── uv.lock
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### Clone the repository

```bash
git clone https://github.com/Swainakash0799/Tripmate-AI.git

cd Tripmate-AI
```

### Install dependencies

Using **uv**

```bash
uv sync
```

---

## 🔑 Environment Variables

Create a `.env` file.

```env
# Groq
GROQ_API_KEY=your_groq_api_key

# PostgreSQL (Render)
DATABASE_URL=your_render_postgresql_database_url

# Flight API
AVIATIONSTACK_API_KEY=your_aviationstack_api_key

# Hotel Search
TAVILY_API_KEY=your_tavily_api_key
```

---

## ▶️ Run Locally

```bash
streamlit run app.py
```

---

## 🐳 Docker

Build the Docker image

```bash
docker build -t tripmate-ai .
```

Run the container

```bash
docker run -p 8501:8501 --env-file .env tripmate-ai
```

---

## 📊 Observability

The application is integrated with **LangSmith** to monitor and debug the AI workflow.

- Trace LangGraph execution
- Monitor LLM calls
- Inspect intermediate agent outputs
- Measure response latency
- Debug multi-agent workflows

---

## ☁️ Deployment

The application is deployed on **Render**.

- **Frontend:** Render Web Service
- **Database:** Render Managed PostgreSQL
- **Persistent Memory:** LangGraph Checkpointer + PostgreSQL

---

## 📈 Future Improvements

- 🌦️ Weather forecast integration
- 🚖 Local transportation guidance
- 🗺️ Interactive maps
- 🍽️ Restaurant recommendations
- 🔗 Flight & hotel booking links

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome.

Feel free to fork the repository and submit a pull request.

---

## 👨‍💻 Author

**Akash Swain**
