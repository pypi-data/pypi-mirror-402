"""
Semantic Load Calculator
<followup encodedFollowup="%7B%22snippet%22%3A%22Compute%20%CE%9B(%E2%84%93)%20%3D%20I_concept(%E2%84%93)%20-%20I_surface(%E2%84%93)%22%2C%22question%22%3A%22How%20does%20the%20formula%20%CE%9B(%E2%84%93)%20%3D%20I_concept(%E2%84%93)%20-%20I_surface(%E2%84%93)%20differentiate%20between%20concept-critical%20and%20surface-level%20tokens%3F%22%2C%22id%22%3A%22392d6906-5801-4dcd-b40d-81e0b3ed731d%22%7D" />
"""

import numpy as np
from collections import Counter
from typing import Dict, List, Optional, Tuple
import math
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass
class SemanticLoadConfig:
    """Configuration for semantic load calculation"""
    min_token_frequency: int = 5
    smoothing_factor: float = 1e-10
    concept_weight: float = 1.0
    surface_weight: float = 1.0

class SemanticLoadCalculator:
    """
    Calculate semantic load for tokens using:
    Λ(ℓ) = I_concept(ℓ) - I_surface(ℓ)
    """

    def __init__(self, config: Optional[SemanticLoadConfig] = None):
        self.config = config or SemanticLoadConfig()
        self.surface_probs: Dict[str, float] = {}
        self.concept_probs: Dict[str, Dict[str, float]] = {}

    def load_corpus(self, filepath: str) -> List[str]:
        """Load text corpus from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def load_concepts(self, filepath: str) -> Dict[str, List[str]]:
        """Load concept definitions from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenizer with lowercase"""
        return [token.lower() for token in text.split() if token.isalnum()]

    def compute_surface_probs(self, corpus: List[str]) -> Dict[str, float]:
        """Compute P(token | general text)"""
        all_tokens = []
        for text in corpus:
            tokens = self.tokenize(text)
            all_tokens.extend(tokens)

        token_counts = Counter(all_tokens)
        total_tokens = len(all_tokens)

        # Apply frequency threshold
        filtered_counts = {
            token: count for token, count in token_counts.items()
            if count >= self.config.min_token_frequency
        }

        return {
            token: count / total_tokens
            for token, count in filtered_counts.items()
        }

    def compute_concept_probs(self, concepts: Dict[str, List[str]]) -> Dict[str, Dict[str, float]]:
        """Compute P(token | concept) for each concept"""
        concept_probs = {}

        for concept, definitions in concepts.items():
            concept_tokens = []
            for definition in definitions:
                tokens = self.tokenize(definition)
                concept_tokens.extend(tokens)

            if concept_tokens:  # Only process if there are tokens
                token_counts = Counter(concept_tokens)
                total = len(concept_tokens)

                concept_probs[concept] = {
                    token: count / total
                    for token, count in token_counts.items()
                }

        return concept_probs

    def calculate_semantic_load(self, token: str) -> Optional[float]:
        """
        Calculate semantic load Λ(ℓ) for a token.

        Returns:
            float: Semantic load value, or None if token not found
        """
        # Get surface probability with smoothing
        p_surface = self.surface_probs.get(token, self.config.smoothing_factor)
        I_surface = -math.log2(p_surface) * self.config.surface_weight

        # Get concept probabilities
        concept_log_probs = []
        for concept_probs in self.concept_probs.values():
            p_concept = concept_probs.get(token, self.config.smoothing_factor)
            concept_log_probs.append(-math.log2(p_concept))

        if concept_log_probs:
            I_concept = np.mean(concept_log_probs) * self.config.concept_weight
            lambda_token = I_concept - I_surface
            return lambda_token
        else:
            return None

    def analyze(self, corpus_file: str, concepts_file: str) -> Dict[str, float]:
        """
        Analyze a corpus and compute semantic load for all tokens.

        Args:
            corpus_file: Path to general corpus text file
            concepts_file: Path to concepts JSON file

        Returns:
            Dictionary mapping tokens to their semantic load values
        """
        print("📊 Loading corpus and concepts...")
        corpus = self.load_corpus(corpus_file)
        concepts = self.load_concepts(concepts_file)

        print("📈 Computing probabilities...")
        self.surface_probs = self.compute_surface_probs(corpus)
        self.concept_probs = self.compute_concept_probs(concepts)

        # Get all unique tokens from both sources
        all_tokens = set(self.surface_probs.keys())
        for concept_probs in self.concept_probs.values():
            all_tokens.update(concept_probs.keys())

        print(f"🔍 Calculating semantic load for {len(all_tokens)} tokens...")
        lambda_values = {}
        for token in all_tokens:
            lambda_val = self.calculate_semantic_load(token)
            if lambda_val is not None:
                lambda_values[token] = lambda_val

        # Sort by semantic load (highest first)
        sorted_lambda = dict(sorted(
            lambda_values.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        print("✅ Analysis complete!")
        return sorted_lambda

    def save_results(self, lambda_values: Dict[str, float], output_file: str):
        """Save semantic load results to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(lambda_values, f, indent=2, ensure_ascii=False)

        # Also save summary statistics
        summary = {
            "total_tokens": len(lambda_values),
            "mean_lambda": np.mean(list(lambda_values.values())),
            "std_lambda": np.std(list(lambda_values.values())),
            "top_10": list(lambda_values.items())[:10],
            "bottom_10": list(lambda_values.items())[-10:]
        }

        summary_file = output_file.replace('.json', '_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

def main():
    """Example usage"""
    calculator = SemanticLoadCalculator()

    # Example paths - you should replace these with your actual files
    corpus_path = "../../data/corpora/wikipedia_sample.txt"
    concepts_path = "../../data/concepts/atomic_concepts.json"
    output_path = "../../results/semantic_load.json"

    # Create directories if they don't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Run analysis
    lambda_values = calculator.analyze(corpus_path, concepts_path)

    # Save results
    calculator.save_results(lambda_values, output_path)

    # Print summary
    print("\n📋 Semantic Load Summary:")
    print(f"Total tokens analyzed: {len(lambda_values)}")
    print(f"Top 5 high-semantic tokens:")
    for token, value in list(lambda_values.items())[:5]:
        print(f"  {token}: {value:.4f}")

    print(f"\nTop 5 low-semantic tokens:")
    for token, value in list(lambda_values.items())[-5:]:
        print(f"  {token}: {value:.4f}")

if __name__ == "__main__":
    main()
