# API Reference

Base URL: `https://{host}/api`

## Authentication

### `POST /auth/register`
- **Body:** `{ "username": "...", "email": "...", "password": "...", "preferences": {} }`
- **Response:** User object (without password)
- **Notes:** Enforces unique email, hashes password with Argon2.

### `POST /auth/login`
- **Body:** `{ "email": "...", "password": "..." }`
- **Response:** `{ "access_token": "...", "refresh_token": "...", "token_type": "bearer" }`
- **Headers:** `X-Refresh-Token-Id` (UUID of persisted token)

### `POST /auth/refresh`
- **Body:** `{ "refresh_token": "..." }`
- **Response:** Rotated access/refresh token pair
- **Behavior:** Validates refresh token JTI against database and replaces metadata.

### `POST /auth/logout`
- **Body:** `{ "refresh_token": "..." }`
- **Response:** `204 No Content`
- **Behavior:** Revokes refresh token in database.

## Users

### `GET /users/me`
- **Auth:** Bearer access token
- **Response:** Current user profile.

### `PATCH /users/me/preferences`
- **Body:** `{ "preferences": { ... } }`
- **Response:** Updated profile with merged preferences.

## Agents

### `GET /agents/`
- **Auth:** Bearer
- **Response:** List of agent configurations owned by the user.

### `POST /agents/`
- **Body:** `{ "name": "...", "framework": "crewai|langchain|openai", "description": "...", "parameters": {...} }`
- **Response:** Created agent.

### `GET /agents/{id}`
- **Response:** Agent details (ownership enforced).

### `PUT /agents/{id}`
- **Body:** Partial or full payload to update `name`, `framework`, `description`, `parameters`.
- **Response:** Updated agent.

### `DELETE /agents/{id}`
- **Response:** `204 No Content`.

## Experiments

### `GET /experiments/`
- **Auth:** Bearer
- **Response:** List of experiments (latest first).

### `POST /experiments/`
- **Body:** `{ "name": "...", "agent_id": "<uuid>|null", "input_payload": {...} }`
- **Response:** Experiment record with execution result (synchronous engine run).

### `GET /experiments/{id}`
- **Response:** Experiment metadata and payloads.

### `GET /experiments/{id}/status`
- **Response:** `{ "id": "<uuid>", "status": "pending|running|completed|failed", "result_payload": {...}, "error_message": null }`

---

All responses follow JSON format. Submit `Content-Type: application/json`. Use refresh tokens to rotate access tokens when receiving HTTP 401 from expired access tokens.***
