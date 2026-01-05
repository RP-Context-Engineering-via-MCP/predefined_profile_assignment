"""Domain Expertise Tracking Service.

Manages user expertise level tracking across interest domains.
Implements signal detection, confidence calculation, and dynamic level updates.
Supports both prompt-based and JSON-based (behavior extraction) updates.
"""

from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
import re

from app.repositories.user_domain_state_repo import UserDomainStateRepository
from app.core.constants import (
    ExpertiseThresholds,
    ExpertiseSignalWeights,
    ExpertiseSignalKeywords,
    ExpertiseUpdateRules
)


class DomainExpertiseService:
    """Service for tracking and updating user domain expertise."""

    def __init__(self, db: Session):
        """Initialize service with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.repo = UserDomainStateRepository()

    def should_update_expertise(self, prompt: str) -> bool:
        """Determine if expertise should be updated for this prompt.
        
        Do NOT update on:
        - Greetings, acknowledgements
        - Pure follow-ups like "ok", "thanks"
        - Very short prompts
        
        Args:
            prompt: User's prompt text
            
        Returns:
            True if expertise should be updated
        """
        if not prompt or len(prompt.strip()) == 0:
            return False

        prompt_lower = prompt.lower().strip()
        words = prompt_lower.split()

        # Check minimum length
        if len(words) < ExpertiseUpdateRules.MIN_PROMPT_LENGTH:
            return False

        # Check ignore patterns
        for pattern in ExpertiseUpdateRules.IGNORE_PATTERNS:
            if prompt_lower == pattern or prompt_lower.startswith(pattern + " "):
                return False

        return True

    def detect_expertise_signals(self, prompt: str) -> Dict[str, float]:
        """Detect expertise signals in user prompt.
        
        Analyzes prompt for:
        - Beginner indicators (what is, define, etc.)
        - Advanced indicators (optimize, edge cases, etc.)
        - Technical terminology usage
        - Multi-step requests
        - Iterative refinement patterns
        
        Args:
            prompt: User's prompt text
            
        Returns:
            Dictionary mapping signal names to confidence deltas
        """
        signals: Dict[str, float] = {}
        prompt_lower = prompt.lower()

        # Detect beginner signals
        for keyword in ExpertiseSignalKeywords.BEGINNER_KEYWORDS:
            if keyword in prompt_lower:
                signals["BEGINNER_QUESTION"] = ExpertiseSignalWeights.BEGINNER_QUESTION
                break

        # Detect advanced signals
        for keyword in ExpertiseSignalKeywords.ADVANCED_KEYWORDS:
            if keyword in prompt_lower:
                if "assume" in keyword or "skip" in keyword:
                    signals["ASSUME_KNOWLEDGE"] = ExpertiseSignalWeights.ASSUME_KNOWLEDGE
                else:
                    signals["EXPLICIT_ADVANCED"] = ExpertiseSignalWeights.EXPLICIT_ADVANCED_REQUEST
                break

        # Detect multi-step patterns
        multi_step_indicators = ["first", "then", "next", "finally", "step 1", "step 2", "also"]
        if any(indicator in prompt_lower for indicator in multi_step_indicators):
            signals["MULTI_STEP"] = ExpertiseSignalWeights.MULTI_STEP_PROMPT

        # Detect iterative refinement patterns
        iterative_indicators = ["refine", "improve", "optimize", "better", "enhance", "modify"]
        if any(indicator in prompt_lower for indicator in iterative_indicators):
            signals["ITERATIVE"] = ExpertiseSignalWeights.ITERATIVE_REFINEMENT

        # Detect technical terminology (basic check)
        technical_word_count = 0
        words = prompt_lower.split()
        for domain_terms in ExpertiseSignalKeywords.TECHNICAL_TERMS.values():
            for term in domain_terms:
                if term in prompt_lower:
                    technical_word_count += 1

        if technical_word_count >= 2:
            signals["CORRECT_TERMINOLOGY"] = ExpertiseSignalWeights.CORRECT_TERMINOLOGY

        # Generic short prompt (neutral)
        if len(words) < 10 and not signals:
            signals["GENERIC_SHORT"] = ExpertiseSignalWeights.GENERIC_SHORT_PROMPT

        return signals

    def calculate_new_confidence(
        self,
        old_confidence: float,
        signals: Dict[str, float],
        decay: float = 0.0
    ) -> float:
        """Calculate new confidence score based on signals.
        
        Formula:
        new_confidence = clamp(
            old_confidence + sum(signals) - decay,
            0.0, 1.0
        )
        
        Args:
            old_confidence: Current confidence score
            signals: Detected signals with their delta values
            decay: Optional decay value to apply
            
        Returns:
            New confidence score (0.0 to 1.0)
        """
        signal_sum = sum(signals.values())
        new_confidence = old_confidence + signal_sum - decay

        # Clamp to valid range
        return max(
            ExpertiseSignalWeights.MIN_CONFIDENCE,
            min(new_confidence, ExpertiseSignalWeights.MAX_CONFIDENCE)
        )

    def determine_expertise_level(self, confidence_score: float) -> str:
        """Determine expertise level name from confidence score.
        
        Thresholds:
        - BEGINNER: 0.00 – 0.39
        - INTERMEDIATE: 0.40 – 0.74
        - ADVANCED: 0.75 – 1.00
        
        Args:
            confidence_score: Confidence score (0.0 to 1.0)
            
        Returns:
            Expertise level name
        """
        if confidence_score <= ExpertiseThresholds.BEGINNER_MAX:
            return "BEGINNER"
        elif confidence_score <= ExpertiseThresholds.INTERMEDIATE_MAX:
            return "INTERMEDIATE"
        else:
            return "ADVANCED"

    def update_user_expertise(
        self,
        user_id: str,
        interest_id: int,
        prompt: str,
        complexity_score: Optional[float] = None
    ) -> Optional[Dict]:
        """Update user's expertise for a specific domain.
        
        Main entry point for expertise tracking.
        Checks if update is needed, detects signals, calculates
        new confidence, and persists changes.
        
        Args:
            user_id: User identifier
            interest_id: Interest domain identifier
            prompt: User's prompt text
            complexity_score: Optional complexity score from analysis
            
        Returns:
            Dictionary with update details, or None if no update
        """
        # Check if update should proceed
        if not self.should_update_expertise(prompt):
            return None

        # Skip if complexity is too low (if provided)
        if complexity_score is not None:
            if complexity_score < ExpertiseUpdateRules.MIN_COMPLEXITY_THRESHOLD:
                return None

        # Get current state
        current_state = self.repo.get_user_domain_state(self.db, user_id, interest_id)

        if current_state:
            old_confidence = current_state.confidence_score
            old_level_id = current_state.expertise_level_id
        else:
            # Cold start - initialize with beginner
            old_confidence = ExpertiseSignalWeights.COLD_START_CONFIDENCE
            old_level_id = None

        # Detect signals
        signals = self.detect_expertise_signals(prompt)

        # Calculate new confidence
        new_confidence = self.calculate_new_confidence(old_confidence, signals)

        # Determine new expertise level
        new_level_id = self.repo.get_expertise_level_id_by_confidence(
            self.db, new_confidence
        )

        # Persist update
        updated_state = self.repo.upsert_user_domain_state(
            self.db,
            user_id=user_id,
            interest_id=interest_id,
            expertise_level_id=new_level_id,
            confidence_score=new_confidence
        )

        return {
            "user_id": user_id,
            "interest_id": interest_id,
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "confidence_delta": new_confidence - old_confidence,
            "signals_detected": list(signals.keys()),
            "signal_values": signals,
            "expertise_level": self.determine_expertise_level(new_confidence),
            "level_changed": old_level_id != new_level_id if old_level_id else False
        }

    def get_user_expertise(
        self,
        user_id: str,
        interest_id: Optional[int] = None
    ) -> Optional[Dict]:
        """Get user's current expertise state.
        
        Args:
            user_id: User identifier
            interest_id: Optional interest domain identifier
            
        Returns:
            Expertise state dictionary or None
        """
        if interest_id:
            state = self.repo.get_user_domain_state(self.db, user_id, interest_id)
            if not state:
                return None

            return {
                "user_id": state.user_id,
                "interest_id": state.interest_id,
                "expertise_level_id": state.expertise_level_id,
                "expertise_level": self.determine_expertise_level(state.confidence_score),
                "confidence_score": state.confidence_score,
                "last_updated": state.last_updated
            }
        else:
            states = self.repo.get_all_user_domain_states(self.db, user_id)
            return [
                {
                    "user_id": s.user_id,
                    "interest_id": s.interest_id,
                    "expertise_level_id": s.expertise_level_id,
                    "expertise_level": self.determine_expertise_level(s.confidence_score),
                    "confidence_score": s.confidence_score,
                    "last_updated": s.last_updated
                }
                for s in states
            ]

    def apply_decay_to_inactive_domains(self) -> int:
        """Apply time-based decay to all inactive domain states.
        
        Should be run periodically (daily/weekly) to handle drift.
        
        Returns:
            Number of records updated
        """
        return self.repo.apply_decay_to_inactive_states(
            self.db,
            days_threshold=ExpertiseThresholds.DECAY_DAYS_THRESHOLD,
            decay_factor=ExpertiseThresholds.DECAY_FACTOR
        )

    def initialize_cold_start(
        self,
        user_id: str,
        interest_id: int
    ) -> Dict:
        """Initialize expertise tracking for new user-domain pair.
        
        Sets beginner level with low confidence as starting point.
        
        Args:
            user_id: User identifier
            interest_id: Interest domain identifier
            
        Returns:
            Created state dictionary
        """
        beginner_level = self.repo.get_expertise_level_by_name(self.db, "BEGINNER")
        
        state = self.repo.upsert_user_domain_state(
            self.db,
            user_id=user_id,
            interest_id=interest_id,
            expertise_level_id=beginner_level.expertise_level_id,
            confidence_score=ExpertiseSignalWeights.COLD_START_CONFIDENCE
        )

        return {
            "user_id": state.user_id,
            "interest_id": state.interest_id,
            "expertise_level": "BEGINNER",
            "confidence_score": state.confidence_score,
            "initialized": True
        }

    def calculate_confidence_delta_from_json(
        self,
        behavior_level: str,
        signals: List[str],
        consistency: Optional[float] = None,
        complexity: Optional[float] = None
    ) -> float:
        """Calculate confidence delta from JSON behavior extraction data.
        
        Maps behavior components to confidence increments:
        - behavior_level: BASIC=+0.05, INTERMEDIATE=+0.10, ADVANCED=+0.20
        - signals: Sum of signal weights (MULTI_STEP=+0.15, ITERATIVE=+0.20, etc.)
        - consistency: >0.5 → +0.05 bonus
        - complexity: >0.5 → +0.05 bonus
        
        Args:
            behavior_level: User's behavior level (BASIC, INTERMEDIATE, ADVANCED)
            signals: List of detected behavior signals
            consistency: Optional consistency score (0.0-1.0)
            complexity: Optional complexity score (0.0-1.0)
            
        Returns:
            Total confidence delta to add
        """
        delta = 0.0

        # Behavior level contribution
        behavior_level_weights = {
            "BASIC": ExpertiseSignalWeights.BEHAVIOR_LEVEL_BASIC,
            "INTERMEDIATE": ExpertiseSignalWeights.BEHAVIOR_LEVEL_INTERMEDIATE,
            "ADVANCED": ExpertiseSignalWeights.BEHAVIOR_LEVEL_ADVANCED
        }
        delta += behavior_level_weights.get(behavior_level.upper(), 0.0)

        # Signal contributions
        signal_weight_map = {
            "DEEP_REASONING": ExpertiseSignalWeights.CORRECT_TERMINOLOGY,
            "MULTI_STEP": ExpertiseSignalWeights.MULTI_STEP_PROMPT,
            "ITERATIVE": ExpertiseSignalWeights.ITERATIVE_REFINEMENT,
            "GOAL_ORIENTED": 0.05,  # Neutral positive
            "CASUAL": ExpertiseSignalWeights.GENERIC_SHORT_PROMPT
        }
        
        for signal in signals:
            signal_upper = signal.upper()
            delta += signal_weight_map.get(signal_upper, 0.0)

        # Optional modifiers
        if consistency is not None and consistency > 0.5:
            delta += ExpertiseSignalWeights.CONSISTENCY_BONUS

        if complexity is not None and complexity > 0.5:
            delta += ExpertiseSignalWeights.COMPLEXITY_BONUS

        return delta

    def update_expertise_from_json(
        self,
        user_id: str,
        behavior_data: Dict
    ) -> List[Dict]:
        """Update user expertise from JSON behavior extraction data.
        
        Processes behavior JSON and updates expertise for each interest domain.
        Each interest is treated independently with its own confidence update.
        
        Expected JSON structure:
        {
            "user_id": "user123",
            "interests": ["AI", "PROGRAMMING"],
            "behavior_level": "INTERMEDIATE",
            "signals": ["MULTI_STEP", "ITERATIVE"],
            "intents": ["LEARNING"],  # Not used for expertise
            "consistency": 0.65,
            "complexity": 0.70
        }
        
        Args:
            user_id: User identifier
            behavior_data: Extracted behavior dictionary
            
        Returns:
            List of update results for each interest domain
        """
        results = []
        
        # Extract components
        interests = behavior_data.get("interests", [])
        behavior_level = behavior_data.get("behavior_level", "BASIC")
        signals = behavior_data.get("signals", [])
        consistency = behavior_data.get("consistency")
        complexity = behavior_data.get("complexity")

        # Calculate confidence delta from behavior components
        confidence_delta = self.calculate_confidence_delta_from_json(
            behavior_level=behavior_level,
            signals=signals,
            consistency=consistency,
            complexity=complexity
        )

        # Update each interest domain
        for interest_name in interests:
            # Map interest name to ID
            interest_id = self._map_interest_name_to_id(interest_name)
            if not interest_id:
                continue

            # Get current state or initialize
            current_state = self.repo.get_user_domain_state(self.db, user_id, interest_id)
            
            if current_state:
                old_confidence = current_state.confidence_score
                old_level_id = current_state.expertise_level_id
            else:
                # Cold start
                old_confidence = ExpertiseSignalWeights.COLD_START_CONFIDENCE
                old_level_id = None

            # Calculate new confidence
            new_confidence = self.calculate_new_confidence(
                old_confidence=old_confidence,
                signals={"json_update": confidence_delta},
                decay=0.0
            )

            # Determine new level
            new_level_id = self.repo.get_expertise_level_id_by_confidence(
                self.db, new_confidence
            )

            # Persist update
            updated_state = self.repo.upsert_user_domain_state(
                self.db,
                user_id=user_id,
                interest_id=interest_id,
                expertise_level_id=new_level_id,
                confidence_score=new_confidence
            )

            results.append({
                "user_id": user_id,
                "interest_id": interest_id,
                "interest_name": interest_name,
                "old_confidence": old_confidence,
                "new_confidence": new_confidence,
                "confidence_delta": new_confidence - old_confidence,
                "expertise_level": self.determine_expertise_level(new_confidence),
                "level_changed": old_level_id != new_level_id if old_level_id else False,
                "behavior_level": behavior_level,
                "signals": signals
            })

        return results

    def update_expertise_from_json_batch(
        self,
        user_id: str,
        behavior_batch: List[Dict]
    ) -> Dict:
        """Update user expertise from batch of behavior JSONs (DRIFT mode).
        
        Processes multiple behavior observations and aggregates updates.
        Used in DRIFT_FALLBACK mode with multiple prompts.
        
        Args:
            user_id: User identifier
            behavior_batch: List of behavior dictionaries
            
        Returns:
            Aggregated update results
        """
        all_results = []
        
        for behavior_data in behavior_batch:
            results = self.update_expertise_from_json(user_id, behavior_data)
            all_results.extend(results)

        # Aggregate by interest
        aggregated = {}
        for result in all_results:
            interest_id = result["interest_id"]
            if interest_id not in aggregated:
                aggregated[interest_id] = result
            else:
                # Keep the latest update
                aggregated[interest_id] = result

        return {
            "user_id": user_id,
            "total_updates": len(all_results),
            "unique_domains": len(aggregated),
            "domain_updates": list(aggregated.values())
        }

    def _map_interest_name_to_id(self, interest_name: str) -> Optional[int]:
        """Map interest name to interest_id.
        
        Maps common interest names to their database IDs.
        
        Args:
            interest_name: Interest name string
            
        Returns:
            Interest ID or None if not found
        """
        # Interest mapping based on seed data
        interest_map = {
            "AI": 1,
            "DATA_SCIENCE": 2,
            "WRITING": 3,
            "PROGRAMMING": 4,
            "CREATIVE": 5,
            "HEALTH": 6,
            "PERSONAL_GROWTH": 7,
            "ENTERTAINMENT": 8
        }
        
        return interest_map.get(interest_name.upper())
