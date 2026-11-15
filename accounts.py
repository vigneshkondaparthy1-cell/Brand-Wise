from contextlib import closing
from email.message import EmailMessage
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest, new as hmac_new
from http.cookies import SimpleCookie, CookieError
from pathlib import Path
import os
import re
import secrets
import smtplib
import ssl
import sqlite3
import time

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
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS accounts (
      username TEXT PRIMARY KEY COLLATE NOCASE, email TEXT UNIQUE COLLATE NOCASE NOT NULL,
      name TEXT NOT NULL, role TEXT NOT NULL, organization TEXT NOT NULL,
      work TEXT NOT NULL, responsibilities TEXT NOT NULL, salt BLOB NOT NULL, password_hash BLOB NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
      token BLOB PRIMARY KEY, username TEXT NOT NULL, expires INTEGER NOT NULL
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
    return db

def digest(password, salt):
    return pbkdf2_hmac('sha256', password.encode(), salt, 600000)

def normalize_email(value):
    if not isinstance(value, str):
        raise ValueError('Enter a valid email address.')
    email = value.strip().casefold()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(email) > 254:
        raise ValueError('Enter a valid email address.')
    return email

def _send_otp_message(email, code, password_reset=False):
    host = os.environ.get('SMTP_HOST', '').strip()
    user = os.environ.get('SMTP_USER', '').strip()
    password = os.environ.get('SMTP_PASSWORD', '')
    sender = os.environ.get('SMTP_FROM', '').strip() or user
    try:
        port = int(os.environ.get('SMTP_PORT', '587'))
    except ValueError:
        raise EmailDeliveryError('Email delivery is not configured. Check the SMTP settings in .env.') from None
    if not host or not sender or not user or not password:
        raise EmailDeliveryError('Email delivery is not configured. Add SMTP settings in .env before requesting a code.')

    message = EmailMessage()
    message['Subject'] = 'Reset your BrandWise password' if password_reset else 'Your BrandWise verification code'
    message['From'] = sender
    message['To'] = email
    if password_reset:
        message.set_content(
            f'Your BrandWise password reset code is {code}.\n\n'
            'Enter this code in the password reset form. It expires in 10 minutes. '
            'If you did not request a password reset, you can ignore this email.'
        )
    else:
        message.set_content(
            f'Your BrandWise email verification code is {code}.\n\n'
            f'This code expires in 10 minutes. If you did not request it, you can ignore this email.'
        )
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
    except (OSError, smtplib.SMTPException) as exc:
        raise EmailDeliveryError('We could not send the code. Check the SMTP settings in .env and try again.') from exc

def send_email_otp(raw_email):
    email = normalize_email(raw_email)
    now = int(time.time())
    code = f'{secrets.randbelow(1_000_000):06d}'
    salt = secrets.token_bytes(16)
    code_hash = hmac_new(salt, code.encode(), 'sha256').digest()
    with closing(connect()) as db, db:
        if db.execute('SELECT 1 FROM accounts WHERE email = ?', (email,)).fetchone():
            raise ValueError('This email is already registered.')
        old = db.execute('SELECT * FROM email_verifications WHERE email = ?', (email,)).fetchone()
        if old and now - old['last_sent'] < OTP_COOLDOWN:
            wait = OTP_COOLDOWN - (now - old['last_sent'])
            raise ValueError(f'Please wait {wait} seconds before requesting another code.')
        window = old['send_window'] if old and now - old['send_window'] < 86400 else now
        sends = old['sends_in_window'] + 1 if old and window == old['send_window'] else 1
        if sends > OTP_DAILY_LIMIT:
            raise ValueError('Too many codes requested for this email. Try again later.')
        db.execute("""INSERT INTO email_verifications
                      (email, code_hash, salt, expires, attempts, verified_until, last_sent, send_window, sends_in_window)
                      VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?)
                      ON CONFLICT(email) DO UPDATE SET code_hash=excluded.code_hash, salt=excluded.salt,
                        expires=excluded.expires, attempts=0, verified_until=0, last_sent=excluded.last_sent,
                        send_window=excluded.send_window, sends_in_window=excluded.sends_in_window""",
                   (email, code_hash, salt, now + OTP_TTL, now, window, sends))
    try:
        _send_otp_message(email, code)
    except EmailDeliveryError:
        with closing(connect()) as db, db:
            db.execute('DELETE FROM email_verifications WHERE email = ? AND verified_until = 0', (email,))
        raise

def verify_email_otp(raw_email, code):
    email = normalize_email(raw_email)
    if not isinstance(code, str) or not re.fullmatch(r'\d{6}', code.strip()):
        raise ValueError('Enter the six-digit code from your email.')
    now = int(time.time())
    with closing(connect()) as db, db:
        row = db.execute('SELECT * FROM email_verifications WHERE email = ?', (email,)).fetchone()
        if not row:
            raise ValueError('Request a new verification code first.')
        if row['expires'] < now:
            db.execute('DELETE FROM email_verifications WHERE email = ?', (email,))
            db.commit()
            raise ValueError('That code has expired. Request a new one.')
        if row['attempts'] >= OTP_MAX_ATTEMPTS:
            raise ValueError('Too many incorrect codes. Request a new one.')
        expected = hmac_new(row['salt'], code.strip().encode(), 'sha256').digest()
        if not compare_digest(expected, row['code_hash']):
            db.execute('UPDATE email_verifications SET attempts = attempts + 1 WHERE email = ?', (email,))
            db.commit()
            raise ValueError('That code is incorrect. Check the email and try again.')
        db.execute('UPDATE email_verifications SET verified_until = ? WHERE email = ?', (now + OTP_TTL, email))


def send_password_reset_otp(raw_email):
    email = normalize_email(raw_email)
    now = int(time.time())
    with closing(connect()) as db, db:
        account = db.execute('SELECT 1 FROM accounts WHERE email = ?', (email,)).fetchone()
        if not account:
            return False
        old = db.execute('SELECT * FROM password_resets WHERE email = ?', (email,)).fetchone()
        if old and now - old['last_sent'] < OTP_COOLDOWN:
            return False
        window = old['send_window'] if old and now - old['send_window'] < 86400 else now
        sends = old['sends_in_window'] + 1 if old and window == old['send_window'] else 1
        if sends > OTP_DAILY_LIMIT:
            return False
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
        _send_otp_message(email, code, password_reset=True)
    except EmailDeliveryError:
        with closing(connect()) as db, db:
            db.execute('DELETE FROM password_resets WHERE email = ?', (email,))
        raise
    return True


def reset_password_with_email_otp(raw_email, code, new_password):
    email = normalize_email(raw_email)
    if not isinstance(code, str) or not re.fullmatch(r'\d{6}', code.strip()):
        raise ValueError('Enter the six-digit code from your email.')
    if not isinstance(new_password, str) or not 4 <= len(new_password) <= 128:
        raise ValueError('Use a new password between 4 and 128 characters.')
    now = int(time.time())
    with closing(connect()) as db:
        db.execute('BEGIN IMMEDIATE')
        reset = db.execute('SELECT * FROM password_resets WHERE email = ?', (email,)).fetchone()
        account = db.execute('SELECT username FROM accounts WHERE email = ?', (email,)).fetchone()
        if not reset or not account:
            db.rollback()
            raise ValueError('The email or verification code is invalid. Request a new code and try again.')
        if reset['expires'] < now:
            db.execute('DELETE FROM password_resets WHERE email = ?', (email,))
            db.commit()
            raise ValueError('That code has expired. Request a new one.')
        if reset['attempts'] >= OTP_MAX_ATTEMPTS:
            db.rollback()
            raise ValueError('Too many incorrect codes. Request a new one.')
        expected = hmac_new(reset['salt'], code.strip().encode(), 'sha256').digest()
        if not compare_digest(expected, reset['code_hash']):
            db.execute('UPDATE password_resets SET attempts = attempts + 1 WHERE email = ?', (email,))
            db.commit()
            raise ValueError('That code is incorrect. Check the email and try again.')
        salt = secrets.token_bytes(16)
        db.execute('UPDATE accounts SET salt=?, password_hash=? WHERE email=?', (salt, digest(new_password, salt), email))
        db.execute('DELETE FROM sessions WHERE username=?', (account['username'],))
        db.execute('DELETE FROM password_resets WHERE email=?', (email,))
        db.commit()
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
    except sqlite3.IntegrityError:
        raise ValueError('That username or email is already registered.') from None

def login(data):
    username, password = data.get('username'), data.get('password')
    if not isinstance(username, str) or not isinstance(password, str) or len(username) > 32 or len(password) > 128:
        return None
    with closing(connect()) as db, db:
        row = db.execute('SELECT * FROM accounts WHERE username = ?', (username.strip(),)).fetchone()
        hashed = digest(password, row['salt'] if row else bytes(16))
        if not row or not compare_digest(hashed, row['password_hash']):
            return None
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
        db.execute('INSERT INTO sessions VALUES (?, ?, ?)', (sha256(token.encode()).digest(), row['username'], now + SESSION_AGE))
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
                                   accounts.organization, accounts.work, accounts.responsibilities
                            FROM sessions JOIN accounts USING (username)
                            WHERE sessions.token = ? AND sessions.expires > ?""", (token, int(time.time()))).fetchone()
    return dict(row) if row else None

def list_users():
    """Return non-secret profile/work fields for the admin team overview."""
    with closing(connect()) as db:
        rows = db.execute("""SELECT username, email, name, role, organization, work, responsibilities
                            FROM accounts ORDER BY role COLLATE NOCASE, name COLLATE NOCASE""").fetchall()
    return [dict(row) for row in rows]

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
    role = data.get('role', user['role'])
    if user['role'] == 'Admin':
        if role != 'Admin':
            raise ValueError('The Admin role is managed separately and cannot be changed here.')
    elif role not in ROLES:
        raise ValueError('Choose a valid work role.')
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
    except sqlite3.IntegrityError:
        raise ValueError('That username or email is already in use.') from None
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
        db.execute('DELETE FROM accounts WHERE username=?', (user['username'],))
        db.commit()
    return True

def cleanup_expired_sessions():
    """Remove expired sessions during server maintenance."""
    with closing(connect()) as db, db:
        cursor = db.execute('DELETE FROM sessions WHERE expires <= ?', (int(time.time()),))
        return cursor.rowcount
