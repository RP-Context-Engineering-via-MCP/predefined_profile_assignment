"""Profile assignment orchestration service.

Coordinates profile matching, ranking state management, and assignment decisions
for both cold-start and drift-fallback scenarios."""

from app.services.profile_matcher import ProfileMatcher
from app.services.consistency_calculator import ConsistencyCalculator
from app.repositories.predefined_profile_repo import PredefinedProfileRepository
from app.services.ranking_state_service import RankingStateService
from app.repositories.user_repo import UserRepository
from typing import Optional, Tuple, Union, List


class ProfileAssigner:
    """Profile assignment orchestration service.
    
    Manages end-to-end profile assignment workflow including matching,
    ranking state updates, and assignment decision logic.
    
    Attributes:
        repo: Predefined profile repository
        ranking_service: Ranking state service
        user_repo: User repository
        db: Database session
    """

    def __init__(self, db):
        """Initialize profile assigner with database session.
        
        Args:
            db: Active SQLAlchemy session
        """
        self.repo = PredefinedProfileRepository(db)
        self.ranking_service = RankingStateService(db)
        self.user_repo = UserRepository(db)
        self.db = db

    def get_assignment_status(self, user_id: str) -> dict:
        """Retrieve current profile assignment status without triggering new assignment.
        
        Provides comprehensive view of user's profile assignment state including
        confidence level, mode, and aggregated ranking statistics.
        
        Args:
            user_id: User unique identifier
            
        Returns:
            Dictionary containing:
                - status: ASSIGNED, PENDING, or NOT_FOUND
                - confidence_level: HIGH, MEDIUM, LOW, or NONE
                - user_mode: Current profile mode
                - prompt_count: Number of processed prompts
                - assigned_profile_id: Currently assigned profile or None
                - aggregated_rankings: List of all profile ranking states
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
        
        # Check if user has assigned profile
        assigned_profile_id = user.predefined_profile_id if user else None
        
        # Get user mode from user database (profile_mode field)
        user_mode = user.profile_mode.value
        
        # Determine status and confidence level
        if assigned_profile_id:
            status = "ASSIGNED"
            # Get confidence from top profile's average score
            if aggregated_states:
                top_score = aggregated_states[0].average_score
                confidence_level = "HIGH" if top_score >= 0.70 else "MEDIUM"
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
        """Determine if profile should be assigned based on ranking state.
        
        Applies different criteria for cold-start vs drift-fallback scenarios:
        - Cold-start: requires min_prompts, cold_threshold, and 2+ consecutive tops
        - Drift-fallback: requires fallback_threshold and 3+ consecutive tops
        
        Args:
            user_id: User unique identifier
            user_mode: Assignment mode (COLD_START or DRIFT_FALLBACK)
            min_prompts: Minimum observations required for cold-start
            cold_threshold: Average score threshold for cold-start (default 0.60)
            fallback_threshold: Average score threshold for drift-fallback (default 0.70)
            
        Returns:
            Tuple of (should_assign, profile_id, average_score)
        """
        top_states = self.ranking_service.get_top_profiles_for_user(user_id, limit=1)
        if not top_states:
            return False, None, 0.0

        best = top_states[0]

        if user_mode == 'COLD_START':
            if best.observation_count < min_prompts:
                return False, None, best.average_score

            if best.average_score >= cold_threshold and best.consecutive_top_count >= 2:
                return True, best.profile_id, best.average_score

        elif user_mode == 'DRIFT_FALLBACK':
            if best.average_score >= fallback_threshold and best.consecutive_top_count >= 3:
                return True, best.profile_id, best.average_score

        return False, None, best.average_score

    def assign(
        self, 
        extracted_behavior: Union[dict, List[dict]], 
        user_id: str
    ) -> dict:
        """Assign profile based on extracted behavioral data.
        
        Main orchestration method that:
        1. Fetches user mode from database
        2. Validates behavior format based on user mode
        3. Loads profiles and matching factors
        4. Processes behavior(s) through profile matcher
        5. Updates ranking state with results
        6. Determines if assignment criteria met
        7. Persists assignment if applicable
        
        Args:
            extracted_behavior: Single behavior dict (COLD_START) or list of dicts (DRIFT_FALLBACK).
                Each dict contains: intents, interests, signals, behavior_level, 
                consistency, complexity
            user_id: User unique identifier for ranking persistence and mode retrieval
            
        Returns:
            dict: Assignment result containing:
                - status: ASSIGNED or PENDING
                - confidence_level: HIGH, MEDIUM, or LOW
                - user_mode: Assignment mode used
                - prompt_count: Total prompts processed
                - assigned_profile_id: Assigned profile or None
                - aggregated_rankings: List of all profile ranking states
                
        Raises:
            ValueError: If user not found or behavior format invalid for user mode
        """
        # Fetch user and get their current mode from database
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        user_mode = user.profile_mode.value
        
        # Validate behavior format based on user_mode from database
        if user_mode == 'DRIFT_FALLBACK':
            if isinstance(extracted_behavior, dict):
                raise ValueError(
                    "DRIFT_FALLBACK mode expects a list of behavior dicts, not a single dict"
                )
            if not isinstance(extracted_behavior, list) or len(extracted_behavior) == 0:
                raise ValueError(
                    "DRIFT_FALLBACK mode requires at least one behavior dict in the list"
                )
        elif user_mode == 'COLD_START':
            if isinstance(extracted_behavior, list):
                raise ValueError(
                    "COLD_START mode expects a single behavior dict, not a list"
                )
        
        # Load profiles and matching factors
        profiles = self.repo.load_full_profiles()
        standard_weights = self.repo.load_matching_factors(mode='STANDARD')
        cold_start_weights = self.repo.load_matching_factors(mode='COLD_START')
        matcher = ProfileMatcher(standard_weights, cold_start_weights)
        
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
        min_prompts = 5 if user_mode == 'COLD_START' else 3
        cold_threshold = 0.60
        fallback_threshold = 0.70
        
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
            confidence_level = "HIGH" if avg_score >= 0.70 else "MEDIUM"
            
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