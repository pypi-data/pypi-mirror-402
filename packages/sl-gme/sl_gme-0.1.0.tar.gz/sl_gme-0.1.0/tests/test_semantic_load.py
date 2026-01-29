"""
Tests for semantic load calculation
"""

import unittest
import tempfile
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from semantic_load.calculator import SemanticLoadCalculator

class TestSemanticLoad(unittest.TestCase):
    def setUp(self):
        self.calculator = SemanticLoadCalculator()

        # Create temporary files for testing
        self.temp_dir = tempfile.mkdtemp()

        # Create sample corpus
        self.corpus_file = Path(self.temp_dir) / "corpus.txt"
        self.corpus_file.write_text("""
        mathematics physics biology chemistry
        the quick brown fox jumps over the lazy dog
        science art philosophy linguistics
        """)

        # Create sample concepts
        self.concepts_file = Path(self.temp_dir) / "concepts.json"
        concepts = {
            "science": ["The study of the natural world"],
            "art": ["Creative expression and imagination"]
        }
        self.concepts_file.write_text(json.dumps(concepts))

    def test_tokenize(self):
        tokens = self.calculator.tokenize("Hello World! Test 123.")
        self.assertEqual(tokens, ["hello", "world", "test"])

    def test_compute_surface_probs(self):
        corpus = ["hello world", "world test"]
        probs = self.calculator.compute_surface_probs(corpus)

        self.assertIn("hello", probs)
        self.assertIn("world", probs)
        self.assertIn("test", probs)

        # Check probabilities sum to ~1 for these tokens
        total_prob = sum(probs.values())
        self.assertAlmostEqual(total_prob, 1.0, places=5)

    def test_analyze(self):
        lambda_values = self.calculator.analyze(
            str(self.corpus_file),
            str(self.concepts_file)
        )

        # Should have calculated lambda values
        self.assertGreater(len(lambda_values), 0)

        # Check that specialized words have higher lambda
        # (this is a simplified test - actual values depend on the data)
        if "science" in lambda_values and "the" in lambda_values:
            # "science" should have higher semantic load than "the"
            self.assertGreater(lambda_values["science"], lambda_values["the"])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

if __name__ == "__main__":
    unittest.main()
