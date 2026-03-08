"""Profile assignment orchestration service.

Coordinates profile matching, ranking state management, and assignment decisions
for both cold-start and drift-fallback scenarios."""

import logging
from app.services.profile_matcher import ProfileMatcher
from app.services.consistency_calculator import ConsistencyCalculator
from app.repositories.predefined_profile_repo import PredefinedProfileRepository
from app.services.ranking_state_service import RankingStateService
from app.services.user_management_client import UserManagementClient
from typing import Optional, Tuple, Union, List

logger = logging.getLogger(__name__)


class ProfileAssigner:
    """Profile assignment orchestration service.
    
    Manages end-to-end profile assignment workflow including matching,
    ranking state updates, and assignment decision logic.
    
    Attributes:
        repo: Predefined profile repository
        ranking_service: Ranking state service
        user_client: User Management Service HTTP client
        db: Database session
    """

    def __init__(self, db):
        """Initialize profile assigner with database session.
        
        Args:
            db: Active SQLAlchemy session
        """
        self.repo = PredefinedProfileRepository(db)
        self.ranking_service = RankingStateService(db)
        self.user_client = UserManagementClient()
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
        # Get user data from User Management Service
        user_data = self.user_client.get_user_profile_sync(user_id)
        if not user_data:
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
        assigned_profile_id = user_data.get("predefined_profile_id")
        
        # Get user mode from user data
        user_mode = user_data.get("profile_mode", "COLD_START")
        
        # Determine status and confidence level using dominance ratio
        if assigned_profile_id:
            status = "ASSIGNED"
            # Calculate confidence based on dominance ratio
            if aggregated_states and len(aggregated_states) >= 2:
                top_score = aggregated_states[0].average_score
                second_score = aggregated_states[1].average_score
                consecutive = aggregated_states[0].consecutive_top_count
                
                # Calculate dominance ratio
                if second_score == 0:
                    dominance_ratio = float('inf')
                else:
                    dominance_ratio = top_score / second_score
                
                # Apply same three-tier logic as should_assign_profile
                if dominance_ratio >= 1.5 and consecutive >= 3:
                    confidence_level = "HIGH"
                elif dominance_ratio >= 1.2 and consecutive >= 5:
                    confidence_level = "MEDIUM"
                else:
                    confidence_level = "LOW"
            elif aggregated_states and len(aggregated_states) == 1:
                # Only one profile exists, assign HIGH if it has consistency
                confidence_level = "HIGH" if aggregated_states[0].consecutive_top_count >= 3 else "MEDIUM"
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
        min_prompts: int = 3
    ) -> Tuple[bool, Optional[str], str, float]:
        """Determine if profile should be assigned based on dominance ratio.
        
        Uses dominance ratio (top_score / second_score) instead of absolute thresholds
        to detect when a profile is genuinely dominant vs. tied with another.
        
        Three-tier confidence system:
        - HIGH: dominance_ratio >= 1.5 AND consecutive >= 3
        - MEDIUM: dominance_ratio >= 1.2 AND consecutive >= 5
        - LOW/PENDING: dominance_ratio < 1.2 (genuine tie, wait for more data)
        
        Args:
            user_id: User unique identifier
            user_mode: Assignment mode (COLD_START or DRIFT_FALLBACK)
            min_prompts: Minimum observations required for cold-start
            
        Returns:
            Tuple of (should_assign, profile_id, confidence_level, dominance_ratio)
        """
        # Get top 2 profiles to calculate dominance ratio
        top_states = self.ranking_service.get_top_profiles_for_user(user_id, limit=2)
        if not top_states:
            return False, None, "NONE", 0.0

        top_state = top_states[0]
        
        # Check minimum prompts for cold-start
        if user_mode == 'COLD_START':
            if top_state.observation_count < min_prompts:
                return False, None, "LOW", 0.0
        
        # If there's no second profile, top profile wins by default
        if len(top_states) < 2:
            # Still require some consistency
            if top_state.consecutive_top_count >= 3:
                return True, top_state.profile_id, "HIGH", float('inf')
            else:
                return False, None, "LOW", float('inf')
        
        second_state = top_states[1]
        
        # Calculate dominance ratio
        # Avoid division by zero
        if second_state.average_score == 0:
            dominance_ratio = float('inf')
        else:
            dominance_ratio = top_state.average_score / second_state.average_score
        
        consecutive = top_state.consecutive_top_count
        
        # Three-tier confidence system
        if dominance_ratio >= 1.5 and consecutive >= 3:
            # Clear winner — assign with HIGH confidence
            logger.info(
                f"HIGH confidence assignment: {top_state.profile_id} (ratio={dominance_ratio:.2f}, "
                f"consecutive={consecutive}, score={top_state.average_score:.3f})"
            )
            return True, top_state.profile_id, "HIGH", dominance_ratio
        
        elif dominance_ratio >= 1.2 and consecutive >= 5:
            # Soft winner — needs more consistency to confirm
            # Allow assignment but flag as MEDIUM confidence
            logger.info(
                f"MEDIUM confidence assignment: {top_state.profile_id} (ratio={dominance_ratio:.2f}, "
                f"consecutive={consecutive}, score={top_state.average_score:.3f})"
            )
            return True, top_state.profile_id, "MEDIUM", dominance_ratio
        
        elif dominance_ratio < 1.2:
            # Genuine tie — do not assign, wait for signal to separate
            # Log which two profiles are competing for debugging
            logger.info(
                f"Tie detected: {top_state.profile_id} vs {second_state.profile_id}, "
                f"ratio={dominance_ratio:.2f} (scores: {top_state.average_score:.3f} vs "
                f"{second_state.average_score:.3f}, consecutive={consecutive})"
            )
            return False, None, "LOW", dominance_ratio
        
        # Fallback: ratio between 1.2 and 1.5 but not enough consecutive
        logger.info(
            f"Insufficient consistency: {top_state.profile_id} (ratio={dominance_ratio:.2f}, "
            f"consecutive={consecutive}, needs 3 for HIGH or 5 for MEDIUM)"
        )
        return False, None, "LOW", dominance_ratio

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
        # Get user data from User Management Service
        user_data = self.user_client.get_user_profile_sync(user_id)
        if not user_data:
            raise ValueError(f"User with ID {user_id} not found in User Management Service")
        
        user_mode = user_data.get("profile_mode", "COLD_START")
        
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
            
            logger.info(f"DRIFT_FALLBACK: Processing {len(behavior_list)} prompts in batch")
            
            # Process each prompt in the list
            for idx, behavior in enumerate(behavior_list):
                prompt_count = current_prompt_count + idx + 1
                
                # Fallback mode always uses full matching (not cold-start)
                is_cold_start = False
                
                # Reduce logging for batch operations - only log every 5 prompts or at boundaries
                if idx % 5 == 0 or idx == len(behavior_list) - 1:
                    logger.debug(f"Processing prompt {idx + 1}/{len(behavior_list)} (total: {prompt_count})")
                
                # Match profiles for this prompt
                result = matcher.match(profiles, behavior, is_cold_start=is_cold_start, verbose=False)
                
                # Update ranking state with this prompt's results
                ranked_profiles = result["ranked_profiles"]
                self.ranking_service.update_from_ranked_profiles(
                    user_id=user_id,
                    ranked_profiles=ranked_profiles
                )
            
            # Final prompt count after processing all prompts
            prompt_count = current_prompt_count + len(behavior_list)
            logger.info(f"Batch processing complete: {len(behavior_list)} prompts, total: {prompt_count}")
            
        else:  # COLD_START mode
            # Single prompt processing
            if isinstance(extracted_behavior, list):
                raise ValueError("COLD_START mode expects a single behavior dict, not a list")
            
            prompt_count = current_prompt_count + 1
            
            # Cold-start: first 5 prompts use Intent + Domain only
            is_cold_start = prompt_count < 5
            
            # Match profiles for current prompt
            result = matcher.match(profiles, extracted_behavior, is_cold_start=is_cold_start, verbose=True)
            
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

        # Determine if assignment should happen based on dominance ratio
        min_prompts = 5 if user_mode == 'COLD_START' else 3
        
        should_assign, assigned_profile_id, confidence_level, dominance_ratio = self.should_assign_profile(
            user_id=user_id,
            user_mode=user_mode,
            min_prompts=min_prompts
        )

        # Determine status
        if should_assign:
            status = "ASSIGNED"
            
            # Persist assignment to User Management Service
            try:
                success = self.user_client.update_user_profile_sync(
                    user_id=user_id,
                    predefined_profile_id=assigned_profile_id
                )
                if not success:
                    logger.warning(
                        f"Failed to update user profile assignment in User Management Service for user {user_id}"
                    )
            except Exception as e:
                logger.warning(f"Failed to update user profile assignment for user {user_id}: {e}")
        else:
            status = "PENDING"

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