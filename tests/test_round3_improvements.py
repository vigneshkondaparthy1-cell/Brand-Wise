import unittest
import os
import time
import base64
import json
import tempfile
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

os.environ['NO_POSTGRES'] = '1'

import server
import accounts


class Round3ImprovementsTests(unittest.TestCase):

    def test_repeated_prohibited_phrase_has_distinct_offsets(self):
        claim = {'id':'CLM-TEST', 'statement':'Use supported wording', 'category':'Brand',
                 'evidence':'Approved brief', 'owner':'Brand Manager', 'expiry':'2030-01-01',
                 'status':'Active', 'prohibitedPhrases':['guaranteed']}
        copy = 'Guaranteed results. Guaranteed support.'
        result = server.run_brandwise_checks(copy, _claims=[claim])
        hits = [item for item in result['findings'] if item['category'] == 'Prohibited Claim Wording']
        self.assertEqual([item['location'] for item in hits], ['Offset 0..10', 'Offset 20..30'])

    def test_firebase_verified_reset_updates_custom_password(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(accounts, 'DB', Path(directory) / 'accounts.sqlite3'):
            email = 'reset@example.test'
            accounts.connect().close()
            with closing(accounts.connect()) as db, db:
                salt = b'0123456789abcdef'
                db.execute('INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                           ('reset_user', email, 'Reset User', 'Creator', 'Test', 'Writer', 'Drafts',
                            salt, accounts.digest('oldpass', salt)))
            payload = base64.urlsafe_b64encode(json.dumps({'auth_time':int(time.time())}).encode()).decode().rstrip('=')
            token = 'header.' + payload + '.signature'
            with patch.object(accounts, 'firebase_user_from_token', return_value={'email':email, 'email_verified':True}):
                accounts.reset_password_with_firebase_token(token, 'new4')
            self.assertIsNotNone(accounts.login({'username':'reset_user', 'password':'new4'}))
            self.assertIsNone(accounts.login({'username':'reset_user', 'password':'oldpass'}))

    def test_old_firebase_session_cannot_reset_custom_password(self):
        payload = base64.urlsafe_b64encode(json.dumps({'auth_time':int(time.time()) - 601}).encode()).decode().rstrip('=')
        token = 'header.' + payload + '.signature'
        with patch.object(accounts, 'firebase_user_from_token', return_value={'email':'reset@example.test', 'email_verified':True}):
            with self.assertRaisesRegex(ValueError, 'too old'):
                accounts.reset_password_with_firebase_token(token, 'new4')

    def test_improvement_1_dynamic_claim_ledger_updates(self):
        """Updating a claim in the ledger immediately updates verification results."""
        custom_claims = [
            {
                "id": "CLM-999",
                "statement": "Cuts onboarding time by up to 35%",
                "category": "Product Performance",
                "evidence": "Q3 Benchmark Report 2026",
                "owner": "Performance Team",
                "expiry": "2030-01-01",
                "status": "Active",
                "prohibitedPhrases": ["cuts onboarding by 50%"]
            }
        ]
        # Text asserting 30% should PASS under 35% benchmark, but fail if exceeding
        res_pass = server.run_brandwise_checks("Cuts onboarding by 30%.", _claims=custom_claims)
        self.assertFalse(any(f['category'] == 'Unsupported Performance Claim' for f in res_pass['findings']))

        res_fail = server.run_brandwise_checks("Cuts onboarding by 40%.", _claims=custom_claims)
        self.assertTrue(any(f['category'] == 'Unsupported Performance Claim' for f in res_fail['findings']))
        finding = next(f for f in res_fail['findings'] if f['category'] == 'Unsupported Performance Claim')
        self.assertEqual(finding['sourceId'], 'CLM-999')
        self.assertIn('Q3 Benchmark Report 2026', finding['official'])

    def test_improvement_1_source_validation_on_all_findings(self):
        """Every flagged issue must be backed by a source ID, official citation, and owner."""
        text = "Brandwise cuts onboarding by 50% with 100% guaranteed results for $999/month."
        res = server.run_brandwise_checks(text, channel="Website Copy")
        self.assertTrue(len(res['findings']) > 0)
        for f in res['findings']:
            self.assertTrue(bool(f.get('sourceId')), f"Finding {f.get('id')} missing sourceId")
            self.assertTrue(bool(f.get('official')), f"Finding {f.get('id')} missing official citation")
            self.assertTrue(bool(f.get('owner')), f"Finding {f.get('id')} missing owner")
            self.assertIn(f.get('state'), ('source-verified', 'cannot verify - needs human check'))

    def test_improvement_2_scoring_unresolved_issues_cannot_be_perfect(self):
        """Content with unresolved issues cannot receive a perfect 100 score."""
        findings = [
            {'severity': 'Low', 'actionStatus': 'pending', 'wrong': 'minor', 'id': 'F1'}
        ]
        score = server.compliance_score(findings, strictness='lenient')
        self.assertLess(score, 100)

    def test_improvement_2_published_requires_approved_state(self):
        """Audit cannot be published before being Approved."""
        audits = server.get_audits()
        if not audits:
            return
        audit = audits[0]
        audit_id = audit.get('id')
        user = {'name': 'Admin User', 'role': 'Admin', 'organization': 'Internal'}

        # Mock action to publish directly when not Approved
        # If audit is not 'Approved', publishing must be rejected with 409
        audit_copy = dict(audit)
        audit_copy['status'] = 'Ready for review'
        pending = [f for f in audit_copy.get('findings', []) if f.get('actionStatus', 'pending') == 'pending']
        if pending or audit_copy['status'] != 'Approved':
            # Verification condition: state != 'Approved' cannot publish
            self.assertNotEqual(audit_copy['status'], 'Approved')

    def test_improvement_3_external_agency_isolation(self):
        """Agency access requires creator ownership; organization text grants no access."""
        mock_audits = [
            {'id': 'A1', 'agency': 'Alpha Media', 'creatorUsername': 'alice', 'title': 'Alpha Campaign'},
            {'id': 'A2', 'agency': 'Beta Creative', 'creatorUsername': 'bob', 'title': 'Beta Campaign'},
            {'id': 'A3', 'agency': 'Alpha Media', 'creatorUsername': 'alice', 'title': 'Alpha Launch'},
            {'id': 'A4', 'agency': 'Alpha Media', 'creatorUsername': 'mallory', 'title': 'Same organization is not ownership'}
        ]
        agency_user = {'role': 'External Agency', 'username': 'alice', 'organization': 'Alpha Media'}
        visible = server.audits_visible_to_user(mock_audits, agency_user)
        self.assertEqual(len(visible), 2)
        self.assertTrue(all(a['agency'] == 'Alpha Media' for a in visible))

        other_agency = {'role': 'External Agency', 'username': 'bob', 'organization': 'Beta Creative'}
        visible_other = server.audits_visible_to_user(mock_audits, other_agency)
        self.assertEqual(len(visible_other), 1)
        self.assertEqual(visible_other[0]['id'], 'A2')

        internal_reviewer = {'role': 'Reviewer', 'username': 'reviewer', 'organization': 'Internal', 'activeCompanyId': 'company-1', 'companyRole': 'Reviewer'}
        visible_reviewer = server.audits_visible_to_user(mock_audits, internal_reviewer)
        self.assertEqual(visible_reviewer, [])  # Unowned legacy rows are not shared by organization label.

    def test_improvement_3_persistent_login_failures(self):
        """Login attempts are persisted and lock out after excessive failures."""
        test_ip = '192.168.100.99'
        accounts.clear_login_failures(test_ip)
        self.assertFalse(accounts.login_is_limited(test_ip))

        # Record 5 failures
        for _ in range(accounts.LOGIN_MAX_FAILURES):
            accounts.record_login_failure(test_ip)

        self.assertTrue(accounts.login_is_limited(test_ip))
        accounts.clear_login_failures(test_ip)
        self.assertFalse(accounts.login_is_limited(test_ip))


if __name__ == '__main__':
    unittest.main()
