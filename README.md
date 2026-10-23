# CodeGuard AI 🛡️

CodeGuard AI is an asynchronous, full-stack static code analysis tool that leverages the Google Gemini LLM to automatically identify security vulnerabilities, bugs, and anti-patterns in source code. 

Built with a FastAPI backend and a responsive Tailwind CSS frontend, it features persistent review history via SQLite and a zero-contamination client-side Demo Mode.

## 🚀 Features

- **AI-Powered Analysis**: Integrates with Google Gemini API for deep semantic code review.
- **Asynchronous Architecture**: Non-blocking FastAPI endpoints ensure high performance during downstream LLM API calls.
- **Data Persistence**: Automatically serializes and saves AI findings to a local SQLite database using SQLAlchemy ORM.
- **Resilience & Validation**: Enforces strict Pydantic schemas for data integrity and handles downstream API outages gracefully.
- **Client-Side Demo Mode**: A built-in UI toggle that simulates API responses, allowing UI testing without consuming LLM quotas or polluting the production database.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, Pydantic, SQLAlchemy
- **Database**: SQLite
- **AI Integration**: Google GenAI SDK (Gemini)
- **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS

## 📸 Screenshots

*(Add a screenshot of your main dashboard here once published)*
*(Add a screenshot of your active findings and history panel here)*

## ⚙️ Local Setup & Installation

### 1. Clone the repository
```bash
git clone [https://github.com/yourusername/codeguard-ai.git](https://github.com/yourusername/codeguard-ai.git)
cd codeguard-ai