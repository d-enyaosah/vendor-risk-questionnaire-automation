import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vendor_risk_analyzer import load_reviews, normalize_response, review_row, write_csv, write_dashboard


class VendorRiskAnalyzerTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize_response(" implemented "), "Yes")
        self.assertEqual(normalize_response("in progress"), "Partial")
        self.assertEqual(normalize_response("unknown"), "Unclear")

    def test_missing_evidence_increases_risk(self):
        review = review_row({"control_id": "A", "domain": "IAM", "question": "MFA?", "response": "No",
                             "severity": "critical", "evidence_required": "yes", "evidence": "", "owner": "Security"})
        self.assertEqual(review.risk_score, 12)
        self.assertEqual(review.risk_rating, "Critical")
        self.assertEqual(review.evidence_status, "Missing")

    def test_end_to_end_outputs(self):
        source = Path(__file__).parents[1] / "data" / "sample_vendor_questionnaire.csv"
        reviews = load_reviews(source)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_csv(reviews, root / "review.csv")
            write_dashboard(reviews, root / "dashboard.html", "Test Vendor")
            self.assertTrue((root / "review.csv").read_text().startswith("control_id"))
            self.assertIn("Test Vendor", (root / "dashboard.html").read_text())


if __name__ == "__main__":
    unittest.main()
