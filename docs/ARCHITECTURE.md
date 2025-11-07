# PerplexiPlay Architecture

## Components

| Layer     | Technology | Responsibilities |
|-----------|------------|------------------|
| Frontend  | Streamlit  | Authentication UI, agent CRUD, experiment execution & results |
| Backend   | FastAPI    | REST API, JWT auth, orchestration, validation |
| Database  | PostgreSQL | Persistent storage for users, agents, experiments, refresh tokens |
| Testing   | Pytest + HTTPX | Async API contract tests, regression coverage |

### Backend Modules

- `app/core`: configuration, JWT security helpers
- `app/db`: async SQLAlchemy engine/session management
- `app/models`: ORM models (users, agents, experiments, refresh tokens)
- `app/schemas`: Pydantic models for request/response validation
- `app/services`: authentication + agent execution engine
- `app/api`: versioned routers (`/auth`, `/users`, `/agents`, `/experiments`)

### Agent Engine

`app/services/agent_engine.py` exposes a pluggable abstraction. Each supported framework (CrewAI, LangChain, OpenAI) has a dedicated executor with a consistent return shape. Replace the stub implementations with the actual SDK integrations to connect to live agents.

### Authentication Flow

1. `POST /auth/register` hashes password (Argon2) and persists user.
2. `POST /auth/login` issues access + refresh JWTs and saves refresh token metadata for revocation.
3. `POST /auth/refresh` rotates tokens with JTI verification.
4. `POST /auth/logout` revokes refresh tokens, preventing reuse.

### Experiments Lifecycle

1. User selects an agent configuration via Streamlit.
2. Frontend sends payload to `POST /experiments/`.
3. Backend persists experiment, executes agent engine synchronously, and stores structured results.
4. Experiment history is accessible through `/experiments/` and `/experiments/{id}/status`.

### Local Development Modes

- **SQLite** (default): `DATABASE_URL=sqlite+aiosqlite:///./perplexiplay.db`
- **PostgreSQL** (production / Docker): `postgresql+asyncpg://...`

### Containerization

- `backend/Dockerfile`: Uvicorn ASGI server
- `frontend/Dockerfile`: Streamlit service
- `docker-compose.yml`: orchestrates backend, frontend, and PostgreSQL database

### CI/CD

`.github/workflows/ci.yml` runs backend unit tests and a frontend import smoke test on each push/PR into `main`.

### Security Considerations

- Unique user emails enforced at the database level
- Argon2 password hashing via Passlib
- Refresh token persistence enables server-side revocation
- JWT secrets injected via environment variables

### Extension Ideas

- Replace simulated agent outputs with real SDK calls
- Add experiment scheduling & asynchronous background workers (Celery / RQ)
- Integrate vector storage for datasets and evaluations
- Expand CI to include linting, type checking, and dockerized integration tests
