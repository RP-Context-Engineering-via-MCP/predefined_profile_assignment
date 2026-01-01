# app/services/consistency_calculator.py

"""
Consistency Calculator for Session-Level Consistency Scoring

Computes user consistency (0-1 scale) based on:
- Repeated intent across prompts
- Domain stability across prompts
- Session duration
- Return frequency (if session history available)
- Pattern consistency
"""

from typing import Dict, List
from collections import Counter


class ConsistencyCalculator:
    """Calculates session-level consistency from behavioral patterns."""
    
    @staticmethod
    def compute_from_history(intent_history: List[str], 
                            domain_history: List[str],
                            signal_history: List[Dict] = None) -> float:
        """
        Compute consistency from session history.
        
        Args:
            intent_history: List of intents from each prompt (ordered chronologically)
            domain_history: List of domains from each prompt (ordered chronologically)
            signal_history: Optional list of signal dicts from each prompt
            
        Returns:
            float: Consistency score (0.0 = no pattern, 1.0 = highly consistent)
        """
        if not intent_history or len(intent_history) == 0:
            return 0.5  # Default neutral
        
        # Special case: single prompt has no consistency pattern yet
        if len(intent_history) == 1:
            return 0.5  # Neutral default for single prompt
        
        consistency_score = 0.0
        
        # Factor 1: Intent Repetition (0-0.40 points) - Increased from 0.35
        # Measure how often the same intent appears
        intent_consistency = ConsistencyCalculator._calculate_repetition_score(
            intent_history,
            weight=0.40
        )
        consistency_score += intent_consistency
        
        # Factor 2: Domain Stability (0-0.40 points) - Increased from 0.35
        # Measure how often the same domain appears
        domain_consistency = ConsistencyCalculator._calculate_repetition_score(
            domain_history,
            weight=0.40
        )
        consistency_score += domain_consistency
        
        # Factor 3: Temporal Consistency (0-0.20 points)
        # Measure if pattern is maintained over time
        temporal_consistency = ConsistencyCalculator._calculate_temporal_consistency(
            intent_history,
            domain_history,
            weight=0.20
        )
        consistency_score += temporal_consistency
        
        # Factor 4: Signal Consistency (0-0.10 points, optional)
        if signal_history and len(signal_history) > 0:
            signal_consistency = ConsistencyCalculator._calculate_signal_consistency(
                signal_history,
                weight=0.10
            )
            consistency_score += signal_consistency
        
        # Normalize to 0-1 scale
        normalized_score = min(1.0, max(0.0, consistency_score))
        
        return round(normalized_score, 2)
    
    @staticmethod
    def _calculate_repetition_score(history: List[str], weight: float = 1.0) -> float:
        """
        Calculate repetition score based on frequency distribution.
        
        High frequency of one item = high consistency
        Equal distribution = low consistency
        
        Args:
            history: List of items (intents, domains, etc.)
            weight: Maximum weight to apply
            
        Returns:
            float: Repetition score (0-weight)
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
    def _calculate_temporal_consistency(intent_history: List[str],
                                       domain_history: List[str],
                                       weight: float = 1.0) -> float:
        """
        Calculate if pattern is consistent over time (not just repetition).
        
        Checks if recent prompts maintain same intent/domain as earlier ones.
        
        Args:
            intent_history: List of intents over time
            domain_history: List of domains over time
            weight: Maximum weight to apply
            
        Returns:
            float: Temporal consistency score (0-weight)
        """
        if not intent_history or len(intent_history) < 2:
            return 0.0
        
        temporal_score = 0.0
        
        # Check intent consistency
        intent_transitions = ConsistencyCalculator._calculate_transition_stability(
            intent_history
        )
        temporal_score += intent_transitions * (weight * 0.6)
        
        # Check domain consistency
        domain_transitions = ConsistencyCalculator._calculate_transition_stability(
            domain_history
        )
        temporal_score += domain_transitions * (weight * 0.4)
        
        return temporal_score
    
    @staticmethod
    def _calculate_transition_stability(history: List[str]) -> float:
        """
        Measure stability of transitions (how often do we stay with same item).
        
        Low transitions = high stability
        Many transitions = low stability
        
        Args:
            history: Ordered list of items
            
        Returns:
            float: Stability score (0-1)
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
    def _calculate_signal_consistency(signal_history: List[Dict],
                                     weight: float = 1.0) -> float:
        """
        Calculate signal consistency (behavior style stability).
        
        Args:
            signal_history: List of signal dicts from each prompt
            weight: Maximum weight to apply
            
        Returns:
            float: Signal consistency score (0-weight)
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
        """
        Quick consistency score: how much does current prompt match history?
        
        Useful for incremental updates.
        
        Args:
            current_intent: Current prompt's intent
            current_domain: Current prompt's domain
            intent_history: Previous intents
            domain_history: Previous domains
            
        Returns:
            float: Match score (0-1)
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
        """
        Return detailed consistency breakdown.
        
        Args:
            intent_history: List of intents
            domain_history: List of domains
            
        Returns:
            dict: Consistency metrics breakdown
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
