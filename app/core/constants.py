# app/core/constants.py

"""
Application-wide constants and configuration values.
Centralized location for magic numbers, thresholds, and default values.
"""

from enum import Enum
from typing import Dict


# ==================== Profile Matching Weights ====================

class MatchingWeights:
    """Default weights for profile matching factors (PDF-aligned)."""
    
    # Standard mode weights (sum = 1.0)
    INTENT = 0.35       # Intent signals
    INTEREST = 0.25     # Interest domain
    COMPLEXITY = 0.15   # Task complexity & depth
    STYLE = 0.15        # Interaction style & control
    CONSISTENCY = 0.10  # Temporal consistency
    
    # Cold-start mode weights (sum = 1.0)
    COLD_START_INTENT = 0.60      # Increased from 35%
    COLD_START_INTEREST = 0.40    # Increased from 25%
    COLD_START_COMPLEXITY = 0.0   # Disabled
    COLD_START_STYLE = 0.0        # Disabled
    COLD_START_CONSISTENCY = 0.0  # Disabled
    
    @classmethod
    def get_standard_weights(cls) -> Dict[str, float]:
        """Get standard matching weights."""
        return {
            "INTENT": cls.INTENT,
            "INTEREST": cls.INTEREST,
            "COMPLEXITY": cls.COMPLEXITY,
            "STYLE": cls.STYLE,
            "CONSISTENCY": cls.CONSISTENCY
        }
    
    @classmethod
    def get_cold_start_weights(cls) -> Dict[str, float]:
        """Get cold-start matching weights."""
        return {
            "INTENT": cls.COLD_START_INTENT,
            "INTEREST": cls.COLD_START_INTEREST,
            "COMPLEXITY": cls.COLD_START_COMPLEXITY,
            "STYLE": cls.COLD_START_STYLE,
            "CONSISTENCY": cls.COLD_START_CONSISTENCY
        }


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
