# Quick Reference Guide - Refactored Codebase

## New Modules & Usage

### 1. Constants (`app/core/constants.py`)

```python
from app.core.constants import (
    MatchingWeights,
    AssignmentThresholds,
    ComplexityConstants,
    ConsistencyConstants,
    DefaultValues,
    ConfidenceLevel,
    AssignmentStatus,
    ResponseMessages
)

# Get matching weights
weights = MatchingWeights.get_standard_weights()
cold_weights = MatchingWeights.get_cold_start_weights()

# Use thresholds
if prompt_count >= AssignmentThresholds.MIN_PROMPTS_COLD_START:
    # Check for assignment

# Use enums
status = AssignmentStatus.ASSIGNED
confidence = ConfidenceLevel.HIGH
```

### 2. Exceptions (`app/core/exceptions.py`)

```python
from app.core.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    ProfileNotFoundError,
    InsufficientDataError,
    ValidationError
)

# Raise specific exceptions
if not user:
    raise UserNotFoundError(user_id=user_id)

if existing_user:
    raise UserAlreadyExistsError(field="email", value=email)

# Catch specific exceptions
try:
    user = get_user(user_id)
except UserNotFoundError as e:
    logger.error(f"User not found: {e.message}")
    # Access details
    logger.debug(f"Details: {e.details}")
```

### 3. Logging (`app/core/logging_config.py`)

```python
from app.core.logging_config import get_logger

# Get a logger for your module
logger = get_logger(__name__)

# Use structured logging
logger.info("User created successfully", extra={"user_id": user_id})
logger.debug(f"Processing {len(items)} items")
logger.warning("Approaching rate limit")
logger.error("Failed to save data", exc_info=True)

# Or use pre-configured loggers
from app.core.logging_config import matcher_logger, calculator_logger
matcher_logger.info("Starting profile matching")
```

### 4. Utilities (`app/core/utils.py`)

```python
from app.core.utils import (
    to_float, to_bool, safe_divide,
    is_valid_email, is_valid_username,
    normalize_score, get_nested,
    truncate_string, chunk_list
)

# Data conversion
score = to_float(user.score, default=0.0)
is_active = to_bool(user.status)

# Validation
if not is_valid_email(email):
    raise InvalidEmailError(email)

# Safe operations
avg = safe_divide(total_score, count, default=0.0)

# Normalize scores
final_score = normalize_score(raw_score, 0.0, 1.0)

# Nested dict access
value = get_nested(data, "user", "profile", "score", default=0.0)
```

## Configuration Changes

### Environment Variables (`.env`)

Add these new optional settings:

```bash
# Application Settings
DEBUG=false
LOG_LEVEL=INFO

# Profile Assignment Thresholds
MIN_PROMPTS_COLD_START=3
MIN_PROMPTS_FALLBACK=5
COLD_START_THRESHOLD=0.60
FALLBACK_THRESHOLD=0.70
HIGH_CONFIDENCE_THRESHOLD=0.70
```

## Migration Guide

### Updating Existing Code

#### Before:
```python
# Old way with magic numbers
if score >= 0.70:
    confidence = "HIGH"

# Old way with print
print(f"Processing user: {user_id}")

# Old way with generic exceptions
if not user:
    raise ValueError("User not found")
```

#### After:
```python
from app.core.constants import AssignmentThresholds, ConfidenceLevel
from app.core.logging_config import get_logger
from app.core.exceptions import UserNotFoundError

logger = get_logger(__name__)

# New way with named constants
if score >= AssignmentThresholds.HIGH_CONFIDENCE_THRESHOLD:
    confidence = ConfidenceLevel.HIGH

# New way with logging
logger.info(f"Processing user: {user_id}")

# New way with specific exceptions
if not user:
    raise UserNotFoundError(user_id=user_id)
```

## Common Patterns

### Service Implementation Pattern

```python
from app.core.logging_config import get_logger
from app.core.exceptions import UserNotFoundError, ValidationError
from app.core.constants import DefaultValues
from app.core.utils import is_valid_email

logger = get_logger(__name__)

class MyService:
    def __init__(self, db):
        self.db = db
        logger.info("MyService initialized")
    
    def process_user(self, user_id: str) -> dict:
        """
        Process user with proper error handling and logging.
        
        Args:
            user_id: User identifier
            
        Returns:
            dict: Processing results
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        logger.info(f"Processing user: {user_id}")
        
        try:
            user = self.get_user(user_id)
            if not user:
                raise UserNotFoundError(user_id=user_id)
            
            # Business logic here
            result = self._do_processing(user)
            
            logger.info(f"User processed successfully: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process user {user_id}: {str(e)}", exc_info=True)
            raise
```

### API Route Pattern

```python
from fastapi import APIRouter, HTTPException, status
from app.core.logging_config import api_logger
from app.core.exceptions import UserNotFoundError, ValidationError

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user by ID."""
    try:
        api_logger.info(f"GET request for user: {user_id}")
        user = service.get_user(user_id)
        return user
    except UserNotFoundError as e:
        api_logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        api_logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

## Testing

### Unit Test Example

```python
import pytest
from app.core.constants import DefaultValues
from app.core.exceptions import UserNotFoundError
from app.core.utils import normalize_score

def test_normalize_score():
    assert normalize_score(1.5) == 1.0
    assert normalize_score(-0.5) == 0.0
    assert normalize_score(0.5) == 0.5

def test_user_not_found_exception():
    with pytest.raises(UserNotFoundError) as exc_info:
        raise UserNotFoundError(user_id="123")
    
    assert "123" in str(exc_info.value)
    assert exc_info.value.details["user_id"] == "123"
```

## Best Practices

1. **Always use constants** instead of magic numbers
2. **Use specific exceptions** instead of generic ones
3. **Use structured logging** instead of print statements
4. **Add type hints** to function signatures
5. **Write comprehensive docstrings** for public methods
6. **Use utilities** for common operations
7. **Handle errors gracefully** with try-except blocks
8. **Log at appropriate levels** (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

### Import Errors
If you see import errors, ensure all new modules are in the correct locations:
- `app/core/constants.py`
- `app/core/exceptions.py`
- `app/core/logging_config.py`
- `app/core/utils.py`

### Logging Not Working
Initialize logging in main.py startup:
```python
from app.core.logging_config import setup_logging
setup_logging()
```

### Type Errors
Ensure you're using the correct types from constants:
```python
from app.core.constants import ConfidenceLevel, AssignmentStatus
status = AssignmentStatus.ASSIGNED  # Not "ASSIGNED"
```
