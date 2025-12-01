# MedQueue AI — Local Database Setup (Docker)

## Overview

This project uses three Dockerized services:

- **MySQL 8** — main transactional DB (patients, doctors, tokens)
- **MongoDB 6** — analytics, event logs, ML data
- **Redis 7** — WebSocket backend (Django Channels)

All services run locally via `docker-compose.yml`.

---

## Services & Ports

| Service | Port  | Purpose            |
| ------- | ----- | ------------------ |
| MySQL   | 3306  | Relational DB      |
| MongoDB | 27017 | NoSQL analytics DB |
| Redis   | 6379  | Cache + WebSockets |

---

## Credentials

### MySQL
