import json
import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, request, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = Path(os.getenv("ABKNET_DB", DATA_DIR / "abknet.db"))

PRIMARY_CONTACT_EMAIL = os.getenv("PRIMARY_CONTACT_EMAIL", "abubakarumuhammadumar2026@gmail.com")
SECONDARY_CONTACT_EMAIL = os.getenv("SECONDARY_CONTACT_EMAIL", "muhammadabk2090@gmail.com")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ALLOWED_CATEGORIES = {
    "General",
    "Technical Support",
    "Tool Feedback",
    "Partnership",
    "Business",
    "Bug Report",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def clean(value, max_len=2000):
    if value is None:
        return ""
    text = str(value).strip()
    return text[:max_len]


def using_postgres():
    return bool(os.getenv("DATABASE_URL"))


def get_db():
    if "db" in g:
        return g.db

    if using_postgres():
        import psycopg

        g.db = psycopg.connect(os.environ["DATABASE_URL"])
        g.db.autocommit = True
    else:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app_teardown = None


def app_teardown_appcontext(sender):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def convert_sql_for_db(sql):
    if using_postgres():
        return sql.replace("?", "%s")
    return sql


def execute(sql, params=()):
    db = get_db()
    sql = convert_sql_for_db(sql)
    if using_postgres():
        with db.cursor() as cur:
            cur.execute(sql, params)
            return cur
    return db.execute(sql, params)


def fetchall(sql, params=()):
    db = get_db()
    sql = convert_sql_for_db(sql)
    if using_postgres():
        cur = db.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    cur = db.execute(sql, params)
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetchone(sql, params=()):
    rows = fetchall(sql, params)
    return rows[0] if rows else None


def _create_sqlite_schema(db):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_verified INTEGER NOT NULL DEFAULT 0,
            is_admin INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS email_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS contact_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            category TEXT,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            spam_score INTEGER NOT NULL DEFAULT 0,
            source TEXT DEFAULT 'website'
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL UNIQUE,
            user_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            category TEXT,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'NEW',
            priority TEXT NOT NULL DEFAULT 'NORMAL',
            assigned_admin TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            closed_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS ticket_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            user_id INTEGER,
            author_name TEXT NOT NULL,
            message TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY(ticket_id) REFERENCES support_tickets(ticket_id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            unsubscribed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER NOT NULL,
            category TEXT,
            message TEXT NOT NULL,
            email TEXT,
            page TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS admin_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT NOT NULL,
            target TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL,
            ip_address TEXT,
            FOREIGN KEY(admin_id) REFERENCES admin_users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS saved_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            item_url TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS site_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT,
            updated_at TEXT NOT NULL
        );
        """
    )
    db.commit()


def _create_postgres_schema(db):
    with db.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                last_login TIMESTAMPTZ
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                session_token TEXT NOT NULL UNIQUE,
                created_at TIMESTAMPTZ NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS email_verifications (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token TEXT NOT NULL UNIQUE,
                created_at TIMESTAMPTZ NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                used BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token TEXT NOT NULL UNIQUE,
                created_at TIMESTAMPTZ NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                used BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_messages (
                id BIGSERIAL PRIMARY KEY,
                ticket_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                category TEXT,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                spam_score INTEGER NOT NULL DEFAULT 0,
                source TEXT DEFAULT 'website'
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS support_tickets (
                id BIGSERIAL PRIMARY KEY,
                ticket_id TEXT NOT NULL UNIQUE,
                user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                category TEXT,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'NEW',
                priority TEXT NOT NULL DEFAULT 'NORMAL',
                assigned_admin TEXT,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                closed_at TIMESTAMPTZ
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_replies (
                id BIGSERIAL PRIMARY KEY,
                ticket_id TEXT NOT NULL REFERENCES support_tickets(ticket_id) ON DELETE CASCADE,
                user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
                author_name TEXT NOT NULL,
                message TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL,
                unsubscribed_at TIMESTAMPTZ
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id BIGSERIAL PRIMARY KEY,
                rating INTEGER NOT NULL,
                category TEXT,
                message TEXT NOT NULL,
                email TEXT,
                page TEXT,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL,
                metadata TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_activity (
                id BIGSERIAL PRIMARY KEY,
                admin_id BIGINT REFERENCES admin_users(id) ON DELETE SET NULL,
                action TEXT NOT NULL,
                target TEXT,
                metadata TEXT,
                created_at TIMESTAMPTZ NOT NULL,
                ip_address TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_items (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                item_type TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_url TEXT,
                metadata TEXT,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS site_settings (
                id BIGSERIAL PRIMARY KEY,
                key TEXT NOT NULL UNIQUE,
                value TEXT,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """
        )


def init_db():
    if using_postgres():
        db = get_db()
        _create_postgres_schema(db)
    else:
        db = get_db()
        _create_sqlite_schema(db)
        db.commit()


def create_ticket_id():
    now = datetime.now(timezone.utc)
    return f"ABK-{now.strftime('%Y')}-{now.strftime('%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def create_notification(user_id, notification_type, title, message, metadata=None):
    execute(
        "INSERT INTO notifications(user_id, type, title, message, created_at, metadata) VALUES(?,?,?,?,?,?)",
        (
            user_id,
            notification_type,
            title,
            message,
            now_iso(),
            json.dumps(metadata or {}),
        ),
    )


def create_admin_activity(admin_id, action, target=None, metadata=None, ip_address=None):
    execute(
        "INSERT INTO admin_activity(admin_id, action, target, metadata, created_at, ip_address) VALUES(?,?,?,?,?,?)",
        (
            admin_id,
            action,
            target,
            json.dumps(metadata or {}),
            now_iso(),
            ip_address,
        ),
    )


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return fetchone("SELECT * FROM users WHERE id = ?", (user_id,))


def current_admin_user():
    if session.get("is_admin"):
        user_id = session.get("user_id")
        if user_id:
            return fetchone("SELECT * FROM users WHERE id = ? AND is_admin = 1", (user_id,))
    return None


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"ok": False, "error": "Authentication required."}), 401
        if not user.get("is_active"):
            return jsonify({"ok": False, "error": "This account has been suspended."}), 403
        return f(*args, **kwargs)

    return wrapper


def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-Admin-Token"):
            expected = os.getenv("ADMIN_TOKEN")
            if expected and secrets.compare_digest(request.headers.get("X-Admin-Token"), expected):
                return f(*args, **kwargs)
        if session.get("is_admin"):
            user = current_user()
            if user and user.get("is_admin"):
                return f(*args, **kwargs)
        return jsonify({"ok": False, "error": "Admin access denied."}), 403

    return wrapper


@app = Flask(__name__, static_folder=None)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "https://abknet.work.gd,https://www.abknet.work.gd,https://abk-d-young-coder.github.io,http://127.0.0.1:5000,http://localhost:5000",
    ).split(",")
    if origin.strip()
]
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=True)


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "accelerometer=(), camera=(), geolocation=(), microphone=()")
    if request.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    else:
        response.headers.setdefault("Cache-Control", "public, max-age=300")
    return response


@app.route("/api/health")
def api_health():
    return jsonify({
        "ok": True,
        "service": "ABKNET TECHNOLOGIES API",
        "database": "postgresql" if using_postgres() else "sqlite",
        "timestamp": now_iso(),
    })


@app.route("/api/auth/register", methods=["POST"])
def register_user():
    payload = request.get_json(silent=True) or request.form or {}
    full_name = clean(payload.get("full_name"), 120)
    username = clean(payload.get("username"), 40).lower()
    email = clean(payload.get("email"), 160).lower()
    password = payload.get("password") or ""
    confirm_password = payload.get("confirm_password") or ""

    if not full_name or not username or not email or not password:
        return jsonify({"ok": False, "error": "Full name, username, email and password are required."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"ok": False, "error": "Please provide a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"ok": False, "error": "Password must be at least 8 characters long."}), 400
    if password != confirm_password:
        return jsonify({"ok": False, "error": "Passwords do not match."}), 400
    if re.search(r"\s", username):
        return jsonify({"ok": False, "error": "Username cannot contain spaces."}), 400

    existing = fetchone("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
    if existing:
        return jsonify({"ok": False, "error": "An account with that email or username already exists."}), 409

    user_id = execute(
        "INSERT INTO users(full_name, username, email, password_hash, is_verified, is_admin, is_active, created_at, updated_at) VALUES(?,?,?,?,?,?,?, ?, ?)",
        (
            full_name,
            username,
            email,
            generate_password_hash(password),
            0,
            0,
            1,
            now_iso(),
            now_iso(),
        ),
    )
    user = fetchone("SELECT * FROM users WHERE email = ?", (email,))
    token = uuid.uuid4().hex
    execute(
        "INSERT INTO email_verifications(user_id, token, created_at, expires_at) VALUES(?,?,?,?)",
        (user["id"], token, now_iso(), (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()),
    )
    create_notification(user["id"], "account", "Welcome to ABKNET", "Your account has been created successfully.")

    return jsonify({
        "ok": True,
        "message": "Account created. Please verify your email to activate your account.",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "username": user["username"],
            "email": user["email"],
            "is_verified": bool(user["is_verified"]),
        },
        "verification_token": token,
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login_user():
    payload = request.get_json(silent=True) or request.form or {}
    email = clean(payload.get("email"), 160).lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"ok": False, "error": "Email and password are required."}), 400

    user = fetchone("SELECT * FROM users WHERE email = ?", (email,))
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"ok": False, "error": "Invalid email or password."}), 401
    if not user.get("is_active"):
        return jsonify({"ok": False, "error": "This account is inactive."}), 403

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session.permanent = True
    execute("UPDATE users SET last_login = ?, updated_at = ? WHERE id = ?", (now_iso(), now_iso(), user["id"]))

    return jsonify({
        "ok": True,
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "username": user["username"],
            "email": user["email"],
            "is_verified": bool(user["is_verified"]),
            "is_admin": bool(user["is_admin"]),
        },
    })


@app.route("/api/auth/admin-login", methods=["POST"])
def admin_login():
    payload = request.get_json(silent=True) or request.form or {}
    secret = payload.get("secret") or ""
    expected = os.getenv("ADMIN_SECRET") or os.getenv("ADMIN_TOKEN")
    if not expected or not secret or not secrets.compare_digest(secret, expected):
        return jsonify({"ok": False, "error": "Invalid admin credentials."}), 401

    user = fetchone("SELECT * FROM users WHERE is_admin = 1 LIMIT 1")
    if not user:
        # Create a fallback admin if one doesn't exist yet
        username = "admin"
        email = PRIMARY_CONTACT_EMAIL
        password_hash = generate_password_hash(secret)
        execute(
            "INSERT INTO users(full_name, username, email, password_hash, is_verified, is_admin, is_active, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
            ("System Administrator", username, email, password_hash, 1, 1, 1, now_iso(), now_iso()),
        )
        user = fetchone("SELECT * FROM users WHERE email = ?", (email,))

    session["user_id"] = user["id"]
    session["is_admin"] = True
    session["username"] = user["username"]

    return jsonify({"ok": True, "message": "Admin login successful.", "user": {"id": user["id"], "username": user["username"], "is_admin": True}})


@app.route("/api/auth/logout", methods=["POST"])
def logout_user():
    session.clear()
    return jsonify({"ok": True, "message": "Logged out successfully."})


@app.route("/api/auth/verify-email", methods=["POST"])
def verify_email():
    payload = request.get_json(silent=True) or request.form or {}
    token = clean(payload.get("token"), 200)
    if not token:
        return jsonify({"ok": False, "error": "Verification token is required."}), 400

    record = fetchone("SELECT * FROM email_verifications WHERE token = ? AND used = 0", (token,))
    if not record:
        return jsonify({"ok": False, "error": "Verification token is invalid or already used."}), 400

    user = fetchone("SELECT * FROM users WHERE id = ?", (record["user_id"],))
    if not user:
        return jsonify({"ok": False, "error": "User not found."}), 404

    execute("UPDATE users SET is_verified = 1, updated_at = ? WHERE id = ?", (now_iso(), user["id"]))
    execute("UPDATE email_verifications SET used = 1 WHERE token = ?", (token,))
    return jsonify({"ok": True, "message": "Email verified successfully."})


@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    payload = request.get_json(silent=True) or request.form or {}
    email = clean(payload.get("email"), 160).lower()
    if not email:
        return jsonify({"ok": False, "error": "Email is required."}), 400

    user = fetchone("SELECT * FROM users WHERE email = ?", (email,))
    if not user:
        return jsonify({"ok": True, "message": "If that account exists, a reset email will be sent."})

    token = uuid.uuid4().hex
    execute(
        "INSERT INTO password_resets(user_id, token, created_at, expires_at) VALUES(?,?,?,?)",
        (user["id"], token, now_iso(), (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()),
    )
    return jsonify({"ok": True, "message": "If that account exists, a reset email will be sent.", "token": token})


@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    payload = request.get_json(silent=True) or request.form or {}
    token = clean(payload.get("token"), 200)
    password = payload.get("password") or ""
    confirm_password = payload.get("confirm_password") or ""

    if not token or not password:
        return jsonify({"ok": False, "error": "Token and password are required."}), 400
    if len(password) < 8:
        return jsonify({"ok": False, "error": "Password must be at least 8 characters long."}), 400
    if password != confirm_password:
        return jsonify({"ok": False, "error": "Passwords do not match."}), 400

    record = fetchone("SELECT * FROM password_resets WHERE token = ? AND used = 0", (token,))
    if not record:
        return jsonify({"ok": False, "error": "Reset token is invalid or has already been used."}), 400

    execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", (generate_password_hash(password), now_iso(), record["user_id"]))
    execute("UPDATE password_resets SET used = 1 WHERE token = ?", (token,))
    return jsonify({"ok": True, "message": "Password reset successful."})


@app.route("/api/users/me")
@require_auth
def get_current_user():
    user = current_user()
    return jsonify({
        "ok": True,
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "username": user["username"],
            "email": user["email"],
            "is_verified": bool(user["is_verified"]),
            "is_admin": bool(user["is_admin"]),
            "is_active": bool(user["is_active"]),
            "created_at": user["created_at"],
        },
    })


@app.route("/api/users/me", methods=["PUT"])
@require_auth
def update_current_user():
    payload = request.get_json(silent=True) or request.form or {}
    full_name = clean(payload.get("full_name"), 120)
    username = clean(payload.get("username"), 40).lower()
    user = current_user()

    if full_name:
        execute("UPDATE users SET full_name = ?, updated_at = ? WHERE id = ?", (full_name, now_iso(), user["id"]))
    if username:
        dup = fetchone("SELECT id FROM users WHERE username = ? AND id != ?", (username, user["id"]))
        if dup:
            return jsonify({"ok": False, "error": "That username is already taken."}), 409
        execute("UPDATE users SET username = ?, updated_at = ? WHERE id = ?", (username, now_iso(), user["id"]))

    return jsonify({"ok": True, "message": "Profile updated successfully."})


@app.route("/api/users/me/password", methods=["PUT"])
@require_auth
def update_password():
    payload = request.get_json(silent=True) or request.form or {}
    current_password = payload.get("current_password") or ""
    new_password = payload.get("new_password") or ""
    confirm_password = payload.get("confirm_password") or ""
    user = current_user()

    if not check_password_hash(user["password_hash"], current_password):
        return jsonify({"ok": False, "error": "Current password is incorrect."}), 401
    if len(new_password) < 8:
        return jsonify({"ok": False, "error": "New password must be at least 8 characters long."}), 400
    if new_password != confirm_password:
        return jsonify({"ok": False, "error": "Passwords do not match."}), 400

    execute("UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?", (generate_password_hash(new_password), now_iso(), user["id"]))
    return jsonify({"ok": True, "message": "Password updated successfully."})


@app.route("/api/users/me", methods=["DELETE"])
@require_auth
def delete_current_user():
    user = current_user()
    execute("DELETE FROM users WHERE id = ?", (user["id"],))
    session.clear()
    return jsonify({"ok": True, "message": "Account deleted successfully."})


@app.route("/api/contact", methods=["POST"])
def submit_contact():
    payload = request.get_json(silent=True) or request.form or {}
    name = clean(payload.get("name"), 120)
    email = clean(payload.get("email"), 160).lower()
    phone = clean(payload.get("phone"), 30)
    category = clean(payload.get("category"), 60)
    subject = clean(payload.get("subject"), 200)
    message = clean(payload.get("message"), 5000)
    extra = clean(payload.get("website") or payload.get("url") or "", 200)
    if extra:
        return jsonify({"ok": True, "message": "Message received."})

    if not name or not EMAIL_RE.match(email) or not subject or not message:
        return jsonify({"ok": False, "error": "Name, valid email, subject and message are required."}), 400
    if category and category not in ALLOWED_CATEGORIES:
        return jsonify({"ok": False, "error": "Invalid category."}), 400

    ticket_id = create_ticket_id()
    execute(
        "INSERT INTO contact_messages(ticket_id, name, email, phone, category, subject, message, status, created_at, updated_at, source) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (ticket_id, name, email, phone or None, category or "General", subject, message, "new", now_iso(), now_iso(), "website"),
    )
    execute(
        "INSERT INTO support_tickets(ticket_id, user_id, name, email, subject, category, message, status, priority, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (ticket_id, None, name, email, subject, category or "General", message, "NEW", "NORMAL", now_iso(), now_iso()),
    )

    return jsonify({
        "ok": True,
        "message": "Your message has been received.",
        "ticket_id": ticket_id,
    }), 201


@app.route("/api/contact")
@require_admin
def list_contact_messages():
    rows = fetchall("SELECT * FROM contact_messages ORDER BY id DESC LIMIT 200")
    return jsonify({"ok": True, "messages": rows})


@app.route("/api/newsletter", methods=["POST"])
def subscribe_newsletter():
    payload = request.get_json(silent=True) or request.form or {}
    email = clean(payload.get("email"), 160).lower()
    if not EMAIL_RE.match(email):
        return jsonify({"ok": False, "error": "Please provide a valid email address."}), 400

    try:
        execute("INSERT INTO newsletter_subscribers(email, is_active, created_at) VALUES(?,?,?)", (email, 1, now_iso()))
    except Exception:
        return jsonify({"ok": True, "message": "This email is already subscribed."})

    return jsonify({"ok": True, "message": "You are subscribed to ABKNET updates."}), 201


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    payload = request.get_json(silent=True) or request.form or {}
    try:
        rating = int(payload.get("rating", 0))
    except (TypeError, ValueError):
        rating = 0
    category = clean(payload.get("category"), 40)
    message = clean(payload.get("message"), 2000)
    email = clean(payload.get("email"), 160).lower()
    page = clean(payload.get("page"), 300)

    if rating not in range(1, 6) or not message:
        return jsonify({"ok": False, "error": "Provide a rating from 1 to 5 and a brief message."}), 400

    execute(
        "INSERT INTO feedback(rating, category, message, email, page, created_at) VALUES(?,?,?,?,?,?)",
        (rating, category or "General", message, email or None, page or None, now_iso()),
    )
    return jsonify({"ok": True, "message": "Thank you for the feedback."}), 201


@app.route("/api/tickets", methods=["POST"])
@require_auth
def create_ticket():
    payload = request.get_json(silent=True) or request.form or {}
    subject = clean(payload.get("subject"), 200)
    message = clean(payload.get("message"), 5000)
    category = clean(payload.get("category"), 60)
    user = current_user()

    if not subject or not message:
        return jsonify({"ok": False, "error": "Subject and message are required."}), 400

    ticket_id = create_ticket_id()
    execute(
        "INSERT INTO support_tickets(ticket_id, user_id, name, email, subject, category, message, status, priority, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            ticket_id,
            user["id"],
            user["full_name"],
            user["email"],
            subject,
            category or "General",
            message,
            "NEW",
            "NORMAL",
            now_iso(),
            now_iso(),
        ),
    )
    create_notification(user["id"], "ticket", "Ticket created", f"Your ticket {ticket_id} has been received.")
    return jsonify({"ok": True, "ticket_id": ticket_id, "message": "Ticket created successfully."}), 201


@app.route("/api/tickets")
@require_auth
def list_tickets():
    user = current_user()
    if user.get("is_admin"):
        rows = fetchall("SELECT * FROM support_tickets ORDER BY id DESC LIMIT 200")
    else:
        rows = fetchall("SELECT * FROM support_tickets WHERE user_id = ? ORDER BY id DESC", (user["id"],))
    return jsonify({"ok": True, "tickets": rows})


@app.route("/api/tickets/<ticket_id>")
@require_auth
def get_ticket(ticket_id):
    user = current_user()
    ticket = fetchone("SELECT * FROM support_tickets WHERE ticket_id = ?", (ticket_id,))
    if not ticket:
        return jsonify({"ok": False, "error": "Ticket not found."}), 404
    if not user.get("is_admin") and ticket["user_id"] != user["id"]:
        return jsonify({"ok": False, "error": "Access denied."}), 403

    replies = fetchall("SELECT * FROM ticket_replies WHERE ticket_id = ? ORDER BY id ASC", (ticket_id,))
    return jsonify({"ok": True, "ticket": ticket, "replies": replies})


@app.route("/api/tickets/<ticket_id>/replies", methods=["POST"])
@require_auth
def add_ticket_reply(ticket_id):
    payload = request.get_json(silent=True) or request.form or {}
    message = clean(payload.get("message"), 3000)
    if not message:
        return jsonify({"ok": False, "error": "Reply message is required."}), 400

    user = current_user()
    ticket = fetchone("SELECT * FROM support_tickets WHERE ticket_id = ?", (ticket_id,))
    if not ticket:
        return jsonify({"ok": False, "error": "Ticket not found."}), 404
    if not user.get("is_admin") and ticket["user_id"] != user["id"]:
        return jsonify({"ok": False, "error": "Access denied."}), 403

    execute(
        "INSERT INTO ticket_replies(ticket_id, user_id, author_name, message, is_admin, created_at) VALUES(?,?,?,?,?,?)",
        (ticket_id, user["id"], user["full_name"], message, 1 if user.get("is_admin") else 0, now_iso()),
    )
    execute("UPDATE support_tickets SET updated_at = ?, status = ? WHERE ticket_id = ?", (now_iso(), "OPEN" if ticket["status"] == "NEW" else ticket["status"], ticket_id))
    return jsonify({"ok": True, "message": "Reply added successfully."})


@app.route("/api/notifications")
@require_auth
def get_notifications():
    user = current_user()
    rows = fetchall("SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC LIMIT 200", (user["id"],))
    return jsonify({"ok": True, "notifications": rows})


@app.route("/api/notifications/<notification_id>/read", methods=["PUT"])
@require_auth
def mark_notification_read(notification_id):
    user = current_user()
    execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notification_id, user["id"]))
    return jsonify({"ok": True, "message": "Notification marked as read."})


@app.route("/api/admin/dashboard")
@require_admin
def admin_dashboard():
    summary = {
        "total_users": fetchone("SELECT COUNT(*) AS count FROM users")["count"],
        "active_users": fetchone("SELECT COUNT(*) AS count FROM users WHERE is_active = 1")["count"],
        "new_users": fetchone("SELECT COUNT(*) AS count FROM users WHERE created_at >= ?", ((datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),))["count"],
        "open_tickets": fetchone("SELECT COUNT(*) AS count FROM support_tickets WHERE status NOT IN ('RESOLVED','CLOSED')")["count"],
        "new_contact_messages": fetchone("SELECT COUNT(*) AS count FROM contact_messages WHERE created_at >= ?", ((datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),))["count"],
        "newsletter_subscribers": fetchone("SELECT COUNT(*) AS count FROM newsletter_subscribers WHERE is_active = 1")["count"],
        "feedback_count": fetchone("SELECT COUNT(*) AS count FROM feedback")["count"],
        "database_status": "healthy",
        "backend_status": "online",
    }
    return jsonify({"ok": True, "summary": summary})


@app.route("/api/admin/users")
@require_admin
def admin_users():
    rows = fetchall("SELECT id, full_name, username, email, is_verified, is_admin, is_active, created_at FROM users ORDER BY id DESC LIMIT 200")
    return jsonify({"ok": True, "users": rows})


@app.route("/api/admin/tickets")
@require_admin
def admin_tickets():
    rows = fetchall("SELECT * FROM support_tickets ORDER BY id DESC LIMIT 200")
    return jsonify({"ok": True, "tickets": rows})


@app.route("/api/admin/messages")
@require_admin
def admin_messages():
    rows = fetchall("SELECT * FROM contact_messages ORDER BY id DESC LIMIT 200")
    return jsonify({"ok": True, "messages": rows})


@app.route("/api/admin/activity")
@require_admin
def admin_activity():
    rows = fetchall("SELECT * FROM admin_activity ORDER BY id DESC LIMIT 200")
    return jsonify({"ok": True, "activity": rows})


@app.route("/api/search")
def search_api():
    q = clean(request.args.get("q"), 80).lower()
    items = [
        {"title": "JSON Formatter", "type": "Tool", "url": "/tools/json-formatter.html", "description": "Format and validate JSON."},
        {"title": "QR Generator", "type": "Tool", "url": "/tools/qr-generator.html", "description": "Create QR codes."},
        {"title": "Password Generator", "type": "Tool", "url": "/tools/password-generator.html", "description": "Generate strong passwords."},
        {"title": "Word Counter", "type": "Tool", "url": "/tools/word-counter.html", "description": "Count text statistics."},
        {"title": "Unit Converter", "type": "Tool", "url": "/tools/unit-converter.html", "description": "Convert common units."},
        {"title": "HTML First Website", "type": "Tutorial", "url": "/tutorials/html-first-website.html", "description": "Learn HTML foundations."},
        {"title": "JavaScript Interactivity", "type": "Tutorial", "url": "/tutorials/javascript-interactivity.html", "description": "Add interactivity."},
        {"title": "Python Basics", "type": "Tutorial", "url": "/tutorials/python-basics.html", "description": "Learn practical Python."},
        {"title": "Services", "type": "Service", "url": "/services/index.html", "description": "Technology services and support."},
        {"title": "Blog", "type": "Article", "url": "/blog/index.html", "description": "ABKNET technology articles."},
    ]
    if not q:
        return jsonify({"ok": True, "results": items[:10]})
    filtered = [item for item in items if q in (item["title"] + " " + item["type"] + " " + item["description"]).lower()]
    return jsonify({"ok": True, "results": filtered[:20]})


@app.route("/api/contact-info")
def contact_info():
    return jsonify({"ok": True, "primary": PRIMARY_CONTACT_EMAIL, "secondary": SECONDARY_CONTACT_EMAIL})


@app.route("/admin")
def admin_panel():
    if request.headers.get("X-Admin-Token"):
        expected = os.getenv("ADMIN_TOKEN")
        if expected and secrets.compare_digest(request.headers.get("X-Admin-Token"), expected):
            return jsonify({"ok": True, "message": "Admin API access granted."})
    if session.get("is_admin"):
        return jsonify({"ok": True, "message": "Admin session active."})
    return jsonify({"ok": False, "error": "Admin access denied. Use X-Admin-Token or session admin login."}), 403


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static(path):
    if path.startswith("api/"):
        return jsonify({"ok": False, "error": "Not found."}), 404
    if path == "admin":
        return admin_panel()

    candidate = BASE_DIR / path
    if path and candidate.is_file():
        return send_from_directory(BASE_DIR, path)
    if path and candidate.is_dir() and (candidate / "index.html").exists():
        return send_from_directory(candidate, "index.html")
    if not path:
        return send_from_directory(BASE_DIR, "index.html")
    return send_from_directory(BASE_DIR, "404.html")


with app.app_context():
    init_db()


app = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG") == "1")
