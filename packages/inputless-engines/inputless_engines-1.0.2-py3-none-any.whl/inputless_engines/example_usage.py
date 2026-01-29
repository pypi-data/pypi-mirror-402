"""
Example usage of the engines package.

This file demonstrates how to use the mutation engine, metamorphic code,
and reasoning engine to evolve patterns and perform meta-cognitive reasoning.
"""

# Import from package
from .mutation_engine import MutationEngine, MutationEngineConfig
from .metamorphic_code import MetamorphicCode, MetamorphicCodeConfig
from .reasoning_engine import SelfReasoningEngine
from .types import SelfReasoningConfig, ReasoningStrategy, Premise


def example_mutation_engine():
    """Example: Using mutation engine to evolve patterns."""
    print("=" * 60)
    print("Example 1: Mutation Engine - Pattern Evolution")
    print("=" * 60)

    # Initialize mutation engine
    config = MutationEngineConfig(
        population_size=50,
        max_generations=20,
        mutation_rate=0.1,
        crossover_rate=0.7,
        elitism=True,
        elite_size=5,
        selection_method="tournament",
        tournament_size=3,
    )

    engine = MutationEngine(config)

    # Example behavioral events
    behavioral_events = [
        {"type": "ui.click", "timestamp": 1000, "sessionId": "s1"},
        {"type": "ui.hover", "timestamp": 2000, "sessionId": "s1"},
        {"type": "scroll", "timestamp": 3000, "sessionId": "s1"},
        {"type": "ui.click", "timestamp": 4000, "sessionId": "s2"},
        {"type": "nav.pageview", "timestamp": 5000, "sessionId": "s2"},
    ]

    # Evolve patterns
    print("\nEvolving patterns...")
    evolved_patterns = engine.evolve(behavioral_events=behavioral_events)

    print(f"\nGenerated {len(evolved_patterns)} evolved patterns")

    # Get best patterns
    best_patterns = engine.get_best_patterns(n=3)
    print(f"\nBest {len(best_patterns)} patterns:")
    for i, pattern in enumerate(best_patterns, 1):
        print(f"  {i}. Pattern ID: {pattern.pattern_id}")
        print(f"     Event types: {pattern.event_types}")
        print(f"     Fitness: {pattern.fitness:.3f}")
        print(f"     Generation: {pattern.generation}")

    # Get population statistics
    stats = engine.get_population_stats()
    print(f"\nPopulation Statistics:")
    print(f"  Generation: {stats['generation']}")
    print(f"  Population size: {stats['population_size']}")
    print(f"  Best fitness: {stats['best_fitness']:.3f}")
    print(f"  Average fitness: {stats['average_fitness']:.3f}")
    print(f"  Diversity: {stats['diversity']:.3f}")

    # Real-time adaptation
    print("\n\nPerforming micro-evolution with new data...")
    new_events = [
        {"type": "ui.click", "timestamp": 6000, "sessionId": "s3"},
        {"type": "focus", "timestamp": 7000, "sessionId": "s3"},
    ]
    engine.adapt_to_new_data(new_events)
    print("Micro-evolution completed")

    return engine


def example_metamorphic_code():
    """Example: Using metamorphic code for self-modification."""
    print("\n" + "=" * 60)
    print("Example 2: Metamorphic Code - Self-Modification")
    print("=" * 60)

    # Initialize metamorphic code
    config = MetamorphicCodeConfig(
        max_generations=10,
        mutation_rate=0.05,
        crossover_rate=0.3,
        fitness_threshold=0.8,
        self_modification_enabled=True,
        learning_rate=0.01,
        adaptation_rate=0.1,
    )

    metamorphic = MetamorphicCode(config)

    # Evolve code structure
    print("\nEvolving code structure...")
    evolved_code = metamorphic.evolve()

    print(f"\nCode tree evolved to generation {metamorphic.generation}")
    print(f"Fitness score: {metamorphic.fitness_score:.3f}")
    print(f"Mutation history: {metamorphic.mutation_history}")

    # Adapt to patterns
    patterns = [
        {
            "id": "pattern-1",
            "type": "behavioral",
            "frequency": 0.9,
            "complexity": 0.6,
            "novelty": 0.4,
        }
    ]

    print("\nAdapting code to patterns...")
    adapted_code = metamorphic.adapt_to_patterns(patterns)
    print("Code adapted successfully")

    # Execute with input data
    print("\nExecuting code tree with input data...")
    input_data = {"events": [{"type": "click", "value": 1}]}
    result = metamorphic.execute(input_data)
    print(f"Execution result: {result}")

    return metamorphic


def example_reasoning_engine():
    """Example: Using reasoning engine for meta-cognitive analysis."""
    print("\n" + "=" * 60)
    print("Example 3: Self-Reasoning Engine - Meta-Cognitive Reasoning")
    print("=" * 60)

    # Initialize reasoning engine
    config = SelfReasoningConfig(
        reasoning_strategy=ReasoningStrategy.DEDUCTIVE,
        confidence_threshold=0.8,
        max_reasoning_depth=10,
    )

    reasoning = SelfReasoningEngine(config)

    # Infer conclusions from premises
    print("\nInferring conclusions from premises...")
    premises = [
        Premise(
            statement="User shows frustration patterns",
            confidence=0.9,
        ),
        Premise(
            statement="Page load time is high",
            confidence=0.8,
        ),
    ]

    conclusion = reasoning.infer(premises)
    print(f"\nConclusion: {conclusion.statement}")
    print(f"Confidence: {conclusion.confidence:.3f}")
    print(f"Reasoning type: {conclusion.reasoning_type}")

    # Analyze problems
    print("\nAnalyzing problem...")
    problem = {
        "type": "behavioral",
        "description": "User abandonment detected",
        "data": {"abandonment_rate": 0.15, "session_duration": 30},
    }

    analysis = reasoning.analyze(problem)
    print(f"\nAnalysis confidence: {analysis['confidence']:.3f}")
    print(f"Best hypothesis: {analysis['best_hypothesis'].get('hypothesis', {}).get('statement', 'N/A')}")
    print(f"Recommendations: {len(analysis['recommendations'])}")

    # Self-analysis
    print("\nPerforming self-analysis...")
    self_analysis = reasoning.self_analyze()
    print(f"Reasoning quality: {self_analysis['reasoning_quality']:.3f}")
    print(f"Strengths: {self_analysis['strengths']}")
    print(f"Improvement areas: {self_analysis['improvement_areas']}")

    return reasoning


def example_integrated_usage():
    """Example: Integrated usage of all engines."""
    print("\n" + "=" * 60)
    print("Example 4: Integrated Usage - All Engines")
    print("=" * 60)

    # Initialize all engines
    mutation_config = MutationEngineConfig(
        population_size=30,
        max_generations=10,
        mutation_rate=0.1,
        crossover_rate=0.7,
    )
    mutation_engine = MutationEngine(mutation_config)

    metamorphic_config = MetamorphicCodeConfig(
        max_generations=5,
        self_modification_enabled=True,
    )
    metamorphic = MetamorphicCode(metamorphic_config)

    reasoning_config = SelfReasoningConfig(
        reasoning_strategy=ReasoningStrategy.DEDUCTIVE,
        confidence_threshold=0.8,
    )
    reasoning = SelfReasoningEngine(reasoning_config)

    # Behavioral events
    behavioral_events = [
        {"type": "ui.click", "timestamp": i * 1000, "sessionId": f"s{i % 3}"}
        for i in range(20)
    ]

    # Evolve patterns
    print("\n1. Evolving patterns with mutation engine...")
    evolved_patterns = mutation_engine.evolve(behavioral_events=behavioral_events)
    print(f"   Generated {len(evolved_patterns)} evolved patterns")

    # Adapt code to patterns
    print("\n2. Adapting metamorphic code to evolved patterns...")
    adapted_code = metamorphic.adapt_to_patterns(evolved_patterns)
    print("   Code adapted successfully")

    # Reason about results
    print("\n3. Reasoning about evolution results...")
    premises = [
        Premise(
            statement="Pattern evolution successful",
            confidence=0.9,
        ),
        Premise(
            statement="Fitness improved",
            confidence=0.85,
        ),
    ]
    conclusion = reasoning.infer(premises)
    print(f"   Conclusion: {conclusion.statement}")
    print(f"   Confidence: {conclusion.confidence:.3f}")

    print("\n" + "=" * 60)
    print("Integrated example completed!")
    print("=" * 60)


def main():
    """Main entry point for running examples."""
    try:
        # Run individual examples
        example_mutation_engine()
        example_metamorphic_code()
        example_reasoning_engine()

        # Run integrated example
        example_integrated_usage()

    except ImportError as e:
        print(f"\nError: Missing dependency - {e}")
        print("Please install dependencies: poetry install")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

