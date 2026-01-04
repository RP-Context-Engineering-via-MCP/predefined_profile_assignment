"""Session-level consistency calculator.

Computes user behavioral consistency (0-1 scale) across multiple prompts,
analyzing intent repetition, domain stability, and temporal patterns.
"""

from typing import Dict, List, Optional
from collections import Counter
from app.core.constants import ConsistencyConstants, DefaultValues
from app.core.logging_config import calculator_logger


class ConsistencyCalculator:
    """Behavioral consistency analysis service.
    
    Analyzes user behavior patterns across sessions to determine consistency
    in intents, domains, and interaction styles over time.
    """
    
    @staticmethod
    def compute_from_history(
        intent_history: List[str], 
        domain_history: List[str],
        signal_history: Optional[List[Dict]] = None
    ) -> float:
        """Compute consistency from session behavioral history.
        
        Analyzes multiple consistency dimensions:
        - Intent repetition: frequency of same intent usage
        - Domain stability: frequency of same domain usage
        - Temporal consistency: pattern maintenance over time
        - Signal consistency: behavioral style stability (optional)
        
        Single-prompt sessions return default consistency (no pattern yet).
        
        Args:
            intent_history: Chronologically ordered list of intents
            domain_history: Chronologically ordered list of domains
            signal_history: Optional list of signal dictionaries per prompt
            
        Returns:
            Consistency score from 0.0 (no pattern) to 1.0 (highly consistent)
        """
        if not intent_history or len(intent_history) == 0:
            calculator_logger.debug("No intent history, returning default consistency")
            return DefaultValues.DEFAULT_CONSISTENCY
        
        if len(intent_history) == 1:
            calculator_logger.debug("Single prompt, returning default consistency")
            return DefaultValues.DEFAULT_CONSISTENCY
        
        consistency_score = 0.0
        
        # Factor 1: Intent Repetition
        intent_consistency = ConsistencyCalculator._calculate_repetition_score(
            intent_history,
            weight=ConsistencyConstants.INTENT_WEIGHT
        )
        consistency_score += intent_consistency
        
        # Factor 2: Domain Stability
        domain_consistency = ConsistencyCalculator._calculate_repetition_score(
            domain_history,
            weight=ConsistencyConstants.DOMAIN_WEIGHT
        )
        consistency_score += domain_consistency
        
        # Factor 3: Temporal Consistency
        temporal_consistency = ConsistencyCalculator._calculate_temporal_consistency(
            intent_history,
            domain_history,
            weight=ConsistencyConstants.TEMPORAL_WEIGHT
        )
        consistency_score += temporal_consistency
        
        # Factor 4: Signal Consistency (optional)
        if signal_history and len(signal_history) > 0:
            signal_consistency = ConsistencyCalculator._calculate_signal_consistency(
                signal_history,
                weight=ConsistencyConstants.SIGNAL_WEIGHT
            )
            consistency_score += signal_consistency
        
        # Normalize to 0-1 scale
        normalized_score = min(1.0, max(0.0, consistency_score))
        final_score = round(normalized_score, 2)
        
        calculator_logger.debug(
            f"Consistency calculated: {final_score:.2f} "
            f"(intent={intent_consistency:.2f}, domain={domain_consistency:.2f}, "
            f"temporal={temporal_consistency:.2f})"
        )
        
        return final_score
    
    @staticmethod
    def _calculate_repetition_score(history: List[str], weight: float = 1.0) -> float:
        """Calculate repetition-based consistency score.
        
        High frequency of single item indicates high consistency.
        Equal distribution indicates low consistency.
        
        Args:
            history: List of items (intents, domains, etc.)
            weight: Maximum score weight to apply
            
        Returns:
            Repetition score from 0 to weight
        """
        if not history or len(history) == 0:
            return 0.0
        
        if len(history) == 1:
            return weight  # Single item is maximally consistent
        
        # Count occurrences
        counter = Counter(history)
        total = len(history)
        
        # If all items are unique, consistency is low
        if len(counter) == 1:
            return weight  # Single unique item across all prompts = max consistency
        
        # Calculate dominance: how much the top item dominates
        top_count = counter.most_common(1)[0][1]
        dominance = top_count / total  # Range: 1/n to 1.0
        
        # Map dominance to score
        # dominance=1/n → score=0, dominance=1.0 → score=weight
        min_dominance = 1.0 / len(counter)
        dominance_range = 1.0 - min_dominance
        
        if dominance_range == 0:
            return weight  # All same items
        
        normalized_dominance = (dominance - min_dominance) / dominance_range
        normalized_dominance = max(0.0, min(1.0, normalized_dominance))
        
        return weight * normalized_dominance
    
    @staticmethod
    def _calculate_temporal_consistency(
        intent_history: List[str],
        domain_history: List[str],
        weight: float = 1.0
    ) -> float:
        """Calculate temporal pattern consistency.
        
        Measures if patterns remain stable over time,
        checking transition stability between prompts.
        
        Args:
            intent_history: Chronological intent list
            domain_history: Chronological domain list
            weight: Maximum score weight to apply
            
        Returns:
            Temporal consistency score from 0 to weight
        """
        if not intent_history or len(intent_history) < 2:
            return 0.0
        
        temporal_score = 0.0
        
        # Check intent consistency (60% of temporal weight)
        intent_transitions = ConsistencyCalculator._calculate_transition_stability(
            intent_history
        )
        temporal_score += intent_transitions * (weight * 0.6)
        
        # Check domain consistency (40% of temporal weight)
        domain_transitions = ConsistencyCalculator._calculate_transition_stability(
            domain_history
        )
        temporal_score += domain_transitions * (weight * 0.4)
        
        return temporal_score
    
    @staticmethod
    def _calculate_transition_stability(history: List[str]) -> float:
        """Measure transition stability in sequential data.
        
        Low transitions (staying with same item) = high stability.
        Many transitions (frequent changes) = low stability.
        
        Args:
            history: Ordered list of items
            
        Returns:
            Stability score from 0.0 to 1.0
        """
        if len(history) < 2:
            return 1.0
        
        # Count transitions (changes from one item to another)
        transitions = 0
        for i in range(len(history) - 1):
            if history[i] != history[i + 1]:
                transitions += 1
        
        # Max possible transitions is len-1
        transition_rate = transitions / (len(history) - 1)
        
        # Stability = 1 - transition_rate
        stability = 1.0 - transition_rate
        
        return stability
    
    @staticmethod
    def _calculate_signal_consistency(
        signal_history: List[Dict],
        weight: float = 1.0
    ) -> float:
        """Calculate behavioral signal consistency.
        
        Analyzes stability of dominant interaction style signals.
        
        Args:
            signal_history: List of signal dictionaries per prompt
            weight: Maximum score weight to apply
            
        Returns:
            Signal consistency score from 0 to weight
        """
        if not signal_history or len(signal_history) == 0:
            return 0.0
        
        # Extract dominant signal from each prompt
        dominant_signals = []
        for signals in signal_history:
            if signals:
                # Get the signal with highest score
                top_signal = max(signals.items(), key=lambda x: x[1])[0]
                dominant_signals.append(top_signal)
        
        if not dominant_signals:
            return 0.0
        
        # Calculate repetition of dominant signals
        counter = Counter(dominant_signals)
        top_count = counter.most_common(1)[0][1]
        dominance = top_count / len(dominant_signals)
        
        # Map to weight
        return weight * dominance
    
    @staticmethod
    def compute_from_current_prompt(current_intent: str,
                                   current_domain: str,
                                   intent_history: List[str],
                                   domain_history: List[str]) -> float:
        """Compute incremental consistency from current prompt.
        
        Quick consistency check: how well does current prompt match history?
        Useful for real-time consistency updates.
        
        Args:
            current_intent: Current prompt's intent
            current_domain: Current prompt's domain
            intent_history: Previous intent history
            domain_history: Previous domain history
            
        Returns:
            Match score from 0.0 to 1.0
        """
        if not intent_history or len(intent_history) == 0:
            return 0.5  # Default neutral
        
        consistency_score = 0.0
        
        # Check if current intent matches most common historical intent
        intent_counter = Counter(intent_history)
        top_intent = intent_counter.most_common(1)[0][0]
        if current_intent == top_intent:
            consistency_score += 0.5
        
        # Check if current domain matches most common historical domain
        domain_counter = Counter(domain_history)
        top_domain = domain_counter.most_common(1)[0][0]
        if current_domain == top_domain:
            consistency_score += 0.5
        
        return round(consistency_score, 2)
    
    @staticmethod
    def compute_summary(intent_history: List[str],
                       domain_history: List[str]) -> Dict:
        """Generate detailed consistency breakdown.
        
        Provides comprehensive consistency analysis with metrics
        for intent and domain patterns.
        
        Args:
            intent_history: List of intents
            domain_history: List of domains
            
        Returns:
            Dictionary with consistency metrics breakdown
        """
        intent_counter = Counter(intent_history)
        domain_counter = Counter(domain_history)
        
        return {
            "overall_consistency": ConsistencyCalculator.compute_from_history(
                intent_history, domain_history
            ),
            "dominant_intent": intent_counter.most_common(1)[0][0] if intent_counter else None,
            "intent_dominance": (
                intent_counter.most_common(1)[0][1] / len(intent_history)
                if intent_counter else 0.0
            ),
            "unique_intents": len(intent_counter),
            "dominant_domain": domain_counter.most_common(1)[0][0] if domain_counter else None,
            "domain_dominance": (
                domain_counter.most_common(1)[0][1] / len(domain_history)
                if domain_counter else 0.0
            ),
            "unique_domains": len(domain_counter),
            "total_prompts": len(intent_history)
        }
