from contextlib import closing
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
from http.cookies import SimpleCookie, CookieError
from pathlib import Path
import json
import ipaddress
import os
import re
import secrets
import sqlite3
import time
import urllib.error
import urllib.request
import database
import uuid

try:
    import psycopg
except ImportError:  # SQLite-only local installs can run without the optional driver.
    psycopg = None

DB = Path(__file__).with_name('accounts.sqlite3')
ROLES = {
    'Creator': ('Team or organization', 'Job title', 'What content do you create?'),
    'External Agency': ('Agency name', 'Job title', 'Which clients or campaigns do you work on?'),
    'Reviewer': ('Team or organization', 'Review specialty', 'What types of content do you review?'),
    'Brand Manager': ('Organization', 'Brand or portfolio', 'Which guidelines do you manage?'),
}
SESSION_AGE = 86400
OTP_TTL = 600
def connect():
    if database.uses_postgres():
        return database.connect()
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS accounts (
      username TEXT PRIMARY KEY COLLATE NOCASE, email TEXT UNIQUE COLLATE NOCASE NOT NULL,
      name TEXT NOT NULL, role TEXT NOT NULL, organization TEXT NOT NULL,
      work TEXT NOT NULL, responsibilities TEXT NOT NULL, salt BLOB NOT NULL, password_hash BLOB NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
      token BLOB PRIMARY KEY, username TEXT NOT NULL, expires INTEGER NOT NULL,
      active_company_id TEXT
    );
    CREATE TABLE IF NOT EXISTS email_verifications (
      email TEXT PRIMARY KEY COLLATE NOCASE,
      code_hash BLOB NOT NULL,
      salt BLOB NOT NULL,
      expires INTEGER NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0,
      verified_until INTEGER NOT NULL DEFAULT 0,
      last_sent INTEGER NOT NULL,
      send_window INTEGER NOT NULL,
      sends_in_window INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS login_failures (
      ip TEXT NOT NULL,
      attempted_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS companies (
      id TEXT PRIMARY KEY, name TEXT NOT NULL, owner_username TEXT NOT NULL,
      created_at INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS company_memberships (
      company_id TEXT NOT NULL, username TEXT NOT NULL, role TEXT NOT NULL,
      joined_at INTEGER NOT NULL, PRIMARY KEY(company_id, username)
    );
    CREATE TABLE IF NOT EXISTS company_invitations (
      code_hash BLOB PRIMARY KEY, company_id TEXT NOT NULL,
      email TEXT NOT NULL COLLATE NOCASE, role TEXT NOT NULL,
      expires INTEGER NOT NULL, created_by TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS password_resets (
      email TEXT PRIMARY KEY COLLATE NOCASE,
      code_hash BLOB NOT NULL,
      salt BLOB NOT NULL,
      expires INTEGER NOT NULL,
      attempts INTEGER NOT NULL DEFAULT 0,
      last_sent INTEGER NOT NULL,
      send_window INTEGER NOT NULL,
      sends_in_window INTEGER NOT NULL DEFAULT 1
    );
    """)
    columns = {row['name'] for row in db.execute('PRAGMA table_info(sessions)').fetchall()}
    if 'active_company_id' not in columns:
        db.execute('ALTER TABLE sessions ADD COLUMN active_company_id TEXT')
    return db

LOGIN_WINDOW_SECONDS = 900
LOGIN_MAX_FAILURES = 5
LOGIN_LOCK_SECONDS = 300

def login_is_limited(client_ip):
    now = int(time.time())
    cutoff = now - LOGIN_WINDOW_SECONDS
    client_ip = ipaddress.ip_address(client_ip).compressed
    with closing(connect()) as db, db:
        db.execute("DELETE FROM login_failures WHERE attempted_at < ?", (cutoff,))
        row = db.execute(
            "SELECT COUNT(*) AS total, MAX(attempted_at) AS latest FROM login_failures WHERE ip = ? AND attempted_at >= ?",
            (client_ip, cutoff),
        ).fetchone()
        total = row['total'] if row else 0
        latest = row['latest'] if row else None
        if total >= LOGIN_MAX_FAILURES and latest and now - latest < LOGIN_LOCK_SECONDS:
            return True
        if total >= LOGIN_MAX_FAILURES:
            db.execute("DELETE FROM login_failures WHERE ip = ?", (client_ip,))
        return False

def record_login_failure(client_ip):
    now = int(time.time())
    client_ip = ipaddress.ip_address(client_ip).compressed
    with closing(connect()) as db, db:
        db.execute("INSERT INTO login_failures (ip, attempted_at) VALUES (?, ?)", (client_ip, now))

def clear_login_failures(client_ip):
    client_ip = ipaddress.ip_address(client_ip).compressed
    with closing(connect()) as db, db:
        db.execute("DELETE FROM login_failures WHERE ip = ?", (client_ip,))

def migrate_local_accounts():
    """Copy local account records to a new Neon database without copying sessions or OTPs."""
    if not database.uses_postgres() or not DB.exists():
        return 0
    with closing(sqlite3.connect(DB)) as local:
        local.row_factory = sqlite3.Row
        rows = local.execute(
            "SELECT username, email, name, role, organization, work, responsibilities, salt, password_hash FROM accounts"
        ).fetchall()
    if not rows:
        return 0
    with closing(database.connect()) as remote, remote:
        count = remote.execute("SELECT count(*) AS total FROM accounts").fetchone()["total"]
        if count:
            return 0
        for row in rows:
            remote.execute(
                "INSERT INTO accounts (username, email, name, role, organization, work, responsibilities, salt, password_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
                tuple(row),
            )
        return len(rows)


def _is_integrity_error(exc):
    return isinstance(exc, sqlite3.IntegrityError) or bool(
        psycopg and isinstance(exc, psycopg.IntegrityError)
    )

def digest(password, salt):
    return pbkdf2_hmac('sha256', password.encode(), salt, 600000)

def normalize_email(value):
    if not isinstance(value, str):
        raise ValueError('Enter a valid email address.')
    email = value.strip().casefold()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 254:
        raise ValueError('Enter a valid email address.')
    return email

def is_local_dev(client_ip=None):
    """Permit lockout bypass only for explicitly configured loopback development."""
    if os.environ.get('RENDER') or os.environ.get('BRANDWISE_ENV', '').strip().casefold() != 'development':
        return False
    try:
        return bool(client_ip) and ipaddress.ip_address(client_ip).is_loopback
    except ValueError:
        return False

def _require_fresh_firebase_link(id_token):
    """Accept only a recently authenticated, verified Firebase email identity."""
    identity = firebase_user_from_token(id_token)
    if not identity['email_verified']:
        raise ValueError('Open the Firebase verification link before continuing.')
    # accounts:lookup validates the token; auth_time prevents reusing an older
    # signed-in Firebase session for a sensitive BrandWise account change.
    try:
        body = id_token.split('.')[1]
        import base64
        claims = json.loads(base64.urlsafe_b64decode(body + '=' * (-len(body) % 4)))
        auth_time = int(claims.get('auth_time', 0))
    except (IndexError, ValueError, TypeError, UnicodeError) as exc:
        raise ValueError('Open a fresh Firebase verification link and try again.') from exc
    if not 0 <= int(time.time()) - auth_time <= 600:
        raise ValueError('That verification is too old. Request a new email link.')
    return identity


def reset_password_with_firebase_token(id_token, new_password):
    """Reset a custom BrandWise password after Firebase verifies email ownership."""
    identity = _require_fresh_firebase_link(id_token)
    if not isinstance(new_password, str) or not 4 <= len(new_password) <= 128:
        raise ValueError('Use a new password between 4 and 128 characters.')
    email = identity['email']
    with closing(connect()) as db, db:
        account = db.execute('SELECT username FROM accounts WHERE lower(email)=lower(?)', (email,)).fetchone()
        if not account:
            raise ValueError('No BrandWise account uses this email.')
        salt = secrets.token_bytes(16)
        db.execute('UPDATE accounts SET salt=?, password_hash=? WHERE username=?',
                   (salt, digest(new_password, salt), account['username']))
        db.execute('DELETE FROM sessions WHERE username=?', (account['username'],))
        db.execute('DELETE FROM password_resets WHERE email=?', (email,))
    return True


def verify_profile_email_with_firebase_token(headers, id_token):
    """Authorize a profile email change using Firebase's verified email link."""
    if not current_user(headers):
        raise ValueError('Sign in before changing your profile email.')
    identity = _require_fresh_firebase_link(id_token)
    now = int(time.time())
    with closing(connect()) as db, db:
        db.execute('INSERT INTO email_verifications (email, salt, code_hash, expires, attempts, verified_until, last_sent, send_window, sends_in_window) VALUES (?, ?, ?, ?, 0, ?, ?, ?, 0) ON CONFLICT(email) DO UPDATE SET verified_until=excluded.verified_until',
                   (identity['email'], b'', b'', now + OTP_TTL, now + OTP_TTL, now, now))
    return identity['email']

def register(data):
    fields = ('username', 'email', 'name', 'role', 'organization', 'work', 'responsibilities', 'password')
    if any(not isinstance(data.get(field), str) for field in fields):
        raise ValueError('Complete all registration fields.')
    username, email, name, role, organization, work, responsibilities = (data[field].strip() for field in fields[:-1])
    password = data['password']
    if not re.fullmatch(r'[A-Za-z0-9_]{3,32}', username):
        raise ValueError('Use 3 to 32 letters, numbers, or underscores for your username.')
    email = normalize_email(email)
    if role not in ROLES or any(not value or len(value) > 500 for value in (name, organization, work, responsibilities)):
        raise ValueError('Complete the profile questions and select a role.')
    if not 4 <= len(password) <= 128:
        raise ValueError('Use a password between 4 and 128 characters.')
    if username.casefold() == 'admin':
        raise ValueError('That username is reserved.')
    salt = secrets.token_bytes(16)
    try:
        with closing(connect()) as db, db:
            verification = db.execute('SELECT verified_until FROM email_verifications WHERE email = ?', (email,)).fetchone()
            if not verification or verification['verified_until'] < int(time.time()):
                raise ValueError('Verify your email address before creating the account.')
            db.execute('INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (username, email, name, role, organization, work, responsibilities, salt, digest(password, salt)))
            db.execute('DELETE FROM email_verifications WHERE email = ?', (email,))
            token = secrets.token_urlsafe(32)
            now = int(time.time())
            db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
            db.execute('INSERT INTO sessions (token, username, expires, active_company_id) VALUES (?, ?, ?, NULL)',
                       (sha256(token.encode()).digest(), username, now + SESSION_AGE))
    except Exception as exc:
        if _is_integrity_error(exc):
            raise ValueError('That username or email is already registered.') from None
        raise
    return token

def firebase_user_from_token(id_token):
    """Validate a Firebase ID token through Identity Toolkit (no service key needed)."""
    api_key = os.environ.get('FIREBASE_API_KEY', 'AIzaSyB5ZWrXltQKygEcdeED10Q9vkIpdQn8CMk').strip()
    if not isinstance(id_token, str) or not id_token or len(id_token) > 8192:
        raise ValueError('Sign in again with Firebase and retry.')
    request = urllib.request.Request(
        f'https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}',
        data=json.dumps({'idToken': id_token}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read(65536).decode('utf-8'))
        users = payload.get('users') or []
        if not users:
            raise ValueError('Firebase did not return a signed-in user.')
        user = users[0]
        return {'uid': user.get('localId'), 'email': normalize_email(user.get('email')), 'email_verified': bool(user.get('emailVerified'))}
    except urllib.error.HTTPError as exc:
        raise ValueError('Firebase session expired or invalid. Sign in again.') from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ValueError('Could not reach Firebase to verify your sign-in. Try again.') from exc

def firebase_register(data):
    fields = ('username', 'name', 'role', 'organization', 'work', 'responsibilities')
    if not isinstance(data, dict) or any(not isinstance(data.get(field), str) for field in fields):
        raise ValueError('Complete all registration fields.')
    identity = firebase_user_from_token(data.get('idToken'))
    if not identity['email_verified']:
        raise ValueError('Verify your email from the Firebase email before registering.')
    clean = dict(data)
    clean['email'] = identity['email']
    clean['password'] = data.get('password')
    username, name, role, organization, work, responsibilities = (clean[field].strip() for field in fields)
    email = clean['email']
    if not re.fullmatch(r'[A-Za-z0-9_]{3,32}', username):
        raise ValueError('Use 3 to 32 letters, numbers, or underscores for your username.')
    if role not in ROLES or any(not value or len(value) > 500 for value in (name, organization, work, responsibilities)):
        raise ValueError('Complete the profile questions and select a role.')
    if not isinstance(clean['password'], str) or not 4 <= len(clean['password']) <= 128:
        raise ValueError('Use a password between 4 and 128 characters.')
    if username.casefold() == 'admin':
        raise ValueError('That username is reserved.')
    salt = secrets.token_bytes(16)
    try:
        with closing(connect()) as db, db:
            # A retry after the profile row committed must restore a session, not strand
            # the verified owner with an 'already registered' error. Firebase's verified
            # token proves ownership of this email; retain the existing profile as-is.
            existing = db.execute('SELECT username FROM accounts WHERE lower(email)=lower(?)', (email,)).fetchone()
            if existing:
                username = existing['username']
            else:
                db.execute('INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           (username, email, name, role, organization, work, responsibilities, salt, digest(clean['password'], salt)))
            token = secrets.token_urlsafe(32)
            now = int(time.time())
            db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
            db.execute('INSERT INTO sessions (token, username, expires, active_company_id) VALUES (?, ?, ?, NULL)',
                       (sha256(token.encode()).digest(), username, now + SESSION_AGE))
    except Exception as exc:
        if _is_integrity_error(exc):
            raise ValueError('That username or email is already registered.') from None
        raise
    return token

def firebase_session(id_token, password=None):
    identity = firebase_user_from_token(id_token)
    if not identity['email_verified']:
        raise ValueError('Verify your email address before signing in.')
    if password is not None and (not isinstance(password, str) or not 4 <= len(password) <= 128):
        raise ValueError('Use a password between 4 and 128 characters.')
    with closing(connect()) as db, db:
        row = db.execute('SELECT username FROM accounts WHERE lower(email)=lower(?)', (identity['email'],)).fetchone()
        if not row:
            raise ValueError('No BrandWise profile is registered for this email. Create an account first.')
        if password is not None:
            # Older Firebase-backed profiles received a random local password.
            # After Firebase verifies the same email and password, migrate that
            # credential so normal BrandWise login works on the next sign-in.
            salt = secrets.token_bytes(16)
            db.execute('UPDATE accounts SET salt=?, password_hash=? WHERE username=?',
                       (salt, digest(password, salt), row['username']))
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
        db.execute('INSERT INTO sessions (token, username, expires, active_company_id) VALUES (?, ?, ?, NULL)',
                   (sha256(token.encode()).digest(), row['username'], now + SESSION_AGE))
    return token

def email_for_login(identifier):
    if not isinstance(identifier, str) or len(identifier) > 254:
        return None
    with closing(connect()) as db:
        row = db.execute('SELECT email FROM accounts WHERE lower(username)=lower(?) OR lower(email)=lower(?)',
                         (identifier.strip(), identifier.strip())).fetchone()
        return row['email'] if row else None

def login(data):
    identifier, password = data.get('username'), data.get('password')
    if not isinstance(identifier, str) or not isinstance(password, str) or len(identifier) > 254 or len(password) > 128:
        return None
    with closing(connect()) as db, db:
        identifier = identifier.strip()
        row = db.execute(
            'SELECT * FROM accounts WHERE lower(username) = lower(?) OR lower(email) = lower(?)',
            (identifier, identifier),
        ).fetchone()
        hashed = digest(password, row['salt'] if row else bytes(16))
        if not row or not compare_digest(hashed, row['password_hash']):
            return None
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
        db.execute('INSERT INTO sessions (token, username, expires, active_company_id) VALUES (?, ?, ?, NULL)', (sha256(token.encode()).digest(), row['username'], now + SESSION_AGE))
        return token

def cookie_token(headers):
    try:
        cookie = SimpleCookie(headers.get('Cookie', '')).get('brandwise_session')
        return sha256(cookie.value.encode()).digest() if cookie else None
    except CookieError:
        return None

def current_user(headers):
    token = cookie_token(headers)
    if token is None:
        return None
    with closing(connect()) as db:
        row = db.execute("""SELECT accounts.username, accounts.email, accounts.name, accounts.role,
                                   accounts.organization, accounts.work, accounts.responsibilities,
                                   sessions.active_company_id AS activeCompanyId,
                                   company_memberships.role AS companyRole,
                                   companies.name AS companyName
                            FROM sessions JOIN accounts USING (username)
                            LEFT JOIN company_memberships ON company_memberships.company_id = sessions.active_company_id AND company_memberships.username = accounts.username
                            LEFT JOIN companies ON companies.id = sessions.active_company_id
                            WHERE sessions.token = ? AND sessions.expires > ?""", (token, int(time.time()))).fetchone()
    return dict(row) if row else None

def list_users():
    """Return non-secret profile/work fields for the admin team overview."""
    with closing(connect()) as db:
        rows = db.execute("""SELECT username, email, name, role, organization, work, responsibilities
                            FROM accounts ORDER BY lower(role), lower(name)""").fetchall()
    return [dict(row) for row in rows]


def list_workspaces(headers):
    user = current_user(headers)
    if not user:
        raise ValueError('Sign in first.')
    with closing(connect()) as db:
        rows = db.execute("""SELECT companies.id, companies.name, company_memberships.role
                             FROM company_memberships JOIN companies ON companies.id=company_memberships.company_id
                             WHERE company_memberships.username=? ORDER BY lower(companies.name)""",
                          (user['username'],)).fetchall()
    return [dict(row) for row in rows]


def list_workspace_users(headers):
    user = current_user(headers)
    membership = active_membership(headers)
    if not user or not membership or membership['role'] != 'Admin':
        raise PermissionError('Only a company admin can open Team Overview.')
    with closing(connect()) as db:
        rows = db.execute("""SELECT accounts.username, accounts.email, accounts.name, accounts.role,
                                   accounts.organization, accounts.work, accounts.responsibilities,
                                   company_memberships.role AS companyRole
                            FROM company_memberships JOIN accounts USING (username)
                            WHERE company_memberships.company_id=? ORDER BY lower(accounts.name)""",
                          (membership['companyId'],)).fetchall()
    return [dict(row) for row in rows]


def ensure_private_workspace(headers, display_name=None):
    user = current_user(headers)
    if not user:
        raise ValueError('Sign in first.')
    memberships = list_workspaces(headers)
    if memberships:
        if not user.get('activeCompanyId'):
            switch_workspace(headers, memberships[0]['id'])
            user = current_user(headers)
        return user.get('activeCompanyId')
    company_id = 'private-' + uuid.uuid4().hex
    name = (display_name or f"{user['name']}'s Private Workspace").strip()[:120]
    now = int(time.time())
    with closing(connect()) as db, db:
        db.execute('INSERT INTO companies (id,name,owner_username,created_at) VALUES (?,?,?,?)',
                   (company_id, name, user['username'], now))
        db.execute('INSERT INTO company_memberships (company_id,username,role,joined_at) VALUES (?,?,?,?)',
                   (company_id, user['username'], 'Admin', now))
        db.execute('UPDATE sessions SET active_company_id=? WHERE token=?',
                   (company_id, cookie_token(headers)))
    return company_id


def create_workspace(headers, name):
    user = current_user(headers)
    if not user:
        raise ValueError('Sign in first.')
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
        raise ValueError('Enter a workspace name between 1 and 120 characters.')
    company_id = 'company-' + uuid.uuid4().hex
    now = int(time.time())
    with closing(connect()) as db, db:
        db.execute('INSERT INTO companies (id,name,owner_username,created_at) VALUES (?,?,?,?)',
                   (company_id, name.strip(), user['username'], now))
        db.execute('INSERT INTO company_memberships (company_id,username,role,joined_at) VALUES (?,?,?,?)',
                   (company_id, user['username'], 'Admin', now))
        db.execute('UPDATE sessions SET active_company_id=? WHERE token=?',
                   (company_id, cookie_token(headers)))
    return {'id': company_id, 'name': name.strip(), 'role': 'Admin'}


def switch_workspace(headers, company_id):
    user = current_user(headers)
    if not user:
        raise ValueError('Sign in first.')
    with closing(connect()) as db, db:
        member = db.execute('SELECT 1 FROM company_memberships WHERE company_id=? AND username=?',
                             (company_id, user['username'])).fetchone()
        if not member:
            raise ValueError('You are not a member of that workspace.')
        db.execute('UPDATE sessions SET active_company_id=? WHERE token=?',
                   (company_id, cookie_token(headers)))
    return current_user(headers)


def active_membership(headers):
    user = current_user(headers)
    if not user or not user.get('activeCompanyId') or not user.get('companyRole'):
        return None
    return {'companyId': user['activeCompanyId'], 'role': user['companyRole'], 'username': user['username']}


def create_workspace_invitation(headers, email, role):
    user = current_user(headers)
    membership = active_membership(headers)
    if not user or not membership or membership['role'] != 'Admin':
        raise PermissionError('Only a company admin can invite members.')
    email = normalize_email(email)
    if role not in ROLES:
        raise ValueError('Choose a valid member role.')
    code = secrets.token_urlsafe(24)
    digest_code = sha256(code.encode()).digest()
    with closing(connect()) as db, db:
        db.execute('INSERT INTO company_invitations (code_hash,company_id,email,role,expires,created_by) VALUES (?,?,?,?,?,?)',
                   (digest_code, membership['companyId'], email, role, int(time.time()) + 7 * 86400, user['username']))
    return {'code': code, 'email': email, 'role': role, 'expiresInDays': 7}


def join_workspace_invitation(headers, code):
    user = current_user(headers)
    if not user or not isinstance(code, str) or not code.strip():
        raise ValueError('Sign in and enter an invitation code.')
    token_hash = sha256(code.strip().encode()).digest()
    now = int(time.time())
    with closing(connect()) as db:
        db.execute('BEGIN IMMEDIATE')
        invite = db.execute('SELECT * FROM company_invitations WHERE code_hash=?', (token_hash,)).fetchone()
        if not invite or invite['expires'] < now:
            db.rollback()
            raise ValueError('This invitation is invalid or expired.')
        if invite['email'].casefold() != user['email'].casefold():
            db.rollback()
            raise ValueError('Sign in with the verified email address this invitation was sent to.')
        db.execute('INSERT INTO company_memberships (company_id,username,role,joined_at) VALUES (?,?,?,?) ON CONFLICT(company_id,username) DO UPDATE SET role=excluded.role',
                   (invite['company_id'], user['username'], invite['role'], now))
        db.execute('DELETE FROM company_invitations WHERE code_hash=?', (token_hash,))
        db.execute('UPDATE sessions SET active_company_id=? WHERE token=?',
                   (invite['company_id'], cookie_token(headers)))
        db.commit()
    return current_user(headers)

def logout(headers):
    with closing(connect()) as db, db:
        db.execute('DELETE FROM sessions WHERE token = ?', (cookie_token(headers),))

def update_profile(headers, data):
    user = current_user(headers)
    if not user:
        raise ValueError('Sign in first.')
    fields = ('username', 'email', 'name', 'organization', 'work', 'responsibilities')
    if any(not isinstance(data.get(field), str) for field in fields):
        raise ValueError('Complete all profile fields.')
    username = data['username'].strip()
    email = normalize_email(data['email'])
    name, organization, work, responsibilities = (data[field].strip() for field in fields[2:])
    role = user['role']
    if data.get('role', role) != role:
        raise ValueError('Roles are granted by a company admin and cannot be changed in profile settings.')
    if not re.fullmatch(r'[A-Za-z0-9_]{3,32}', username):
        raise ValueError('Use 3 to 32 letters, numbers, or underscores for your username.')
    if username.casefold() == 'admin' and user['role'] != 'Admin':
        raise ValueError('That username is reserved.')
    if any(not value or len(value) > 500 for value in (name, organization, work, responsibilities)):
        raise ValueError('Complete each profile field using 1 to 500 characters.')
    email_changed = email.casefold() != user['email'].casefold()
    try:
        with closing(connect()) as db, db:
            if email_changed:
                verification = db.execute('SELECT verified_until FROM email_verifications WHERE email = ?', (email,)).fetchone()
                if not verification or verification['verified_until'] < int(time.time()):
                    raise ValueError('Verify the new email address before saving your profile.')
            db.execute("""UPDATE accounts SET username=?, email=?, name=?, role=?, organization=?, work=?, responsibilities=?
                         WHERE username=?""",
                       (username, email, name, role, organization, work, responsibilities, user['username']))
            db.execute('UPDATE sessions SET username=? WHERE username=?', (username, user['username']))
            if email_changed:
                db.execute('DELETE FROM email_verifications WHERE email = ?', (email,))
    except Exception as exc:
        if _is_integrity_error(exc):
            raise ValueError('That username or email is already in use.') from None
        raise
    return current_user(headers)

def change_password(headers, current_password, new_password):
    user = current_user(headers)
    if not user:
        raise ValueError('Sign in first.')
    if not isinstance(current_password, str) or not current_password or len(current_password) > 128:
        raise ValueError('Enter your current password.')
    if not isinstance(new_password, str) or not 4 <= len(new_password) <= 128:
        raise ValueError('Use a new password between 4 and 128 characters.')
    token = cookie_token(headers)
    with closing(connect()) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT salt, password_hash FROM accounts WHERE username=?', (user['username'],)).fetchone()
        if not row or not compare_digest(digest(current_password, row['salt']), row['password_hash']):
            db.rollback()
            raise ValueError('The current password is incorrect.')
        salt = secrets.token_bytes(16)
        db.execute('UPDATE accounts SET salt=?, password_hash=? WHERE username=?',
                   (salt, digest(new_password, salt), user['username']))
        db.execute('DELETE FROM sessions WHERE username=? AND token<>?', (user['username'], token))
        db.commit()
    return True

def delete_account(headers, password):
    user = current_user(headers)
    if not user:
        raise ValueError('Sign in first.')
    if not isinstance(password, str) or not password or len(password) > 128:
        raise ValueError('Enter your current password to confirm account deletion.')
    with closing(connect()) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT salt, password_hash, email FROM accounts WHERE username=?', (user['username'],)).fetchone()
        if not row or not compare_digest(digest(password, row['salt']), row['password_hash']):
            db.rollback()
            raise ValueError('The current password is incorrect.')
        # Profile details live on the account row. Delete that row and all
        # account-owned verification/session records atomically after auth.
        db.execute('DELETE FROM sessions WHERE username=?', (user['username'],))
        db.execute('DELETE FROM email_verifications WHERE email=?', (row['email'],))
        db.execute('DELETE FROM password_resets WHERE email=?', (row['email'],))
        # Keep audit history for traceability, but remove the deleted user from
        # all company memberships and invitations so the account has no access.
        db.execute('DELETE FROM company_memberships WHERE username=?', (user['username'],))
        db.execute('DELETE FROM company_invitations WHERE lower(email)=lower(?) OR created_by=?',
                   (row['email'], user['username']))
        db.execute('DELETE FROM accounts WHERE username=?', (user['username'],))
        db.commit()
    return True

def cleanup_expired_sessions():
    """Remove expired sessions during server maintenance."""
    with closing(connect()) as db, db:
        cursor = db.execute('DELETE FROM sessions WHERE expires <= ?', (int(time.time()),))
        return cursor.rowcount
