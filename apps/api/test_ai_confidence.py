import unittest
from ai_confidence import calculate_ai_confidence

class TestAIConfidence(unittest.TestCase):
    
    def test_mock_low_confidence(self):
        # Even if score is high, if it's mock (no API key), confidence should be low
        res = calculate_ai_confidence(95, "text", {"is_mock": True})
        self.assertEqual(res, 10)

    def test_text_extremity_boost(self):
        # Score 95 (>90) should boost confidence
        # Text > 150 words should boost confidence
        # Base 50 + 30 (extremity) + 15 (length) = 95
        details = {"word_count": 200, "is_mock": False}
        res = calculate_ai_confidence(95, "text", details)
        self.assertEqual(res, 95)

    def test_text_uncertainty_penalty(self):
        # Score 50 should penalize confidence
        # Text < 30 words should penalize confidence
        # Base 50 - 20 (uncertain) - 15 (short) = 15
        details = {"word_count": 10, "is_mock": False}
        res = calculate_ai_confidence(50, "text", details)
        self.assertEqual(res, 15)

    def test_video_consistency_boost(self):
        # Consistent signals (all high) should boost
        # Base 50 + 30 (score 90+) + 20 (consistency) = 100
        details = {"signals": [90, 95, 92], "is_mock": False}
        res = calculate_ai_confidence(92, "video", details)
        self.assertEqual(res, 100)

    def test_video_mixed_signals_penalty(self):
        # Mixed signals (score 90 vs 10 in frames) should penalize
        # Base 50 + 30 (avg score 60 is not extreme, so no boost... wait)
        # Avg score 55 (uncertain) -> 50 - 20 = 30
        # Mixed signals penalty -> 30 - 25 = 5
        details = {"signals": [95, 15], "is_mock": False}
        res = calculate_ai_confidence(55, "video", details)
        self.assertEqual(res, 5)

if __name__ == '__main__':
    unittest.main()
