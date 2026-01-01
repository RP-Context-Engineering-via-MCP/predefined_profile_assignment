# app/services/complexity_calculator.py

"""
Complexity Calculator for Task Complexity Scoring

Computes task complexity (0-1 scale) based on prompt characteristics:
- Prompt length
- Constraints specified
- Multi-step instructions
- Use of examples or structure
"""


class ComplexityCalculator:
    """Calculates task complexity from prompt characteristics."""
    
    # Word count thresholds
    LOW_COMPLEXITY_THRESHOLD = 20       # Simple prompts: <20 words
    HIGH_COMPLEXITY_THRESHOLD = 100     # Complex prompts: >100 words
    
    # Complexity markers
    CONSTRAINT_KEYWORDS = [
        "must", "should", "not", "except", "avoid", "only",
        "limit", "without", "require", "constraint", "restrict",
        "specific", "exactly", "precisely", "format", "include",
        "handle", "optimize"
    ]
    
    MULTI_STEP_KEYWORDS = [
        "first", "then", "next", "after", "finally", "step",
        "stage", "phase", "follow", "sequence", "order",
        "and then", "subsequently", "moreover"
    ]
    
    STRUCTURE_KEYWORDS = [
        "structure", "organize", "format", "template", "outline",
        "list", "number", "bullet", "table", "section",
        "header", "subheader", "code", "json", "xml"
    ]
    
    EXAMPLE_KEYWORDS = [
        "example", "like", "such as", "for instance", "e.g",
        "show", "demonstrate", "illustration", "sample",
        "template", "reference"
    ]
    
    @staticmethod
    def compute_complexity(prompt_text: str) -> float:
        """
        Compute task complexity from prompt text.
        
        Args:
            prompt_text: The user's prompt/request
            
        Returns:
            float: Complexity score (0.0 = simple, 1.0 = very complex)
        """
        if not prompt_text or not isinstance(prompt_text, str):
            return 0.5  # Default neutral
        
        prompt_lower = prompt_text.lower()
        words = prompt_text.split()
        word_count = len(words)
        
        complexity_score = 0.0
        
        # Factor 1: Prompt Length (0-0.20 points) - Reduced from 0.25
        # Low: <20 words (0.05) | Medium: 20-100 words (0.15) | High: >100 words (0.20)
        if word_count < ComplexityCalculator.LOW_COMPLEXITY_THRESHOLD:
            complexity_score += 0.05
        elif word_count > ComplexityCalculator.HIGH_COMPLEXITY_THRESHOLD:
            complexity_score += 0.20
        else:
            # Linear scaling between thresholds
            normalized = (word_count - ComplexityCalculator.LOW_COMPLEXITY_THRESHOLD) / \
                        (ComplexityCalculator.HIGH_COMPLEXITY_THRESHOLD - ComplexityCalculator.LOW_COMPLEXITY_THRESHOLD)
            complexity_score += 0.05 + (0.15 * normalized)
        
        # Factor 2: Constraint Keywords (0-0.70 points) - Increased from 0.65
        constraint_count = sum(
            prompt_lower.count(keyword) 
            for keyword in ComplexityCalculator.CONSTRAINT_KEYWORDS
        )
        if constraint_count > 0:
            constraint_score = min(0.70, 0.23 * constraint_count)  # 0.23 per keyword
            complexity_score += constraint_score
        
        # Factor 3: Multi-Step Instructions (0-0.60 points) - Increased to 0.60
        multistep_count = sum(
            prompt_lower.count(keyword)
            for keyword in ComplexityCalculator.MULTI_STEP_KEYWORDS
        )
        if multistep_count > 0:
            multistep_score = min(0.60, 0.20 * multistep_count)  # Increased from 0.18 to 0.20
            complexity_score += multistep_score
        
        # Factor 4: Structural/Formatting Keywords (0-0.12 points) - Slightly increased
        structure_count = sum(
            prompt_lower.count(keyword)
            for keyword in ComplexityCalculator.STRUCTURE_KEYWORDS
        )
        if structure_count > 0:
            structure_score = min(0.12, 0.08 * structure_count)
            complexity_score += structure_score
        
        # Factor 5: Examples Provided (0-0.08 points) - Slightly reduced
        example_count = sum(
            prompt_lower.count(keyword)
            for keyword in ComplexityCalculator.EXAMPLE_KEYWORDS
        )
        if example_count > 0:
            example_score = min(0.08, 0.05 * example_count)
            complexity_score += example_score
        
        # Normalize to 0-1 scale
        normalized_score = min(1.0, complexity_score)
        
        return round(normalized_score, 2)
    
    @staticmethod
    def compute_complexity_from_signals(signals: dict) -> float:
        """
        Compute complexity from behavior signals.
        
        Args:
            signals: Dict of signal_name -> score
            
        Returns:
            float: Complexity score (0.0 = simple, 1.0 = very complex)
        """
        if not signals:
            return 0.5
        
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
        
        return round(normalized_score, 2)
