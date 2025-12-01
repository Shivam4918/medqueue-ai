# Week 1 Report — MedQueue AI

**Date:** 2025-12-01  
**Author:** <Your Name>

## What I completed (deliverables)

- Repository initialized with README, LICENSE, .gitignore.
- `.env.example` added (do NOT commit real `.env`).
- Django project scaffold + base apps created:
  - apps: `users`, `hospitals`, `doctors`, `queues`, `api`.
  - key files: `medqueue/asgi.py`, `medqueue/routing.py`, `medqueue/settings.py`.
- Database & local infra (Docker)
  - `docker-compose.yml` for MySQL, MongoDB, Redis.
  - Verified containers running: `mysql`, `mongo`, `redis`.
- Models and admin:
  - Basic models created and registered (Hospital, Doctor, Profile, Token).
- Real-time scaffolding:
  - ASGI & Channels scaffolding added (placeholder `routing.py`).
- Repo process:
  - Branching: `dev` used for development, `main` as stable.
  - Created GitHub issues for initial tasks and created a Kanban project.
- Wireframes:
  - Low-fidelity wireframes exported to `docs/wireframes/` (login, patient home, hospital dashboard, doctor queue).

## Important files (links)

- `README.md`
- `docs/requirements.md`
- `docs/db-setup.md`
- `docs/wireframes/` (PNG files)
- `docker-compose.yml`
- `medqueue/settings.py` (env-based config)
- `core/`, `users/`, `hospitals/`, `doctors/`, `queues/`, `api/`

## Issues encountered & solutions

1. **Docker daemon 500 errors** — Restarted Docker Desktop, shut down WSL (`wsl --shutdown`) and restarted. If persists, use SQLite fallback (`FORCE_SQLITE=1`) to continue development.
2. **MySQL auth & PyMySQL** — MySQL 8 default auth (`caching_sha2_password`) required `cryptography` for PyMySQL. Solution: installed `cryptography` or set MySQL user auth to `mysql_native_password` via SQL.
3. **Port conflict on 3306** — Local MySQL used host port 3306. Solution: remapped container to host `3307` in `docker-compose.yml` (`"3307:3306"`).
4. **Git rebase conflicts (week1 integration)** — Resolved `.gitignore` and `docker-compose.yml` conflicts, completed rebase, then pushed development branch `dev`.
5. **App name conflict** — `queue` is Python stdlib; renamed to `queues`.

## Next week plan (high level)

- Week 2 (API & Auth)
  1. Implement DRF endpoints: hospitals, doctors, tokens.
  2. JWT authentication + OTP login flow.
  3. Token booking flow: POST `/api/tokens/` with auto-numbering + tests.
  4. WebSocket consumer: token created/updated broadcast (Channels).
  5. Basic frontend pages (Tailwind) for patient home + token view.
  6. Dockerize the Django app for local end-to-end testing.

## Notes & run instructions (quick)

1. Start infra: `docker compose up -d`
2. Install deps: `python -m venv .venv` → activate → `pip install -r requirements.txt`
3. Set `.env` (copy `.env.example` → fill secrets)
4. Run migrations: `python manage.py migrate`
5. Run server: `python manage.py runserver`

---
