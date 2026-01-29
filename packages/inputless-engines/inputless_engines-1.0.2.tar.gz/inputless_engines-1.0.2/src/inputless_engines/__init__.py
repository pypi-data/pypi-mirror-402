"""
inputless-engines - Main exports

AI/ML engines with genetic algorithms, metamorphic code, and reasoning engines.
"""

from .mutation_engine import MutationEngine
from .autonomous_mutation import AutonomousMutationEngine
from .metamorphic_code import MetamorphicCode
from .reasoning_engine import SelfReasoningEngine

# Configuration classes
from .types import (
    MutationEngineConfig,
    MetamorphicCodeConfig,
    SelfReasoningConfig,
    ReasoningStrategy,
)

# Data models
from .types import (
    Pattern,
    PatternGene,
    Individual,
    CodeTree,
    Premise,
    Conclusion,
    ReasoningStep,
    ReasoningChain,
)

# Supporting components
from .genetic_operators import GeneticOperators
from .fitness_functions import FitnessEvaluator
from .pattern_encoding import PatternEncoder

# Feature implementations (see features/ directory for details)
try:
    from .features import AutonomousABTesting

    __all__ = [
        # Main classes
        "MutationEngine",
        "AutonomousMutationEngine",
        "MetamorphicCode",
        "SelfReasoningEngine",
        # Configuration
        "MutationEngineConfig",
        "MetamorphicCodeConfig",
        "SelfReasoningConfig",
        "ReasoningStrategy",
        # Data models
        "Pattern",
        "PatternGene",
        "Individual",
        "CodeTree",
        "Premise",
        "Conclusion",
        "ReasoningStep",
        "ReasoningChain",
        # Supporting components
        "GeneticOperators",
        "FitnessEvaluator",
        "PatternEncoder",
        # Features
        "AutonomousABTesting",
    ]
except ImportError:
    # Features not yet implemented
    __all__ = [
        # Main classes
        "MutationEngine",
        "AutonomousMutationEngine",
        "MetamorphicCode",
        "SelfReasoningEngine",
        # Configuration
        "MutationEngineConfig",
        "MetamorphicCodeConfig",
        "SelfReasoningConfig",
        "ReasoningStrategy",
        # Data models
        "Pattern",
        "PatternGene",
        "Individual",
        "CodeTree",
        "Premise",
        "Conclusion",
        "ReasoningStep",
        "ReasoningChain",
        # Supporting components
        "GeneticOperators",
        "FitnessEvaluator",
        "PatternEncoder",
    ]
