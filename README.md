# ReUnion ✦

> *"To bring together again that which has drifted apart—talent and opportunity—through radical transparency."*

**ReUnion** is an intelligent Career Assistance Platform built for **SCDS TechFest 2026**. It bridges the widening chasm between evolving employer requirements and static candidate profiles by transforming fragmented job data into personalized, actionable upskilling roadmaps.

---

## 📖 The Philosophy

In the modern tech ecosystem, a lack of transparency leads to "hiring scope creep," where job requirements silently drift away from the skills candidates actually possess.

**ReUnion** derives its name from two core pillars:
*   **Re (Again):** Acknowledging that employment is a continuous cycle of re-evaluation and re-skilling, not a one-time transaction.
*   **Union (Together):** Bringing disparate entities—"Job Requirements" and "Candidate Profiles"—back into a cohesive whole.

Like the volcanic island of **La Réunion** that constantly reshapes itself, this project aims to be the stable ground in the chaotic ocean of recruitment data.

---

## 🚀 Key Features

### 1. Centralized Intelligence (The "Brain")
*   **Multi-Source Ingestion**: Aggregates data from diverse sources including official CSV datasets (MyCareersFuture, Glassdoor) and unstructured PDFs (Problem Statements).
*   **Hybrid Search**: Combines SQL-based hard filtering (Salary, Location) with Vector Semantic Search (RAG) to find hidden opportunities.

### 2. Actionable Roadmaps
*   **AI Gap Analysis**: Uses Large Language Models (DeepSeek V3 / OpenAI) to analyze the specific "delta" between your resume and a target job.
*   **Skill Acquisition Plans**: Generates linear, step-by-step learning paths.
*   **Local Integration**: Automatically suggests relevant **SkillsFuture** courses and government subsidies.

### 3. Transparent Tracking
*   **Application Status**: Track your journey from "New" to "Offer" directly within the roadmap interface.
*   **Tech Stack Filtering**: Dynamically filter opportunities based on the specific technologies (e.g., Python, React, AWS) extracted from job descriptions.

---

## 🛠️ Tech Stack

**Frontend**
*   **Streamlit**: Highly customized with a "Transcendant" Glassmorphism CSS theme.
*   **Dynamic UI**: Real-time interaction with the backend database.

**Backend**
*   **FastAPI**: Robust REST API serving the AI agent and data synchronization endpoints.
*   **SQLAlchemy & SQLite**: Relational storage for structured job data and user profiles.

**AI & Data**
*   **LangChain**: Orchestrates the reasoning chains for Gap Analysis.
*   **ChromaDB**: Local Vector Store for semantic document retrieval.
*   **DeepSeek / OpenAI**: Powering the cognitive reasoning engine.

---

## 📦 Installation & Setup

### Prerequisites
*   Python 3.9+
*   An API Key (DeepSeek or OpenAI)

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/SCDS-TechFest26.git
cd SCDS-TechFest26
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```bash
# Choice 1: DeepSeek (Cost-Effective)
DEEPSEEK_API_KEY=your_key_here
LLM_MODEL="deepseek-ai/DeepSeek-V3"
LLM_API_BASE="https://api.siliconflow.cn/v1/"

# Choice 2: OpenAI (Stable)
OPENAI_API_KEY=your_key_here
EMBEDDING_MODEL="text-embedding-3-small"
```

### 3. Ingest Data (Build the Brain)
Initialize the database and vector store with the official datasets:
```bash
python3 ingest.py
```

---

## 🚦 Usage

### Start the Backend
The backend serves the API and the Database connection.
```bash
python3 main.py
# Backend runs at http://localhost:8000
```

### Start the Interface
Open a new terminal to launch the User Interface.
```bash
streamlit run web_app.py
# Frontend runs at http://localhost:8501
```

---

## 📄 License
Project created for SCDS TechFest 2026.
