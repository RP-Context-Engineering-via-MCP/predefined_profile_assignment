"""Profile matching service.

Scores and ranks predefined profiles against user behavioral data
using weighted multi-factor matching algorithms."""

from typing import Dict, List, Optional
from app.models.profile import Profile
from app.core.constants import MatchingWeights, DefaultValues
from app.core.logging_config import matcher_logger


class ProfileMatcher:
    """Profile matching and scoring service.
    
    Implements weighted factor matching with support for both standard
    and cold-start (simplified) matching modes.
    
    Attributes:
        weights: Standard matching weights (all factors)
        cold_start_weights: Simplified cold-start weights (intent + interest only)
    """

    def __init__(self, matching_factors: Dict[str, float]):
        """Initialize matcher with custom factor weights.
        
        Args:
            matching_factors: Dictionary of factor weights to override defaults
        """
        # Start with default standard weights
        self.weights = MatchingWeights.get_standard_weights()
        # Override with provided factors
        self.weights.update(matching_factors)
        
        # Cold-start weights (INTENT + INTEREST only)
        self.cold_start_weights = MatchingWeights.get_cold_start_weights()
        
        matcher_logger.info(
            f"ProfileMatcher initialized with weights: {self.weights}"
        )

    def match(
        self,
        profiles: List[Profile],
        extracted_behavior: Dict,
        is_cold_start: bool = False
    ) -> Dict:
        """Match user behavior against profiles and return ranked results.
        
        Applies weighted scoring across multiple behavioral dimensions,
        normalizes scores, and ranks profiles by match quality.
        
        Args:
            profiles: List of Profile objects to evaluate
            extracted_behavior: Behavioral data dictionary containing:
                - intents: {intent_code: score}
                - interests: {interest_code: score}
                - behavior_level: str (e.g., "INTERMEDIATE")
                - signals: {signal_code: score}
                - consistency: float (0-1)
                - complexity: float (0-1)
            is_cold_start: If True, uses simplified weights (intent + interest only)
            
        Returns:
            Dictionary with:
                - ranked_profiles: List of (profile_id, score) tuples (descending)
                - best_profile: ID of top-ranked profile
                - confidence: Normalized score of top-ranked profile
        """
        # Select weights based on cold-start status
        active_weights = self.cold_start_weights if is_cold_start else self.weights
        
        matcher_logger.info(
            f"Starting profile matching (cold_start={is_cold_start}) "
            f"for {len(profiles)} profiles"
        )

        scores = {}

        for profile in profiles:
            score = self._calculate_profile_score(profile, extracted_behavior, active_weights)
            scores[profile.profile_id] = score

        # Normalize scores
        total = sum(scores.values()) or 1.0
        
        if total == 0:
            matcher_logger.warning(
                "All raw scores are 0; check that seeds and input codes match"
            )
        else:
            matcher_logger.debug(f"Total raw score sum: {total:.3f}")
        
        scores = {k: v / total for k, v in scores.items()}
        
        # Log normalized scores
        matcher_logger.debug("Normalized scores:")
        for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            matcher_logger.debug(f"  {pid}: {score:.4f}")

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        result = {
            "ranked_profiles": ranked,
            "best_profile": ranked[0][0] if ranked else None,
            "confidence": ranked[0][1] if ranked else 0.0
        }
        
        matcher_logger.info(
            f"Matching complete. Best profile: {result['best_profile']} "
            f"(confidence: {result['confidence']:.4f})"
        )

        return result

    def _calculate_profile_score(
        self, 
        profile: Profile, 
        behavior: Dict, 
        weights: Dict
    ) -> float:
        """Calculate weighted score for single profile.
        
        Computes component scores for each dimension and applies weights.
        
        Args:
            profile: Profile object to score
            behavior: Extracted behavior dictionary
            weights: Factor weights to apply
            
        Returns:
            Raw weighted score for the profile
        """
        intent_score = self._intent_score(profile, behavior["intents"])
        interest_score = self._interest_score(profile, behavior["interests"])
        behavior_score = self._behavior_level_score(profile, behavior["behavior_level"])
        signal_score = self._signal_score(profile, behavior["signals"])
        complexity_score = behavior.get("complexity", DefaultValues.DEFAULT_COMPLEXITY)

        raw_score = (
            weights["INTENT"] * intent_score +
            weights["INTEREST"] * interest_score +
            weights["COMPLEXITY"] * complexity_score +
            weights["STYLE"] * signal_score +
            weights["CONSISTENCY"] * behavior["consistency"]
        )
        
        matcher_logger.debug(
            f"\nProfile {profile.profile_id} - {profile.profile_name}:\n"
            f"  Intent: {intent_score:.3f} × {weights['INTENT']:.2f} = {weights['INTENT'] * intent_score:.3f}\n"
            f"  Interest: {interest_score:.3f} × {weights['INTEREST']:.2f} = {weights['INTEREST'] * interest_score:.3f}\n"
            f"  Complexity: {complexity_score:.3f} × {weights['COMPLEXITY']:.2f} = {weights['COMPLEXITY'] * complexity_score:.3f}\n"
            f"  Signal: {signal_score:.3f} × {weights['STYLE']:.2f} = {weights['STYLE'] * signal_score:.3f}\n"
            f"  Consistency: {behavior['consistency']:.3f} × {weights['CONSISTENCY']:.2f} = {weights['CONSISTENCY'] * behavior['consistency']:.3f}\n"
            f"  Raw total: {raw_score:.3f}"
        )
        
        return raw_score

    def _intent_score(self, profile: Profile, intents: Dict) -> float:
        """Calculate weighted intent matching score.
        
        Args:
            profile: Profile with intent associations
            intents: User's intent scores
            
        Returns:
            Aggregated intent match score
        """
        return sum(
            intents.get(pi.intent.intent_name, 0) * float(pi.weight)
            for pi in profile.intents
        )

    def _interest_score(self, profile: Profile, interests: Dict) -> float:
        """Calculate weighted interest matching score.
        
        Args:
            profile: Profile with interest associations
            interests: User's interest scores
            
        Returns:
            Aggregated interest match score
        """
        return sum(
            interests.get(pint.interest.interest_name, 0) * float(pint.weight)
            for pint in profile.interests
        )

    def _behavior_level_score(self, profile: Profile, level: str) -> float:
        """Calculate behavior level matching score.
        
        Returns full score for exact match, default otherwise.
        
        Args:
            profile: Profile with behavior level associations
            level: User's behavior level
            
        Returns:
            1.0 for exact match, default score otherwise
        """
        has_match = any(bl.level.level_name == level for bl in profile.behavior_levels)
        return 1.0 if has_match else DefaultValues.DEFAULT_BEHAVIOR_SCORE

    def _signal_score(self, profile: Profile, signals: Dict) -> float:
        """Calculate weighted behavioral signal matching score.
        
        Args:
            profile: Profile with signal associations
            signals: User's behavioral signal scores
            
        Returns:
            Aggregated signal match score
        """
        return sum(
            signals.get(ps.signal.signal_name, 0) * float(ps.weight)
            for ps in profile.behavior_signals
        )

