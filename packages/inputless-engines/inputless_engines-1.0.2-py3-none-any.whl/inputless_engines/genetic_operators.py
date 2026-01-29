"""
inputless-engines - genetic_operators.py

Genetic operators for selection, crossover, and mutation operations.
"""

from typing import List, Any, Tuple
import numpy as np
import random
from deap import tools
from .types import MutationEngineConfig


class GeneticOperators:
    """
    Genetic operators for selection, crossover, and mutation.
    
    Provides implementations for:
    - Selection: Tournament, roulette wheel, rank-based
    - Crossover: Uniform, single-point, two-point
    - Mutation: Point, structural, behavioral
    """

    def __init__(self, config: MutationEngineConfig):
        """
        Initialize genetic operators.
        
        Args:
            config: Mutation engine configuration
        """
        self.config = config

    def select(
        self, individuals: List[Any], k: int
    ) -> List[Any]:
        """
        Select individuals from population.
        
        Args:
            individuals: Population
            k: Number to select
            
        Returns:
            Selected individuals
        """
        if self.config.selection_method == "tournament":
            return tools.selTournament(individuals, k, self.config.tournament_size)
        elif self.config.selection_method == "roulette":
            return tools.selRoulette(individuals, k)
        elif self.config.selection_method == "rank":
            return tools.selBest(individuals, k)
        else:
            return tools.selTournament(individuals, k, self.config.tournament_size)

    def crossover(
        self, ind1: Any, ind2: Any
    ) -> Tuple[Any, Any]:
        """
        Perform crossover between two individuals.
        
        Args:
            ind1: First parent
            ind2: Second parent
            
        Returns:
            Two offspring
        """
        if random.random() > self.config.crossover_rate:
            return ind1, ind2

        if self.config.crossover_type == "uniform":
            return self._uniform_crossover(ind1, ind2)
        elif self.config.crossover_type == "single_point":
            return self._single_point_crossover(ind1, ind2)
        elif self.config.crossover_type == "two_point":
            return self._two_point_crossover(ind1, ind2)
        else:
            return self._uniform_crossover(ind1, ind2)

    def _uniform_crossover(self, ind1: Any, ind2: Any) -> Tuple[Any, Any]:
        """Uniform crossover."""
        child1 = ind1[:]
        child2 = ind2[:]

        min_len = min(len(child1), len(child2))
        for i in range(min_len):
            if random.random() < 0.5:
                child1[i], child2[i] = child2[i], child1[i]

        return child1, child2

    def _single_point_crossover(self, ind1: Any, ind2: Any) -> Tuple[Any, Any]:
        """Single-point crossover."""
        if len(ind1) < 2 or len(ind2) < 2:
            return ind1, ind2

        point = random.randint(1, min(len(ind1), len(ind2)) - 1)
        child1 = ind1[:point] + ind2[point:]
        child2 = ind2[:point] + ind1[point:]

        return child1, child2

    def _two_point_crossover(self, ind1: Any, ind2: Any) -> Tuple[Any, Any]:
        """Two-point crossover."""
        if len(ind1) < 3 or len(ind2) < 3:
            return ind1, ind2

        point1 = random.randint(1, min(len(ind1), len(ind2)) - 1)
        point2 = random.randint(1, min(len(ind1), len(ind2)) - 1)
        start, end = min(point1, point2), max(point1, point2)

        child1 = ind1[:start] + ind2[start:end] + ind1[end:]
        child2 = ind2[:start] + ind1[start:end] + ind2[end:]

        return child1, child2

    def mutate(self, individual: Any) -> Tuple[Any]:
        """
        Mutate an individual.
        
        Args:
            individual: Individual to mutate
            
        Returns:
            Mutated individual (tuple for DEAP)
        """
        if random.random() > self.config.mutation_rate:
            return (individual,)

        mutated = individual[:]
        mutation_type = random.choice(["point", "structural", "behavioral"])

        if mutation_type == "point":
            self._point_mutation(mutated)
        elif mutation_type == "structural":
            self._structural_mutation(mutated)
        elif mutation_type == "behavioral":
            self._behavioral_mutation(mutated)

        return (mutated,)

    def _point_mutation(self, individual: Any) -> None:
        """Point mutation: modify gene parameters."""
        if not individual:
            return

        index = random.randint(0, len(individual) - 1)
        gene = individual[index]

        if "parameters" in gene:
            params = gene["parameters"]
            if "duration" in params:
                params["duration"] = max(
                    0, params["duration"] + self._get_mutation_value()
                )
            if "frequency" in params:
                params["frequency"] = np.clip(
                    params["frequency"] + self._get_mutation_value(), 0, 1
                )

        if "weight" in gene:
            gene["weight"] = np.clip(
                gene["weight"] + self._get_mutation_value(), 0, 1
            )

        if "timing_window" in gene:
            gene["timing_window"] = max(
                0, gene["timing_window"] + self._get_mutation_value() * 1000
            )

    def _structural_mutation(self, individual: Any) -> None:
        """Structural mutation: add or remove genes."""
        from .pattern_encoding import PatternEncoder

        encoder = PatternEncoder()

        if random.random() < 0.5 and len(individual) > 1:
            # Remove gene
            index = random.randint(0, len(individual) - 1)
            individual.pop(index)
        else:
            # Add gene
            new_gene = encoder.create_random_gene()
            individual.append(new_gene)

    def _behavioral_mutation(self, individual: Any) -> None:
        """Behavioral mutation: change event type."""
        if not individual:
            return

        index = random.randint(0, len(individual) - 1)
        gene = individual[index]

        event_types = ["ui.click", "ui.hover", "scroll", "nav.pageview", "focus"]
        if "event_types" in gene and gene["event_types"]:
            # Change one event type
            gene["event_types"][0] = random.choice(event_types)
        elif "type" in gene:
            # Legacy format
            gene["type"] = random.choice(event_types)

    def _get_mutation_value(self) -> float:
        """Get mutation value based on mutation type."""
        if self.config.mutation_type == "gaussian":
            return np.random.normal(0, self.config.mutation_strength)
        elif self.config.mutation_type == "uniform":
            return (random.random() - 0.5) * 2 * self.config.mutation_strength
        else:  # adaptive
            # Adaptive mutation based on diversity (simplified)
            diversity_factor = random.random()  # Would be calculated from actual diversity
            return np.random.normal(
                0, self.config.mutation_strength * (1 + diversity_factor)
            )
