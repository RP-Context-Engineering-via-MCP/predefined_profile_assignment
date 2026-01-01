# app/services/profile_matcher.py

from typing import Dict, List, Tuple
from app.models.profile import Profile


class ProfileMatcher:

    def __init__(self, matching_factors: Dict[str, float]):
        # Set defaults and override with provided factors
        # PDF-aligned weights: INTENT(35%), INTEREST(25%), COMPLEXITY(15%), STYLE(15%), CONSISTENCY(10%)
        self.weights = {
            "INTENT": 0.35,
            "INTEREST": 0.25,
            "COMPLEXITY": 0.15,
            "STYLE": 0.15,
            "CONSISTENCY": 0.10
        }
        self.weights.update(matching_factors)
        
        # Cold-start weights: INTENT + INTEREST only (simplify for first 3-5 prompts)
        self.cold_start_weights = {
            "INTENT": 0.60,      # Increased from 35%
            "INTEREST": 0.40,    # Increased from 25%
            "COMPLEXITY": 0.0,   # Disabled
            "STYLE": 0.0,        # Disabled
            "CONSISTENCY": 0.0   # Disabled
        }

    def match(
        self,
        profiles: List[Profile],
        extracted_behavior: Dict,
        is_cold_start: bool = False
    ) -> Dict:
        """
        extracted_behavior = {
            "intents": {intent_code: score},
            "interests": {interest_code: score},
            "behavior_level": "INTERMEDIATE",
            "signals": {signal_code: score},
            "consistency": float,
            "complexity": float (0-1, computed from prompt characteristics)
        }
        is_cold_start: bool - if True, use only INTENT + INTEREST factors (first 3-5 prompts)
        """
        
        # Select weights based on cold-start status
        active_weights = self.cold_start_weights if is_cold_start else self.weights
        
        print(f"\n=== MATCHING (Cold-Start: {is_cold_start}) ===")

        scores = {}

        for profile in profiles:
            score = self._calculate_profile_score(profile, extracted_behavior, active_weights)
            scores[profile.profile_id] = score

        # Normalize
        total = sum(scores.values()) or 1.0
        if total == 0:
            print("\n  WARNING: All raw scores are 0; check seeds and input codes match")
        else:
            print(f"\n=== Normalization ===")
            print(f"Total raw score sum: {total:.3f}")
        
        scores = {k: v / total for k, v in scores.items()}
        
        print(f"Normalized scores:")
        for pid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            print(f"  {pid}: {score:.4f}")

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "ranked_profiles": ranked,
            "best_profile": ranked[0][0],
            "confidence": ranked[0][1]
        }

    def _calculate_profile_score(self, profile: Profile, behavior: Dict, weights: Dict) -> float:
        intent_score = self._intent_score(profile, behavior["intents"])
        interest_score = self._interest_score(profile, behavior["interests"])
        behavior_score = self._behavior_level_score(profile, behavior["behavior_level"])
        signal_score = self._signal_score(profile, behavior["signals"])
        complexity_score = behavior.get("complexity", 0.5)  # Extract complexity (0-1 scale)

        raw_score = (
            weights["INTENT"] * intent_score +
            weights["INTEREST"] * interest_score +
            weights["COMPLEXITY"] * complexity_score +
            weights["STYLE"] * signal_score +
            weights["CONSISTENCY"] * behavior["consistency"]
        )
        
        # Debug: Print scores
        print(f"\nProfile {profile.profile_id} - {profile.profile_name}:")
        print(f"  Intent score: {intent_score:.3f} × {weights['INTENT']:.2f} = {weights['INTENT'] * intent_score:.3f}")
        print(f"  Interest score: {interest_score:.3f} × {weights['INTEREST']:.2f} = {weights['INTEREST'] * interest_score:.3f}")
        print(f"  Complexity score: {complexity_score:.3f} × {weights['COMPLEXITY']:.2f} = {weights['COMPLEXITY'] * complexity_score:.3f}")
        print(f"  Signal score: {signal_score:.3f} × {weights['STYLE']:.2f} = {weights['STYLE'] * signal_score:.3f}")
        print(f"  Consistency: {behavior['consistency']:.3f} × {weights['CONSISTENCY']:.2f} = {weights['CONSISTENCY'] * behavior['consistency']:.3f}")
        print(f"  Raw total: {raw_score:.3f}")
        
        return raw_score

    def _intent_score(self, profile: Profile, intents: Dict) -> float:
        return sum(
            intents.get(pi.intent.intent_name, 0) * float(pi.weight)
            for pi in profile.intents
        )

    def _interest_score(self, profile: Profile, interests: Dict) -> float:
        return sum(
            interests.get(pint.interest.interest_name, 0) * float(pint.weight)
            for pint in profile.interests
        )

    def _behavior_level_score(self, profile: Profile, level: str) -> float:
        return 1.0 if any(bl.level.level_name == level for bl in profile.behavior_levels) else 0.5

    def _signal_score(self, profile: Profile, signals: Dict) -> float:
        return sum(
            signals.get(ps.signal.signal_name, 0) * float(ps.weight)
            for ps in profile.behavior_signals
        )
