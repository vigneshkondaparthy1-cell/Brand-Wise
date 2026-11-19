import unittest

from server import get_current_ai_reference_claims, run_brandwise_checks


class DeterministicRuleTests(unittest.TestCase):
    def test_exact_claim_phrase_is_flagged_without_ai(self):
        result = run_brandwise_checks('Our website cuts onboarding by 30%.', channel='Internal Memo')
        self.assertTrue(any(f['category'] == 'Prohibited Claim Wording' for f in result['findings']))

    def test_expired_pricing_is_explicitly_a_demo_cannot_verify_case(self):
        result = run_brandwise_checks('Starter pricing is $49/month.', channel='Internal Memo')
        expired = [f for f in result['findings'] if f.get('sourceId') == 'CLM-005']
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0]['state'], 'cannot verify - needs human check')
        self.assertIn('demo', expired[0]['title'].casefold())

    def test_active_pricing_claim_is_recognized_and_unknown_price_is_not(self):
        current = run_brandwise_checks('Starter tiers start at $79 per seat per month.', channel='Internal Memo')
        unknown = run_brandwise_checks('Starter tiers start at $88/month.', channel='Internal Memo')
        self.assertFalse(any(f['category'] == 'Expired Claim / Missing Current Proof' for f in current['findings']))
        self.assertTrue(any(f['category'] == 'Expired Claim / Missing Current Proof' for f in unknown['findings']))

    def test_full_disclaimer_is_required_for_customer_copy(self):
        short = run_brandwise_checks('Terms and conditions apply.', channel='Website Copy')
        full = run_brandwise_checks(
            'Terms and conditions apply. Performance metrics reflect verified customer benchmarks and may vary based on deployment configuration.',
            channel='Website Copy',
        )
        self.assertTrue(any(f['category'] == 'Missing Legal Notice' for f in short['findings']))
        self.assertFalse(any(f['category'] == 'Missing Legal Notice' for f in full['findings']))

    def test_exact_rule_matches_show_full_confidence(self):
        result = run_brandwise_checks('This is the world\'s best product.', channel='Internal Memo')
        finding = next(f for f in result['findings'] if f['category'] == 'Prohibited Terminology')
        self.assertEqual(finding['confidence'], 100)
        self.assertEqual(finding['confidenceBasis'], 'Exact deterministic rule match')

    def test_blanket_gdpr_claim_is_flagged_as_unverified_pending_legal_review(self):
        result = run_brandwise_checks('We are fully GDPR compliant.', channel='Internal Memo')
        finding = next(f for f in result['findings'] if f.get('sourceId') == 'CLM-004')
        self.assertEqual(finding['state'], 'cannot verify - needs human check')
        self.assertIn('legal review', finding['why'].casefold())

    def test_ai_context_excludes_expired_and_pending_review_claims(self):
        claims = get_current_ai_reference_claims()
        ids = {claim['id'] for claim in claims}
        self.assertIn('CLM-001', ids)
        self.assertNotIn('CLM-004', ids)
        self.assertNotIn('CLM-005', ids)


if __name__ == '__main__':
    unittest.main()
