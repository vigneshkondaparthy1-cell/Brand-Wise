import json
import unittest
from pathlib import Path

from review_validation import citation_matches, validate_findings


CLAIMS = json.loads((Path(__file__).resolve().parents[1] / 'claims-data.json').read_text(encoding='utf-8'))


class CitationValidationTests(unittest.TestCase):
    def test_related_phrase_is_relevant(self):
        claim = next(item for item in CLAIMS if item['id'] == 'CLM-001')
        self.assertTrue(citation_matches('cuts onboarding by 30%', claim))

    def test_unrelated_phrase_is_not_relevant(self):
        claim = next(item for item in CLAIMS if item['id'] == 'CLM-001')
        self.assertFalse(citation_matches("world's best platform", claim))

    def test_numeric_claim_requires_matching_evidence_number(self):
        claim = next(item for item in CLAIMS if item['id'] == 'CLM-001')
        self.assertFalse(citation_matches('cuts onboarding time by 70%', claim))

    def test_irrelevant_citation_is_removed_and_flag_is_labelled(self):
        finding = {'title': 'Unrelated flag', 'wrong': "world's best", 'sourceId': 'CLM-001'}
        checked = validate_findings([finding], "This is the world's best.", CLAIMS, 'Gemini', 'demo-model')
        self.assertEqual(len(checked), 1)
        self.assertEqual(checked[0]['sourceId'], '')
        self.assertIn('does not match', checked[0]['citationIssue'])
        self.assertEqual(checked[0]['confidence'], 72)


if __name__ == '__main__':
    unittest.main()
