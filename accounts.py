from contextlib import closing
from email.message import EmailMessage
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest, new as hmac_new
from http.cookies import SimpleCookie, CookieError
from pathlib import Path
import json
import ipaddress
import logging
import os
import re
import secrets
import smtplib
import ssl
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
OTP_COOLDOWN = 60
OTP_DAILY_LIMIT = 8
OTP_MAX_ATTEMPTS = 5

class EmailDeliveryError(ValueError):
    pass

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

def request_client_ip(headers, remote_addr):
    """Use the edge-provided visitor address only on Render's trusted ingress."""
    candidates = []
    if os.environ.get('RENDER'):
        candidates.append(headers.get('CF-Connecting-IP', ''))
        # Render appends to X-Forwarded-For; ignore caller-supplied left entries.
        candidates.append((headers.get('X-Forwarded-For', '').split(',')[-1]).strip())
    candidates.append(remote_addr or '127.0.0.1')
    for candidate in candidates:
        try:
            return ipaddress.ip_address(candidate).compressed
        except ValueError:
            continue
    return '127.0.0.1'

def _login_failure_keys(client_ip, identifier=None):
    keys = [ipaddress.ip_address(client_ip).compressed]
    if isinstance(identifier, str) and identifier.strip():
        normalized = identifier.strip().casefold()[:254]
        keys.append('account:' + sha256(normalized.encode('utf-8')).hexdigest())
    return keys

def login_is_limited(client_ip, identifier=None):
    now = int(time.time())
    cutoff = now - LOGIN_WINDOW_SECONDS
    keys = _login_failure_keys(client_ip, identifier)
    with closing(connect()) as db, db:
        db.execute("DELETE FROM login_failures WHERE attempted_at < ?", (cutoff,))
        for key in keys:
            row = db.execute(
                "SELECT COUNT(*) AS total, MAX(attempted_at) AS latest FROM login_failures WHERE ip = ? AND attempted_at >= ?",
                (key, cutoff),
            ).fetchone()
            total = row['total'] if row else 0
            latest = row['latest'] if row else None
            if total >= LOGIN_MAX_FAILURES and latest and now - latest < LOGIN_LOCK_SECONDS:
                return True
            if total >= LOGIN_MAX_FAILURES:
                db.execute("DELETE FROM login_failures WHERE ip = ?", (key,))
        return False

def record_login_failure(client_ip, identifier=None):
    now = int(time.time())
    with closing(connect()) as db, db:
        for key in _login_failure_keys(client_ip, identifier):
            db.execute("INSERT INTO login_failures (ip, attempted_at) VALUES (?, ?)", (key, now))

def clear_login_failures(client_ip, identifier=None):
    with closing(connect()) as db, db:
        for key in _login_failure_keys(client_ip, identifier):
            db.execute("DELETE FROM login_failures WHERE ip = ?", (key,))

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

from argon2 import PasswordHasher

ph = PasswordHasher(time_cost=2, memory_cost=102400, parallelism=8, hash_len=32, salt_len=16)

def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)

def verify_password(hash_: str, password: str) -> bool:
    """Verify a password against an Argon2id hash. Returns False on any error."""
    try:
        if isinstance(hash_, (bytes, bytearray, memoryview)):
            hash_ = bytes(hash_).decode('utf-8')
        return ph.verify(hash_, password)
    except Exception:
        return False

def password_matches(password, salt, stored_hash):
    """Accept current Argon2 hashes and legacy PBKDF2 account records."""
    stored = bytes(stored_hash) if isinstance(stored_hash, (bytes, bytearray, memoryview)) else stored_hash
    if isinstance(stored, bytes) and stored.startswith(b'$argon2'):
        return verify_password(stored, password)
    if isinstance(stored, str) and stored.startswith('$argon2'):
        return verify_password(stored, password)
    return isinstance(stored, bytes) and compare_digest(
        pbkdf2_hmac('sha256', password.encode(), bytes(salt), 600000), stored
    )

# Backwards‑compatible wrapper (old name still used elsewhere)
def digest(password, salt):
    # Salt is unused by Argon2 (it generates its own). Keep signature for callers.
    return hash_password(password).encode('utf-8')

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

def _send_otp_message(email, code, password_reset=False, client_ip=None):
    resend_api_key = os.environ.get('RESEND_API_KEY', '').strip()
    resend_sender = os.environ.get('RESEND_FROM', '').strip()
    subject = f'BrandWise: {code} is your password reset code' if password_reset else f'BrandWise: {code} is your verification code'
    purpose = 'password reset' if password_reset else 'email verification'
    action_desc = 'reset your BrandWise password' if password_reset else 'verify your email address on BrandWise'

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; padding: 32px 16px; margin: 0;">
  <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 32px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
    <h2 style="margin: 0 0 16px; color: #1e293b; font-size: 22px; font-weight: 700;">BrandWise</h2>
    <p style="color: #475569; font-size: 15px; line-height: 1.5; margin: 0 0 24px;">
      Use the verification code below to {action_desc}:
    </p>
    <div style="background: #f1f5f9; border-radius: 12px; padding: 20px; text-align: center; margin: 0 0 24px;">
      <span style="font-family: monospace; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #0f172a;">{code}</span>
    </div>
    <p style="color: #64748b; font-size: 13px; line-height: 1.4; margin: 0 0 8px;">
      This code expires in 10 minutes. If you did not request this email, you can safely ignore it.
    </p>
  </div>
</body>
</html>"""

    text_body = (
        f'Your BrandWise password reset code is {code}.\n\n'
        'Enter this code in the password reset form. It expires in 10 minutes. '
        'If you did not request a password reset, you can ignore this email.'
        if password_reset else
        f'Your BrandWise email verification code is {code}.\n\n'
        'This code expires in 10 minutes. If you did not request it, you can ignore this email.'
    )

    if resend_api_key and not resend_api_key.startswith('re_your_key'):
        if not resend_sender:
            if not is_local_dev(client_ip):
                raise EmailDeliveryError('Resend is enabled, but RESEND_FROM is empty. Set it to a sender address on your verified domain (e.g. noreply@getbrandwise.xyz).')
        else:
            payload = json.dumps({
                'from': resend_sender,
                'to': [email],
                'subject': subject,
                'html': html_body,
                'text': text_body,
            }).encode('utf-8')
            request = urllib.request.Request(
                'https://api.resend.com/emails',
                data=payload,
                headers={
                    'Authorization': f'Bearer {resend_api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'BrandWise/1.0 (+https://getbrandwise.xyz)',
                },
                method='POST',
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    if 200 <= response.status < 300:
                        return None
            except urllib.error.HTTPError as exc:
                if not is_local_dev(client_ip):
                    detail = ''
                    raw_response = exc.read(4096).decode('utf-8', errors='replace')
                    if exc.code == 403:
                        logging.getLogger(__name__).warning(
                            'Resend rejected email send: content_type=%s response=%s',
                            exc.headers.get('Content-Type', ''),
                            raw_response.replace(resend_api_key, '[redacted]')[:300],
                        )
                    try:
                        response_data = json.loads(raw_response)
                        detail = response_data.get('message', '') if isinstance(response_data, dict) else ''
                    except (ValueError, UnicodeDecodeError):
                        pass
                    message = f'Resend could not send the {purpose} code (HTTP {exc.code}).'
                    if exc.code == 403:
                        if raw_response.strip().casefold() == 'error code: 1010':
                            detail = 'The email provider blocked the app connection before processing the request. Please try again after the service is updated.'
                        elif detail:
                            detail = f'Resend says: {detail}'
                        elif 'resend.dev' in resend_sender.casefold():
                            detail = 'The Resend test sender can only deliver to the email address that owns the Resend account. For verification emails to other users, verify your sending domain (like getbrandwise.xyz) in Resend and set RESEND_FROM to that domain.'
                        else:
                            detail = f'Resend denied sender "{resend_sender}". Make sure the domain is verified in your Resend account and RESEND_API_KEY has sending permission.'
                    elif exc.code == 401:
                        detail = 'Resend rejected the API key. Please check your RESEND_API_KEY.'
                    if detail:
                        message += f' {detail[:240]}'
                    raise EmailDeliveryError(message) from None
            except (OSError, urllib.error.URLError, TimeoutError) as exc:
                if not is_local_dev(client_ip):
                    raise EmailDeliveryError('Could not reach Resend to send the code. Check the network connection and Resend service status, then try again.') from exc

    host = os.environ.get('SMTP_HOST', '').strip()
    user = os.environ.get('SMTP_USER', '').strip()
    password = os.environ.get('SMTP_PASSWORD', '')
    if host.casefold() == 'smtp.gmail.com':
        password = ''.join(password.split())
    sender = os.environ.get('SMTP_FROM', '').strip() or user
    try:
        port = int(os.environ.get('SMTP_PORT', '587'))
    except ValueError:
        port = 587

    smtp_configured = bool(host and sender and user and password)
    gmail_invalid_pwd = bool(host.casefold() == 'smtp.gmail.com' and len(password) != 16)

    if smtp_configured and not gmail_invalid_pwd:
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = sender
        message['To'] = email
        message.set_content(text_body)
        message.add_alternative(html_body, subtype='html')
        try:
            context = ssl.create_default_context()
            if port == 465:
                with smtplib.SMTP_SSL(host, port, timeout=15, context=context) as client:
                    client.login(user, password)
                    client.send_message(message)
            else:
                with smtplib.SMTP(host, port, timeout=15) as client:
                    client.ehlo()
                    client.starttls(context=context)
                    client.ehlo()
                    client.login(user, password)
                    client.send_message(message)
            return None
        except (smtplib.SMTPException, OSError) as exc:
            if not is_local_dev(client_ip):
                raise EmailDeliveryError('We could not send the code. Check the email settings and try again.') from exc

    # In local development, fall back to displaying the local OTP
    if is_local_dev(client_ip) or not os.environ.get('RENDER'):
        print(f"\n=======================================================", flush=True)
        print(f"[BrandWise Resend/Local OTP] Email: {email}", flush=True)
        print(f"[BrandWise Resend/Local OTP] Code:  {code}", flush=True)
        print(f"=======================================================\n", flush=True)
        return code

    raise EmailDeliveryError('Email delivery is not configured. Set RESEND_API_KEY and RESEND_FROM in your environment.')


def send_email_otp(raw_email, client_ip=None):
    email = normalize_email(raw_email)
    now = int(time.time())
    code = f'{secrets.randbelow(1_000_000):06d}'
    salt = secrets.token_bytes(16)
    code_hash = hmac_new(salt, code.encode(), 'sha256').digest()
    with closing(connect()) as db, db:
        if db.execute('SELECT 1 FROM accounts WHERE lower(email) = lower(?)', (email,)).fetchone():
            raise ValueError('This email is already registered.')
        old = db.execute('SELECT * FROM email_verifications WHERE lower(email) = lower(?)', (email,)).fetchone()
        if old and now - old['last_sent'] < OTP_COOLDOWN:
            wait = OTP_COOLDOWN - (now - old['last_sent'])
            raise ValueError(f'Please wait {wait} seconds before requesting another code.')
        window = old['send_window'] if old and now - old['send_window'] < 86400 else now
        sends = old['sends_in_window'] + 1 if old and window == old['send_window'] else 1
        if sends > OTP_DAILY_LIMIT:
            raise ValueError('Too many verification codes sent today. Try again tomorrow.')
        db.execute("""INSERT INTO email_verifications
                      (email, code_hash, salt, expires, attempts, verified_until, last_sent, send_window, sends_in_window)
                      VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?)
                      ON CONFLICT(email) DO UPDATE SET code_hash=excluded.code_hash, salt=excluded.salt,
                        expires=excluded.expires, attempts=0, verified_until=0, last_sent=excluded.last_sent,
                        send_window=excluded.send_window, sends_in_window=excluded.sends_in_window""",
                   (email, code_hash, salt, now + OTP_TTL, now, window, sends))
    try:
        dev_code = _send_otp_message(email, code, password_reset=False, client_ip=client_ip)
        return {'ok': True, 'dev_code': dev_code}
    except EmailDeliveryError:
        with closing(connect()) as db, db:
            db.execute('DELETE FROM email_verifications WHERE lower(email) = lower(?) AND verified_until = 0', (email,))
        raise


def verify_email_otp(raw_email, code):
    email = normalize_email(raw_email)
    if not isinstance(code, str) or not re.fullmatch(r'\d{6}', code.strip()):
        raise ValueError('Enter the six-digit code from your email.')
    now = int(time.time())
    with closing(connect()) as db, db:
        row = db.execute('SELECT * FROM email_verifications WHERE lower(email) = lower(?)', (email,)).fetchone()
        if not row:
            raise ValueError('Request a new verification code first.')
        if row['expires'] < now:
            db.execute('DELETE FROM email_verifications WHERE lower(email) = lower(?)', (email,))
            raise ValueError('That code has expired. Request a new one.')
        if row['attempts'] >= OTP_MAX_ATTEMPTS:
            raise ValueError('Too many incorrect codes. Request a new one.')
        expected = hmac_new(row['salt'], code.strip().encode(), 'sha256').digest()
        if not compare_digest(expected, row['code_hash']):
            db.execute('UPDATE email_verifications SET attempts = attempts + 1 WHERE lower(email) = lower(?)', (email,))
            raise ValueError('That code is incorrect. Check the email and try again.')
        db.execute('UPDATE email_verifications SET verified_until = ? WHERE lower(email) = lower(?)', (now + OTP_TTL, email))
    return True


def send_password_reset_otp(raw_email, client_ip=None):
    email = normalize_email(raw_email)
    now = int(time.time())
    with closing(connect()) as db, db:
        account = db.execute('SELECT 1 FROM accounts WHERE lower(email) = lower(?)', (email,)).fetchone()
        if not account:
            if is_local_dev(client_ip):
                raise ValueError('No BrandWise account uses this email.')
            return False
        old = db.execute('SELECT * FROM password_resets WHERE lower(email) = lower(?)', (email,)).fetchone()
        if old and now - old['last_sent'] < OTP_COOLDOWN:
            wait = OTP_COOLDOWN - (now - old['last_sent'])
            raise ValueError(f'Please wait {wait} seconds before requesting another code.')
        window = old['send_window'] if old and now - old['send_window'] < 86400 else now
        sends = old['sends_in_window'] + 1 if old and window == old['send_window'] else 1
        if sends > OTP_DAILY_LIMIT:
            raise ValueError('Too many reset attempts today. Try again tomorrow.')
        code = f'{secrets.randbelow(1_000_000):06d}'
        salt = secrets.token_bytes(16)
        code_hash = hmac_new(salt, code.encode(), 'sha256').digest()
        db.execute("""INSERT INTO password_resets
                      (email, code_hash, salt, expires, attempts, last_sent, send_window, sends_in_window)
                      VALUES (?, ?, ?, ?, 0, ?, ?, ?)
                      ON CONFLICT(email) DO UPDATE SET code_hash=excluded.code_hash, salt=excluded.salt,
                        expires=excluded.expires, attempts=0, last_sent=excluded.last_sent,
                        send_window=excluded.send_window, sends_in_window=excluded.sends_in_window""",
                   (email, code_hash, salt, now + OTP_TTL, now, window, sends))
    try:
        dev_code = _send_otp_message(email, code, password_reset=True, client_ip=client_ip)
        return {'ok': True, 'dev_code': dev_code}
    except EmailDeliveryError:
        with closing(connect()) as db, db:
            db.execute('DELETE FROM password_resets WHERE lower(email) = lower(?)', (email,))
        raise


def reset_password_with_email_otp(raw_email, code, new_password):
    email = normalize_email(raw_email)
    if not isinstance(code, str) or not re.fullmatch(r'\d{6}', code.strip()):
        raise ValueError('Enter the six-digit code from your email.')
    if not isinstance(new_password, str) or not 12 <= len(new_password) <= 128:
        raise ValueError('Use a new password between 12 and 128 characters.')
    now = int(time.time())
    with closing(connect()) as db, db:
        reset = db.execute('SELECT * FROM password_resets WHERE lower(email) = lower(?)', (email,)).fetchone()
        account = db.execute('SELECT username FROM accounts WHERE lower(email) = lower(?)', (email,)).fetchone()
        if not reset or not account:
            raise ValueError('The email or verification code is invalid. Request a new code and try again.')
        if reset['expires'] < now:
            db.execute('DELETE FROM password_resets WHERE lower(email) = lower(?)', (email,))
            raise ValueError('That code has expired. Request a new one.')
        if reset['attempts'] >= OTP_MAX_ATTEMPTS:
            raise ValueError('Too many incorrect codes. Request a new one.')
        expected = hmac_new(reset['salt'], code.strip().encode(), 'sha256').digest()
        if not compare_digest(expected, reset['code_hash']):
            db.execute('UPDATE password_resets SET attempts = attempts + 1 WHERE lower(email) = lower(?)', (email,))
            raise ValueError('That code is incorrect. Check the email and try again.')
        salt = secrets.token_bytes(16)
        db.execute('UPDATE accounts SET salt=?, password_hash=? WHERE lower(email)=lower(?)',
                   (salt, digest(new_password, salt), email))
        db.execute('DELETE FROM sessions WHERE username=?', (account['username'],))
        db.execute('DELETE FROM password_resets WHERE lower(email)=lower(?)', (email,))
    return True


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
    if not 12 <= len(password) <= 128:
        raise ValueError('Use a password between 12 and 128 characters.')
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
        if not row or not password_matches(password, row['salt'], row['password_hash']):
            return None
        if not bytes(row['password_hash']).startswith(b'$argon2'):
            db.execute('UPDATE accounts SET password_hash=? WHERE username=?',
                       (digest(password, row['salt']), row['username']))
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
    if user and user['role'] == 'Admin':
        return list_users()
    membership = active_membership(headers)
    if not user or not membership or membership['role'] != 'Admin':
        raise PermissionError('Only an administrator can open Team Overview.')
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
    if not isinstance(new_password, str) or not 12 <= len(new_password) <= 128:
        raise ValueError('Use a new password between 12 and 128 characters.')
    token = cookie_token(headers)
    with closing(connect()) as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT salt, password_hash FROM accounts WHERE username=?', (user['username'],)).fetchone()
        if not row or not password_matches(current_password, row['salt'], row['password_hash']):
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
        if not row or not password_matches(password, row['salt'], row['password_hash']):
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
