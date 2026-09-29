"""Local authentication API. Run with: python3 backend/server.py."""
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

DB_PATH = Path(os.environ.get('DATABASE_PATH', Path(__file__).with_name('auth.db')))
SESSION_SECONDS = 86400


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def initialize():
    with connect() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                expires INTEGER NOT NULL
            );
        ''')


def hash_password(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, cookie=None):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie is not None:
            secure = '; Secure' if os.environ.get('COOKIE_SECURE') == '1' else ''
            self.send_header('Set-Cookie', f'session={cookie}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_SECONDS if cookie else 0}{secure}')
        self.end_headers()
        self.wfile.write(payload)

    def session_token(self):
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get('Cookie', ''))
            return cookies['session'].value if 'session' in cookies else ''
        except Exception:
            return ''

    def do_GET(self):
        if self.path != '/api/me':
            self.reply(404, {'error': 'Not found.'})
            return
        with connect() as db:
            user = db.execute('''SELECT name, email FROM users JOIN sessions ON users.id = sessions.user_id
                WHERE token_hash = ? AND expires > ?''', (token_hash(self.session_token()), time.time())).fetchone()
        self.reply(200, {'user': dict(user) if user else None})

    
    def do_POST(self):
        origin = self.headers.get('Origin')
        if (origin and urlsplit(origin).netloc != self.headers.get('Host')) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
            self.reply(403, {'error': 'Request origin is not allowed.'})
            return
        if self.path not in ('/api/login', '/api/register', '/api/logout'):
            self.reply(404, {'error': 'Not found.'})
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                raise ValueError()
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise ValueError()
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError()
        except (ValueError, UnicodeDecodeError):
            self.reply(400, {'error': 'Please send a valid JSON request (up to 4 KB).'})
            return
        with connect() as db:
            if self.path == '/api/logout':
                db.execute('DELETE FROM sessions WHERE token_hash = ?', (token_hash(self.session_token()),))
                self.reply(200, {'ok': True}, cookie='')
                return
            email, password = data.get('email'), data.get('password')
            if not isinstance(email, str) or not isinstance(password, str):
                self.reply(400, {'error': 'Email and password are required.'})
                return
            email = email.strip().lower()
            if len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or not 1 <= len(password) <= 128:
                self.reply(400, {'error': 'Enter a valid email and a password of up to 128 characters.'})
                return
            if self.path == '/api/register':
                name = data.get('name')
                if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100 or len(password) < 8:
                    self.reply(400, {'error': 'Enter your name and a password of at least 8 characters.'})
                    return
                salt = secrets.token_hex(16)
                try:
                    db.execute('INSERT INTO users (name, email, salt, password_hash) VALUES (?, ?, ?, ?)',
                               (name.strip(), email, salt, hash_password(password, salt)))
                except sqlite3.IntegrityError:
                    self.reply(409, {'error': 'An account with this email already exists. Please sign in.'})
                    return
            user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            candidate = hash_password(password, user['salt'] if user else '00' * 16)
            if user is None or not hmac.compare_digest(candidate, user['password_hash']):
                self.reply(401, {'error': 'Email or password is incorrect.'})
                return
            token = secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires <= ? OR token_hash = ?', (time.time(), token_hash(self.session_token())))
            db.execute('INSERT INTO sessions VALUES (?, ?, ?)', (token_hash(token), user['id'], int(time.time()) + SESSION_SECONDS))
            db.commit()
            self.reply(201 if self.path == '/api/register' else 200,
                       {'user': {'name': user['name'], 'email': user['email']}}, cookie=token)


if __name__ == '__main__':
    initialize()
    server = ThreadingHTTPServer(('127.0.0.1', int(os.environ.get('PORT', '8000'))), Handler)
    print(f'Authentication API running at http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
