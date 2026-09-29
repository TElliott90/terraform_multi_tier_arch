# Terraform Multi Tier Architecture

This project involves constructing a AWS multi architecture using Terraform to deploy a basic user authentication app which requires a frontend, backend and db. The sole focus of this project is on the utilisation of Terraform, rather than creation of the app itself.

## Authentication app

The React frontend uses the existing login and registration pages. A Python standard-library API stores users and sessions in SQLite; no backend packages are required.

Start the API (Python 3.10+):

```sh
python3 backend/server.py
```

In another terminal, start the frontend:

```sh
cd frontend
pnpm install
pnpm dev
```

Open the URL printed by Vite. Register an account, sign out, and sign in again. Sessions last 24 hours and survive a page refresh. The database is created automatically at `backend/auth.db` and is excluded from Git. Use `DATABASE_PATH` and `PORT` to override backend defaults; update the Vite proxy if you change the port.

API routes: `POST /api/register`, `POST /api/login`, `GET /api/me`, and `POST /api/logout`. Passwords use salted scrypt hashes; opaque session tokens use HttpOnly, SameSite cookies and are stored hashed in the database. The frontend never stores passwords or session tokens.

This is a local starter. Before public deployment, add HTTPS (set `COOKIE_SECURE=1`), login rate limiting, email verification, password recovery, and a production server/reverse proxy that serves the frontend and `/api` from the same origin. Vite's proxy is for development only.

Checks:

```sh
cd frontend
pnpm build
pnpm lint
```

```sh
python3 -m unittest discover -s backend -p 'test_*.py'
```
