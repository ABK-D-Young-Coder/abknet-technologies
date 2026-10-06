# ABKNET TECHNOLOGIES
# Build • Learn • Innovate

A production-ready full-stack platform that keeps the existing GitHub Pages frontend and adds secure backend APIs for auth, contact, tickets, notifications, newsletter, feedback, and admin management.

## Architecture

- Frontend: static HTML/CSS/JS hosted on GitHub Pages
- Backend: Flask API deployed on Render
- Database: PostgreSQL in production, SQLite fallback for local development
- API base URL: https://abknet-technologies.onrender.com

## Project structure

- app.py — Flask API and static-site fallback
- js/api-config.js — frontend API base configuration
- data/ — SQLite data directory for local development
- tests/ — API and auth test coverage
- .env.example — required environment variables

## Local development

1. Create and activate a virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Create a local environment file
   ```bash
   cp .env.example .env
   ```
4. Update the values in `.env` using your local or Render settings.
5. Run the app
   ```bash
   python app.py
   ```
6. Visit http://127.0.0.1:5000

## Environment variables

See `.env.example` for required variables. The main values are:

- DATABASE_URL
- SECRET_KEY
- JWT_SECRET_KEY
- ADMIN_SECRET
- EMAIL_PROVIDER
- SMTP_HOST
- SMTP_PORT
- SMTP_USERNAME
- SMTP_PASSWORD
- EMAIL_FROM
- PRIMARY_CONTACT_EMAIL
- SECONDARY_CONTACT_EMAIL
- FRONTEND_URL

## PostgreSQL setup

For production, set `DATABASE_URL` to your PostgreSQL connection string. Example:

```bash
export DATABASE_URL=postgresql://username:password@host:5432/abknet
```

A local SQLite database is used automatically if `DATABASE_URL` is not set.

## Database migrations

The app creates the required tables automatically on startup. For production, keep the schema versioned in your deployment workflow and back up regularly.

## Email configuration

Supported providers:

- SMTP (default)
- future providers can be added behind the same email abstraction

Set the required SMTP values in `.env` and do not commit real credentials to Git.

## API endpoints

Health:
- GET /api/health

Authentication:
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/verify-email
- POST /api/auth/forgot-password
- POST /api/auth/reset-password

User:
- GET /api/users/me
- PUT /api/users/me
- PUT /api/users/me/password
- DELETE /api/users/me

Contact and tickets:
- POST /api/contact
- GET /api/contact
- POST /api/tickets
- GET /api/tickets
- GET /api/tickets/<id>
- POST /api/tickets/<id>/replies

Newsletter and feedback:
- POST /api/newsletter
- POST /api/feedback

Admin:
- GET /api/admin/dashboard
- GET /api/admin/users
- GET /api/admin/tickets
- GET /api/admin/messages
- GET /api/admin/activity

## Admin setup

Set `ADMIN_SECRET` and `ADMIN_TOKEN` in the environment. Use the `X-Admin-Token` header on admin endpoints. The `/admin` route also checks the header for access.

## GitHub Pages deployment

The static frontend remains deployable on GitHub Pages. The API configuration is set in `js/api-config.js` and uses the Render backend URL.

## Render deployment

1. Push this repo to GitHub.
2. On Render, create a new Web Service linked to the repo.
3. Use the `gunicorn app:app` start command.
4. Provide environment variables from `.env.example`.
5. Configure `DATABASE_URL` and `ADMIN_TOKEN` in Render.
6. Deploy and test `/api/health`.

## Running tests

```bash
pytest -q
```

## Security checklist

- Use HTTPS only in production.
- Never commit real `.env` files.
- Use strong secret values.
- Hash passwords with Werkzeug.
- Validate all server-side request payloads.
- Use PostgreSQL in production.
- Restrict CORS to known frontend domains.
- Protect admin routes with dedicated authorization.
- Keep SQLite for local development only.

## Manual follow-up

The following items still need real deployment values from the project owner:

- SMTP credentials or a production email provider account
- PostgreSQL connection details
- Render service URL and custom domain
- Admin secret values
- Final contact form email delivery provider configuration
