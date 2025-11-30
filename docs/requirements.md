# MedQueue AI — Requirements Spec (1 page)

**Date:** 2003-07-11  
**Author:** Prajapati Shivam

## Actors

- **Patient** — register, book token, view ETA, view history, receive notifications.
- **Doctor** — view queue, advance token, mark delay/break, view schedule.
- **Receptionist** — create walk-in tokens, manage queue, override emergency.
- **HospitalAdmin** — add doctors, edit schedules, view analytics.
- **SuperAdmin** — manage hospitals, site-level config, monitor usage.

## MVP features

1. **Hospital & Doctor registry** — hospitals register and add doctors with OPD times.
2. **Token booking (online + walk-in)** — patients request token, system assigns incremental number.
3. **Live queue view** — patients & doctors can see queue length and current token.
4. **Doctor controls** — mark called/completed, mark break/delay.
5. **Real-time updates** — WebSocket channel broadcasts token events.
6. **Basic analytics logging** — log token events (queuing, called, completed) to an analytics store.

## Acceptance Criteria

- **Hospitals can be added**: /api/hospitals endpoint returns created hospital with id.
- **Doctors can be added**: doctor associated with hospital has OPD times.
- **Patient can create token**: POST /api/tokens returns token with `number` and status `waiting`.
- **WebSocket broadcast works**: when token is created, connected clients receive a `token.created` event.
- **Doctor can mark a token called**: PATCH token -> status `called`, `called_at` populated.
- **Receptionist can create walk-in token**: token created without patient user attached.
- **Docs & run instructions**: README contains run steps for local dev.

## Non-functional

- Logs sufficient for later ML features (timestamped events).
- Privacy: no sensitive info stored in logs for MVP.
