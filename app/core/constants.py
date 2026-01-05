# app/core/constants.py

"""
Application-wide constants and configuration values.
Centralized location for magic numbers, thresholds, and default values.
"""

from enum import Enum
from typing import Dict


# ==================== Profile Matching Weights ====================
# NOTE: Matching weights are now stored in the database (matching_factor table)
# and loaded dynamically. The MatchingWeights class has been deprecated.
# See app/models/matching_factor.py and initial_seed.sql for weight configuration.

# ==================== Profile Assignment Thresholds ====================

class AssignmentThresholds:
    """Thresholds for profile assignment decisions."""
    
    # Minimum prompt counts
    MIN_PROMPTS_COLD_START = 3
    MIN_PROMPTS_FALLBACK = 5
    
    # Score thresholds
    COLD_START_THRESHOLD = 0.60      # Average score for cold-start assignment
    FALLBACK_THRESHOLD = 0.70        # Average score for fallback assignment
    HIGH_CONFIDENCE_THRESHOLD = 0.70  # Threshold for high confidence
    
    # Stability requirements
    COLD_START_CONSECUTIVE_TOP = 2   # Consecutive top rankings needed for cold-start
    FALLBACK_CONSECUTIVE_TOP = 3     # Consecutive top rankings needed for fallback


# ==================== Complexity Calculator Constants ====================

class ComplexityConstants:
    """Constants for task complexity calculation."""
    
    # Word count thresholds
    LOW_COMPLEXITY_THRESHOLD = 20    # Simple prompts: <20 words
    HIGH_COMPLEXITY_THRESHOLD = 100  # Complex prompts: >100 words
    
    # Scoring weights
    LENGTH_MAX_SCORE = 0.20
    LENGTH_MIN_SCORE = 0.05
    CONSTRAINT_MAX_SCORE = 0.70
    CONSTRAINT_PER_KEYWORD = 0.23
    MULTISTEP_MAX_SCORE = 0.60
    MULTISTEP_PER_KEYWORD = 0.20
    STRUCTURE_MAX_SCORE = 0.12
    STRUCTURE_PER_KEYWORD = 0.04
    EXAMPLE_MAX_SCORE = 0.08
    EXAMPLE_PER_KEYWORD = 0.027
    
    # Constraint keywords
    CONSTRAINT_KEYWORDS = [
        "must", "should", "not", "except", "avoid", "only",
        "limit", "without", "require", "constraint", "restrict",
        "specific", "exactly", "precisely", "format", "include",
        "handle", "optimize"
    ]
    
    # Multi-step keywords
    MULTI_STEP_KEYWORDS = [
        "first", "then", "next", "after", "finally", "step",
        "stage", "phase", "follow", "sequence", "order",
        "and then", "subsequently", "moreover"
    ]
    
    # Structure keywords
    STRUCTURE_KEYWORDS = [
        "structure", "organize", "format", "template", "outline",
        "list", "number", "bullet", "table", "section",
        "header", "subheader", "code", "json", "xml"
    ]
    
    # Example keywords
    EXAMPLE_KEYWORDS = [
        "example", "like", "such as", "for instance", "e.g",
        "show", "demonstrate", "illustration", "sample",
        "template", "reference"
    ]


# ==================== Consistency Calculator Constants ====================

class ConsistencyConstants:
    """Constants for consistency calculation."""
    
    # Factor weights
    INTENT_WEIGHT = 0.40       # Intent repetition weight
    DOMAIN_WEIGHT = 0.40       # Domain stability weight
    TEMPORAL_WEIGHT = 0.20     # Temporal consistency weight
    SIGNAL_WEIGHT = 0.10       # Signal consistency weight (optional)
    
    # Default values
    DEFAULT_CONSISTENCY = 0.5  # Neutral default for single prompt or no data
    
    # Temporal window
    RECENT_WINDOW_SIZE = 3     # Number of recent prompts for temporal analysis


# ==================== Default Values ====================

class DefaultValues:
    """Default values used throughout the application."""
    
    # Profile matching
    DEFAULT_BEHAVIOR_SCORE = 0.5      # Default score when behavior level doesn't match
    DEFAULT_COMPLEXITY = 0.5          # Default complexity for invalid/missing prompts
    DEFAULT_CONSISTENCY = 0.5         # Default consistency for insufficient data
    
    # Pagination
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
    # User settings
    DEFAULT_PROFILE_MODE = "COLD_START"
    DEFAULT_CONFIDENCE = 0.0


# ==================== Status Enums ====================

class ConfidenceLevel(str, Enum):
    """Confidence level classifications."""
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AssignmentStatus(str, Enum):
    """Profile assignment status."""
    NOT_FOUND = "NOT_FOUND"
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"


# ==================== API Response Messages ====================

class ResponseMessages:
    """Standard API response messages."""
    
    # Success messages
    USER_CREATED = "User created successfully"
    USER_UPDATED = "User updated successfully"
    USER_DELETED = "User deleted successfully"
    LOGIN_SUCCESS = "Login successful"
    
    # Error messages
    USER_NOT_FOUND = "User not found"
    INVALID_CREDENTIALS = "Invalid username or password"
    USERNAME_EXISTS = "Username already exists"
    EMAIL_EXISTS = "Email already exists"
    PROFILE_NOT_FOUND = "Profile not found"
    INSUFFICIENT_DATA = "Insufficient data for profile assignment"
    
    # Validation messages
    INVALID_EMAIL = "Invalid email format"
    INVALID_PASSWORD = "Password must be at least 8 characters"
    INVALID_USERNAME = "Username must be 3-50 characters"


# ==================== Domain Expertise Constants ====================

class ExpertiseThresholds:
    """Thresholds for domain expertise level determination."""
    
    # Confidence score thresholds
    BEGINNER_MAX = 0.39          # 0.00 – 0.39
    INTERMEDIATE_MIN = 0.40       # 0.40 – 0.74
    INTERMEDIATE_MAX = 0.74
    ADVANCED_MIN = 0.75          # 0.75 – 1.00
    
    # Transition hysteresis
    LEVEL_CHANGE_THRESHOLD = 2   # Number of consecutive interactions before level change
    
    # Decay settings
    DECAY_DAYS_THRESHOLD = 30    # Days of inactivity before decay applies
    DECAY_FACTOR = 0.98          # 2% decay per application


class ExpertiseSignalWeights:
    """Signal weights for expertise confidence calculation."""
    
    # Positive signals (increase confidence)
    CORRECT_TERMINOLOGY = 0.10
    MULTI_STEP_PROMPT = 0.15
    ITERATIVE_REFINEMENT = 0.20
    EXPLICIT_ADVANCED_REQUEST = 0.25
    ASSUME_KNOWLEDGE = 0.20
    
    # Negative signals (decrease confidence)
    BEGINNER_QUESTION = -0.10
    DEFINITION_REQUEST = -0.10
    INCORRECT_TERMINOLOGY = -0.20
    
    # Neutral (no change)
    GENERIC_SHORT_PROMPT = 0.0
    
    # Minimum confidence for any update
    MIN_CONFIDENCE = 0.0
    MAX_CONFIDENCE = 1.0
    
    # Default starting confidence for new domains
    COLD_START_CONFIDENCE = 0.1
    
    # Behavior level weights (for JSON-based updates)
    BEHAVIOR_LEVEL_BASIC = 0.05
    BEHAVIOR_LEVEL_INTERMEDIATE = 0.10
    BEHAVIOR_LEVEL_ADVANCED = 0.20
    
    # Optional modifier bonuses
    CONSISTENCY_BONUS = 0.05  # Applied when consistency > 0.5
    COMPLEXITY_BONUS = 0.05   # Applied when complexity > 0.5


class ExpertiseSignalKeywords:
    """Keywords for detecting expertise signals in user prompts."""
    
    # Beginner indicators
    BEGINNER_KEYWORDS = [
        "what is", "what are", "define", "explain", "how to",
        "tutorial", "basics", "introduction", "beginner",
        "step by step", "simple", "easy way"
    ]
    
    # Advanced indicators
    ADVANCED_KEYWORDS = [
        "optimize", "performance", "edge case", "edge cases",
        "scalability", "architecture", "best practice", "best practices",
        "assume I know", "skip basics", "advanced", "deep dive",
        "low-level", "implementation details", "under the hood"
    ]
    
    # Terminology indicators (domain-specific - to be extended)
    TECHNICAL_TERMS = {
        "PROGRAMMING": ["algorithm", "data structure", "complexity", "recursion", "polymorphism"],
        "DATA_SCIENCE": ["regression", "classification", "feature engineering", "cross-validation"],
        "AI": ["neural network", "gradient descent", "backpropagation", "transformer", "embedding"]
    }


class ExpertiseUpdateRules:
    """Rules for when to update domain expertise."""
    
    # Minimum complexity to trigger update
    MIN_COMPLEXITY_THRESHOLD = 0.3
    
    # Messages that should NOT trigger updates
    IGNORE_PATTERNS = [
        "thanks", "thank you", "ok", "okay", "got it",
        "yes", "no", "sure", "great", "awesome",
        "hi", "hello", "hey", "good morning", "good evening"
    ]
    
    # Minimum prompt length (words) to consider
    MIN_PROMPT_LENGTH = 3
