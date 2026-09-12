# ABKNET TECHNOLOGIES

**BUILD • LEARN • INNOVATE**

A production-structured static technology platform built with HTML, CSS and JavaScript.

## Included
- Responsive multi-page website
- Supplied ABKNET logo integrated throughout
- Functional JSON formatter/validator/download
- Functional local password generator
- Functional word counter
- Functional unit converter
- Browser QR matrix generator
- Tools directory
- Tutorials and project/blog sections
- Downloads center with honest Coming Soon states
- YouTube hub
- About/contact pages
- Global search across tools, tutorials, projects, blog, downloads and legal pages
- Light/dark theme preference
- Tool category filters and tutorial filters
- Tutorial reading-progress bar and share/copy-link controls
- Progressive Web App (PWA) install support and offline fallback
- Accessibility/reduced-motion foundations
- SEO metadata, robots.txt and sitemap.xml
- No fake statistics, testimonials or download files

## Run locally
Open `index.html` in a modern browser, or serve the folder with any static web server.

## Before production
1. Keep `abknet.work.gd` in `robots.txt` and `sitemap.xml` unless the domain changes.
2. Connect the contact form to a secure backend/email provider.
3. Add the official YouTube channel URL.
4. Add only real software releases.
5. Add a real analytics system only if desired and configure its privacy notice.

## Backend v2
The website now includes a Flask + SQLite backend.

### API
- `GET /api/health` — backend health check
- `GET /api/search?q=...` — website search API
- `POST /api/contact` — stores support messages and creates ticket IDs
- `POST /api/newsletter` — stores newsletter subscriptions
- `POST /api/feedback` — stores site feedback
- `GET /admin?token=...` — protected admin inbox

### Run the full website locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```
Set `ADMIN_TOKEN` from `.env.example`, then run:
```bash
python app.py
```
Open `http://127.0.0.1:5000`.

The SQLite database is created automatically at `data/abknet.db`.

## Feature Update v2
The site is designed to remain useful on GitHub Pages without requiring a business email. The new client-side features include theme preference, directory filters, tutorial sharing, PWA installation and offline caching.

The Flask backend remains optional for contact, newsletter and feedback storage; the static GitHub Pages deployment does not provide `/api/*` endpoints by itself.


## Feature update v3
- Added professional Services page and service enquiry links.
- Added primary and secondary Gmail contact options.
- Contact form now falls back to a direct email link when the API is unavailable.
- Added service discovery to global API search.
- Preserved GitHub Pages, PWA, theme, tools and tutorial features.

Public contact emails:
- abubakaruuhammadumar2026@gmail.com
- muhammadabk2090@gmail.com


## Backend v4 — production-ready API architecture
The project now includes a separate-ready Flask backend with PostgreSQL support, SQLite local fallback, CORS for the GitHub Pages domain, protected admin APIs, ticket status updates, and a Render deployment blueprint. The static frontend remains compatible with GitHub Pages. Configure the deployed backend URL in `js/api-config.js`.
