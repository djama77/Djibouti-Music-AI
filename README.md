# Djibouti Music AI

Open-source AI music studio powered by ACE-Step 1.5. This repository is the project starter: a responsive React interface, FastAPI adapter, Docker Compose setup, and backend tests.

## Architecture

- `frontend/`: React + Vite interface, designed for mobile and desktop.
- `backend/`: FastAPI service that forwards generation requests to a separately hosted ACE-Step API.
- GPU inference must run on a GPU-capable host; Vercel is suitable for the frontend, not for hosting the model itself.

## Status

Starter implementation. The ACE-Step service URL and access key must be configured locally. The integration has not yet been validated against a live GPU instance.

## Local setup

1. Copy `.env.example` to `.env` and configure the ACE-Step API URL and application access key.
2. Run `docker compose up --build`.
3. Open the frontend at `http://localhost:5173`.

Do not expose a shared demo access key in a public production frontend. Add real user authentication, per-user quotas, abuse controls, and a privacy notice before opening the service publicly.

## Tests

Run backend tests with `cd backend && pip install -r requirements-dev.txt && pytest`.

## License

See the repository license file before redistributing. ACE-Step has its own license and usage terms; review them separately.
