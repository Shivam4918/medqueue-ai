# MedQueue AI

**One-liner:** MedQueue AI — Real-time OPD queue management for hospitals: digital tokens, live wait-times, AI crowd forecasting.

## MVP (Week 1)

- Register hospital, add doctors
- Patient: take token (online), view current queue & ETA
- Receptionist: create walk-in token
- Doctor: view queue & mark next token as called/completed
- Real-time updates (WebSockets) — token created/updated broadcasts
- Basic analytics storage for ML (logs saved to MongoDB later)

## Tech stack

- Frontend: HTML + Tailwind + HTMX/vanilla JS
- Backend: Django + Django REST Framework + Channels
- DBs: MySQL (relational models) + MongoDB (analytics)
- Real-time: Redis channel layer
