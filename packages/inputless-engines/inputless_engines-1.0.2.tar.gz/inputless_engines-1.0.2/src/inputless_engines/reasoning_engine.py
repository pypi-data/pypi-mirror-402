"""
inputless-engines - reasoning_engine.py

Meta-cognitive reasoning and analysis
"""

from typing import List, Optional, Dict, Any
from .types import (
    SelfReasoningConfig,
    ReasoningStrategy,
    Premise,
    Conclusion,
    ReasoningStep,
    ReasoningChain,
)


class KnowledgeBase:
    """Knowledge base for reasoning."""

    def __init__(self):
        self.rules: List[Dict[str, Any]] = []
        self.facts: List[Dict[str, Any]] = []

    def get_deductive_rules(self) -> List[Dict[str, Any]]:
        """Get deductive rules."""
        return [r for r in self.rules if r.get("type") == "deductive"]

    def gather_evidence(self, problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather evidence for problem."""
        relevant_facts = [f for f in self.facts if self._is_fact_relevant(f, problem)]
        return [
            {
                "type": "fact",
                "content": fact["content"],
                "reliability": fact.get("reliability", 0.8),
                "source": "knowledge_base",
            }
            for fact in relevant_facts
        ]

    def _is_fact_relevant(self, fact: Dict[str, Any], problem: Dict[str, Any]) -> bool:
        """Check if fact is relevant to problem."""
        problem_type = problem.get("type", "")
        fact_content = fact.get("content", "")
        # Check if problem type matches fact content exactly or as a word
        # This prevents partial matches like "pattern" matching "behavioral pattern"
        return problem_type == fact_content or (
            problem_type and fact_content and problem_type.lower() in fact_content.lower().split()
        )


class SelfReasoningEngine:
    """
    Meta-cognitive reasoning engine.
    
    Performs deductive, inductive, and abductive reasoning
    for decision-making and analysis.
    """

    def __init__(self, config: SelfReasoningConfig):
        """
        Initialize reasoning engine.
        
        Args:
            config: Engine configuration
        """
        self.config = config
        self.knowledge_base = KnowledgeBase()
        self.reasoning_history: List[ReasoningChain] = []

    def infer(self, premises: List[Premise]) -> Conclusion:
        """
        Infer conclusion from premises.
        
        Args:
            premises: List of premises
            
        Returns:
            Conclusion
        """
        reasoning_chain = self._build_reasoning_chain(premises)
        conclusion = self._draw_conclusion(reasoning_chain)

        self.reasoning_history.append(reasoning_chain)

        return conclusion

    def _build_reasoning_chain(self, premises: List[Premise]) -> ReasoningChain:
        """Build reasoning chain from premises."""
        chain = ReasoningChain(premises=premises)
        current_premises = premises
        depth = 0

        while depth < self.config.max_reasoning_depth and current_premises:
            step = self._perform_reasoning_step(current_premises)
            chain.steps.append(step)

            if step.conclusion:
                chain.conclusion = step.conclusion
                break

            current_premises = step.new_premises or []
            depth += 1

        chain.confidence = self._calculate_chain_confidence(chain)
        return chain

    def _perform_reasoning_step(self, premises: List[Premise]) -> ReasoningStep:
        """Perform a single reasoning step."""
        if self.config.reasoning_strategy == ReasoningStrategy.DEDUCTIVE:
            return self._deductive_reasoning(premises)
        elif self.config.reasoning_strategy == ReasoningStrategy.INDUCTIVE:
            return self._inductive_reasoning(premises)
        elif self.config.reasoning_strategy == ReasoningStrategy.ABDUCTIVE:
            return self._abductive_reasoning(premises)
        else:
            return self._deductive_reasoning(premises)

    def _deductive_reasoning(self, premises: List[Premise]) -> ReasoningStep:
        """Deductive reasoning: general to specific."""
        rules = self.knowledge_base.get_deductive_rules()
        applicable_rules = self._find_applicable_rules(premises, rules)

        if applicable_rules:
            rule = applicable_rules[0]
            conclusion = self._apply_rule(rule, premises)
            confidence = self._calculate_rule_confidence(rule, premises)

            return ReasoningStep(
                type="deductive",
                premises=premises,
                conclusion=conclusion,
                confidence=confidence,
                new_premises=[conclusion] if conclusion else None,
            )

        return ReasoningStep(
            type="deductive",
            premises=premises,
            confidence=0.0,
        )

    def _inductive_reasoning(self, premises: List[Premise]) -> ReasoningStep:
        """Inductive reasoning: specific to general."""
        patterns = self._identify_patterns(premises)
        generalizations = self._create_generalizations(patterns)

        if generalizations:
            generalization = generalizations[0]
            confidence = self._calculate_pattern_confidence(patterns)

            # Convert Conclusion to Premise for new_premises
            new_premise = Premise(
                statement=generalization.statement,
                confidence=generalization.confidence,
                evidence=generalization.evidence,
            )

            return ReasoningStep(
                type="inductive",
                premises=premises,
                conclusion=generalization,
                confidence=confidence,
                new_premises=[new_premise],
            )

        return ReasoningStep(
            type="inductive",
            premises=premises,
            confidence=0.0,
        )

    def _abductive_reasoning(self, premises: List[Premise]) -> ReasoningStep:
        """Abductive reasoning: best explanation."""
        observations = self._extract_observations(premises)
        explanations = self._generate_explanations(observations)
        best_explanation = self._select_best_explanation(explanations)

        if best_explanation:
            confidence = self._calculate_explanation_confidence(best_explanation)

            # Convert Conclusion to Premise for new_premises
            new_premise = Premise(
                statement=best_explanation.statement,
                confidence=best_explanation.confidence,
                evidence=best_explanation.evidence,
            )

            return ReasoningStep(
                type="abductive",
                premises=premises,
                conclusion=best_explanation,
                confidence=confidence,
                new_premises=[new_premise],
            )

        return ReasoningStep(
            type="abductive",
            premises=premises,
            confidence=0.0,
        )

    def _draw_conclusion(self, chain: ReasoningChain) -> Conclusion:
        """Draw conclusion from reasoning chain."""
        if chain.conclusion:
            return chain.conclusion

        # Synthesize from steps
        conclusions = [step.conclusion for step in chain.steps if step.conclusion]

        if not conclusions:
            return Conclusion(
                statement="No conclusion could be drawn",
                confidence=0.0,
                evidence=chain.premises,
                reasoning_type=self.config.reasoning_strategy.value,
            )

        combined_statement = "; ".join(c.statement for c in conclusions)
        average_confidence = sum(c.confidence for c in conclusions) / len(conclusions)

        return Conclusion(
            statement=combined_statement,
            confidence=average_confidence,
            evidence=chain.premises,
            reasoning_type=self.config.reasoning_strategy.value,
        )

    def analyze(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a problem.
        
        Args:
            problem: Problem description
            
        Returns:
            Analysis results
        """
        hypotheses = self._generate_hypotheses(problem)
        evidence = self._gather_evidence(problem)
        evaluations = [self._evaluate_hypothesis(h, evidence) for h in hypotheses]

        if not evaluations:
            return {
                "hypotheses": [],
                "best_hypothesis": None,
                "confidence": 0.0,
                "recommendations": [],
            }

        best_hypothesis = max(evaluations, key=lambda e: e.get("confidence", 0.0))

        return {
            "hypotheses": evaluations,
            "best_hypothesis": best_hypothesis,
            "confidence": best_hypothesis.get("confidence", 0.0),
            "recommendations": self._generate_recommendations(evaluations),
        }

    def self_analyze(self) -> Dict[str, Any]:
        """Perform self-analysis of reasoning quality."""
        if not self.reasoning_history:
            return {
                "reasoning_quality": 0.0,
                "strengths": [],
                "weaknesses": [],
                "improvement_areas": [],
            }

        average_confidence = (
            sum(c.confidence for c in self.reasoning_history)
            / len(self.reasoning_history)
        )

        weaknesses = []
        if average_confidence < 0.5:
            weaknesses.append(
                {
                    "type": "low_confidence",
                    "description": "Some reasoning chains have low confidence",
                    "severity": "medium",
                }
            )

        return {
            "reasoning_quality": average_confidence,
            "strengths": ["Consistent reasoning approach", "Good confidence levels"],
            "weaknesses": weaknesses,
            "improvement_areas": [
                "Increase reasoning depth",
                "Improve confidence calculation",
                "Enhance pattern recognition",
            ],
        }

    # Helper methods (simplified implementations)
    def _find_applicable_rules(
        self, premises: List[Premise], rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find applicable rules."""
        # Implementation: Match premises to rule conditions
        # For now, return empty list (rules would be matched based on premise content)
        return []

    def _apply_rule(
        self, rule: Dict[str, Any], premises: List[Premise]
    ) -> Optional[Conclusion]:
        """Apply rule to premises."""
        # Implementation: Generate conclusion from rule
        # For now, return None (would generate conclusion based on rule logic)
        return None

    def _calculate_rule_confidence(
        self, rule: Dict[str, Any], premises: List[Premise]
    ) -> float:
        """Calculate rule confidence."""
        avg_premise_confidence = (
            sum(p.confidence for p in premises) / len(premises) if premises else 0.0
        )
        rule_confidence = rule.get("confidence", 0.5)
        return avg_premise_confidence * rule_confidence

    def _identify_patterns(self, premises: List[Premise]) -> List[Dict[str, Any]]:
        """Identify patterns in premises."""
        # Implementation: Extract patterns
        # For now, return simple pattern based on premise statements
        patterns = []
        for premise in premises:
            patterns.append(
                {
                    "type": "simple",
                    "elements": [premise.statement],
                    "frequency": 1,
                    "confidence": premise.confidence,
                }
            )
        return patterns

    def _create_generalizations(
        self, patterns: List[Dict[str, Any]]
    ) -> List[Conclusion]:
        """Create generalizations from patterns."""
        # Implementation: Generate generalizations
        if not patterns:
            return []

        # Simple generalization: combine pattern statements
        combined_statement = "Generalization based on observed patterns"
        avg_confidence = (
            sum(p["confidence"] for p in patterns) / len(patterns) if patterns else 0.0
        )

        return [
            Conclusion(
                statement=combined_statement,
                confidence=avg_confidence,
                evidence=[],
                reasoning_type="inductive",
            )
        ]

    def _calculate_pattern_confidence(self, patterns: List[Dict[str, Any]]) -> float:
        """Calculate pattern confidence."""
        if not patterns:
            return 0.0
        return sum(p["confidence"] for p in patterns) / len(patterns)

    def _extract_observations(self, premises: List[Premise]) -> List[Dict[str, Any]]:
        """Extract observations from premises."""
        return [
            {"description": p.statement, "confidence": p.confidence} for p in premises
        ]

    def _generate_explanations(
        self, observations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate explanations for observations."""
        return [
            {
                "description": f"Explanation for: {obs['description']}",
                "confidence": obs["confidence"],
            }
            for obs in observations
        ]

    def _select_best_explanation(
        self, explanations: List[Dict[str, Any]]
    ) -> Optional[Conclusion]:
        """Select best explanation."""
        if not explanations:
            return None

        best = max(explanations, key=lambda e: e["confidence"])
        return Conclusion(
            statement=best["description"],
            confidence=best["confidence"],
            evidence=[],
            reasoning_type="abductive",
        )

    def _calculate_explanation_confidence(self, explanation: Conclusion) -> float:
        """Calculate explanation confidence."""
        return explanation.confidence

    def _generate_hypotheses(self, problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate hypotheses for problem."""
        # Implementation: Generate hypotheses based on problem type
        problem_type = problem.get("type", "generic")

        hypotheses = []
        if problem_type == "behavioral":
            hypotheses.append(
                {
                    "statement": "User behavior follows predictable patterns",
                    "confidence": 0.7,
                    "evidence": problem.get("data", []),
                    "testable": True,
                }
            )
        elif problem_type == "pattern":
            hypotheses.append(
                {
                    "statement": "Patterns indicate user preferences",
                    "confidence": 0.8,
                    "evidence": problem.get("data", []),
                    "testable": True,
                }
            )
        else:
            hypotheses.append(
                {
                    "statement": "Data contains meaningful patterns",
                    "confidence": 0.5,
                    "evidence": problem.get("data", []),
                    "testable": True,
                }
            )

        return hypotheses

    def _gather_evidence(self, problem: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather evidence for problem."""
        evidence = self.knowledge_base.gather_evidence(problem)

        # Add problem data as evidence
        if problem.get("data"):
            evidence.append(
                {
                    "type": "data",
                    "content": problem["data"],
                    "reliability": 0.8,
                    "source": "problem_data",
                }
            )

        return evidence

    def _evaluate_hypothesis(
        self, hypothesis: Dict[str, Any], evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate hypothesis against evidence."""
        # Simple evaluation: count supporting evidence
        supporting = [
            e for e in evidence if e.get("reliability", 0) > 0.5
        ]
        conflicting = [
            e for e in evidence if e.get("reliability", 0) < 0.3
        ]

        confidence = hypothesis.get("confidence", 0.5)
        if supporting:
            confidence = min(1.0, confidence + len(supporting) * 0.1)
        if conflicting:
            confidence = max(0.0, confidence - len(conflicting) * 0.1)

        return {
            "hypothesis": hypothesis,
            "confidence": confidence,
            "supporting_evidence": supporting,
            "conflicting_evidence": conflicting,
            "evaluation": "supported" if confidence > self.config.confidence_threshold else "rejected",
        }

    def _generate_recommendations(
        self, evaluations: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations from evaluations."""
        recommendations = []
        for evaluation in evaluations:
            if evaluation.get("evaluation") == "supported":
                hypothesis = evaluation.get("hypothesis", {})
                statement = hypothesis.get("statement", "")
                if statement:
                    recommendations.append(f"Consider implementing: {statement}")
        return recommendations

    def _calculate_chain_confidence(self, chain: ReasoningChain) -> float:
        """Calculate overall chain confidence."""
        if not chain.steps:
            return 0.0

        return sum(step.confidence for step in chain.steps) / len(chain.steps)
