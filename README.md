# PerplexiPlay – Agent Playground & Testing Environment

PerplexiPlay is an open-source platform for building, testing, and benchmarking agentic AI systems powered by CrewAI, LangChain, and OpenAI. The project ships with a FastAPI backend, Streamlit frontend, PostgreSQL (SQLite for local dev) storage, JWT-based authentication, automated tests, and CI/CD assets ready for Vercel or container-based deployments.

- **Backend:** FastAPI, SQLAlchemy (async), JWT auth (Argon2 password hashing)
- **Frontend:** Streamlit dashboard for managing agents and experiments
- **Database:** PostgreSQL in production, SQLite fallback for local development/tests
- **Agents:** Framework-aware engine supporting CrewAI, LangChain, and OpenAI integrations
- **Experiments:** Run, track, and review agent experiment results in real time

---

## Project Structure

```
backend/
  app/
    api/           # FastAPI routers
    core/          # Settings & security utilities
    db/            # Async SQLAlchemy session management
    models/        # SQLAlchemy ORM models
    schemas/       # Pydantic request/response schemas
    services/      # Auth and agent engine services
    main.py        # FastAPI application factory
  tests/           # Pytest suite (async HTTPX)
  Dockerfile
  requirements.txt
frontend/
  app.py           # Streamlit application
  Dockerfile
  requirements.txt
.github/workflows/ci.yml
docker-compose.yml
.env.example
pytest.ini
README.md
```

---

## Quick Start

### 1. Clone & Bootstrap

```bash
git clone <repo-url>
cd <repo-dir>
cp .env.example .env
```

Update `.env` with secure secrets and (optionally) set `DATABASE_URL` to a PostgreSQL instance.

### 2. Local Development (SQLite)

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend/app --reload

# Frontend (new shell with virtualenv)
python -m venv .venv-frontend && source .venv-frontend/bin/activate
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

FastAPI is served at `http://127.0.0.1:8000`, Streamlit UI at `http://127.0.0.1:8501`. The frontend defaults to the backend URL specified in `.env`.

### 3. Docker Compose (PostgreSQL)

```bash
docker compose up --build
```

Services:

- `backend`: http://localhost:8000
- `frontend`: http://localhost:8501
- `db`: PostgreSQL running on localhost:5432

---

## Testing

```bash
pytest
# or targeted
pytest backend/tests/test_auth.py
```

Pytest uses an in-memory SQLite database with async fixtures. The root `pytest.ini` already injects the backend package onto `PYTHONPATH`.

---

## API Reference (v1)

Base URL: `http://localhost:8000/api`

### Auth

- `POST /auth/register` – Create a user account.
- `POST /auth/login` – Obtain access/refresh tokens.
- `POST /auth/refresh` – Rotate access/refresh tokens (refresh token body).
- `POST /auth/logout` – Revoke refresh token.

### Users

- `GET /users/me` – Retrieve current profile.
- `PATCH /users/me/preferences` – Update preference JSON.

### Agents

- `GET /agents/` – List authenticated user’s agent configs.
- `POST /agents/` – Create agent (framework: `crewai | langchain | openai`).
- `GET /agents/{id}` – Retrieve agent.
- `PUT /agents/{id}` – Update agent.
- `DELETE /agents/{id}` – Delete agent.

### Experiments

- `GET /experiments/` – List experiments.
- `POST /experiments/` – Launch experiment run.
- `GET /experiments/{id}` – Fetch experiment details.
- `GET /experiments/{id}/status` – Status/result snapshot.

---

## Streamlit Frontend Highlights

- Authenticated dashboard with login/registration
- Agent CRUD: create, view, and manage agent configs
- Experiment runner with JSON payload builder
- Result explorer displaying structured experiment outputs

Set `BACKEND_URL` env var (or `.env`) if the backend runs on a non-default host.

---

## Continuous Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

1. Python lint/test (backend)
2. Backend pytest suite
3. Frontend Streamlit smoke-import

Extend the pipeline with deployment steps as needed.

---

## Deployment

### Backend

- Containerized via `backend/Dockerfile`
- Deploy to any container runtime or use serverless (e.g., Vercel functions) with minor adjustments
- Configure environment variables (`DATABASE_URL`, `SECRET_KEY`, `REFRESH_SECRET_KEY`, `ENV`)

### Frontend

- Streamlit app containerized in `frontend/Dockerfile`
- For Vercel, package as a Python app or deploy via container build
- Ensure `BACKEND_URL` points to the publicly reachable FastAPI instance

### Production Database

Provision PostgreSQL and set:

```
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>
```

---

## Agent Engine Extensibility

`app/services/agent_engine.py` contains a pluggable execution layer. Replace the simulation stubs with real CrewAI, LangChain, or OpenAI integration logic:

- Instantiate framework-specific chains/agents
- Execute with `experiment.input_payload`
- Persist metrics/outputs to `experiment.result_payload`

---

## Contributing

1. Fork the repo & create a feature branch
2. Implement changes with tests
3. Run `pytest`
4. Open a pull request describing the change & steps to reproduce

---

## License

MIT License – see `LICENSE` (add your organization’s preferred license file if needed).

---

PerplexiPlay is designed for rapid experimentation with agentic AI workflows. Enjoy building! 🚀
