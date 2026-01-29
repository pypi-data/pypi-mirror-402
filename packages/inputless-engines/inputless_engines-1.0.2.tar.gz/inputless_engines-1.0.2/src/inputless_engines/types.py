"""
inputless-engines - types.py

Type definitions for mutation engine components.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ReasoningStrategy(str, Enum):
    """Reasoning strategies for self-reasoning engine."""

    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"


class MutationEngineConfig(BaseModel):
    """Configuration for mutation engine."""

    population_size: int = Field(100, ge=10, le=1000, description="Population size")
    max_generations: int = Field(50, ge=1, le=1000, description="Maximum generations")
    mutation_rate: float = Field(0.1, ge=0.0, le=1.0, description="Mutation rate")
    crossover_rate: float = Field(0.7, ge=0.0, le=1.0, description="Crossover rate")
    elitism: bool = Field(True, description="Enable elitism")
    elite_size: int = Field(10, ge=1, description="Number of elite individuals")
    selection_method: Literal["tournament", "roulette", "rank"] = Field(
        "tournament", description="Selection method"
    )
    tournament_size: int = Field(3, ge=2, description="Tournament size")
    mutation_type: Literal["gaussian", "uniform", "adaptive"] = Field(
        "gaussian", description="Mutation type"
    )
    mutation_strength: float = Field(0.1, ge=0.0, description="Mutation strength")
    crossover_type: Literal["uniform", "single_point", "two_point"] = Field(
        "uniform", description="Crossover type"
    )
    convergence_threshold: float = Field(
        0.001, ge=0.0, description="Convergence threshold"
    )
    micro_evolution_size: int = Field(5, ge=1, description="Micro-evolution size")


class PatternGene(BaseModel):
    """Represents a single pattern gene (genotype component)."""

    event_types: List[str] = Field(..., description="Event types in pattern")
    sequence_length: int = Field(..., ge=1, description="Sequence length")
    timing_window: float = Field(..., ge=0.0, description="Timing window in ms")
    spatial_cluster: bool = Field(False, description="Spatial clustering enabled")
    weight: float = Field(0.5, ge=0.0, le=1.0, description="Pattern weight")


class Pattern(BaseModel):
    """Behavioral pattern representation (phenotype)."""

    pattern_id: str = Field(..., description="Pattern identifier")
    event_types: List[str] = Field(..., description="Event types")
    sequence: List[str] = Field(..., description="Event sequence")
    timing_constraints: Dict[str, float] = Field(
        ..., description="Timing constraints"
    )
    spatial_constraints: Optional[Dict[str, Any]] = Field(
        None, description="Spatial constraints"
    )
    conditions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Pattern conditions"
    )
    fitness: float = Field(0.0, ge=0.0, le=1.0, description="Pattern fitness")
    generation: int = Field(0, ge=0, description="Generation number")


class Individual(BaseModel):
    """Represents a single individual in the population."""

    genotype: List[Dict[str, Any]] = Field(..., description="Genotype (genes)")
    fitness: float = Field(0.0, ge=0.0, description="Fitness score")
    generation: int = Field(0, ge=0, description="Generation number")
    mutation_history: List[str] = Field(
        default_factory=list, description="Mutation history"
    )


class CodeTree(BaseModel):
    """Represents a code tree structure for metamorphic code."""

    type: str = Field(..., description="Node type")
    children: List["CodeTree"] = Field(
        default_factory=list, description="Child nodes"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Node parameters"
    )
    algorithm: Optional[str] = Field(None, description="Algorithm identifier")


# Update forward reference for recursive model
CodeTree.model_rebuild()


class MetamorphicCodeConfig(BaseModel):
    """Configuration for metamorphic code."""

    max_generations: int = Field(30, ge=1, description="Maximum generations")
    mutation_rate: float = Field(0.05, ge=0.0, le=1.0, description="Mutation rate")
    crossover_rate: float = Field(0.3, ge=0.0, le=1.0, description="Crossover rate")
    fitness_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Fitness threshold"
    )
    self_modification_enabled: bool = Field(
        True, description="Enable self-modification"
    )
    learning_rate: float = Field(0.01, ge=0.0, le=1.0, description="Learning rate")
    adaptation_rate: float = Field(
        0.1, ge=0.0, le=1.0, description="Adaptation rate"
    )


class Premise(BaseModel):
    """A premise for reasoning."""

    statement: str = Field(..., description="Premise statement")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    evidence: Optional[List[Dict[str, Any]]] = Field(
        None, description="Supporting evidence"
    )


class Conclusion(BaseModel):
    """A conclusion from reasoning."""

    statement: str = Field(..., description="Conclusion statement")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    evidence: List[Premise] = Field(
        default_factory=list, description="Supporting evidence"
    )
    reasoning_type: str = Field(..., description="Reasoning type")


class ReasoningStep(BaseModel):
    """A single reasoning step."""

    type: str = Field(..., description="Reasoning step type")
    premises: List[Premise] = Field(..., description="Input premises")
    conclusion: Optional[Conclusion] = Field(None, description="Conclusion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Step confidence")
    new_premises: Optional[List[Premise]] = Field(
        None, description="New premises generated"
    )


class ReasoningChain(BaseModel):
    """A chain of reasoning steps."""

    premises: List[Premise] = Field(..., description="Initial premises")
    steps: List[ReasoningStep] = Field(
        default_factory=list, description="Reasoning steps"
    )
    conclusion: Optional[Conclusion] = Field(None, description="Final conclusion")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Chain confidence")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp"
    )


class SelfReasoningConfig(BaseModel):
    """Configuration for reasoning engine."""

    reasoning_strategy: ReasoningStrategy = Field(
        ReasoningStrategy.DEDUCTIVE, description="Reasoning strategy"
    )
    confidence_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Confidence threshold"
    )
    max_reasoning_depth: int = Field(10, ge=1, le=100, description="Max depth")
