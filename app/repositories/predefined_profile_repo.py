"""Predefined profile repository.

Provides data access layer for profile entities with eager loading
of all related attributes for efficient matching operations.
"""

from sqlalchemy.orm import joinedload
from app.models.profile import Profile
from app.models.profile_intent import ProfileIntent
from app.models.profile_interest import ProfileInterest
from app.models.profile_behavior_level import ProfileBehaviorLevel
from app.models.profile_behavior_signal import ProfileBehaviorSignal
from app.models.standard_matching_factor import StandardMatchingFactor
from app.models.cold_start_matching_factor import ColdStartMatchingFactor


class PredefinedProfileRepository:
    """Predefined profile data access repository.
    
    Optimized for profile matching by eagerly loading all relationships.
    Retrieves complete profile configurations including intents, interests,
    behavior levels, and signals in a single query.
    
    Attributes:
        db: SQLAlchemy database session
    """

    def __init__(self, db):
        """Initialize repository with database session.
        
        Args:
            db: Active SQLAlchemy session
        """
        self.db = db

    def load_full_profiles(self):
        """Load all profiles with eager-loaded relationships.
        
        Uses joinedload to fetch all related entities (intents, interests,
        behavior levels, signals) in a single optimized query, avoiding N+1.
        
        Returns:
            List of Profile objects with all relationships loaded
        """
        profiles = (
            self.db.query(Profile)
            .options(
                joinedload(Profile.intents).joinedload(ProfileIntent.intent),
                joinedload(Profile.interests).joinedload(ProfileInterest.interest),
                joinedload(Profile.behavior_levels).joinedload(ProfileBehaviorLevel.level),
                joinedload(Profile.behavior_signals).joinedload(ProfileBehaviorSignal.signal),
            )
            .all()
        )
        
        return profiles

    def load_matching_factors(self, mode='STANDARD'):
        """Load matching factor weights for specified mode.
        
        Retrieves configurable weights for each matching dimension
        from the appropriate table based on mode.
        
        Args:
            mode: Matching mode ('STANDARD' or 'COLD_START')
        
        Returns:
            Dictionary mapping factor names (uppercase) to float weights
        """
        if mode == 'COLD_START':
            factors = self.db.query(ColdStartMatchingFactor).all()
        else:
            factors = self.db.query(StandardMatchingFactor).all()
        
        return {
            f.factor_name.upper(): float(f.weight)
            for f in factors
        }