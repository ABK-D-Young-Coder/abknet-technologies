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
- Global search on the homepage
- Accessibility/reduced-motion foundations
- SEO metadata, robots.txt and sitemap.xml
- No fake statistics, testimonials or download files

## Run locally
Open `index.html` in a modern browser, or serve the folder with any static web server.

## Before production
1. Replace `YOUR-DOMAIN.example` in `robots.txt` and `sitemap.xml`.
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
