# Campus Copilot API 🚀

Campus Copilot is a powerful, AI-driven resume analysis backend built with FastAPI. It helps candidates optimize their resumes against specific Job Descriptions (JDs) using advanced LLMs like Google Gemini.

## ✨ Features

- **AI-Powered Analysis**: Evaluates resumes against JDs with surgical precision using Google Gemini (and planned Claude integration).
- **Deep Insights**: Provides a match score, detailed reasoning, identified gaps (missing keywords), and highlighted strengths.
- **Actionable Feedback**: Automatically rewrites weak resume bullets into high-impact, metric-driven achievements.
- **Interview Prep**: Generates tailored technical and behavioral interview questions based on the JD and resume.
- **Smart Caching**: Implements Redis caching to prevent redundant AI API calls for identical resume/JD combinations.
- **Usage Quotas**: Built-in monthly scan limits (2 scans/month for free users) with bypass for admin/VIP users.
- **Scan History**: Persistent storage of past analyses for users to track their progress.
- **Secure Auth**: Integration-ready for Google OAuth (validated via JWT).

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python)
- **AI Engine**: [Google Gemini 1.5 Flash](https://ai.google.dev/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Async)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Caching**: [Redis](https://redis.io/)
- **PDF Parsing**: [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)
- **Containerization**: Docker (Database only, App runs locally)

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- Google Gemini API Key

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd resume-project-backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   ENVIRONMENT=dev
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/resume_db
   REDIS_URL=redis://localhost:6379/0
   GEMINI_API_KEY=your_gemini_api_key
   CLAUDE_API_KEY=your_claude_api_key
   JWT_SECRET=your_jwt_secret
   GOOGLE_CLIENT_ID=your_google_client_id
   ```

5. **Run the Database**:
   ```bash
   docker-compose up -d
   ```

6. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

7. **Start the API**:
   ```bash
   uvicorn app.main:app --reload
   ```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Check API status |
| `POST` | `/api/v1/analyze` | Upload PDF resume + JD text for analysis |
| `GET` | `/api/v1/scans` | Fetch history of scans for current user |
| `POST` | `/auth/google` | Google OAuth authentication |

## 🏗️ Project Structure

```text
├── alembic/              # Database migrations
├── app/
│   ├── ai/               # AI logic (Gemini/Claude routers)
│   ├── cache/            # Redis client & caching logic
│   ├── models/           # SQLAlchemy models (User, Scan)
│   ├── routers/          # API endpoints (Auth, Analysis)
│   ├── utils/            # Helpers (PDF parsing, Auth guards)
│   ├── config.py         # Pydantic settings
│   ├── database.py       # DB engine & session setup
│   └── main.py           # App entry point
├── .env                  # Environment variables (gitignored)
├── docker-compose.yml    # Infrastructure (Postgres)
└── requirements.txt      # Project dependencies
```

## ⚖️ Scoring Rubric

The AI evaluates resumes based on a strict deterministic rubric:
- **Experience Match (30 pts)**: Industry alignment, role title, and years of exp.
- **Skill Match (50 pts)**: Exact and partial keyword matching against the JD.
- **Impact & Metrics (20 pts)**: Presence of hard numbers and quantified achievements.

## 🤝 Contributing

1. Fork the repo.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📄 License

This project is licensed under the MIT License.
