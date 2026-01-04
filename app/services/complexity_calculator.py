# app/services/complexity_calculator.py

"""
Complexity Calculator for Task Complexity Scoring

Computes task complexity (0-1 scale) based on prompt characteristics:
- Prompt length
- Constraints specified
- Multi-step instructions
- Use of examples or structure
"""

from typing import Dict, Optional
from app.core.constants import ComplexityConstants, DefaultValues
from app.core.logging_config import calculator_logger


class ComplexityCalculator:
    """
    Calculates task complexity from prompt characteristics.
    
    Uses keyword detection and prompt analysis to score complexity on 0-1 scale.
    """
    
    @staticmethod
    def compute_complexity(prompt_text: str) -> float:
        """
        Compute task complexity from prompt text.
        
        Analyzes multiple factors:
        - Word count (length)
        - Constraint keywords
        - Multi-step indicators
        - Structural requirements
        - Example usage
        
        Args:
            prompt_text: The user's prompt/request
            
        Returns:
            float: Complexity score (0.0 = simple, 1.0 = very complex)
        """
        if not prompt_text or not isinstance(prompt_text, str):
            calculator_logger.debug(
                f"Invalid prompt text, returning default: {DefaultValues.DEFAULT_COMPLEXITY}"
            )
            return DefaultValues.DEFAULT_COMPLEXITY
        
        prompt_lower = prompt_text.lower()
        words = prompt_text.split()
        word_count = len(words)
        
        complexity_score = 0.0
        
        # Factor 1: Prompt Length
        length_score = ComplexityCalculator._calculate_length_score(word_count)
        complexity_score += length_score
        
        # Factor 2: Constraint Keywords
        constraint_count = sum(
            prompt_lower.count(keyword) 
            for keyword in ComplexityConstants.CONSTRAINT_KEYWORDS
        )
        if constraint_count > 0:
            constraint_score = min(
                ComplexityConstants.CONSTRAINT_MAX_SCORE,
                ComplexityConstants.CONSTRAINT_PER_KEYWORD * constraint_count
            )
            complexity_score += constraint_score
        
        # Factor 3: Multi-Step Instructions
        multistep_count = sum(
            prompt_lower.count(keyword)
            for keyword in ComplexityConstants.MULTI_STEP_KEYWORDS
        )
        if multistep_count > 0:
            multistep_score = min(
                ComplexityConstants.MULTISTEP_MAX_SCORE,
                ComplexityConstants.MULTISTEP_PER_KEYWORD * multistep_count
            )
            complexity_score += multistep_score
        
        # Factor 4: Structural/Formatting Keywords
        structure_count = sum(
            prompt_lower.count(keyword)
            for keyword in ComplexityConstants.STRUCTURE_KEYWORDS
        )
        if structure_count > 0:
            structure_score = min(
                ComplexityConstants.STRUCTURE_MAX_SCORE,
                ComplexityConstants.STRUCTURE_PER_KEYWORD * structure_count
            )
            complexity_score += structure_score
        
        # Factor 5: Examples Provided
        example_count = sum(
            prompt_lower.count(keyword)
            for keyword in ComplexityConstants.EXAMPLE_KEYWORDS
        )
        if example_count > 0:
            example_score = min(
                ComplexityConstants.EXAMPLE_MAX_SCORE,
                ComplexityConstants.EXAMPLE_PER_KEYWORD * example_count
            )
            complexity_score += example_score
        
        # Normalize to 0-1 scale
        normalized_score = min(1.0, complexity_score)
        final_score = round(normalized_score, 2)
        
        calculator_logger.debug(
            f"Complexity calculated: {final_score:.2f} "
            f"(words={word_count}, constraints={constraint_count}, "
            f"multistep={multistep_count}, structure={structure_count}, "
            f"examples={example_count})"
        )
        
        return final_score
    
    @staticmethod
    def _calculate_length_score(word_count: int) -> float:
        """
        Calculate complexity score based on word count.
        
        Args:
            word_count: Number of words in prompt
            
        Returns:
            float: Length-based complexity score
        """
        if word_count < ComplexityConstants.LOW_COMPLEXITY_THRESHOLD:
            return ComplexityConstants.LENGTH_MIN_SCORE
        elif word_count > ComplexityConstants.HIGH_COMPLEXITY_THRESHOLD:
            return ComplexityConstants.LENGTH_MAX_SCORE
        else:
            # Linear scaling between thresholds
            normalized = (
                (word_count - ComplexityConstants.LOW_COMPLEXITY_THRESHOLD) /
                (ComplexityConstants.HIGH_COMPLEXITY_THRESHOLD - 
                 ComplexityConstants.LOW_COMPLEXITY_THRESHOLD)
            )
            return ComplexityConstants.LENGTH_MIN_SCORE + (
                (ComplexityConstants.LENGTH_MAX_SCORE - ComplexityConstants.LENGTH_MIN_SCORE) * 
                normalized
            )
    
    @staticmethod
    def compute_complexity_from_signals(signals: Dict[str, float]) -> float:
        """
        Compute complexity from behavior signals.
        
        Alternative method that derives complexity from behavioral signals
        rather than prompt text analysis.
        
        Args:
            signals: Dict of signal_name -> score
            
        Returns:
            float: Complexity score (0.0 = simple, 1.0 = very complex)
        """
        if not signals:
            calculator_logger.debug("No signals provided, returning default complexity")
            return DefaultValues.DEFAULT_COMPLEXITY
        
        complexity_score = 0.0
        
        # MULTI_STEP signal strongly indicates complexity
        if signals.get("MULTI_STEP", 0) > 0:
            complexity_score += signals.get("MULTI_STEP", 0) * 0.4
        
        # ITERATIVE and GOAL_ORIENTED indicate moderate complexity
        if signals.get("ITERATIVE", 0) > 0:
            complexity_score += signals.get("ITERATIVE", 0) * 0.3
        
        if signals.get("GOAL_ORIENTED", 0) > 0:
            complexity_score += signals.get("GOAL_ORIENTED", 0) * 0.2
        
        # CASUAL indicates low complexity
        if signals.get("CASUAL", 0) > 0:
            complexity_score -= signals.get("CASUAL", 0) * 0.2
        
        # Normalize to 0-1 scale
        normalized_score = max(0.0, min(1.0, complexity_score))
        final_score = round(normalized_score, 2)
        
        calculator_logger.debug(
            f"Complexity from signals: {final_score:.2f} (signals={signals})"
        )
        
        return final_score

