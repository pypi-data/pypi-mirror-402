"""
inputless-engines - pattern_encoding.py

Pattern encoding/decoding utilities for genotype-phenotype conversion.
"""

from typing import List, Dict, Any, Optional
import random
from .types import Pattern, PatternGene


class PatternEncoder:
    """
    Encodes and decodes patterns between genotype and phenotype representations.
    
    Genotype: Genetic representation (for genetic algorithms)
    Phenotype: Behavioral pattern representation (for pattern recognition)
    """

    @staticmethod
    def encode_pattern(pattern: Pattern) -> Dict[str, Any]:
        """
        Encode a Pattern (phenotype) to genotype representation.
        
        Args:
            pattern: Pattern to encode
            
        Returns:
            Genotype dictionary
        """
        return {
            "event_types": pattern.event_types,
            "sequence_length": len(pattern.sequence),
            "timing_window": pattern.timing_constraints.get("window_ms", 5000),
            "spatial_cluster": pattern.spatial_constraints is not None,
            "weight": pattern.fitness or 0.5,
        }

    @staticmethod
    def decode_genotype(
        gene: Dict[str, Any], pattern_id: str, generation: int = 0
    ) -> Pattern:
        """
        Decode genotype to Pattern (phenotype).
        
        Args:
            gene: Genotype dictionary
            pattern_id: Pattern identifier
            generation: Generation number
            
        Returns:
            Pattern object
        """
        return Pattern(
            pattern_id=pattern_id,
            event_types=gene.get("event_types", []),
            sequence=[
                f"step_{i}" for i in range(gene.get("sequence_length", 2))
            ],
            timing_constraints={"window_ms": gene.get("timing_window", 5000)},
            spatial_constraints={"cluster": True}
            if gene.get("spatial_cluster", False)
            else None,
            fitness=gene.get("weight", 0.5),
            generation=generation,
        )

    @staticmethod
    def create_random_gene() -> Dict[str, Any]:
        """
        Create a random pattern gene.
        
        Returns:
            Random genotype dictionary
        """
        event_types = ["ui.click", "ui.hover", "scroll", "nav.pageview", "focus"]
        return {
            "event_types": random.sample(
                event_types, k=random.randint(1, min(3, len(event_types)))
            ),
            "sequence_length": random.randint(2, 5),
            "timing_window": random.uniform(1000, 10000),
            "spatial_cluster": random.choice([True, False]),
            "weight": random.uniform(0.1, 1.0),
        }

    @staticmethod
    def validate_genotype(gene: Dict[str, Any]) -> bool:
        """
        Validate genotype structure.
        
        Args:
            gene: Genotype to validate
            
        Returns:
            True if valid
        """
        required_keys = ["event_types", "sequence_length", "timing_window", "weight"]
        if not all(key in gene for key in required_keys):
            return False

        if not isinstance(gene["event_types"], list) or len(gene["event_types"]) == 0:
            return False

        if not isinstance(gene["sequence_length"], int) or gene["sequence_length"] < 1:
            return False

        if (
            not isinstance(gene["timing_window"], (int, float))
            or gene["timing_window"] < 0
        ):
            return False

        if (
            not isinstance(gene["weight"], (int, float))
            or not (0.0 <= gene["weight"] <= 1.0)
        ):
            return False

        return True

    @staticmethod
    def normalize_genotype(gene: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize genotype values to valid ranges.
        
        Args:
            gene: Genotype to normalize
            
        Returns:
            Normalized genotype
        """
        normalized = gene.copy()

        # Ensure weight is in [0, 1]
        if "weight" in normalized:
            normalized["weight"] = max(0.0, min(1.0, normalized["weight"]))

        # Ensure timing_window is positive
        if "timing_window" in normalized:
            normalized["timing_window"] = max(0.0, normalized["timing_window"])

        # Ensure sequence_length is at least 1
        if "sequence_length" in normalized:
            normalized["sequence_length"] = max(1, normalized["sequence_length"])

        # Ensure event_types is a list
        if "event_types" in normalized and not isinstance(
            normalized["event_types"], list
        ):
            normalized["event_types"] = []

        return normalized
