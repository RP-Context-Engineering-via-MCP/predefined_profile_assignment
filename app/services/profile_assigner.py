# app/services/profile_assigner.py

from app.services.profile_matcher import ProfileMatcher
from app.services.consistency_calculator import ConsistencyCalculator
from app.repositories.predefined_profile_repo import PredefinedProfileRepository
from app.services.ranking_state_service import RankingStateService
from typing import Optional, Tuple


class ProfileAssigner:

    def __init__(self, db):
        self.repo = PredefinedProfileRepository(db)
        self.ranking_service = RankingStateService(db)
        self.db = db

    def should_assign_profile(
        self,
        user_id: str,
        user_mode: str = 'COLD_START',
        min_prompts: int = 3,
        cold_threshold: float = 0.60,
        fallback_threshold: float = 0.70
    ) -> Tuple[bool, Optional[str], float]:
        """
        Decide if profile should be assigned based on accumulated ranking state.
        
        This implements the unified assignment logic from fullplan.txt section 4.
        
        Args:
            user_id: User ID
            user_mode: 'COLD_START' or 'DRIFT_FALLBACK'
            min_prompts: Minimum observations required for cold-start
            cold_threshold: Average score threshold for cold-start assignment
            fallback_threshold: Average score threshold for fallback assignment
            
        Returns:
            Tuple of (should_assign, profile_id, average_score)
        """
        # Get top profile from accumulated ranking state
        top_states = self.ranking_service.get_top_profiles_for_user(user_id, limit=1)
        
        if not top_states:
            return False, None, 0.0
        
        best = top_states[0]
        
        if user_mode == 'COLD_START':
            # Cold-start: Wait for minimum observations
            if best.observation_count < min_prompts:
                return False, None, best.average_score
            
            # Check if accumulated average meets threshold AND rank is stable
            # Per fullplan.txt: average_score >= threshold AND consecutive_top_count >= 2
            if best.average_score >= cold_threshold and best.consecutive_top_count >= 2:
                return True, best.profile_id, best.average_score
                
        elif user_mode == 'DRIFT_FALLBACK':
            # Fallback: Immediate assignment if threshold met (no prompt count check)
            if best.average_score >= fallback_threshold:
                return True, best.profile_id, best.average_score
        
        return False, None, best.average_score

    def assign(
        self, 
        extracted_behavior: dict, 
        prompt_count: int,
        user_id: str,
        user_mode: str = 'COLD_START',
        session_history: dict = None, 
        consistency: float = None,
        min_prompts_for_assignment: int = 3,
        cold_start_threshold: float = 0.60,
        fallback_threshold: float = 0.70
    ) -> dict:
        """
        Assign profiles based on extracted behavior and update ranking state.
        
        CORRECTED: Now uses accumulated ranking state for assignment decisions,
        not just current prompt confidence.
        
        Args:
            extracted_behavior: Extracted behavior features
            prompt_count: Number of prompts in session
            user_id: User ID for ranking state persistence
            user_mode: 'COLD_START' or 'DRIFT_FALLBACK'
            session_history: Optional session history for consistency
            consistency: Optional pre-computed consistency score
            min_prompts_for_assignment: Min observations before assignment (cold-start)
            cold_start_threshold: Average score threshold for cold-start
            fallback_threshold: Average score threshold for fallback
            
        Returns:
            Dict with assignment results
        """
        profiles = self.repo.load_full_profiles()
        matching_factors = self.repo.load_matching_factors()

        matcher = ProfileMatcher(matching_factors)
        
        # Cold-start strategy: first 3-5 prompts use Intent + Domain only
        is_cold_start = prompt_count < 5

        # Compute consistency from session history if not provided
        if consistency is None and session_history:
            consistency = ConsistencyCalculator.compute_from_history(
                intent_history=session_history.get("intent_history", []),
                domain_history=session_history.get("domain_history", []),
                signal_history=session_history.get("signal_history")
            )
        
        # Fallback to default if still None
        if consistency is None:
            consistency = 0.5  # Neutral default
        
        # Inject computed consistency into behavior
        extracted_behavior["consistency"] = consistency

        # STEP 1: Match profiles for current prompt
        result = matcher.match(profiles, extracted_behavior, is_cold_start=is_cold_start)

        # STEP 2: Update ranking state table with current prompt results
        ranked_profiles = result["ranked_profiles"]
        self.ranking_service.update_from_ranked_profiles(
            user_id=user_id,
            ranked_profiles=ranked_profiles
        )

        #STEP 3: Decide if assignment should happen (based on accumulated state)
        should_assign, assigned_profile_id, avg_score = self.should_assign_profile(
            user_id=user_id,
            user_mode=user_mode,
            min_prompts=min_prompts_for_assignment,
            cold_threshold=cold_start_threshold,
            fallback_threshold=fallback_threshold
        )

        # Get current prompt's best profile for comparison
        current_best_profile = result["best_profile"]
        current_confidence = result["confidence"]

        # Determine status and confidence level
        if should_assign:
            status = "ASSIGNED"
            # Use accumulated average score for confidence level
            if avg_score >= 0.70:
                confidence_level = "HIGH"
            elif avg_score >= 0.60:
                confidence_level = "MEDIUM"
            else:
                confidence_level = "MEDIUM"  # Meets threshold but not high
            
            # Use the profile from accumulated ranking state
            primary_profile_id = assigned_profile_id
            primary_confidence = avg_score
        else:
            status = "PENDING"
            confidence_level = "LOW"
            # Still show current prompt's best match
            primary_profile_id = current_best_profile
            primary_confidence = current_confidence
        
        # Filter secondary profiles: include those with score ≥ 40% of best profile score
        secondary_threshold = current_confidence * 0.40
        secondary_profiles = [
            (profile_id, score)
            for profile_id, score in ranked_profiles[1:]  # Skip best profile
            if score >= secondary_threshold
        ]
        
        # Build response
        response = {
            "status": status,
            "confidence_level": confidence_level,
            "user_mode": user_mode,
            "primary_profile": {
                "profile_code": primary_profile_id,
                "confidence": round(primary_confidence, 4),
                "source": "accumulated" if should_assign else "current_prompt"
            },
            "secondary_profiles": [
                {
                    "profile_code": profile_id,
                    "confidence": round(score, 4)
                }
                for profile_id, score in secondary_profiles
            ],
            "all_ranked_profiles": [
                {"profile_code": profile_id, "confidence": round(score, 4)}
                for profile_id, score in ranked_profiles
            ],
            "accumulated_stats": {
                "average_score": round(avg_score, 4) if avg_score > 0 else None,
                "should_assign": should_assign
            }
        }
        
        return response