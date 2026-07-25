# CampusOne

CampusOne is a modular FastAPI + PostgreSQL backend with a React/Vite frontend for MANIT students and alumni.

## What is included

- Campus-only authentication using `@stu.manit.ac.in`
- Buy and sell marketplace with privacy-aware seller display
- Private lost-and-found reporting with match suggestions
- Anonymous community chat backed by API endpoints and WebSockets
- Responsive React UI with a campus dashboard layout

## Project structure

- `backend/` FastAPI app, SQLAlchemy models, JWT auth, and feature modules
- `frontend/` React app with the polished UI and API integration
- `docker-compose.yml` builds and runs Postgres, FastAPI, and React containers

## Local setup

1. Copy the example environment file:

   ```bash
   cp backend/.env.example backend/.env
   ```

   Configure the `SMTP_*` values in `backend/.env` for a local backend run. For Docker Compose, put the same values in
   a root `.env` file (or export them in your shell) so Compose can pass them to the backend. New accounts must enter
   the six-digit code sent to their campus email before they can log in.

2. Build and start the full stack:

   ```bash
   docker compose up -d --build
   ```

3. Apply migrations and seed data on the backend container if needed:

   ```bash
   docker compose exec backend alembic upgrade head
   docker compose exec backend python -m app.seed
   ```

4. Open the app at `http://localhost:5173`.

## Notes

- The frontend container is built with `VITE_API_URL=http://localhost:8000`.
- The backend container connects to Postgres through the Compose network at `db:5432`.
- Seeded admin login: `admin@stu.manit.ac.in` / `Admin1234!`
- Seeded student login: `ananya@stu.manit.ac.in` / `Student1234!`
