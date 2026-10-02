import unittest

from plagiarism import detect

ORIGINAL = "Machine learning is used to predict rainfall using historical weather data."


class DetectorTests(unittest.TestCase):
    def test_identical_text_is_100_percent(self):
        r = detect(ORIGINAL, ORIGINAL)
        self.assertTrue(r["plagiarism_detected"])
        self.assertEqual(r["similarity"], 100.0)
        self.assertEqual(r["matches"][0]["text"], ORIGINAL)

    def test_case_and_punctuation_are_ignored(self):
        r = detect(ORIGINAL, "MACHINE LEARNING, is used to predict rainfall... using historical weather data")
        self.assertEqual(r["similarity"], 100.0)

    def test_unrelated_text_is_not_plagiarism(self):
        r = detect(ORIGINAL, "The cricket match was postponed because of heavy traffic near the stadium.")
        self.assertFalse(r["plagiarism_detected"])
        self.assertEqual(r["similarity"], 0.0)

    def test_partial_copy(self):
        sub = "Today I learned that machine learning is used to predict rainfall using old records of the sky."
        r = detect(ORIGINAL, sub)
        self.assertTrue(0 < r["similarity"] < 100)
        self.assertIn("machine learning is used to predict rainfall using", r["matches"][0]["text"].lower())

    def test_kmp_exact_sentence(self):
        sub = "Rainfall is nice. " + ORIGINAL
        r = detect(ORIGINAL + " Other text here.", sub, algorithm="kmp")
        self.assertTrue(r["plagiarism_detected"])
        self.assertEqual(len(r["matches"]), 1)

    def test_highlight_segments_rebuild_text(self):
        sub = "Intro words here. " + ORIGINAL + " Closing words here."
        r = detect(ORIGINAL, sub)
        self.assertEqual("".join(s["text"] for s in r["submitted_segments"]), sub)
        self.assertEqual("".join(s["text"] for s in r["original_segments"]), ORIGINAL)

    def test_errors(self):
        with self.assertRaises(ValueError):
            detect("!!! ???", ORIGINAL)
        with self.assertRaises(ValueError):
            detect(ORIGINAL, ORIGINAL, algorithm="nope")


if __name__ == "__main__":
    unittest.main()
