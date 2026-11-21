"""Check the deployed login path across rotating client addresses."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import os

import accounts
with patch.dict(os.environ, {'BRANDWISE_LOCAL_STORAGE': '1'}):
    import wsgi_backend


class LoginThrottlingTests(unittest.TestCase):
    def test_render_client_ip_ignores_spoofed_forwarded_prefix(self):
        headers = {'CF-Connecting-IP': '203.0.113.5',
                   'X-Forwarded-For': '198.51.100.9, 203.0.113.5'}
        with patch.dict(os.environ, {'RENDER': 'true'}):
            self.assertEqual(accounts.request_client_ip(headers, '10.0.0.1'), '203.0.113.5')
            self.assertEqual(accounts.request_client_ip({'X-Forwarded-For': headers['X-Forwarded-For']}, '10.0.0.1'), '203.0.113.5')

    def test_same_account_is_limited_across_client_ips(self):
        with TemporaryDirectory() as directory, \
             patch.object(accounts, 'DB', Path(directory) / 'accounts.sqlite3'), \
             patch.object(accounts, 'is_local_dev', return_value=False), \
             patch.object(accounts, 'email_for_login', return_value='owner@example.org'), \
             patch.object(accounts, 'login', return_value=None), \
             patch.dict('os.environ', {'BRANDWISE_LOCAL_STORAGE': '1'}):
            client = wsgi_backend.app.test_client()
            for index in range(accounts.LOGIN_MAX_FAILURES):
                response = client.post(
                    '/api/auth/login',
                    json={'username': 'owner', 'password': 'wrong-password'},
                    headers={'Origin': 'http://localhost'},
                    environ_base={'REMOTE_ADDR': f'192.0.2.{index + 1}'},
                )
                self.assertEqual(response.status_code, 401, response.get_json())
            response = client.post(
                '/api/auth/login',
                json={'username': 'owner@example.org', 'password': 'wrong-password'},
                headers={'Origin': 'http://localhost'},
                environ_base={'REMOTE_ADDR': '192.0.2.99'},
            )
            self.assertEqual(response.status_code, 429, response.get_json())

    def test_homepage_allows_model_assets_and_inline_scripts(self):
        response = wsgi_backend.app.test_client().get('/')
        self.assertEqual(response.status_code, 200)
        policy = response.headers['Content-Security-Policy']
        for expected in ('https://cdn.jsdelivr.net', 'https://huggingface.co',
                         'https://raw.githubusercontent.com', 'worker-src',
                         'blob:', 'wasm-unsafe-eval', 'sha256-'):
            self.assertIn(expected, policy)


if __name__ == '__main__':
    unittest.main()
