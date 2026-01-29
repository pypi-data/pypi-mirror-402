"""
inputless-engines - mutation_engine.py

Genetic algorithms for pattern evolution
"""

from typing import List, Optional, Dict, Any
from deap import base, creator, tools
import numpy as np
import random

from .types import MutationEngineConfig, Pattern, Individual
from .genetic_operators import GeneticOperators
from .fitness_functions import FitnessEvaluator
from .pattern_encoding import PatternEncoder


class MutationEngine:
    """
    Genetic algorithm engine for evolving behavioral patterns.
    
    Uses DEAP framework for genetic algorithm operations.
    Evolves patterns to discover optimal recognition strategies.
    """

    def __init__(self, config: Optional[MutationEngineConfig] = None):
        """
        Initialize mutation engine.
        
        Args:
            config: Engine configuration (uses defaults if None)
        """
        self.config = config or MutationEngineConfig()
        self.toolbox = self._setup_toolbox()
        self.population = None
        self.generation = 0
        self.best_individual: Optional[Individual] = None
        self.fitness_history: List[float] = []
        self.hall_of_fame = tools.HallOfFame(self.config.elite_size)
        self.stats = tools.Statistics(lambda ind: ind.fitness.values[0])
        self._setup_statistics()
        self.behavioral_events: Optional[List[Dict[str, Any]]] = None

        # Initialize operators and evaluator
        self.genetic_operators = GeneticOperators(self.config)
        self.fitness_evaluator = FitnessEvaluator()

    def _setup_toolbox(self) -> base.Toolbox:
        """Setup DEAP toolbox with operators."""
        # Create fitness and individual classes
        if not hasattr(creator, "FitnessMax"):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()

        # Register individual creation
        encoder = PatternEncoder()
        toolbox.register("pattern_gene", encoder.create_random_gene)
        toolbox.register(
            "individual",
            tools.initRepeat,
            creator.Individual,
            toolbox.pattern_gene,
            n=10,  # Initial pattern count per individual
        )

        # Register population creation
        toolbox.register(
            "population", tools.initRepeat, list, toolbox.individual
        )

        # Register genetic operators
        toolbox.register("evaluate", self._evaluate_fitness)
        toolbox.register("mate", self._crossover)
        toolbox.register("mutate", self._mutate)
        toolbox.register("select", self._select)

        return toolbox

    def _setup_statistics(self) -> None:
        """Setup evolution statistics tracking."""
        self.stats.register("avg", np.mean)
        self.stats.register("std", np.std)
        self.stats.register("min", np.min)
        self.stats.register("max", np.max)

    def _evaluate_fitness(self, individual: Any) -> tuple:
        """
        Evaluate fitness of an individual.
        
        Args:
            individual: Individual to evaluate
            
        Returns:
            Fitness score (tuple for DEAP)
        """
        fitness = self.fitness_evaluator.evaluate_individual(
            individual, self.behavioral_events, self.population
        )
        return (fitness,)

    def _crossover(self, ind1: Any, ind2: Any) -> tuple:
        """
        Perform crossover between two individuals.
        
        Args:
            ind1: First parent
            ind2: Second parent
            
        Returns:
            Two offspring
        """
        return self.genetic_operators.crossover(ind1, ind2)

    def _mutate(self, individual: Any) -> tuple:
        """
        Mutate an individual.
        
        Args:
            individual: Individual to mutate
            
        Returns:
            Mutated individual (tuple for DEAP)
        """
        return self.genetic_operators.mutate(individual)

    def _select(self, individuals: List[Any], k: int) -> List[Any]:
        """
        Select individuals from population.
        
        Args:
            individuals: Population
            k: Number to select
            
        Returns:
            Selected individuals
        """
        return self.genetic_operators.select(individuals, k)

    def evolve(
        self, behavioral_events: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Evolve patterns using genetic algorithm.
        
        Args:
            behavioral_events: Optional behavioral events for fitness evaluation
            
        Returns:
            Evolved patterns
        """
        # Store events for fitness evaluation
        self.behavioral_events = behavioral_events

        # Initialize population
        self.population = self.toolbox.population(n=self.config.population_size)

        # Evaluate initial population
        fitnesses = list(map(self.toolbox.evaluate, self.population))
        for ind, fit in zip(self.population, fitnesses):
            ind.fitness.values = fit

        # Update hall of fame
        self.hall_of_fame.update(self.population)

        # Evolution loop
        for gen in range(self.config.max_generations):
            self.generation = gen

            # Select parents
            parents = self.toolbox.select(self.population, len(self.population))

            # Clone parents
            offspring = list(map(self.toolbox.clone, parents))

            # Crossover
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < self.config.crossover_rate:
                    self.toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            # Mutation
            for mutant in offspring:
                if random.random() < self.config.mutation_rate:
                    self.toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate offspring
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(self.toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # Update hall of fame
            self.hall_of_fame.update(offspring)

            # Replacement with elitism
            if self.config.elitism:
                elite = tools.selBest(self.population, self.config.elite_size)
                offspring = tools.selBest(
                    offspring, len(self.population) - self.config.elite_size
                ) + elite

            # Replace population
            self.population[:] = offspring

            # Track best individual
            best = tools.selBest(self.population, 1)[0]
            self.best_individual = Individual(
                genotype=best[:],
                fitness=best.fitness.values[0],
                generation=self.generation,
            )
            self.fitness_history.append(best.fitness.values[0])

            # Record statistics
            record = self.stats.compile(self.population)

            # Check convergence
            if self._check_convergence():
                break

        # Convert to pattern format
        return self._convert_to_patterns(self.population)

    def _check_convergence(self) -> bool:
        """Check if population has converged."""
        if self.generation < 10:
            return False

        recent_fitness = self.fitness_history[-10:]
        if len(recent_fitness) < 2:
            return False

        variance = np.var(recent_fitness)
        # Convert numpy.bool_ to Python bool
        return bool(variance < self.config.convergence_threshold)

    def _convert_to_patterns(
        self, population: List[Any]
    ) -> List[Dict[str, Any]]:
        """Convert population to pattern format."""
        encoder = PatternEncoder()
        patterns = []
        for ind in population:
            genotype = ind[:]
            fitness = ind.fitness.values[0] if ind.fitness.valid else 0.0
            pattern = {
                "id": f"pattern-{id(ind)}",
                "genotype": genotype,
                "fitness": fitness,
                "generation": self.generation,
            }
            patterns.append(pattern)
        return patterns

    def get_elite(self, size: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get elite individuals.
        
        Args:
            size: Number of elite individuals (default: config.elite_size)
            
        Returns:
            Elite patterns
        """
        if not self.population:
            return []

        elite_size = size or self.config.elite_size
        elite = tools.selBest(self.population, elite_size)
        return self._convert_to_patterns(elite)

    def adapt_to_new_data(self, new_events: List[Dict[str, Any]]) -> None:
        """
        Perform micro-evolution with new data.
        
        Args:
            new_events: New behavioral events
        """
        if not self.population:
            return

        # Update behavioral events
        self.behavioral_events = new_events

        # Perform micro-evolution
        elite = tools.selBest(self.population, self.config.micro_evolution_size)
        variations = []

        for ind in elite:
            for _ in range(self.config.micro_evolution_size):
                variation = self.toolbox.clone(ind)
                self.toolbox.mutate(variation)
                del variation.fitness.values
                variations.append(variation)

        # Evaluate variations
        fitnesses = map(self.toolbox.evaluate, variations)
        for ind, fit in zip(variations, fitnesses):
            ind.fitness.values = fit

        # Replace worst individuals with best variations
        worst = tools.selWorst(self.population, self.config.micro_evolution_size)
        best_variations = tools.selBest(variations, self.config.micro_evolution_size)

        for i, worst_ind in enumerate(worst):
            worst_idx = self.population.index(worst_ind)
            if i < len(best_variations):
                self.population[worst_idx] = best_variations[i]

    def get_population_stats(self) -> Dict[str, Any]:
        """Get population statistics."""
        if not self.population:
            return {
                "generation": self.generation,
                "population_size": 0,
                "best_fitness": 0.0,
                "average_fitness": 0.0,
                "diversity": 0.0,
            }

        fitnesses = [
            ind.fitness.values[0]
            for ind in self.population
            if ind.fitness.valid
        ]

        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "best_fitness": max(fitnesses) if fitnesses else 0.0,
            "average_fitness": np.mean(fitnesses) if fitnesses else 0.0,
            "diversity": self._calculate_diversity(),
        }

    def _calculate_diversity(self) -> float:
        """Calculate population diversity."""
        if not self.population:
            return 0.0

        unique_genotypes = set(str(ind) for ind in self.population)
        return len(unique_genotypes) / len(self.population)

    def get_best_patterns(self, n: int = 10) -> List[Pattern]:
        """
        Get best evolved patterns from hall of fame.
        
        Args:
            n: Number of patterns to return
            
        Returns:
            List of best patterns
        """
        if not self.hall_of_fame:
            return []

        encoder = PatternEncoder()
        best = tools.selBest(self.hall_of_fame, min(n, len(self.hall_of_fame)))
        patterns = []

        for ind in best:
            genotype = ind[:]
            for i, gene in enumerate(genotype):
                pattern = encoder.decode_genotype(
                    gene, f"pattern_{i}", generation=self.generation
                )
                pattern.fitness = ind.fitness.values[0] if ind.fitness.valid else 0.0
                patterns.append(pattern)

        return sorted(patterns, key=lambda p: p.fitness, reverse=True)[:n]
