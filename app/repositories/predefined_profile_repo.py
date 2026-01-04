from sqlalchemy.orm import joinedload
from app.models.profile import Profile
from app.models.profile_intent import ProfileIntent
from app.models.profile_interest import ProfileInterest
from app.models.profile_behavior_level import ProfileBehaviorLevel
from app.models.profile_behavior_signal import ProfileBehaviorSignal
from app.models.matching_factor import MatchingFactor


class PredefinedProfileRepository:

    def __init__(self, db):
        self.db = db

    def load_full_profiles(self):
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

    def load_matching_factors(self):
        return {
            f.factor_name.upper(): float(f.weight)
            for f in self.db.query(MatchingFactor).all()
        }