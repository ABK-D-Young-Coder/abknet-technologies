# ABKNET TECHNOLOGIES — Backend Setup

The frontend remains on GitHub Pages. The Flask backend is designed to run separately on Render and provides API endpoints for contact tickets, newsletter subscriptions, feedback, search, health checks, and a protected admin area.

## Architecture
- Frontend: GitHub Pages (`https://abknet.work.gd`)
- Backend: Flask + Gunicorn
- Production database: PostgreSQL (`DATABASE_URL`)
- Local development database: SQLite fallback
- Backend hosting: Render Web Service

## Deploy
1. Push this project to GitHub.
2. In Render, create a Web Service from the repository.
3. Use `pip install -r requirements.txt` as the build command.
4. Use `gunicorn app:app` as the start command.
5. Add environment variables: `ADMIN_TOKEN`, `DATABASE_URL`, and `ALLOWED_ORIGINS`.
6. Create a PostgreSQL database and connect its `DATABASE_URL` to the web service.
7. Copy the resulting Render API URL into `js/api-config.js` as `window.ABKNET_API_BASE`.
8. Push the frontend change to GitHub Pages.

## API endpoints
- `GET /api/health`
- `GET /api/contact-info`
- `GET /api/search?q=...`
- `POST /api/contact`
- `POST /api/newsletter`
- `POST /api/feedback`
- `GET /api/admin/summary` (X-Admin-Token required)
- `GET /api/admin/contacts` (X-Admin-Token required)
- `PATCH /api/admin/contacts/<ticket_id>` (X-Admin-Token required)
- `GET /admin` (X-Admin-Token required)

## Important production note
Do not put `ADMIN_TOKEN`, database passwords, API keys, or SMTP credentials into HTML/JavaScript. Keep secrets in Render environment variables.

Render Free web services are suitable for testing but spin down after inactivity, and free Render Postgres expires after 30 days. For permanent business data, use a paid persistent database/service or another production database provider.
