import unittest

from server import check_text_accessibility, run_brandwise_checks


class AccessibilityChecksTests(unittest.TestCase):
    def test_readability_grade_uses_guideline_threshold(self):
        result = check_text_accessibility('Clear words help teams review copy. Keep each sentence short.')
        self.assertIsNotNone(result['readingGrade'])
        self.assertEqual(result['maxGrade'], 12.0)

    def test_readability_over_limit_is_reported_in_audit(self):
        copy = ('The methodological characteristics of organizational implementation require comprehensive interdisciplinary coordination and communication. ' * 3)
        result = run_brandwise_checks(copy, channel='Internal Memo')
        self.assertTrue(any(f['category'] == 'Accessibility - Readability' for f in result['findings']))

    def test_heading_level_skip_is_reported(self):
        result = check_text_accessibility('# Campaign\n### Results')
        self.assertEqual(result['headingCount'], 2)
        self.assertEqual(len(result['headingIssues']), 1)
        self.assertIn('skips', result['headingIssues'][0]['message'])

    def test_correct_heading_order_passes(self):
        result = check_text_accessibility('# Campaign\n## Results\n### Details')
        self.assertEqual(result['headingIssues'], [])

    def test_fixed_required_disclaimer_is_excluded_from_copy_readability_estimate(self):
        from server import get_guidelines
        disclaimer = get_guidelines()['requiredDisclaimer']
        result = check_text_accessibility(disclaimer)
        self.assertIsNone(result['readingGrade'])


if __name__ == '__main__':
    unittest.main()
