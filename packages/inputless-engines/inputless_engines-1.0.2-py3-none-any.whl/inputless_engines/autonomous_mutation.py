"""
inputless-engines - autonomous_mutation.py

Autonomous mutation system that automatically triggers mutations based on conditions,
triggers, and performance metrics without explicit user intervention.
"""

from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timedelta
import threading
import time
from .mutation_engine import MutationEngine
from .types import MutationEngineConfig


class AutonomousMutationEngine(MutationEngine):
    """
    Autonomous mutation engine that automatically evolves patterns based on:
    - Time-based triggers (periodic evolution)
    - Performance-based triggers (fitness degradation)
    - Event-based triggers (new data arrival)
    - Condition-based triggers (custom conditions)
    
    Runs evolution cycles automatically in the background without explicit calls.
    """

    def __init__(
        self,
        config: Optional[MutationEngineConfig] = None,
        autonomous_enabled: bool = True,
        auto_evolution_interval: Optional[float] = None,  # seconds
        performance_threshold: float = 0.7,
        min_events_for_evolution: int = 100,
    ):
        """
        Initialize autonomous mutation engine.
        
        Args:
            config: Mutation engine configuration
            autonomous_enabled: Enable autonomous mutations
            auto_evolution_interval: Automatic evolution interval in seconds (None = disabled)
            performance_threshold: Trigger evolution if fitness drops below this
            min_events_for_evolution: Minimum events needed before auto-evolution
        """
        super().__init__(config)
        self.autonomous_enabled = autonomous_enabled
        self.auto_evolution_interval = auto_evolution_interval
        self.performance_threshold = performance_threshold
        self.min_events_for_evolution = min_events_for_evolution
        
        # Autonomous mutation state
        self._evolution_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_evolution_time: Optional[datetime] = None
        self._event_buffer: List[Dict[str, Any]] = []
        self._trigger_callbacks: List[Callable[[], bool]] = []
        self._evolution_lock = threading.Lock()

    def start_autonomous_evolution(self) -> None:
        """
        Start autonomous evolution in background thread.
        
        Evolution will trigger automatically based on:
        - Time intervals (if auto_evolution_interval is set)
        - Performance degradation
        - Event accumulation
        - Custom triggers
        """
        if not self.autonomous_enabled:
            return

        if self._running:
            return  # Already running

        self._running = True
        self._evolution_thread = threading.Thread(
            target=self._autonomous_evolution_loop, daemon=True
        )
        self._evolution_thread.start()

    def stop_autonomous_evolution(self) -> None:
        """Stop autonomous evolution."""
        self._running = False
        if self._evolution_thread:
            self._evolution_thread.join(timeout=5.0)

    def add_event(self, event: Dict[str, Any]) -> None:
        """
        Add event to buffer for autonomous evolution.
        
        Args:
            event: Behavioral event
        """
        if not self.autonomous_enabled:
            return

        with self._evolution_lock:
            self._event_buffer.append(event)

        # Trigger micro-evolution if buffer is large enough
        if len(self._event_buffer) >= self.min_events_for_evolution:
            self._trigger_micro_evolution()

    def add_events_batch(self, events: List[Dict[str, Any]]) -> None:
        """
        Add multiple events at once.
        
        Args:
            events: List of behavioral events
        """
        for event in events:
            self.add_event(event)

    def register_trigger(self, condition: Callable[[], bool]) -> None:
        """
        Register a custom trigger condition for autonomous evolution.
        
        Args:
            condition: Function that returns True to trigger evolution
        """
        self._trigger_callbacks.append(condition)

    def _autonomous_evolution_loop(self) -> None:
        """Main loop for autonomous evolution."""
        while self._running:
            try:
                # Check time-based trigger
                if self.auto_evolution_interval:
                    if self._should_trigger_time_based():
                        self._trigger_evolution()

                # Check performance-based trigger
                if self._should_trigger_performance_based():
                    self._trigger_evolution()

                # Check custom triggers
                if self._should_trigger_custom():
                    self._trigger_evolution()

                # Sleep before next check
                time.sleep(1.0)  # Check every second

            except Exception as e:
                # Log error but continue running
                print(f"Error in autonomous evolution loop: {e}")
                time.sleep(5.0)  # Wait longer on error

    def _should_trigger_time_based(self) -> bool:
        """Check if time-based evolution should trigger."""
        if not self.auto_evolution_interval:
            return False

        if not self._last_evolution_time:
            return True  # First evolution

        elapsed = (datetime.now() - self._last_evolution_time).total_seconds()
        return elapsed >= self.auto_evolution_interval

    def _should_trigger_performance_based(self) -> bool:
        """Check if performance-based evolution should trigger."""
        if not self.fitness_history:
            return False

        # Check if recent fitness is below threshold
        recent_fitness = self.fitness_history[-10:] if len(self.fitness_history) >= 10 else self.fitness_history
        avg_fitness = sum(recent_fitness) / len(recent_fitness) if recent_fitness else 0.0

        return avg_fitness < self.performance_threshold

    def _should_trigger_custom(self) -> bool:
        """Check if custom triggers should trigger evolution."""
        for callback in self._trigger_callbacks:
            try:
                if callback():
                    return True
            except Exception:
                continue  # Ignore errors in custom triggers
        return False

    def _trigger_evolution(self) -> None:
        """Trigger a full evolution cycle."""
        with self._evolution_lock:
            if not self.population:
                # Initialize population first
                if self.behavioral_events or self._event_buffer:
                    events = self.behavioral_events or self._event_buffer
                    self.evolve(behavioral_events=events)
                    self._last_evolution_time = datetime.now()
                return

            # Use buffered events if available
            if self._event_buffer:
                events = self._event_buffer.copy()
                self._event_buffer.clear()
                self.behavioral_events = events
            elif not self.behavioral_events:
                return  # No events to evolve with

            # Perform evolution
            self.evolve(behavioral_events=self.behavioral_events)
            self._last_evolution_time = datetime.now()

    def _trigger_micro_evolution(self) -> None:
        """Trigger micro-evolution with buffered events."""
        with self._evolution_lock:
            if not self.population:
                return

            if len(self._event_buffer) < self.min_events_for_evolution:
                return

            events = self._event_buffer[:self.min_events_for_evolution]
            self._event_buffer = self._event_buffer[self.min_events_for_evolution:]

            # Perform micro-evolution
            self.adapt_to_new_data(events)
            self._last_evolution_time = datetime.now()

    def get_autonomous_status(self) -> Dict[str, Any]:
        """
        Get status of autonomous evolution.
        
        Returns:
            Dictionary with autonomous evolution status
        """
        return {
            "autonomous_enabled": self.autonomous_enabled,
            "running": self._running,
            "last_evolution_time": self._last_evolution_time.isoformat() if self._last_evolution_time else None,
            "event_buffer_size": len(self._event_buffer),
            "registered_triggers": len(self._trigger_callbacks),
            "auto_evolution_interval": self.auto_evolution_interval,
            "performance_threshold": self.performance_threshold,
        }

