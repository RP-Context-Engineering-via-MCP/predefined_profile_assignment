# app/services/profile_assigner.py

from app.services.profile_matcher import ProfileMatcher
from app.services.consistency_calculator import ConsistencyCalculator
from app.repositories.predefined_profile_repo import PredefinedProfileRepository
from app.services.ranking_state_service import RankingStateService
from app.repositories.user_repo import UserRepository
from typing import Optional, Tuple, Union, List


class ProfileAssigner:

    def __init__(self, db):
        self.repo = PredefinedProfileRepository(db)
        self.ranking_service = RankingStateService(db)
        self.user_repo = UserRepository(db)
        self.db = db

    def get_assignment_status(self, user_id: str) -> dict:
        """
        Get current profile assignment status for a user without performing new assignment.
        
        Args:
            user_id: User ID to retrieve status for
            
        Returns:
            Dict with status, confidence_level, user_mode, prompt_count, assigned_profile_id, aggregated_rankings
        """
        # Get user to check assigned profile
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            return {
                "status": "NOT_FOUND",
                "confidence_level": "NONE",
                "user_mode": "UNKNOWN",
                "prompt_count": 0,
                "assigned_profile_id": None,
                "aggregated_rankings": []
            }
        
        # Get aggregated ranking states
        aggregated_states, _ = self.ranking_service.get_all_states_for_user(
            user_id=user_id,
            skip=0,
            limit=1000
        )
        
        # Get prompt count from top state
        prompt_count = aggregated_states[0].observation_count if aggregated_states else 0
        
        # Determine user mode based on prompt count
        user_mode = "COLD_START" if prompt_count < 5 else "DRIFT_FALLBACK"
        
        # Check if user has assigned profile
        assigned_profile_id = user.predefined_profile_id if user else None
        
        # Determine status and confidence level
        if assigned_profile_id:
            status = "ASSIGNED"
            # Get confidence from top profile's average score
            if aggregated_states:
                top_score = aggregated_states[0].average_score
                confidence_level = "HIGH" if top_score >= 0.45 else "MEDIUM"
            else:
                confidence_level = "MEDIUM"
        else:
            status = "PENDING"
            confidence_level = "LOW"
        
        # Build aggregated rankings list
        aggregated_rankings = [
            {
                "profile_code": s.profile_id,
                "average_score": round(s.average_score, 4),
                "cumulative_score": round(s.cumulative_score, 4),
                "max_score": round(s.max_score, 4),
                "observations": s.observation_count,
                "last_rank": s.last_rank,
                "consecutive_top_count": s.consecutive_top_count,
                "consecutive_drop_count": s.consecutive_drop_count,
                "updated_at": s.updated_at
            }
            for s in aggregated_states
        ]
        
        return {
            "status": status,
            "confidence_level": confidence_level,
            "user_mode": user_mode,
            "prompt_count": prompt_count,
            "assigned_profile_id": assigned_profile_id,
            "aggregated_rankings": aggregated_rankings
        }

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

        Args:
            user_id: User ID
            user_mode: 'COLD_START' or 'DRIFT_FALLBACK'
            min_prompts: Minimum observations required (only applies to COLD_START mode)
            cold_threshold: Average score threshold for cold-start assignment
            fallback_threshold: Average score threshold for fallback assignment
        """
        top_states = self.ranking_service.get_top_profiles_for_user(user_id, limit=1)
        if not top_states:
            return False, None, 0.0

        best = top_states[0]

        if user_mode == 'COLD_START':
            # Cold-start: wait for required prompts (e.g., 5) and check stability
            if best.observation_count < min_prompts:
                return False, None, best.average_score

            # Stability + threshold
            if best.average_score >= cold_threshold and best.consecutive_top_count >= 2:
                return True, best.profile_id, best.average_score

        elif user_mode == 'DRIFT_FALLBACK':
            # Fallback: assign immediately if threshold is exceeded (no prompt count wait)
            # Since fallback receives a list of prompts, checking min_prompts is pointless
            if best.average_score >= fallback_threshold:
                return True, best.profile_id, best.average_score

        return False, None, best.average_score

    def assign(
        self, 
        extracted_behavior: Union[dict, List[dict]], 
        user_id: str,
        user_mode: str = 'COLD_START'
    ) -> dict:
        """
        Assign profiles based on extracted behavior and update ranking state.
        
        Args:
            extracted_behavior: Single behavior dict for COLD_START or list of behavior dicts for DRIFT_FALLBACK
                               Each dict contains: (intents, interests, signals, behavior_level, consistency, complexity)
            user_id: User ID for ranking state persistence
            user_mode: 'COLD_START' or 'DRIFT_FALLBACK'
            
        Returns:
            Dict with status, confidence_level, user_mode, prompt_count, assigned_profile_id, aggregated_rankings
        """
        # Load profiles and matching factors
        profiles = self.repo.load_full_profiles()
        matching_factors = self.repo.load_matching_factors()
        matcher = ProfileMatcher(matching_factors)
        
        # Get current prompt count from aggregated state
        aggregated_states_pre, _ = self.ranking_service.get_all_states_for_user(
            user_id=user_id,
            skip=0,
            limit=1
        )
        current_prompt_count = aggregated_states_pre[0].observation_count if aggregated_states_pre else 0
        
        # For DRIFT_FALLBACK mode, expect a list of prompts
        if user_mode == 'DRIFT_FALLBACK':
            if not isinstance(extracted_behavior, list):
                # Wrap single dict in a list for consistent processing
                behavior_list = [extracted_behavior]
            else:
                behavior_list = extracted_behavior
            
            print(f"\n=== FALLBACK MODE: Processing {len(behavior_list)} prompts ===")
            
            # Process each prompt in the list
            for idx, behavior in enumerate(behavior_list):
                prompt_count = current_prompt_count + idx + 1
                
                # Fallback mode always uses full matching (not cold-start)
                is_cold_start = False
                
                print(f"\n--- Processing prompt {idx + 1}/{len(behavior_list)} (Total count: {prompt_count}) ---")
                
                # Match profiles for this prompt
                result = matcher.match(profiles, behavior, is_cold_start=is_cold_start)
                
                # Update ranking state with this prompt's results
                ranked_profiles = result["ranked_profiles"]
                self.ranking_service.update_from_ranked_profiles(
                    user_id=user_id,
                    ranked_profiles=ranked_profiles
                )
            
            # Final prompt count after processing all prompts
            prompt_count = current_prompt_count + len(behavior_list)
            
        else:  # COLD_START mode
            # Single prompt processing
            if isinstance(extracted_behavior, list):
                raise ValueError("COLD_START mode expects a single behavior dict, not a list")
            
            prompt_count = current_prompt_count + 1
            
            # Cold-start: first 5 prompts use Intent + Domain only
            is_cold_start = prompt_count < 5
            
            # Match profiles for current prompt
            result = matcher.match(profiles, extracted_behavior, is_cold_start=is_cold_start)
            
            # Update ranking state with current prompt results
            ranked_profiles = result["ranked_profiles"]
            self.ranking_service.update_from_ranked_profiles(
                user_id=user_id,
                ranked_profiles=ranked_profiles
            )

        # Fetch updated aggregated ranking state
        aggregated_states, _ = self.ranking_service.get_all_states_for_user(
            user_id=user_id,
            skip=0,
            limit=1000
        )

        # Determine if assignment should happen
        # Cold-start: wait for 5 prompts with stability check
        # Fallback: assign immediately if threshold exceeded (no prompt wait)
        min_prompts = 5 if user_mode == 'COLD_START' else 0  # Fallback doesn't need min_prompts
        cold_threshold = 0.60
        fallback_threshold = 0.35  # Realistic for normalized scores across 6 profiles (>2x average)
        
        should_assign, assigned_profile_id, avg_score = self.should_assign_profile(
            user_id=user_id,
            user_mode=user_mode,
            min_prompts=min_prompts,
            cold_threshold=cold_threshold,
            fallback_threshold=fallback_threshold
        )

        # Determine status and confidence level
        if should_assign:
            status = "ASSIGNED"
            # Adjusted confidence levels for realistic thresholds
            confidence_level = "HIGH" if avg_score >= 0.45 else "MEDIUM"
            
            # Persist assignment to user table
            try:
                self.user_repo.update_user(
                    user_id=user_id,
                    predefined_profile_id=assigned_profile_id
                )
            except Exception as e:
                print(f"Warning: Failed to update user profile assignment: {e}")
        else:
            status = "PENDING"
            confidence_level = "LOW"

        # Build aggregated rankings list
        aggregated_rankings = [
            {
                "profile_code": s.profile_id,
                "average_score": round(s.average_score, 4),
                "cumulative_score": round(s.cumulative_score, 4),
                "max_score": round(s.max_score, 4),
                "observations": s.observation_count,
                "last_rank": s.last_rank,
                "consecutive_top_count": s.consecutive_top_count,
                "consecutive_drop_count": s.consecutive_drop_count,
                "updated_at": s.updated_at
            }
            for s in aggregated_states
        ]

        return {
            "status": status,
            "confidence_level": confidence_level,
            "user_mode": user_mode,
            "prompt_count": prompt_count,
            "assigned_profile_id": assigned_profile_id if should_assign else None,
            "aggregated_rankings": aggregated_rankings
        }