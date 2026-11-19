import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.engines.claims_engine import claims_engine
from app.engines.rules_engine import rules_engine
from app.engines.tone_engine import tone_engine
from app.engines.visual_engine import visual_engine
from app.engines.orchestrator import orchestrator
from app.store import store

class TestBrandWiseBackend(unittest.TestCase):

    def test_claims_engine_unsupported_percentage(self):
        """PDF Page 6: 'Cuts onboarding time by 30%' must flag unsupported claim against approved 20% limit."""
        content = "BrandWise cuts onboarding time by 30% for high velocity teams."
        claims = store.get_claims()
        findings = claims_engine.verify_claims(content, claims)
        self.assertTrue(any("30%" in f["title"] and f["severity"] == "High" for f in findings))
        f_perf = next(f for f in findings if "30%" in f["title"])
        self.assertEqual(f_perf["sourceId"], "CLM-001")
        self.assertEqual(f_perf["fix"], "cuts onboarding time by up to 20%")

    def test_claims_engine_expired_claim_uncertainty(self):
        """PDF Page 6 & 7: Expired pricing evidence must trigger explicit 'cannot verify - needs human check'."""
        content = "Get BrandWise today starting at $49/month with full features."
        claims = store.get_claims()
        findings = claims_engine.verify_claims(content, claims)
        f_exp = next((f for f in findings if "$49" in f["wrong"]), None)
        self.assertIsNotNone(f_exp)
        self.assertEqual(f_exp["state"], "cannot verify - needs human check")
        self.assertEqual(f_exp["sourceId"], "CLM-005")

    def test_rules_engine_brand_casing(self):
        """'Brandwise' (incorrect casing) must be flagged; 'BrandWise' (correct casing) must NOT be flagged."""
        guidelines = store.get_guidelines()
        
        # Test incorrect casing
        findings_bad = rules_engine.verify_rules("Check out Brandwise today.", guidelines)
        self.assertTrue(any(f["wrong"] == "Brandwise" for f in findings_bad))
        
        # Test correct casing
        findings_good = rules_engine.verify_rules("Check out BrandWise today.", guidelines)
        self.assertFalse(any(f["wrong"] == "BrandWise" for f in findings_good))

    def test_tone_engine_indian_english_fairness(self):
        """PDF Page 10: Indian English phrasing ('prepone', 'revert back') must not be penalized."""
        guidelines = store.get_guidelines()
        text = "Kindly note: We have preponed the product launch to Friday. Please revert back."
        findings = tone_engine.verify_tone(text, guidelines)
        self.assertEqual(len(findings), 0)

    def test_visual_engine_contrast(self):
        """WCAG 2.1 AA/AAA contrast calculations."""
        # White on Brand Blue (#0079C8) is approx 4.62:1 (Passes AA Normal Text >= 4.5)
        res = visual_engine.calculate_contrast("#FFFFFF", "#0079C8")
        self.assertTrue(res["passesAANormalText"])
        self.assertTrue(res["passesAALargeText"])

        # Low contrast pair (e.g. #888888 on #999999) must fail
        res_fail = visual_engine.calculate_contrast("#888888", "#999999")
        self.assertFalse(res_fail["passesAANormalText"])

    def test_visual_engine_readability(self):
        """Flesch-Kincaid ease and grade level calculator."""
        text = "BrandWise is a brand governance platform. It checks content against approved guidelines, facts, and assets."
        res = visual_engine.calculate_readability(text)
        self.assertIn("readingEase", res)
        self.assertIn("gradeLevel", res)
        self.assertGreater(res["readingEase"], 0)

    def test_orchestrator_scoring(self):
        """Orchestrator computes deductions and grounded score."""
        clean_text = "Acme Technologies was established in 2012. BrandWise cuts onboarding time by up to 20%. Terms and conditions apply."
        res = orchestrator.run_full_audit(clean_text, channel="Website Copy")
        self.assertEqual(len(res["findings"]), 0)
        self.assertEqual(res["score"], 100)

if __name__ == "__main__":
    unittest.main()
