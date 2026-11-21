"""Check Gemini request handling and its audit fallback contract."""

from io import BytesIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import accounts
import full_backend
import gemini_review


class GeminiReviewTests(unittest.TestCase):
    def test_structured_review_uses_current_model_and_validates_findings(self):
        response = {
            'candidates': [{
                'finishReason': 'STOP',
                'content': {'parts': [{'text': json.dumps({'findings': [{
                    'title': 'Unsupported guarantee', 'category': 'Claims',
                    'severity': 'High', 'wrong': 'guaranteed 10x results',
                    'why': 'Needs evidence', 'sourceId': '', 'fix': 'Results may vary',
                }]})}]},
            }],
        }
        requests = []

        def fake_urlopen(request, timeout):
            requests.append((request, timeout))
            return BytesIO(json.dumps(response).encode('utf-8'))

        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}, clear=True), \
             patch.object(gemini_review.urllib.request, 'urlopen', side_effect=fake_urlopen):
            findings, status, used = gemini_review.review(
                'We promise guaranteed 10x results.', [], {'tone': {'primary': 'clear'}}
            )

        self.assertTrue(used)
        self.assertEqual(len(findings), 1)
        self.assertIn('gemini-3.8-flash', status)
        self.assertEqual(requests[0][1], 45)
        self.assertIn('/models/gemini-3.8-flash:generateContent', requests[0][0].full_url)
        self.assertEqual(requests[0][0].get_header('X-goog-api-key'), 'test-key')

    def test_provider_failure_is_not_counted_as_ai_review(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}, clear=True), \
             patch.object(gemini_review.urllib.request, 'urlopen', side_effect=OSError('offline')), \
             patch.object(gemini_review.LOGGER, 'exception'):
            findings, status, used = gemini_review.review('A draft', [], {})
        self.assertEqual(findings, [])
        self.assertFalse(used)
        self.assertIn('unavailable', status)


class AuditGeminiStatusTests(unittest.TestCase):
    def test_audit_records_rules_only_when_gemini_fails(self):
        user = {
            'username': 'reviewer', 'name': 'Reviewer', 'organization': 'Test',
            'role': 'Brand Manager', 'activeCompanyId': 'test-company',
            'companyRole': 'Admin',
        }
        with TemporaryDirectory() as directory, \
             patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key', 'BRANDWISE_LOCAL_STORAGE': '1'}), \
             patch.object(accounts, 'current_user', return_value=user), \
             patch.object(accounts, 'ensure_private_workspace', return_value='test-company'), \
             patch.object(full_backend, 'DB', Path(directory) / 'audit-data.json'), \
             patch.object(full_backend, 'get_workspace_audit_preferences', return_value={'strictness': 'balanced', 'passingThreshold': 80}), \
             patch.object(full_backend, 'claims_for_user', return_value=[]), \
             patch.object(full_backend, 'guidelines_for_user', return_value=full_backend.DEFAULT_GUIDELINES), \
             patch.object(full_backend, 'gemini_review', return_value=([], 'Gemini review unavailable; deterministic findings only.', False)):
            import wsgi_backend
            response = wsgi_backend.app.test_client().post(
                '/api/audits', json={'content': 'Our product is useful.', 'useAI': True, 'aiProvider': 'gemini'},
                headers={'Origin': 'http://localhost'},
            )
            self.assertEqual(response.status_code, 201, response.get_json())
            audit = response.get_json()
            self.assertFalse(audit['settings']['useAI'])
            self.assertEqual(audit['aiProvider'], 'rules')


if __name__ == '__main__':
    unittest.main()
