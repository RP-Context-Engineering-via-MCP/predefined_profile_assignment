#!/usr/bin/env python3
"""
Unit Tests for Profile Assignment Services
Tests individual components:
- ComplexityCalculator
- ConsistencyCalculator
- ProfileMatcher
- ProfileAssigner
"""

import unittest
from app.services.complexity_calculator import ComplexityCalculator
from app.services.consistency_calculator import ConsistencyCalculator

class TestComplexityCalculator(unittest.TestCase):
    """Test complexity calculation from prompts."""
    
    def test_simple_prompt_low_complexity(self):
        """Simple short prompt should have low complexity."""
        prompt = "What is AI?"
        complexity = ComplexityCalculator.compute_complexity(prompt)
        self.assertLess(complexity, 0.25, "Simple prompt should have low complexity")
    
    def test_constrained_prompt_medium_complexity(self):
        """Prompt with constraints should have medium complexity."""
        prompt = "Write a Python function that validates email addresses. Must use regex and handle edge cases."
        complexity = ComplexityCalculator.compute_complexity(prompt)
        self.assertGreater(complexity, 0.30, "Constrained prompt should have medium+ complexity")
    
    def test_multistep_prompt_high_complexity(self):
        """Multi-step prompt should have high complexity."""
        prompt = "First, analyze the dataset. Then, prepare features. Next, train the model with cross-validation. Finally, evaluate performance and generate reports."
        complexity = ComplexityCalculator.compute_complexity(prompt)
        self.assertGreater(complexity, 0.60, "Multi-step prompt should have high complexity")
    
    def test_structured_prompt_high_complexity(self):
        """Prompt with structure requests should have high complexity."""
        prompt = "Create a JSON template with the following fields: id, name, email. Format as valid JSON."
        complexity = ComplexityCalculator.compute_complexity(prompt)
        self.assertGreater(complexity, 0.40, "Structured prompt should have medium+ complexity")
    
    def test_empty_prompt_default(self):
        """Empty prompt should return default."""
        complexity = ComplexityCalculator.compute_complexity("")
        self.assertEqual(complexity, 0.5, "Empty prompt should return neutral default")
    
    def test_complexity_from_signals(self):
        """Complexity from signals should work correctly."""
        signals = {
            "MULTI_STEP": 0.8,
            "ITERATIVE": 0.6,
            "GOAL_ORIENTED": 0.5,
            "CASUAL": 0.1
        }
        complexity = ComplexityCalculator.compute_complexity_from_signals(signals)
        self.assertGreater(complexity, 0.40, "Signals with MULTI_STEP should indicate high complexity")


class TestConsistencyCalculator(unittest.TestCase):
    """Test consistency calculation from session history."""
    
    def test_perfectly_consistent_intent(self):
        """Same intent repeated should have high consistency."""
        intent_history = ["LEARNING", "LEARNING", "LEARNING", "LEARNING"]
        domain_history = ["ACADEMIC", "ACADEMIC", "ACADEMIC", "ACADEMIC"]
        
        consistency = ConsistencyCalculator.compute_from_history(intent_history, domain_history)
        self.assertGreater(consistency, 0.85, "Perfectly consistent history should have high consistency")
    
    def test_low_consistency_diverse_intents(self):
        """Diverse intents should have low consistency."""
        intent_history = ["LEARNING", "TASK_COMPLETION", "GUIDANCE", "ENGAGEMENT"]
        domain_history = ["ACADEMIC", "BUSINESS", "LIFESTYLE", "ENTERTAINMENT"]
        
        consistency = ConsistencyCalculator.compute_from_history(intent_history, domain_history)
        self.assertLess(consistency, 0.40, "Diverse intent history should have low consistency")
    
    def test_moderate_consistency(self):
        """Majority consistent with some variation should have moderate consistency."""
        intent_history = ["LEARNING", "LEARNING", "LEARNING", "TASK_COMPLETION"]
        domain_history = ["ACADEMIC", "ACADEMIC", "ACADEMIC", "BUSINESS"]
        
        consistency = ConsistencyCalculator.compute_from_history(intent_history, domain_history)
        self.assertTrue(0.50 < consistency < 0.85, "Mostly consistent history should have moderate consistency")
    
    def test_single_prompt_default(self):
        """Single prompt should return default."""
        consistency = ConsistencyCalculator.compute_from_history(["LEARNING"], ["ACADEMIC"])
        self.assertEqual(consistency, 0.5, "Single prompt should return neutral default")
    
    def test_consistency_with_signals(self):
        """Consistency with signal history should include signal factor."""
        intent_history = ["PROBLEM_SOLVING", "PROBLEM_SOLVING", "PROBLEM_SOLVING"]
        domain_history = ["TECHNICAL", "TECHNICAL", "TECHNICAL"]
        signal_history = [
            {"MULTI_STEP": 0.8},
            {"MULTI_STEP": 0.7},
            {"MULTI_STEP": 0.9}
        ]
        
        consistency = ConsistencyCalculator.compute_from_history(
            intent_history, domain_history, signal_history
        )
        self.assertGreater(consistency, 0.80, "Consistent signals should increase consistency score")
    
    def test_transition_stability(self):
        """Few transitions should indicate high stability."""
        history = ["LEARNING", "LEARNING", "LEARNING", "TASK_COMPLETION", "TASK_COMPLETION"]
        stability = ConsistencyCalculator._calculate_transition_stability(history)
        self.assertGreater(stability, 0.60, "Few transitions should indicate high stability")
    
    def test_high_transitions_low_stability(self):
        """Many transitions should indicate low stability."""
        history = ["A", "B", "C", "D", "E"]  # Maximum transitions
        stability = ConsistencyCalculator._calculate_transition_stability(history)
        self.assertEqual(stability, 0.0, "Maximum transitions should have zero stability")
    
    def test_consistency_summary(self):
        """Consistency summary should provide detailed breakdown."""
        intent_history = ["LEARNING", "LEARNING", "PROBLEM_SOLVING"]
        domain_history = ["ACADEMIC", "ACADEMIC", "TECHNICAL"]
        
        summary = ConsistencyCalculator.compute_summary(intent_history, domain_history)
        
        self.assertIn("overall_consistency", summary)
        self.assertIn("dominant_intent", summary)
        self.assertIn("intent_dominance", summary)
        self.assertEqual(summary["dominant_intent"], "LEARNING")
        self.assertAlmostEqual(summary["intent_dominance"], 2/3, places=2)
    
    def test_current_prompt_match_high(self):
        """Current prompt matching history should score correctly."""
        current_intent = "PROBLEM_SOLVING"
        current_domain = "TECHNICAL"
        intent_history = ["PROBLEM_SOLVING", "PROBLEM_SOLVING"]
        domain_history = ["TECHNICAL", "TECHNICAL"]
        
        match_score = ConsistencyCalculator.compute_from_current_prompt(
            current_intent, current_domain, intent_history, domain_history
        )
        self.assertEqual(match_score, 1.0, "Perfect match should score 1.0")
    
    def test_current_prompt_match_partial(self):
        """Partial match with history should score accordingly."""
        current_intent = "PROBLEM_SOLVING"
        current_domain = "ACADEMIC"  # Doesn't match TECHNICAL
        intent_history = ["PROBLEM_SOLVING", "PROBLEM_SOLVING"]
        domain_history = ["TECHNICAL", "TECHNICAL"]
        
        match_score = ConsistencyCalculator.compute_from_current_prompt(
            current_intent, current_domain, intent_history, domain_history
        )
        self.assertEqual(match_score, 0.5, "Partial match should score 0.5")
    
    def test_current_prompt_no_match(self):
        """No match with history should score 0."""
        current_intent = "GUIDANCE"  # Different intent
        current_domain = "LIFESTYLE"  # Different domain
        intent_history = ["LEARNING", "LEARNING"]
        domain_history = ["ACADEMIC", "ACADEMIC"]
        
        match_score = ConsistencyCalculator.compute_from_current_prompt(
            current_intent, current_domain, intent_history, domain_history
        )
        self.assertEqual(match_score, 0.0, "No match should score 0.0")


class TestComplexityAndConsistencyIntegration(unittest.TestCase):
    """Test integration of complexity and consistency."""
    
    def test_high_complexity_technical_prompt(self):
        """Technical complex prompt characteristics."""
        prompt = "Implement a multi-threaded Python service with database connection pooling. Must handle concurrent requests, optimize performance, and include error recovery."
        complexity = ComplexityCalculator.compute_complexity(prompt)
        self.assertGreater(complexity, 0.70, "Technical complex prompt should have high complexity")
    
    def test_consistency_improves_confidence(self):
        """Consistent history should produce higher consistency scores."""
        # Highly consistent
        consistent_history_intent = ["PROBLEM_SOLVING"] * 5
        consistent_history_domain = ["TECHNICAL"] * 5
        
        # Diverse
        diverse_history_intent = ["LEARNING", "TASK_COMPLETION", "GUIDANCE", "ENGAGEMENT", "EXPLORATION"]
        diverse_history_domain = ["ACADEMIC", "BUSINESS", "LIFESTYLE", "ENTERTAINMENT", "CREATIVE"]
        
        consistent_score = ConsistencyCalculator.compute_from_history(
            consistent_history_intent, consistent_history_domain
        )
        diverse_score = ConsistencyCalculator.compute_from_history(
            diverse_history_intent, diverse_history_domain
        )
        
        self.assertGreater(consistent_score, diverse_score,
                          "Consistent history should have higher consistency")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_complexity_with_mixed_keywords(self):
        """Multiple complexity factors should accumulate."""
        prompt = "Create a multi-step process: first, validate input with constraints; then, structure output as JSON; finally, test with examples."
        complexity = ComplexityCalculator.compute_complexity(prompt)
        self.assertGreater(complexity, 0.60, "Multiple factors should produce high complexity")
    
    def test_very_long_prompt_bounded(self):
        """Very long prompts should be bounded to max 1.0."""
        long_prompt = "word " * 500  # 500+ words
        complexity = ComplexityCalculator.compute_complexity(long_prompt)
        self.assertLessEqual(complexity, 1.0, "Complexity should be bounded to 1.0")
    
    def test_empty_history_default(self):
        """Empty session history should return default."""
        consistency = ConsistencyCalculator.compute_from_history([], [])
        self.assertEqual(consistency, 0.5, "Empty history should return neutral default")
    
    def test_none_signals_handled(self):
        """None signals should be handled gracefully."""
        intent_history = ["LEARNING", "LEARNING"]
        domain_history = ["ACADEMIC", "ACADEMIC"]
        
        # Should not raise exception
        consistency = ConsistencyCalculator.compute_from_history(
            intent_history, domain_history, signal_history=None
        )
        self.assertGreater(consistency, 0.70, "Should handle None signals gracefully")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
