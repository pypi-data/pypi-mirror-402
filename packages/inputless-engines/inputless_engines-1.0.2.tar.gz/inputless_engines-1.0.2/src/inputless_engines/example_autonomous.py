"""
Example usage of autonomous mutation engine.

Demonstrates how the mutation engine can autonomously evolve patterns
without explicit user intervention.
"""

from .autonomous_mutation import AutonomousMutationEngine
from .types import MutationEngineConfig


def example_autonomous_evolution():
    """Example: Autonomous evolution with time-based triggers."""
    print("=" * 60)
    print("Example: Autonomous Mutation Engine")
    print("=" * 60)

    # Initialize autonomous mutation engine
    config = MutationEngineConfig(
        population_size=30,
        max_generations=10,
        mutation_rate=0.1,
        crossover_rate=0.7,
    )

    engine = AutonomousMutationEngine(
        config=config,
        autonomous_enabled=True,
        auto_evolution_interval=5.0,  # Evolve every 5 seconds
        performance_threshold=0.7,
        min_events_for_evolution=50,
    )

    # Start autonomous evolution
    print("\nStarting autonomous evolution...")
    engine.start_autonomous_evolution()

    # Simulate events arriving
    print("\nSimulating event arrival...")
    for i in range(100):
        event = {
            "type": "ui.click",
            "timestamp": i * 1000,
            "sessionId": f"s{i % 5}",
        }
        engine.add_event(event)

        if i % 20 == 0:
            status = engine.get_autonomous_status()
            print(f"  Events processed: {i}, Buffer: {status['event_buffer_size']}")

    # Wait a bit for autonomous evolution
    import time
    print("\nWaiting for autonomous evolution cycles...")
    time.sleep(6)  # Wait for at least one evolution cycle

    # Check status
    status = engine.get_autonomous_status()
    print(f"\nAutonomous Status:")
    print(f"  Running: {status['running']}")
    print(f"  Last evolution: {status['last_evolution_time']}")
    print(f"  Buffer size: {status['event_buffer_size']}")

    # Get evolved patterns
    if engine.population:
        best_patterns = engine.get_best_patterns(n=3)
        print(f"\nBest evolved patterns: {len(best_patterns)}")
        for i, pattern in enumerate(best_patterns, 1):
            print(f"  {i}. Fitness: {pattern.fitness:.3f}, Events: {pattern.event_types}")

    # Stop autonomous evolution
    print("\nStopping autonomous evolution...")
    engine.stop_autonomous_evolution()
    print("Autonomous evolution stopped.")


def example_custom_triggers():
    """Example: Using custom triggers for autonomous evolution."""
    print("\n" + "=" * 60)
    print("Example: Custom Triggers")
    print("=" * 60)

    engine = AutonomousMutationEngine(
        autonomous_enabled=True,
        auto_evolution_interval=None,  # Disable time-based
    )

    # Register custom trigger: evolve when diversity drops
    def low_diversity_trigger():
        if not engine.population:
            return False
        stats = engine.get_population_stats()
        return stats.get("diversity", 1.0) < 0.3

    engine.register_trigger(low_diversity_trigger)

    # Register custom trigger: evolve when generation count is high
    def high_generation_trigger():
        return engine.generation > 20

    engine.register_trigger(high_generation_trigger)

    print("\nCustom triggers registered:")
    print("  - Low diversity trigger (< 0.3)")
    print("  - High generation trigger (> 20)")

    # Start autonomous evolution
    engine.start_autonomous_evolution()

    # Add some events
    for i in range(50):
        engine.add_event({"type": "ui.click", "timestamp": i * 1000})

    # Wait for triggers
    import time
    time.sleep(2)

    status = engine.get_autonomous_status()
    print(f"\nRegistered triggers: {status['registered_triggers']}")

    engine.stop_autonomous_evolution()


def example_performance_based():
    """Example: Performance-based autonomous evolution."""
    print("\n" + "=" * 60)
    print("Example: Performance-Based Evolution")
    print("=" * 60)

    engine = AutonomousMutationEngine(
        autonomous_enabled=True,
        performance_threshold=0.6,  # Trigger if fitness < 0.6
        auto_evolution_interval=None,
    )

    # Initialize with some events
    events = [
        {"type": "ui.click", "timestamp": i * 1000, "sessionId": f"s{i % 3}"}
        for i in range(100)
    ]

    # Initial evolution
    print("\nPerforming initial evolution...")
    engine.evolve(behavioral_events=events)
    print(f"Initial fitness: {engine.fitness_history[-1] if engine.fitness_history else 0.0:.3f}")

    # Start autonomous evolution
    engine.start_autonomous_evolution()

    # Simulate performance degradation by adding poor events
    print("\nSimulating performance degradation...")
    for i in range(50):
        engine.add_event({"type": "error", "timestamp": i * 1000})

    # Wait for performance-based trigger
    import time
    time.sleep(2)

    print("\nPerformance-based evolution may have triggered if fitness dropped.")
    status = engine.get_autonomous_status()
    print(f"Status: {status}")

    engine.stop_autonomous_evolution()


def main():
    """Main entry point."""
    try:
        example_autonomous_evolution()
        example_custom_triggers()
        example_performance_based()

        print("\n" + "=" * 60)
        print("All autonomous mutation examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

