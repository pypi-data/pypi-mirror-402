"""
inputless-engines - fitness_functions.py

Fitness evaluation functions for pattern quality assessment.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from .types import Pattern, Individual


class FitnessEvaluator:
    """
    Evaluates fitness of patterns and individuals.
    
    Fitness is based on:
    - Accuracy: How well pattern matches actual behavior
    - Relevance: Relevance to current context
    - Novelty: Uniqueness compared to population
    """

    def __init__(
        self,
        accuracy_weight: float = 0.7,
        relevance_weight: float = 0.2,
        novelty_weight: float = 0.1,
    ):
        """
        Initialize fitness evaluator.
        
        Args:
            accuracy_weight: Weight for accuracy component
            relevance_weight: Weight for relevance component
            novelty_weight: Weight for novelty component
        """
        self.accuracy_weight = accuracy_weight
        self.relevance_weight = relevance_weight
        self.novelty_weight = novelty_weight

        # Normalize weights
        total = accuracy_weight + relevance_weight + novelty_weight
        if total > 0:
            self.accuracy_weight /= total
            self.relevance_weight /= total
            self.novelty_weight /= total

    def evaluate_individual(
        self,
        individual: Any,
        behavioral_events: Optional[List[Dict[str, Any]]] = None,
        population: Optional[List[Any]] = None,
    ) -> float:
        """
        Evaluate fitness of an individual.
        
        Args:
            individual: Individual to evaluate (DEAP Individual or genotype)
            behavioral_events: Optional behavioral events for evaluation
            population: Optional population for novelty calculation
            
        Returns:
            Fitness score (0.0 - 1.0)
        """
        # Convert individual to patterns if needed
        if isinstance(individual, list):
            # Assume it's a genotype (list of genes)
            patterns = self._genotype_to_patterns(individual)
        else:
            # Assume it's already patterns
            patterns = individual if isinstance(individual, list) else [individual]

        # Calculate components
        accuracy = self._calculate_accuracy(patterns, behavioral_events)
        relevance = self._calculate_relevance(patterns, behavioral_events)
        novelty = self._calculate_novelty(patterns, population)

        # Weighted combination
        fitness = (
            accuracy * self.accuracy_weight
            + relevance * self.relevance_weight
            + novelty * self.novelty_weight
        )

        return max(0.0, min(1.0, fitness))

    def evaluate_pattern(
        self,
        pattern: Pattern,
        behavioral_events: Optional[List[Dict[str, Any]]] = None,
    ) -> float:
        """
        Evaluate fitness of a single pattern.
        
        Args:
            pattern: Pattern to evaluate
            behavioral_events: Optional behavioral events
            
        Returns:
            Fitness score (0.0 - 1.0)
        """
        accuracy = self._calculate_pattern_accuracy(pattern, behavioral_events)
        relevance = self._calculate_pattern_relevance(pattern, behavioral_events)
        novelty = 0.5  # Default novelty for single pattern

        fitness = (
            accuracy * self.accuracy_weight
            + relevance * self.relevance_weight
            + novelty * self.novelty_weight
        )

        return max(0.0, min(1.0, fitness))

    def _calculate_accuracy(
        self,
        patterns: List[Pattern],
        behavioral_events: Optional[List[Dict[str, Any]]],
    ) -> float:
        """
        Calculate accuracy component of fitness.
        
        Args:
            patterns: Patterns to evaluate
            behavioral_events: Behavioral events for matching
            
        Returns:
            Accuracy score (0.0 - 1.0)
        """
        if not patterns:
            return 0.0

        if not behavioral_events:
            # No events to match against, return default
            return 0.5

        # Count how many patterns match events
        matches = 0
        total = len(patterns)

        for pattern in patterns:
            if self._pattern_matches_events(pattern, behavioral_events):
                matches += 1

        return matches / total if total > 0 else 0.0

    def _calculate_relevance(
        self,
        patterns: List[Pattern],
        behavioral_events: Optional[List[Dict[str, Any]]],
    ) -> float:
        """
        Calculate relevance component of fitness.
        
        Args:
            patterns: Patterns to evaluate
            behavioral_events: Behavioral events for context
            
        Returns:
            Relevance score (0.0 - 1.0)
        """
        if not patterns:
            return 0.0

        if not behavioral_events:
            return 0.5

        # Calculate relevance based on event frequency
        event_type_counts = {}
        for event in behavioral_events:
            event_type = event.get("type", "unknown")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        total_events = len(behavioral_events)
        if total_events == 0:
            return 0.0

        relevance_scores = []
        for pattern in patterns:
            pattern_relevance = 0.0
            for event_type in pattern.event_types:
                count = event_type_counts.get(event_type, 0)
                pattern_relevance += count / total_events
            relevance_scores.append(pattern_relevance / len(pattern.event_types) if pattern.event_types else 0.0)

        return np.mean(relevance_scores) if relevance_scores else 0.0

    def _calculate_novelty(
        self,
        patterns: List[Pattern],
        population: Optional[List[Any]],
    ) -> float:
        """
        Calculate novelty component of fitness.
        
        Args:
            patterns: Patterns to evaluate
            population: Population for comparison
            
        Returns:
            Novelty score (0.0 - 1.0)
        """
        if not patterns:
            return 0.0

        if not population:
            # No population to compare, return default
            return 0.5

        # Calculate uniqueness compared to population
        pattern_signatures = set()
        for pattern in patterns:
            signature = self._pattern_signature(pattern)
            pattern_signatures.add(signature)

        population_signatures = set()
        for individual in population:
            if isinstance(individual, list):
                ind_patterns = self._genotype_to_patterns(individual)
            else:
                ind_patterns = [individual] if hasattr(individual, 'event_types') else []
            
            for p in ind_patterns:
                signature = self._pattern_signature(p)
                population_signatures.add(signature)

        # Novelty = proportion of unique patterns
        unique_count = len(pattern_signatures - population_signatures)
        total_count = len(pattern_signatures)

        return unique_count / total_count if total_count > 0 else 0.0

    def _pattern_matches_events(
        self, pattern: Pattern, events: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if pattern matches events.
        
        Args:
            pattern: Pattern to check
            events: Events to match against
            
        Returns:
            True if pattern matches
        """
        if not pattern.event_types or not events:
            return False

        # Check if pattern event types appear in events
        event_types = {event.get("type", "unknown") for event in events}
        pattern_types = set(pattern.event_types)

        return len(pattern_types & event_types) > 0

    def _pattern_signature(self, pattern: Pattern) -> str:
        """
        Create a signature for pattern uniqueness.
        
        Args:
            pattern: Pattern to create signature for
            
        Returns:
            Signature string
        """
        event_types_str = ",".join(sorted(pattern.event_types))
        sequence_str = ",".join(pattern.sequence)
        return f"{event_types_str}|{sequence_str}|{pattern.timing_constraints.get('window_ms', 0)}"

    def _genotype_to_patterns(self, genotype: List[Dict[str, Any]]) -> List[Pattern]:
        """
        Convert genotype to patterns.
        
        Args:
            genotype: Genotype representation
            
        Returns:
            List of patterns
        """
        from .pattern_encoding import PatternEncoder

        encoder = PatternEncoder()
        patterns = []
        for i, gene in enumerate(genotype):
            pattern = encoder.decode_genotype(gene, f"pattern_{i}", generation=0)
            patterns.append(pattern)
        return patterns

    def _calculate_pattern_accuracy(
        self, pattern: Pattern, behavioral_events: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Calculate accuracy for a single pattern."""
        if not behavioral_events:
            return 0.5

        matches = sum(
            1
            for event in behavioral_events
            if event.get("type") in pattern.event_types
        )
        return matches / len(behavioral_events) if behavioral_events else 0.0

    def _calculate_pattern_relevance(
        self, pattern: Pattern, behavioral_events: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Calculate relevance for a single pattern."""
        if not behavioral_events:
            return 0.5

        event_type_counts = {}
        for event in behavioral_events:
            event_type = event.get("type", "unknown")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        total_events = len(behavioral_events)
        if total_events == 0:
            return 0.0

        relevance = 0.0
        for event_type in pattern.event_types:
            count = event_type_counts.get(event_type, 0)
            relevance += count / total_events

        return relevance / len(pattern.event_types) if pattern.event_types else 0.0
