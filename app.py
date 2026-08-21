import os
import re
import sqlite3
import secrets
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, g, render_template_string

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv('ABKNET_DB', BASE_DIR / 'data' / 'abknet.db'))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=None)
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 7000 * 1024

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
ALLOWED_CATEGORIES = {'General', 'Technical Support', 'Tool Feedback', 'Partnership', 'Business', 'Bug Report'}


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db:
        db.close()


def init_db():
    db = get_db()
    db.executescript('''
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        category TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'new'
    );
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rating INTEGER NOT NULL,
        message TEXT NOT NULL,
        page TEXT,
        created_at TEXT NOT NULL
    );
    ''')
    db.commit()


def clean(value, max_len):
    return str(value or '').strip()[:max_len]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


@app.get('/api/health')
def health():
    return jsonify({'ok': True, 'service': 'ABKNET TECHNOLOGIES API', 'time': now_iso()})


@app.post('/api/contact')
def contact():
    data = request.get_json(silent=True) or request.form
    name = clean(data.get('name'), 100)
    email = clean(data.get('email'), 160).lower()
    category = clean(data.get('category'), 50)
    subject = clean(data.get('subject'), 180)
    message = clean(data.get('message'), 5000)
    website = clean(data.get('website'), 200)  # honeypot

    if website:
        return jsonify({'ok': True, 'message': 'Message received.'})
    if not name or not EMAIL_RE.match(email) or category not in ALLOWED_CATEGORIES or not subject or not message:
        return jsonify({'ok': False, 'error': 'Please provide a valid name, email, category, subject and message.'}), 400
    if len(message) < 10:
        return jsonify({'ok': False, 'error': 'Please provide a little more detail in your message.'}), 400

    ticket = 'ABK-' + datetime.now(timezone.utc).strftime('%Y%m%d') + '-' + secrets.token_hex(3).upper()
    db = get_db()
    db.execute('INSERT INTO contacts(ticket_id,name,email,category,subject,message,created_at) VALUES(?,?,?,?,?,?,?)',
               (ticket, name, email, category, subject, message, now_iso()))
    db.commit()
    return jsonify({'ok': True, 'ticket_id': ticket, 'message': 'Your message has been received.'}), 201


@app.post('/api/newsletter')
def newsletter():
    data = request.get_json(silent=True) or request.form
    email = clean(data.get('email'), 160).lower()
    if not EMAIL_RE.match(email):
        return jsonify({'ok': False, 'error': 'Enter a valid email address.'}), 400
    db = get_db()
    try:
        db.execute('INSERT INTO subscribers(email,created_at) VALUES(?,?)', (email, now_iso()))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'ok': True, 'message': 'This email is already subscribed.'})
    return jsonify({'ok': True, 'message': 'You are subscribed to ABKNET updates.'}), 201


@app.post('/api/feedback')
def feedback():
    data = request.get_json(silent=True) or request.form
    try:
        rating = int(data.get('rating', 0))
    except (ValueError, TypeError):
        rating = 0
    message = clean(data.get('message'), 2000)
    page = clean(data.get('page'), 300)
    if rating not in range(1, 6) or len(message) < 3:
        return jsonify({'ok': False, 'error': 'Choose a rating from 1 to 5 and enter a short message.'}), 400
    db = get_db()
    db.execute('INSERT INTO feedback(rating,message,page,created_at) VALUES(?,?,?,?)', (rating, message, page, now_iso()))
    db.commit()
    return jsonify({'ok': True, 'message': 'Thanks for the feedback.'}), 201


@app.get('/api/search')
def search():
    q = clean(request.args.get('q'), 80).lower()
    items = [
        {'title':'JSON Formatter','type':'Tool','url':'/tools/json-formatter.html','description':'Format and validate JSON.'},
        {'title':'QR Generator','type':'Tool','url':'/tools/qr-generator.html','description':'Create QR codes.'},
        {'title':'Password Generator','type':'Tool','url':'/tools/password-generator.html','description':'Generate strong passwords locally.'},
        {'title':'Word Counter','type':'Tool','url':'/tools/word-counter.html','description':'Count text statistics.'},
        {'title':'Unit Converter','type':'Tool','url':'/tools/unit-converter.html','description':'Convert common units.'},
        {'title':'HTML First Website','type':'Tutorial','url':'/tutorials/html-first-website.html','description':'Build your first website.'},
        {'title':'JavaScript Interactivity','type':'Tutorial','url':'/tutorials/javascript-interactivity.html','description':'Make web pages interactive.'},
        {'title':'Python Basics','type':'Tutorial','url':'/tutorials/python-basics.html','description':'Learn Python through practical projects.'},
        {'title':'Projects','type':'Project','url':'/projects/index.html','description':'Explore ABKNET projects.'},
        {'title':'Downloads','type':'Software','url':'/downloads/index.html','description':'ABKNET software center.'},
        {'title':'Blog','type':'Article','url':'/blog/index.html','description':'Technology articles.'}
    ]
    if not q:
        return jsonify({'ok': True, 'results': items})
    results = [x for x in items if q in (x['title'] + ' ' + x['type'] + ' ' + x['description']).lower()]
    return jsonify({'ok': True, 'results': results[:20]})


ADMIN_TEMPLATE = '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ABKNET Admin</title><style>body{font-family:system-ui;background:#06152b;color:#eefaff;padding:30px}table{width:100%;border-collapse:collapse;background:#081c33}th,td{padding:10px;border:1px solid #173c5a;text-align:left;font-size:13px}h1{color:#27f2df}small{color:#8aa5ba}</style></head><body><h1>ABKNET Admin Inbox</h1><small>Private dashboard — protect this endpoint with ADMIN_TOKEN.</small><p>Contacts: {{ contacts|length }} · Subscribers: {{ subscribers|length }} · Feedback: {{ feedback|length }}</p><h2>Contact Messages</h2><table><tr><th>Ticket</th><th>Name</th><th>Email</th><th>Category</th><th>Subject</th><th>Message</th><th>Time</th></tr>{% for c in contacts %}<tr><td>{{c.ticket_id}}</td><td>{{c.name}}</td><td>{{c.email}}</td><td>{{c.category}}</td><td>{{c.subject}}</td><td>{{c.message}}</td><td>{{c.created_at}}</td></tr>{% endfor %}</table><h2>Subscribers</h2><table><tr><th>Email</th><th>Joined</th></tr>{% for s in subscribers %}<tr><td>{{s.email}}</td><td>{{s.created_at}}</td></tr>{% endfor %}</table><h2>Feedback</h2><table><tr><th>Rating</th><th>Message</th><th>Page</th><th>Time</th></tr>{% for f in feedback %}<tr><td>{{f.rating}}/5</td><td>{{f.message}}</td><td>{{f.page}}</td><td>{{f.created_at}}</td></tr>{% endfor %}</table></body></html>'''


@app.get('/admin')
def admin():
    token = request.args.get('token', '')
    expected = os.getenv('ADMIN_TOKEN')
    if not expected or not secrets.compare_digest(token, expected):
        return jsonify({'ok': False, 'error': 'Admin access denied.'}), 403
    db = get_db()
    return render_template_string(ADMIN_TEMPLATE,
        contacts=db.execute('SELECT * FROM contacts ORDER BY id DESC').fetchall(),
        subscribers=db.execute('SELECT * FROM subscribers ORDER BY id DESC').fetchall(),
        feedback=db.execute('SELECT * FROM feedback ORDER BY id DESC').fetchall())


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def static_site(path):
    if path.startswith('api/') or path == 'admin':
        return jsonify({'ok': False, 'error': 'Not found'}), 404
    target = BASE_DIR / path
    if path and target.is_file():
        return send_from_directory(BASE_DIR, path)
    if path and target.is_dir() and (target / 'index.html').is_file():
        return send_from_directory(target, 'index.html')
    return send_from_directory(BASE_DIR, 'index.html')


with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', 5000)), debug=os.getenv('FLASK_DEBUG') == '1')
