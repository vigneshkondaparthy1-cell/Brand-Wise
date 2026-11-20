"""Exercise the account flow without sending email or touching user data."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from hashlib import pbkdf2_hmac
import secrets
from contextlib import closing

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import accounts
from auth_routes import register_auth_routes


class AccountRoutesSmokeTest(unittest.TestCase):
    def test_registration_login_and_password_reset(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(accounts, 'DB', Path(directory) / 'accounts.sqlite3'), \
             patch.dict('os.environ', {'BRANDWISE_LOCAL_STORAGE': '1'}, clear=False):
            codes = {}

            def capture_code(email, code, password_reset=False, client_ip=None):
                codes['reset' if password_reset else 'verify'] = code
                return code

            with patch.object(accounts, '_send_otp_message', side_effect=capture_code):
                app = Flask(__name__)
                limiter = Limiter(key_func=get_remote_address)
                limiter.init_app(app)
                register_auth_routes(app, limiter)
                client = app.test_client()

                self.assertEqual(client.get('/api/auth/roles').status_code, 200)
                self.assertEqual(client.get('/api/auth/me').status_code, 401)
                self.assertEqual(client.post('/api/auth/send-otp', json={'email': 'example@example.org'}).status_code, 200)
                self.assertEqual(client.post('/api/auth/verify-otp', json={
                    'email': 'example@example.org', 'code': codes['verify']
                }).status_code, 200)
                registration = {
                    'username': 'test_person', 'email': 'example@example.org',
                    'password': 'first-password', 'name': 'Test Person',
                    'role': 'Creator', 'organization': 'Example',
                    'work': 'Copy', 'responsibilities': 'Review',
                }
                self.assertEqual(client.post('/api/auth/register', json=registration).status_code, 201)
                self.assertEqual(client.get('/api/auth/me').get_json()['username'], 'test_person')
                self.assertEqual(client.post('/api/auth/password-reset/send', json={
                    'email': 'example@example.org'
                }).status_code, 200)
                self.assertEqual(client.post('/api/auth/password-reset', json={
                    'email': 'example@example.org', 'code': codes['reset'],
                    'newPassword': 'second-password',
                }).status_code, 200)
                self.assertEqual(client.post('/api/auth/login', json={
                    'username': 'test_person', 'password': 'first-password'
                }).status_code, 401)
                self.assertEqual(client.post('/api/auth/login', json={
                    'username': 'test_person', 'password': 'second-password'
                }).status_code, 200)

                # Accounts created before the Argon2 change must still sign in.
                salt = secrets.token_bytes(16)
                old_hash = pbkdf2_hmac('sha256', b'legacy-password', salt, 600000)
                with closing(accounts.connect()) as db, db:
                    db.execute('UPDATE accounts SET salt=?, password_hash=? WHERE username=?',
                               (salt, old_hash, 'test_person'))
                self.assertEqual(client.post('/api/auth/login', json={
                    'username': 'test_person', 'password': 'legacy-password'
                }).status_code, 200)
                with closing(accounts.connect()) as db:
                    stored = db.execute('SELECT password_hash FROM accounts WHERE username=?',
                                        ('test_person',)).fetchone()['password_hash']
                self.assertTrue(stored.startswith(b'$argon2'))


if __name__ == '__main__':
    unittest.main()

