# MedQueue AI — Week 2 Report

**Sprint:** Week 2 — User & Core Models, Auth, CRUD  
**Dates:** Week 2 (Day 1 → Day 7)  
**Author:** Shiv Prajapati

## What I completed

### Authentication & Users

- Implemented **CustomUser** model (extends `AbstractUser`) with:
  - `phone` field
  - `role` choices: `patient`, `doctor`, `receptionist`, `hospital_admin`
- Implemented **OTP** model and OTP flow:
  - `POST /api/auth/send-otp/` — sends OTP (console email)
  - `POST /api/auth/verify-otp/` — verifies OTP, creates/returns user
- Configured email backend to console for local dev.

### Core Models & CRUD

- Added `Hospital` model with fields: `name`, `address`, `city`, `contact_phone`, `timezone`.
- Added `Doctor` model linking to `User` and `Hospital`:
  - `user` (OneToOne -> CustomUser)
  - `hospital` (FK)
  - `specialization`, `opd_start`, `opd_end`
- Created serializers, viewsets and URL routers for hospitals and doctors.

### Permissions & Roles

- Implemented role-based permission classes (examples):
  - `IsHospitalAdminOrSuperuser`
  - `IsDoctorOwnerOrHospitalAdminOrSuperuser`
  - `IsHospitalAdminForOwnHospitalOrReadOnly`
- Protected endpoints so only correct roles can create/update/delete as intended.

### Admin Dashboard (Basic)

- Added a small `dashboard` app with:
  - login page: `/dashboard/login/`
  - hospital list: `/dashboard/` (staff only)
  - hospital detail page (lists doctors)

### Dev infra & DB

- Added `docker-compose.yml` for local MySQL, MongoDB, Redis (when running Docker).
- Updated `settings.py` to read `.env` and use `FORCE_SQLITE` fallback for quick dev.
- Email backend set to console for OTP dev.

## Issues encountered & resolutions

1. **Missing `add_class` filter in login template**

   - Cause: used `|add_class` from `django-widget-tweaks` without installing the package.
   - Fix: installed `django-widget-tweaks` and added to `INSTALLED_APPS`, or removed the filter in template.

2. **MySQL container port conflict / Docker errors**

   - Cause: local MySQL already using port 3306.
   - Fix: updated docker-compose to map container port to host `3307` and ensured proper CREATE USER / GRANT configuration.

3. **Migration order with custom user model**

   - Cause: admin/app migrations applied before `users` migration.
   - Fix: reset `django_migrations` table in DB (dev only), re-created `users` migrations and ensured consistent migration history.

4. **Permission import errors during startup**
   - Cause: missing permission classes or circular import.
   - Fix: ensured permission classes live in `users.permissions` and used them consistently.

## What’s next (Week 3 plan)

- Real-time token Queue: implement token lifecycle (issued, called, completed, skipped)
- WebSockets / Channels integration for live queue updates
- Receptionist & Doctor dashboards (call next / skip / emergency)
- Mobile-friendly patient UI: search hospitals, book token
- Integrate simple predictive model (baseline wait-time estimator)
- Add unit tests for auth flows, permission checks, and token logic

## Artifacts & Links

- Repo: `https://github.com/<your-username>/medqueue-ai`
- Week2 tag: `v0.2-week2` (created after this report)
- Important files:
  - `medqueue/settings.py` (env-driven settings, email console)
  - `users/models.py` (CustomUser, OTP)
  - `hospitals/models.py`, `doctors/models.py`
  - `users/views.py` (OTP endpoints)
  - `dashboard/` (templates + views)
