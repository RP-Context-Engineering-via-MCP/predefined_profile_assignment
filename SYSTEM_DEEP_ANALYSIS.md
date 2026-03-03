# Predefined Profile Assignment Service - Deep System Analysis

**Version:** 1.0.0  
**Date:** March 3, 2026  
**Purpose:** Comprehensive LLM-Parseable System Documentation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Data Models & Database Schema](#data-models--database-schema)
4. [Core Business Logic](#core-business-logic)
5. [API Endpoints](#api-endpoints)
6. [Event-Driven Architecture](#event-driven-architecture)
7. [Configuration & Environment](#configuration--environment)
8. [Deployment & Infrastructure](#deployment--infrastructure)
9. [Data Flow Diagrams](#data-flow-diagrams)
10. [Algorithm Details](#algorithm-details)
11. [External Dependencies](#external-dependencies)
12. [Error Handling & Resilience](#error-handling--resilience)

---

## 1. Executive Summary

### 1.1 What This System Does

The **Predefined Profile Assignment Service** is an AI-powered user profiling system that automatically classifies users into one of six predefined behavioral profiles based on their interactions with LLM applications. It continuously analyzes user behavior patterns and adapts to behavioral changes (drift) over time.

### 1.2 Core Capabilities

- **Intelligent Profile Matching**: Weighted multi-factor scoring algorithm matching users to 6 predefined profiles
- **Cold-Start Support**: Simplified matching for new users with limited data (first 5 prompts)
- **Drift Detection Integration**: Responds to behavioral drift by reassigning profiles using fallback mode
- **Domain Expertise Tracking**: Monitors user expertise levels across different interest domains
- **Temporal Ranking State**: Maintains historical profile ranking evolution for trend analysis
- **Event-Driven Architecture**: Consumes drift events from Redis and publishes assignment events

### 1.3 Six Predefined Profiles

| Profile ID | Name | Primary Intent | Description |
|------------|------|----------------|-------------|
| **P1** | Knowledge Seeker | LEARNING | Learns concepts, seeks explanations |
| **P2** | Productivity Professional | TASK_COMPLETION | Uses LLMs for efficient task completion |
| **P3** | Technical Problem Solver | PROBLEM_SOLVING | Solves technical/engineering problems |
| **P4** | Creative Generator | EXPLORATION | Generates creative ideas and content |
| **P5** | Lifestyle Advisor Seeker | GUIDANCE | Seeks personal and lifestyle guidance |
| **P6** | Casual Explorer | ENGAGEMENT | Uses LLMs casually for curiosity/fun |

### 1.4 Technology Stack

- **Language**: Python 3.11
- **Framework**: FastAPI (async web framework)
- **Database**: PostgreSQL 13+ with SQLAlchemy ORM
- **Message Queue**: Redis Streams (for event-driven communication)
- **Containerization**: Docker + Docker Compose
- **HTTP Client**: httpx (for external service calls)
- **Validation**: Pydantic v2

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES (Microservices)              │
├─────────────────────────────────────────────────────────────────┤
│  • User Management Service (Port 8080)                          │
│  • Behavior Resolution Engine (Port 8001)                       │
│  • Drift Detection Service (Redis consumer)                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓ ↑ (HTTP + Redis Streams)
┌─────────────────────────────────────────────────────────────────┐
│         PREDEFINED PROFILE ASSIGNMENT SERVICE (Port 8002)       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────┐            │
│  │  HTTP Server     │         │  Redis Consumer  │            │
│  │  (FastAPI)       │         │  (Async Loop)    │            │
│  │  Port 8000       │         │  Background Task │            │
│  └──────────────────┘         └──────────────────┘            │
│           ↓                            ↓                        │
│  ┌────────────────────────────────────────────────┐           │
│  │         API Layer (Route Handlers)             │           │
│  │  • predefined_profile_routes.py                │           │
│  │  • ranking_state_routes.py                     │           │
│  │  • domain_expertise_routes.py                  │           │
│  └────────────────────────────────────────────────┘           │
│           ↓                                                     │
│  ┌────────────────────────────────────────────────┐           │
│  │      Orchestration Layer                       │           │
│  │  • IntakeOrchestrator (central entry point)    │           │
│  │  • DriftEventHandler (event processor)         │           │
│  └────────────────────────────────────────────────┘           │
│           ↓                                                     │
│  ┌────────────────────────────────────────────────┐           │
│  │         Service Layer (Business Logic)         │           │
│  │  • ProfileAssigner (orchestrates assignment)   │           │
│  │  • ProfileMatcher (scoring algorithm)          │           │
│  │  • ComplexityCalculator (prompt analysis)      │           │
│  │  • ConsistencyCalculator (pattern analysis)    │           │
│  │  • DomainExpertiseService (expertise tracking) │           │
│  │  • RankingStateService (state management)      │           │
│  │  • UserManagementClient (HTTP client)          │           │
│  └────────────────────────────────────────────────┘           │
│           ↓                                                     │
│  ┌────────────────────────────────────────────────┐           │
│  │      Repository Layer (Data Access)            │           │
│  │  • PredefinedProfileRepository                 │           │
│  │  • RankingStateRepository                      │           │
│  │  • UserDomainStateRepository                   │           │
│  └────────────────────────────────────────────────┘           │
│           ↓                                                     │
│  ┌────────────────────────────────────────────────┐           │
│  │       Database Layer (PostgreSQL)              │           │
│  │  • SQLAlchemy ORM Models                       │           │
│  │  • Async & Sync Session Management             │           │
│  └────────────────────────────────────────────────┘           │
│                                                                 │
│  ┌────────────────────────────────────────────────┐           │
│  │         Publisher Layer                        │           │
│  │  • ProfilePublisher (to profile.assigned)      │           │
│  └────────────────────────────────────────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓ ↑
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                             │
├─────────────────────────────────────────────────────────────────┤
│  • PostgreSQL Database                                          │
│  • Redis (DB 0) - Streams: drift.events, profile.assigned      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Layered Architecture Pattern

The system follows a **strict layered architecture** pattern:

1. **API Layer**: Handles HTTP requests/responses, input validation
2. **Orchestration Layer**: Coordinates workflows, manages transactions
3. **Service Layer**: Implements business logic, algorithms
4. **Repository Layer**: Abstracts data access operations
5. **Database Layer**: Persistence with SQLAlchemy ORM
6. **Publisher/Consumer Layer**: Event-driven messaging

**Key Principle**: Each layer only communicates with the layer directly below it. No layer skipping.

### 2.3 Concurrent Processes

The application runs **two concurrent processes** in the same container:

1. **HTTP Server (FastAPI/Uvicorn)**: Serves REST API on port 8000
2. **Redis Consumer Loop (asyncio task)**: Listens to `drift.events` stream in background

Both processes start during application lifespan startup and stop during shutdown.

---

## 3. Data Models & Database Schema

### 3.1 Database Technology

- **RDBMS**: PostgreSQL 13+
- **ORM**: SQLAlchemy 2.0 (with both sync and async engines)
- **Migration Strategy**: SQL-based with idempotent CREATE/ALTER statements
- **Seed Data**: Loaded from `app/core/initial_seed.sql` at startup

### 3.2 Core Tables

#### 3.2.1 Profile Table

**Purpose**: Stores predefined behavioral profiles with AI context.

```sql
CREATE TABLE profile (
    profile_id VARCHAR(10) PRIMARY KEY,  -- P1, P2, P3, P4, P5, P6
    profile_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    context_statement TEXT,              -- "This user wants to..."
    assumptions TEXT,                    -- JSON array
    ai_guidance TEXT,                    -- JSON array
    preferred_response_style TEXT,       -- JSON array
    context_injection_prompt TEXT,       -- Ready-to-use prompt
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Key Points**:
- Only 6 profiles exist (P1-P6), seeded at startup
- AI context fields enable LLM personalization
- JSON arrays stored as TEXT (parsed in application layer)

#### 3.2.2 User Profile Ranking State Table

**Purpose**: Tracks temporal evolution of user-profile matching scores.

```sql
CREATE TABLE user_profile_ranking_state (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    user_id VARCHAR(36) NOT NULL,         -- Foreign key to User Management Service
    profile_id VARCHAR(24) NOT NULL,      -- Foreign key to profile table
    
    -- Aggregated Statistics
    cumulative_score FLOAT DEFAULT 0.0,   -- Sum of all scores
    average_score FLOAT DEFAULT 0.0,      -- Mean score
    max_score FLOAT DEFAULT 0.0,          -- Highest score ever
    observation_count INT DEFAULT 0,      -- Number of prompts processed
    
    -- Ranking Metadata
    last_rank INT DEFAULT 0,              -- Most recent rank position
    consecutive_top_count INT DEFAULT 0,  -- Consecutive times ranked #1
    consecutive_drop_count INT DEFAULT 0, -- Consecutive rank drops
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uix_user_profile UNIQUE (user_id, profile_id)
);
```

**Key Points**:
- One row per user-profile combination (36 rows for 1 user with 6 profiles)
- Updated after every prompt processing
- `consecutive_top_count` drives assignment decisions
- `average_score` used for confidence thresholds

#### 3.2.3 User Domain State Table

**Purpose**: Tracks user expertise level per interest domain.

```sql
CREATE TABLE user_domain_state (
    user_id VARCHAR(36) NOT NULL,
    interest_id INT NOT NULL,             -- Foreign key to interest_area
    expertise_level_id INT NOT NULL,      -- Foreign key to domain_expertise_level
    confidence_score FLOAT DEFAULT 0.0,   -- 0.0 to 1.0
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (user_id, interest_id)
);
```

**Expertise Levels**:
- `BEGINNER` (0.00 - 0.39)
- `INTERMEDIATE` (0.40 - 0.74)
- `ADVANCED` (0.75 - 1.00)

#### 3.2.4 Reference Tables

**Intent Table**:
```sql
CREATE TABLE intent (
    intent_id INT PRIMARY KEY,
    intent_name VARCHAR(50) UNIQUE NOT NULL,  -- LEARNING, TASK_COMPLETION, etc.
    description TEXT
);
```

**Interest Area Table**:
```sql
CREATE TABLE interest_area (
    interest_id INT PRIMARY KEY,
    interest_name VARCHAR(50) UNIQUE NOT NULL,  -- PROGRAMMING, WRITING, etc.
    description TEXT
);
```

**Behavior Level Table**:
```sql
CREATE TABLE behavior_level (
    behavior_level_id INT PRIMARY KEY,
    level_name VARCHAR(50) UNIQUE NOT NULL,  -- BASIC, INTERMEDIATE, ADVANCED
    description TEXT
);
```

**Behavior Signal Table**:
```sql
CREATE TABLE behavior_signal (
    signal_id INT PRIMARY KEY,
    signal_name VARCHAR(50) UNIQUE NOT NULL,  -- DEEP_REASONING, GOAL_ORIENTED, etc.
    description TEXT
);
```

#### 3.2.5 Association Tables (Many-to-Many)

**Profile Intent** (with weights):
```sql
CREATE TABLE profile_intent (
    profile_id VARCHAR(10) REFERENCES profile(profile_id),
    intent_id INT REFERENCES intent(intent_id),
    weight DECIMAL(3, 2) NOT NULL,  -- 0.00 to 1.00
    PRIMARY KEY (profile_id, intent_id)
);
```

**Profile Interest** (with weights):
```sql
CREATE TABLE profile_interest (
    profile_id VARCHAR(10) REFERENCES profile(profile_id),
    interest_id INT REFERENCES interest_area(interest_id),
    weight DECIMAL(3, 2) NOT NULL,
    PRIMARY KEY (profile_id, interest_id)
);
```

**Profile Behavior Level**:
```sql
CREATE TABLE profile_behavior_level (
    profile_id VARCHAR(10) REFERENCES profile(profile_id),
    behavior_level_id INT REFERENCES behavior_level(behavior_level_id),
    PRIMARY KEY (profile_id, behavior_level_id)
);
```

**Profile Behavior Signal** (with weights):
```sql
CREATE TABLE profile_behavior_signal (
    profile_id VARCHAR(10) REFERENCES profile(profile_id),
    signal_id INT REFERENCES behavior_signal(signal_id),
    weight DECIMAL(3, 2) NOT NULL,
    PRIMARY KEY (profile_id, signal_id)
);
```

#### 3.2.6 Matching Factor Tables

**Standard Matching Factor**:
```sql
CREATE TABLE standard_matching_factor (
    factor_name VARCHAR(50) PRIMARY KEY,
    weight DECIMAL(3, 2) NOT NULL
);

-- Seeded weights:
-- INTENT: 0.30
-- INTEREST: 0.25
-- COMPLEXITY: 0.20
-- STYLE: 0.15
-- CONSISTENCY: 0.10
```

**Cold Start Matching Factor**:
```sql
CREATE TABLE cold_start_matching_factor (
    factor_name VARCHAR(50) PRIMARY KEY,
    weight DECIMAL(3, 2) NOT NULL
);

-- Seeded weights:
-- INTENT: 0.55
-- INTEREST: 0.45
-- COMPLEXITY: 0.00
-- STYLE: 0.00
-- CONSISTENCY: 0.00
```

**Key Point**: Cold start uses only Intent + Interest for first 5 prompts.

### 3.3 ORM Models (SQLAlchemy)

All models are defined in `app/models/` and extend `Base` from SQLAlchemy.

**Key Model Classes**:
- `Profile`: Main profile entity with relationships
- `UserProfileRankingState`: Temporal ranking state
- `UserDomainState`: Domain expertise tracking
- `Intent`, `InterestArea`, `BehaviorLevel`, `BehaviorSignal`: Reference data
- `StandardMatchingFactor`, `ColdStartMatchingFactor`: Algorithm weights

**Relationship Patterns**:
- Profiles have many intents, interests, behavior levels, signals (via association tables)
- All relationships use `back_populates` for bidirectional navigation
- Cascade deletes configured where appropriate

---

## 4. Core Business Logic

### 4.1 Profile Assignment Workflow

**Entry Point**: `IntakeOrchestrator.process()`

**Step-by-Step Flow**:

```
1. Receive Request
   ↓
2. Create Database Session
   ↓
3. Initialize ProfileAssigner
   ↓
4. Call ProfileAssigner.assign(extracted_behavior, user_id)
   ↓
   4.1 Fetch user mode from User Management Service
   ↓
   4.2 Validate behavior format (single dict for COLD_START, list for DRIFT_FALLBACK)
   ↓
   4.3 Load profiles and matching factors from database
   ↓
   4.4 Initialize ProfileMatcher with weights
   ↓
   4.5 Determine if cold-start mode (first 5 prompts)
   ↓
   4.6 For each prompt in behavior list:
       ↓
       4.6.1 Call ProfileMatcher.match(profiles, behavior, is_cold_start)
       ↓
       4.6.2 Receive ranked_profiles [(P1, 0.35), (P2, 0.28), ...]
       ↓
       4.6.3 Call RankingStateService.update_from_ranked_profiles()
       ↓
       4.6.4 Update cumulative_score, average_score, max_score
       ↓
       4.6.5 Update last_rank, consecutive_top_count, consecutive_drop_count
   ↓
   4.7 Fetch updated aggregated ranking states
   ↓
   4.8 Call should_assign_profile() to check assignment criteria
   ↓
   4.9 If criteria met:
       ↓
       4.9.1 Call UserManagementClient.update_user_profile()
       ↓
       4.9.2 Set assigned_profile_id in User Management Service
   ↓
   4.10 Return assignment result dict
   ↓
5. Commit database transaction
   ↓
6. If profile assigned, publish event via ProfilePublisher
   ↓
7. Return result to caller
```

### 4.2 Profile Matching Algorithm (ProfileMatcher)

**Location**: `app/services/profile_matcher.py`

**Purpose**: Scores each profile against user behavior using weighted factors.

**Algorithm Pseudocode**:

```python
def match(profiles, extracted_behavior, is_cold_start):
    # Select weights based on mode
    if is_cold_start:
        weights = cold_start_weights  # Only intent + interest
    else:
        weights = standard_weights    # All 5 factors
    
    scores = {}
    
    for profile in profiles:
        # Calculate component scores
        intent_score = sum(
            user_intent[intent.name] * profile.intent_weight(intent)
            for intent in profile.intents
        )
        
        interest_score = sum(
            user_interest[interest.name] * profile.interest_weight(interest)
            for interest in profile.interests
        )
        
        behavior_score = 1.0 if user_behavior_level in profile.behavior_levels else 0.5
        
        signal_score = sum(
            user_signal[signal.name] * profile.signal_weight(signal)
            for signal in profile.signals
        )
        
        complexity_score = user_complexity  # 0.0 to 1.0
        consistency_score = user_consistency  # 0.0 to 1.0
        
        # Weighted aggregation
        raw_score = (
            weights["INTENT"] * intent_score +
            weights["INTEREST"] * interest_score +
            weights["COMPLEXITY"] * complexity_score +
            weights["STYLE"] * signal_score +
            weights["CONSISTENCY"] * consistency_score
        )
        
        scores[profile.profile_id] = raw_score
    
    # Normalize scores to sum to 1.0
    total = sum(scores.values())
    normalized_scores = {pid: score / total for pid, score in scores.items()}
    
    # Rank profiles by score (descending)
    ranked = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "ranked_profiles": ranked,
        "best_profile": ranked[0][0],
        "confidence": ranked[0][1]
    }
```

**Key Points**:
- Cold-start uses simplified weights (only intent + interest)
- Standard mode uses all 5 factors (intent, interest, complexity, style, consistency)
- Scores are normalized so they sum to 1.0
- Returns ranked list of all profiles, not just top one

### 4.3 Assignment Decision Logic

**Location**: `ProfileAssigner.should_assign_profile()`

**Purpose**: Determines if user has enough data and consistency to assign a profile.

**Decision Criteria**:

```python
def should_assign_profile(user_id, user_mode, min_prompts, cold_threshold, fallback_threshold):
    # Fetch top-ranked profile state
    top_state = get_top_profile_state(user_id)
    
    if not top_state:
        return False, None, 0.0
    
    if user_mode == "COLD_START":
        # Cold-start criteria (stricter)
        if top_state.observation_count < min_prompts:  # Default: 5
            return False, None, top_state.average_score
        
        if top_state.average_score >= cold_threshold (0.60) and \
           top_state.consecutive_top_count >= 2:
            return True, top_state.profile_id, top_state.average_score
    
    elif user_mode == "DRIFT_FALLBACK":
        # Drift fallback criteria (more lenient on prompts, stricter on consistency)
        if top_state.average_score >= fallback_threshold (0.70) and \
           top_state.consecutive_top_count >= 3:
            return True, top_state.profile_id, top_state.average_score
    
    return False, None, top_state.average_score
```

**Thresholds**:
- `MIN_PROMPTS_COLD_START`: 5 prompts required
- `COLD_START_THRESHOLD`: 0.60 average score required
- `COLD_START_CONSECUTIVE_TOP`: 2 consecutive #1 rankings required
- `FALLBACK_THRESHOLD`: 0.70 average score required
- `FALLBACK_CONSECUTIVE_TOP`: 3 consecutive #1 rankings required

**Rationale**: Drift fallback requires higher confidence (0.70 vs 0.60) because user already had a profile and we're overriding it.

### 4.4 Complexity Calculation

**Location**: `app/services/complexity_calculator.py`

**Purpose**: Analyzes prompt text to determine task complexity (0.0 to 1.0).

**Complexity Factors**:

1. **Word Count** (20% max):
   - < 20 words: 0.05
   - 20-100 words: Linear scale
   - > 100 words: 0.20

2. **Constraint Keywords** (70% max):
   - Keywords: "must", "should", "only", "require", "constraint", etc.
   - Score: 0.23 per keyword (capped at 0.70)

3. **Multi-Step Keywords** (60% max):
   - Keywords: "first", "then", "next", "finally", "step", etc.
   - Score: 0.20 per keyword (capped at 0.60)

4. **Structure Keywords** (12% max):
   - Keywords: "format", "template", "structure", "table", etc.
   - Score: 0.04 per keyword (capped at 0.12)

5. **Example Keywords** (8% max):
   - Keywords: "example", "like", "such as", "e.g.", etc.
   - Score: 0.027 per keyword (capped at 0.08)

**Final Complexity** = min(1.0, sum of all factors)

**Example**:
```
Prompt: "Write a Python function that validates email addresses. 
         Make sure it handles edge cases and includes unit tests."

Analysis:
- Word count: 16 words → 0.05
- Constraints: "make sure" (1) → 0.23
- Multi-step: None → 0.0
- Structure: "function" (1) → 0.04
- Examples: None → 0.0

Total: 0.32 (MODERATE complexity)
```

### 4.5 Consistency Calculation

**Location**: `app/services/consistency_calculator.py`

**Purpose**: Measures behavioral consistency across multiple prompts (0.0 to 1.0).

**Consistency Factors**:

1. **Intent Repetition** (40% weight):
   - Analyzes frequency of same intent across prompts
   - High dominance → High consistency

2. **Domain Stability** (40% weight):
   - Analyzes frequency of same interest domain across prompts
   - High dominance → High consistency

3. **Temporal Consistency** (20% weight):
   - Measures transition stability (how often user switches)
   - Few transitions → High consistency

4. **Signal Consistency** (10% weight, optional):
   - Analyzes stability of behavioral signals
   - Consistent style → High consistency

**Algorithm**:
```python
def compute_consistency(intent_history, domain_history):
    if len(intent_history) <= 1:
        return 0.5  # Default for single prompt
    
    # Intent consistency
    intent_counter = Counter(intent_history)
    top_intent_count = intent_counter.most_common(1)[0][1]
    intent_dominance = top_intent_count / len(intent_history)
    intent_consistency = intent_dominance * 0.40
    
    # Domain consistency
    domain_counter = Counter(domain_history)
    top_domain_count = domain_counter.most_common(1)[0][1]
    domain_dominance = top_domain_count / len(domain_history)
    domain_consistency = domain_dominance * 0.40
    
    # Temporal consistency (transition stability)
    intent_transitions = count_transitions(intent_history)
    max_transitions = len(intent_history) - 1
    intent_stability = 1.0 - (intent_transitions / max_transitions)
    temporal_consistency = intent_stability * 0.20
    
    total_consistency = intent_consistency + domain_consistency + temporal_consistency
    return min(1.0, max(0.0, total_consistency))
```

**Example**:
```
User prompts:
1. "Explain Python decorators" → LEARNING, PROGRAMMING
2. "How do I deploy a Flask app?" → LEARNING, PROGRAMMING
3. "Debug my authentication code" → PROBLEM_SOLVING, PROGRAMMING

Analysis:
- Intent repetition: LEARNING (2/3) → Dominance 0.67 → 0.67 * 0.40 = 0.27
- Domain stability: PROGRAMMING (3/3) → Dominance 1.0 → 1.0 * 0.40 = 0.40
- Temporal: 1 intent transition in 3 prompts → Stability 0.5 → 0.5 * 0.20 = 0.10

Total Consistency: 0.77 (HIGH)
```

### 4.6 Ranking State Update Logic

**Location**: `RankingStateService.update_from_ranked_profiles()`

**Purpose**: Updates aggregated statistics after each prompt.

**Update Rules**:

```python
def update_state(state, new_score, new_rank):
    # Update aggregated statistics
    state.observation_count += 1
    state.cumulative_score += new_score
    state.average_score = state.cumulative_score / state.observation_count
    state.max_score = max(state.max_score, new_score)
    
    # Update consecutive counters
    if new_rank == 1:
        # This profile is now #1
        if state.last_rank == 1:
            state.consecutive_top_count += 1  # Still #1
        else:
            state.consecutive_top_count = 1   # New #1
        state.consecutive_drop_count = 0
    else:
        # This profile is not #1
        if state.last_rank == 1:
            state.consecutive_drop_count = 1  # Dropped from #1
        elif state.last_rank < new_rank:
            state.consecutive_drop_count += 1 # Continuing to drop
        else:
            state.consecutive_drop_count = 0  # Rank improved
        state.consecutive_top_count = 0
    
    state.last_rank = new_rank
    state.updated_at = now()
```

**Key Point**: `consecutive_top_count` is the primary signal for assignment decisions.

---

## 5. API Endpoints

### 5.1 Profile Assignment Endpoints

#### POST `/api/predefined-profiles/assign-profile`

**Purpose**: Assign profile based on extracted behavior (async, preferred).

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "mode": "COLD_START",
  "extracted_behavior": {
    "intents": {
      "LEARNING": 0.8,
      "PROBLEM_SOLVING": 0.2
    },
    "interests": {
      "PROGRAMMING": 0.9,
      "AI": 0.1
    },
    "behavior_level": "INTERMEDIATE",
    "signals": {
      "DEEP_REASONING": 0.7,
      "ITERATIVE": 0.3
    },
    "complexity": 0.65,
    "consistency": 0.75
  },
  "trigger_event_id": null
}
```

**Response**:
```json
{
  "status": "ASSIGNED",
  "confidence_level": "HIGH",
  "user_mode": "COLD_START",
  "prompt_count": 5,
  "assigned_profile_id": "P3",
  "aggregated_rankings": [
    {
      "profile_code": "P3",
      "average_score": 0.7845,
      "cumulative_score": 3.9225,
      "max_score": 0.8123,
      "observations": 5,
      "last_rank": 1,
      "consecutive_top_count": 3,
      "consecutive_drop_count": 0,
      "updated_at": "2026-03-03T10:30:00Z"
    },
    {
      "profile_code": "P1",
      "average_score": 0.6234,
      "cumulative_score": 3.1170,
      "max_score": 0.6890,
      "observations": 5,
      "last_rank": 2,
      "consecutive_top_count": 0,
      "consecutive_drop_count": 0,
      "updated_at": "2026-03-03T10:30:00Z"
    }
    // ... other profiles
  ]
}
```

**Behavior Format for DRIFT_FALLBACK**:
```json
{
  "user_id": "...",
  "mode": "DRIFT_FALLBACK",
  "extracted_behavior": [
    {
      "intents": {"EXPLORATION": 0.9},
      "interests": {"CREATIVE": 0.8},
      "behavior_level": "BASIC",
      "signals": {"CASUAL": 0.7},
      "complexity": 0.3,
      "consistency": 0.5
    },
    {
      "intents": {"EXPLORATION": 0.85},
      "interests": {"CREATIVE": 0.9},
      "behavior_level": "BASIC",
      "signals": {"CASUAL": 0.8},
      "complexity": 0.25,
      "consistency": 0.6
    }
    // ... up to 10 prompts
  ],
  "trigger_event_id": "drift-abc123"
}
```

#### GET `/api/predefined-profiles/user/{user_id}`

**Purpose**: Get current assignment status without processing.

**Response**: Same as POST response above.

#### GET `/api/predefined-profiles/`

**Purpose**: Get all profiles with full AI context.

**Response**:
```json
{
  "profiles": [
    {
      "profile_id": "P1",
      "profile_name": "Knowledge Seeker",
      "context_statement": "This user wants to understand.",
      "assumptions": [
        "User values clarity over speed",
        "Explanations are more important than final answers"
      ],
      "ai_guidance": [
        "Explain concepts step-by-step",
        "Use examples and analogies",
        "Avoid skipping reasoning"
      ],
      "preferred_response_style": [
        "Educational",
        "Structured",
        "Patient"
      ],
      "context_injection_prompt": "Respond as a tutor. Prioritize explanation and understanding."
    }
    // ... other profiles
  ],
  "total": 6
}
```

#### GET `/api/predefined-profiles/{profile_id}`

**Purpose**: Get single profile with AI context.

**Response**: Single profile object (same structure as above).

### 5.2 Ranking State Endpoints

#### GET `/api/ranking-states/user/{user_id}`

**Purpose**: Get all ranking states for a user.

#### GET `/api/ranking-states/user/{user_id}/profile/{profile_id}`

**Purpose**: Get specific user-profile ranking state.

#### POST/PUT/DELETE `/api/ranking-states/`

**Purpose**: CRUD operations for ranking states (admin/testing only).

### 5.3 Domain Expertise Endpoints

#### GET `/api/domain-expertise/user/{user_id}`

**Purpose**: Get user's domain expertise levels across all interest areas.

**Response**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "domain_states": [
    {
      "interest_name": "PROGRAMMING",
      "expertise_level": "INTERMEDIATE",
      "confidence_score": 0.68,
      "last_updated": "2026-03-03T10:30:00Z"
    },
    {
      "interest_name": "AI",
      "expertise_level": "BEGINNER",
      "confidence_score": 0.32,
      "last_updated": "2026-03-03T10:25:00Z"
    }
  ]
}
```

---

## 6. Event-Driven Architecture

### 6.1 Redis Streams

**Technology**: Redis Streams (not Pub/Sub)

**Advantages**:
- Message persistence (retained in stream)
- Consumer groups for exactly-once delivery
- Pending Entries List (PEL) for retry on failure
- Multiple consumers for scalability

### 6.2 Consumed Streams

#### `drift.events` Stream

**Producer**: Drift Detection Service

**Consumer**: This service (DriftEventConsumer)

**Event Schema**:
```json
{
  "drift_event_id": "drift-abc123",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "severity": "STRONG_DRIFT",
  "behavior_ref_ids": ["beh_r_001", "beh_r_002", "beh_c_003"]
}
```

**Severity Levels**:
- `NO_DRIFT`: No action taken
- `WEAK_DRIFT`: No action taken
- `MODERATE_DRIFT`: Triggers profile re-evaluation
- `STRONG_DRIFT`: Triggers profile re-evaluation

**Processing Flow**:
```
1. DriftEventConsumer receives message from stream
   ↓
2. Parse payload JSON
   ↓
3. Check severity → Only MODERATE_DRIFT or STRONG_DRIFT proceed
   ↓
4. Fetch specific behaviors by IDs from Behavior Resolution Service
   ↓
5. Call IntakeOrchestrator.process() in DRIFT_FALLBACK mode
   ↓
6. Process all behaviors, update ranking states
   ↓
7. If profile assigned, publish to profile.assigned stream
   ↓
8. ACK message in Redis (remove from PEL)
```

**Consumer Group Configuration**:
- Group Name: `predefined-profile-service`
- Consumer Name: `profile-worker-1`
- Block Time: 5 seconds
- Max Messages per Read: 10

### 6.3 Published Streams

#### `profile.assigned` Stream

**Producer**: This service (ProfilePublisher)

**Consumers**: LLM Orchestration, Recommendation Engine, Analytics

**Event Schema**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "assigned_profile_id": "P3",
  "confidence_level": "HIGH",
  "mode": "COLD_START",
  "trigger_event_id": null,
  "assigned_at": 1740567890
}
```

**When Published**:
- After successful profile assignment
- Both COLD_START and DRIFT_FALLBACK modes
- Only when status changes to "ASSIGNED"

**Purpose**: Notifies downstream services to adapt their behavior based on user's profile.

### 6.4 Redis Configuration

**Database**: Redis DB 0 (shared with other services)

**Connection URL**: `redis://shared-redis:6379/0`

**Connection Management**:
- Consumer: Single long-lived connection with reconnect on error
- Publisher: Lazy-initialized connection (created on first publish)
- Both connections closed gracefully during shutdown

---

## 7. Configuration & Environment

### 7.1 Environment Variables

**File**: `.env` (loaded via `pydantic-settings`)

**Required Variables**:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/profile_db

# Application Settings
APP_NAME=Predefined Profile Assignment Service
ENVIRONMENT=development
DEBUG=False
LOG_LEVEL=INFO

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# External Services
BEHAVIOR_RESOLUTION_BASE_URL=http://localhost:8001
USER_MANAGEMENT_SERVICE_URL=http://localhost:8080
DRIFT_FALLBACK_BEHAVIOR_LIMIT=10

# Profile Assignment Algorithm Parameters
MIN_PROMPTS_COLD_START=5
MIN_PROMPTS_FALLBACK=3
COLD_START_THRESHOLD=0.60
COLD_START_CONSECUTIVE_TOP=2
FALLBACK_THRESHOLD=0.70
FALLBACK_CONSECUTIVE_TOP=3
HIGH_CONFIDENCE_THRESHOLD=0.70
```

### 7.2 Settings Class

**Location**: `app/core/config.py`

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Application
    APP_NAME: str = "Predefined Profile Assignment Service"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # External Services
    BEHAVIOR_RESOLUTION_BASE_URL: str = "http://localhost:8001"
    USER_MANAGEMENT_SERVICE_URL: str = "http://localhost:8080"
    DRIFT_FALLBACK_BEHAVIOR_LIMIT: int = 10
    
    # Algorithm Parameters
    MIN_PROMPTS_COLD_START: int = 5
    MIN_PROMPTS_FALLBACK: int = 3
    COLD_START_THRESHOLD: float = 0.60
    FALLBACK_THRESHOLD: float = 0.70
    HIGH_CONFIDENCE_THRESHOLD: float = 0.70
    
    class Config:
        env_file = ".env"
```

**Access**: `from app.core.config import settings`

### 7.3 Constants

**Location**: `app/core/constants.py`

**Key Constants**:

```python
# Complexity Thresholds
LOW_COMPLEXITY_THRESHOLD = 20    # words
HIGH_COMPLEXITY_THRESHOLD = 100  # words

# Consistency Weights
INTENT_WEIGHT = 0.40
DOMAIN_WEIGHT = 0.40
TEMPORAL_WEIGHT = 0.20

# Expertise Thresholds
BEGINNER_MAX = 0.39
INTERMEDIATE_MIN = 0.40
INTERMEDIATE_MAX = 0.74
ADVANCED_MIN = 0.75

# Default Values
DEFAULT_BEHAVIOR_SCORE = 0.5
DEFAULT_COMPLEXITY = 0.5
DEFAULT_CONSISTENCY = 0.5
```

---

## 8. Deployment & Infrastructure

### 8.1 Docker Configuration

#### Dockerfile (Multi-Stage Build)

**Stage 1: Builder**
```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Stage 2: Production**
```dockerfile
FROM python:3.11-slim as production
WORKDIR /app
RUN apt-get update && apt-get install -y libpq5 && \
    useradd --create-home --shell /bin/bash appuser
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app/ ./app/
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Security Features**:
- Non-root user (`appuser`)
- Minimal base image (slim)
- No unnecessary packages in production

#### Docker Compose

**File**: `docker-compose.yml`

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: predefined-profile-service
    ports:
      - "8002:8000"  # Host 8002 → Container 8000
    environment:
      - REDIS_URL=redis://shared-redis:6379/0
      - BEHAVIOR_RESOLUTION_BASE_URL=http://behavior-extraction-engine:8001
      - USER_MANAGEMENT_SERVICE_URL=http://user-management-service:8080
      - DEBUG=false
      - LOG_LEVEL=INFO
    networks:
      - shared-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: profile-redis-commander
    environment:
      - REDIS_HOSTS=local:shared-redis:6379
    ports:
      - "8083:8081"
    networks:
      - shared-network
    restart: unless-stopped
    profiles:
      - dev-tools  # Only starts with --profile dev-tools

networks:
  shared-network:
    external: true
    name: shared-network
```

**Key Points**:
- Uses external `shared-network` for inter-service communication
- Redis Commander optional (dev-tools profile)
- Health check ensures service is ready before accepting traffic
- Port mapping: Host 8002 → Container 8000

### 8.2 Dependencies (requirements.txt)

```txt
# Web Framework
fastapi==0.110.0
uvicorn==0.27.1

# Database
sqlalchemy==2.0.27
psycopg2-binary==2.9.9
psycopg[binary]==3.3.2
asyncpg==0.29.0

# Validation & Settings
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.1

# HTTP Client
httpx==0.27.0

# Redis
redis==5.0.1

# Security
bcrypt==4.1.2
PyJWT==2.8.0
```

### 8.3 Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: shared-network           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  shared-redis:6379                                          │
│  ├─ drift.events stream                                     │
│  └─ profile.assigned stream                                 │
│                                                             │
│  user-management-service:8080                               │
│  ├─ GET /api/users/{user_id}                                │
│  └─ PUT /api/users/{user_id}                                │
│                                                             │
│  behavior-extraction-engine:8001                            │
│  └─ POST /api/behaviors/by-ids                              │
│                                                             │
│  predefined-profile-service:8000 (this service)             │
│  ├─ HTTP Server (FastAPI)                                   │
│  └─ Redis Consumer (background task)                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
        ↑
        │ Port Mapping
        │
    Host Port 8002 → Container Port 8000
```

**Service Discovery**: Uses Docker DNS (container names as hostnames).

### 8.4 Database Connection

**Sync Connection** (for repositories and services):
```python
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```

**Async Connection** (for consumers and publishers):
```python
async_engine = create_async_engine(
    DATABASE_URL.replace("+psycopg:", "+psycopg_async:"),
    pool_size=10
)
AsyncSessionLocal = async_sessionmaker(bind=async_engine)
```

**Key Point**: Two separate engines to support both sync and async operations.

---

## 9. Data Flow Diagrams

### 9.1 Cold-Start Profile Assignment Flow

```
User submits prompt
        ↓
Behavior Resolution Service extracts behavior
        ↓
POST /api/predefined-profiles/assign-profile
{
  "user_id": "...",
  "mode": "COLD_START",
  "extracted_behavior": { intents, interests, ... }
}
        ↓
IntakeOrchestrator.process()
        ↓
ProfileAssigner.assign()
        ↓
1. Fetch user mode from User Management Service
        ↓
2. Load profiles and weights from database
        ↓
3. Determine if cold-start (first 5 prompts)
        ↓
4. ProfileMatcher.match()
   ├─ If cold-start: Use Intent + Interest only
   └─ Else: Use all 5 factors
        ↓
5. Get ranked profiles: [(P3, 0.35), (P1, 0.28), ...]
        ↓
6. RankingStateService.update_from_ranked_profiles()
   ├─ Update cumulative_score, average_score
   ├─ Update consecutive_top_count
   └─ Persist to database
        ↓
7. Check assignment criteria:
   ├─ observation_count >= 5?
   ├─ average_score >= 0.60?
   └─ consecutive_top_count >= 2?
        ↓
8. If YES:
   ├─ Call User Management Service to set profile
   └─ Return "ASSIGNED"
   Else:
   └─ Return "PENDING"
        ↓
9. If ASSIGNED:
   └─ ProfilePublisher.publish() to profile.assigned stream
        ↓
Return result to caller
```

### 9.2 Drift Fallback Flow

```
User behavior deviates from assigned profile
        ↓
Drift Detection Service detects drift
        ↓
Publishes to drift.events stream:
{
  "drift_event_id": "drift-abc123",
  "user_id": "...",
  "severity": "STRONG_DRIFT",
  "behavior_ref_ids": ["beh_r_001", "beh_r_002", ...]
}
        ↓
DriftEventConsumer receives message
        ↓
DriftEventHandler.handle()
        ↓
1. Check severity → Only MODERATE/STRONG proceed
        ↓
2. Fetch specific behaviors by IDs from Behavior Resolution
        ↓
3. Call IntakeOrchestrator.process()
   {
     "user_id": "...",
     "mode": "DRIFT_FALLBACK",
     "extracted_behavior": [ {...}, {...}, {...} ],
     "trigger_event_id": "drift-abc123"
   }
        ↓
4. ProfileAssigner.assign()
   ├─ Process each behavior in the list
   ├─ Use STANDARD weights (not cold-start)
   └─ Update ranking states for all behaviors
        ↓
5. Check fallback criteria:
   ├─ average_score >= 0.70?
   └─ consecutive_top_count >= 3?
        ↓
6. If YES:
   ├─ Update User Management Service with new profile
   └─ Return "ASSIGNED"
        ↓
7. ProfilePublisher.publish() to profile.assigned stream
   {
     "user_id": "...",
     "assigned_profile_id": "P4",
     "mode": "DRIFT_FALLBACK",
     "trigger_event_id": "drift-abc123"
   }
        ↓
8. ACK message in Redis (remove from PEL)
        ↓
Downstream services react to new profile
```

### 9.3 Domain Expertise Update Flow

```
Behavior data received with interests and signals
        ↓
DomainExpertiseService.update_from_behavior()
        ↓
For each interest in behavior:
        ↓
1. Get or create UserDomainState for (user_id, interest_id)
        ↓
2. Calculate confidence score from signals:
   ├─ CORRECT_TERMINOLOGY → +0.10
   ├─ MULTI_STEP_PROMPT → +0.15
   ├─ ITERATIVE_REFINEMENT → +0.20
   ├─ EXPLICIT_ADVANCED_REQUEST → +0.25
   ├─ BEGINNER_QUESTION → -0.10
   └─ INCORRECT_TERMINOLOGY → -0.20
        ↓
3. Update confidence_score (moving average)
        ↓
4. Determine expertise level:
   ├─ 0.00-0.39 → BEGINNER
   ├─ 0.40-0.74 → INTERMEDIATE
   └─ 0.75-1.00 → ADVANCED
        ↓
5. Update or insert UserDomainState
        ↓
Persist to database
```

---

## 10. Algorithm Details

### 10.1 Profile Matching Weights

**Standard Mode Weights** (after 5 prompts):
```
INTENT:       0.30 (30%)
INTEREST:     0.25 (25%)
COMPLEXITY:   0.20 (20%)
STYLE:        0.15 (15%)
CONSISTENCY:  0.10 (10%)
────────────────────
TOTAL:        1.00 (100%)
```

**Cold-Start Weights** (first 5 prompts):
```
INTENT:       0.55 (55%)
INTEREST:     0.45 (45%)
COMPLEXITY:   0.00 (0%)
STYLE:        0.00 (0%)
CONSISTENCY:  0.00 (0%)
────────────────────
TOTAL:        1.00 (100%)
```

**Rationale**: New users don't have enough data for complexity/consistency/style, so focus on intent and interest only.

### 10.2 Score Normalization

**Raw Score Calculation**:
```
raw_score = Σ(weight_i × component_score_i) for all factors
```

**Normalization**:
```
normalized_score = raw_score / Σ(all_profile_raw_scores)
```

**Result**: All profile scores sum to 1.0, enabling probabilistic interpretation.

### 10.3 Consecutive Top Count Logic

**Purpose**: Ensures stability before assignment.

**Update Rules**:
```
IF current_rank == 1:
    IF previous_rank == 1:
        consecutive_top_count += 1  # Still on top
    ELSE:
        consecutive_top_count = 1   # New winner
ELSE:
    consecutive_top_count = 0       # Lost top position
```

**Assignment Trigger**:
- Cold-start: `consecutive_top_count >= 2`
- Drift fallback: `consecutive_top_count >= 3`

**Example**:
```
Prompt 1: P3 ranked #1 → consecutive_top_count = 1
Prompt 2: P3 ranked #1 → consecutive_top_count = 2 ✅ Can assign
Prompt 3: P1 ranked #1 → P3.consecutive_top_count = 0, P1.consecutive_top_count = 1
Prompt 4: P1 ranked #1 → P1.consecutive_top_count = 2 ✅ Can reassign
```

### 10.4 Average Score Threshold

**Purpose**: Ensures confidence in the match.

**Calculation**:
```
average_score = cumulative_score / observation_count
```

**Thresholds**:
- Cold-start: `average_score >= 0.60` (60% confidence)
- Drift fallback: `average_score >= 0.70` (70% confidence)

**Rationale**: Higher threshold for drift fallback because we're overriding an existing assignment.

### 10.5 Confidence Level Mapping

```
if average_score >= 0.70:
    confidence_level = "HIGH"
elif average_score >= 0.50:
    confidence_level = "MEDIUM"
else:
    confidence_level = "LOW"
```

---

## 11. External Dependencies

### 11.1 User Management Service

**Purpose**: Stores user profile and mode data.

**Base URL**: `http://user-management-service:8080`

**Endpoints Used**:

#### GET `/api/users/{user_id}`
**Purpose**: Fetch user profile mode and assigned profile.

**Response**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "profile_mode": "COLD_START",
  "predefined_profile_id": "P3",
  "dynamic_profile_id": null,
  "dynamic_profile_confidence": 0.0,
  "dynamic_profile_ready": false,
  "fallback_profile_id": null,
  "fallback_reason": null,
  "fallback_activated_at": null
}
```

**Profile Modes**:
- `COLD_START`: New user, building profile
- `HYBRID`: Using both predefined and dynamic profiles
- `DYNAMIC_ONLY`: Using only dynamic profile
- `DRIFT_FALLBACK`: Temporary fallback due to drift

#### PUT `/api/users/{user_id}`
**Purpose**: Update user's assigned profile.

**Request**:
```json
{
  "predefined_profile_id": "P3",
  "profile_mode": "COLD_START"
}
```

**Response**:
```json
{
  "message": "User updated successfully"
}
```

### 11.2 Behavior Resolution Service

**Purpose**: Extracts behavioral signals from user prompts.

**Base URL**: `http://behavior-extraction-engine:8001`

**Endpoints Used**:

#### POST `/api/behaviors/by-ids`
**Purpose**: Fetch specific behaviors by reference IDs (for drift fallback).

**Request**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "behavior_ids": ["beh_r_001", "beh_r_002", "beh_c_003"]
}
```

**Response**:
```json
{
  "behaviors": [
    {
      "behavior_id": "beh_r_001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "intents": {
        "LEARNING": 0.8,
        "PROBLEM_SOLVING": 0.2
      },
      "interests": {
        "PROGRAMMING": 0.9,
        "AI": 0.1
      },
      "behavior_level": "INTERMEDIATE",
      "signals": {
        "DEEP_REASONING": 0.7,
        "ITERATIVE": 0.3
      },
      "complexity": 0.65,
      "consistency": 0.75,
      "created_at": "2026-03-03T10:25:00Z"
    }
    // ... more behaviors
  ]
}
```

### 11.3 Drift Detection Service

**Purpose**: Monitors user behavior for drift from assigned profile.

**Integration**: Publishes to `drift.events` Redis stream (no direct HTTP calls).

**Event Format**: See section 6.2.

### 11.4 Downstream Consumers (of profile.assigned)

**Services**:
- **LLM Orchestration Service**: Adjusts response style based on profile
- **Recommendation Engine**: Personalizes content recommendations
- **Analytics Service**: Tracks profile assignment trends

**Integration**: Subscribe to `profile.assigned` Redis stream.

---

## 12. Error Handling & Resilience

### 12.1 HTTP Client Error Handling

**User Management Client**:
```python
async def get_user_profile(self, user_id: str) -> Optional[Dict]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            
            if response.status_code == 404:
                logger.warning(f"User {user_id} not found")
                return None
            
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException:
        logger.error(f"Timeout getting user {user_id}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
```

**Behavior Resolution Client**: Same pattern with specific error handling.

### 12.2 Redis Consumer Resilience

**Consumer Loop**:
```python
while self._running:
    try:
        messages = await self._redis.xreadgroup(...)
        
        for entry_id, data in messages:
            await self._process(entry_id, data)
            
    except asyncio.CancelledError:
        logger.info("Consumer received cancellation signal")
        break
    except Exception as e:
        logger.error(f"Consumer error: {e}")
        await asyncio.sleep(2)  # Backoff before retry
```

**Key Points**:
- Errors don't crash the consumer loop
- 2-second backoff prevents tight error loops
- Messages remain in PEL if processing fails (can retry)

### 12.3 Database Transaction Management

**Pattern**:
```python
db = SessionLocal()
try:
    # Perform operations
    result = assigner.assign(...)
    db.commit()
except Exception as e:
    db.rollback()
    logger.error(f"Transaction failed: {e}")
    raise
finally:
    db.close()
```

**Key Points**:
- All mutations wrapped in try/except
- Rollback on error
- Session always closed in finally block

### 12.4 Message Acknowledgment Strategy

**Success Path**:
```python
await self._handler.handle(event_payload)
await self._redis.xack(STREAM_NAME, GROUP_NAME, entry_id)
```

**Failure Path**:
```python
except Exception as e:
    logger.error(f"Failed to process: {e}")
    # Do NOT ack - message stays in PEL for retry
```

**Key Point**: Only ACK on success. Failed messages can be retried by same or different consumer.

### 12.5 Graceful Shutdown

**Lifespan Manager**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_async_db()
    _consumer_task = asyncio.create_task(_consumer_instance.start())
    
    yield  # App is running
    
    # Shutdown
    if _consumer_instance:
        _consumer_instance.stop()
        await _consumer_instance.close()
    
    if _consumer_task:
        _consumer_task.cancel()
        await _consumer_task
    
    await close_db()
```

**Key Points**:
- Consumer stopped before task cancelled
- Database connections closed last
- All resources cleaned up properly

### 12.6 Health Checks

**Docker Health Check**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
```

**API Health Endpoint**:
```python
@app.get("/health")
async def health_check():
    consumer_status = "running" if _consumer_instance._running else "stopped"
    
    return {
        "status": "healthy",
        "components": {
            "http_server": "running",
            "drift_consumer": consumer_status,
            "database": "connected"
        }
    }
```

---

## 13. Testing & Development

### 13.1 Running Locally

**Prerequisites**:
- Python 3.11+
- PostgreSQL 13+
- Redis 5+

**Steps**:
```bash
# 1. Clone repository
git clone <repository-url>
cd predefined_profile_assignment

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (see section 7.1)
cp .env.example .env
# Edit .env with your configuration

# 5. Run application
uvicorn app.main:app --reload
```

**Access**:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 13.2 Running with Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down

# Start with Redis Commander (dev tools)
docker-compose --profile dev-tools up -d
```

**Access**:
- API: http://localhost:8002
- Redis Commander: http://localhost:8083

### 13.3 Testing Strategy

**Unit Tests**: Test individual services (ProfileMatcher, ComplexityCalculator, etc.)

**Integration Tests**: Test API endpoints with test database

**Event Tests**: Test Redis consumer/publisher with test Redis instance

**Load Tests**: Simulate high-volume profile assignment requests

---

## 14. Key Design Decisions

### 14.1 Why Two Database Engines?

**Problem**: FastAPI supports both sync and async; Redis consumers must be async.

**Solution**: 
- Sync engine for repositories (used by HTTP endpoints)
- Async engine for event consumers/publishers

**Trade-off**: Slight complexity increase, but enables mixing sync/async code.

### 14.2 Why Redis Streams Instead of Pub/Sub?

**Advantages**:
- Message persistence (can replay)
- Consumer groups (load balancing)
- Pending Entries List (retry on failure)
- No message loss if consumer is down

**Disadvantage**: Slightly more complex than Pub/Sub.

### 14.3 Why Separate Cold-Start Weights?

**Problem**: New users don't have consistency, complexity, or style data.

**Solution**: Use simplified weights (Intent + Interest only) for first 5 prompts.

**Benefit**: Faster initial assignment without waiting for full behavioral data.

### 14.4 Why Consecutive Top Count?

**Problem**: Single prompt might spike a profile's score but not reflect true pattern.

**Solution**: Require 2-3 consecutive top rankings before assignment.

**Benefit**: Reduces false positives and ensures stability.

### 14.5 Why Higher Threshold for Drift Fallback?

**Problem**: User already has a profile; overriding requires high confidence.

**Solution**: 
- Cold-start: 0.60 threshold (no prior profile)
- Drift fallback: 0.70 threshold (overriding existing profile)

**Benefit**: Prevents premature profile switching.

---

## 15. Future Enhancements

### 15.1 Potential Improvements

1. **Profile Confidence Decay**: Reduce confidence over time if user is inactive
2. **A/B Testing**: Test different matching weights for optimization
3. **Profile Hybrids**: Allow users to match multiple profiles with percentages
4. **Real-time Drift Detection**: Detect drift within this service instead of external
5. **Machine Learning**: Train profile classifier instead of rule-based matching
6. **Profile Recommendations**: Suggest optional profile switches to users

### 15.2 Scalability Considerations

**Current Capacity**: ~1000 requests/sec (single instance)

**Horizontal Scaling**:
- Deploy multiple instances behind load balancer
- Redis consumer groups automatically distribute work
- Database connection pooling handles concurrent queries

**Vertical Scaling**:
- Increase container CPU/memory for compute-heavy matching
- Increase PostgreSQL resources for high-volume updates

**Caching**:
- Cache profile data (rarely changes)
- Cache user modes (changes infrequently)

---

## 16. Troubleshooting Guide

### 16.1 Common Issues

**Issue**: "User not found in User Management Service"

**Cause**: User ID doesn't exist or User Management offline

**Solution**: Check User Management health, verify user ID

---

**Issue**: "Consumer not receiving drift events"

**Cause**: Redis connection issue or consumer group misconfigured

**Solution**: 
```bash
# Check Redis connectivity
docker exec -it predefined-profile-service redis-cli -h shared-redis ping

# Check consumer group exists
redis-cli XINFO GROUPS drift.events
```

---

**Issue**: "Profile never gets assigned despite high scores"

**Cause**: Consecutive top count not met or prompt count insufficient

**Solution**: Check ranking state:
```bash
curl http://localhost:8002/api/ranking-states/user/{user_id}
```

Verify:
- `observation_count >= 5` (cold-start)
- `consecutive_top_count >= 2` (cold-start) or `>= 3` (fallback)
- `average_score >= 0.60` (cold-start) or `>= 0.70` (fallback)

---

**Issue**: "Database connection timeout"

**Cause**: Connection pool exhausted or database offline

**Solution**:
- Increase pool size in database.py
- Check PostgreSQL health
- Review slow queries

---

## 17. Glossary

| Term | Definition |
|------|------------|
| **Cold Start** | Initial phase for new users (first 5 prompts) with limited data |
| **Drift** | Behavioral change where user no longer matches assigned profile |
| **Drift Fallback** | Mode triggered by drift detection to reassign profile |
| **Profile** | Predefined behavioral archetype (P1-P6) |
| **Ranking State** | Aggregated statistics tracking user-profile match over time |
| **Consecutive Top Count** | Number of times profile consecutively ranked #1 |
| **Observation Count** | Total number of prompts processed for a user |
| **Average Score** | Mean matching score for a user-profile combination |
| **Complexity** | Task difficulty measure (0.0 to 1.0) from prompt analysis |
| **Consistency** | Behavioral stability measure (0.0 to 1.0) across prompts |
| **Intent** | User's primary goal (LEARNING, TASK_COMPLETION, etc.) |
| **Interest** | Domain/topic area (PROGRAMMING, WRITING, etc.) |
| **Behavior Level** | Engagement depth (BASIC, INTERMEDIATE, ADVANCED) |
| **Behavior Signal** | Interaction style indicator (DEEP_REASONING, ITERATIVE, etc.) |
| **Domain Expertise** | User's skill level in specific interest area |
| **Matching Factor** | Weighted component in profile scoring algorithm |
| **PEL** | Pending Entries List in Redis (unacknowledged messages) |

---

## 18. System Boundaries

### 18.1 What This Service Does

✅ **In Scope**:
- Profile assignment based on extracted behavior
- Ranking state management
- Domain expertise tracking
- Event consumption (drift.events)
- Event publishing (profile.assigned)
- Profile context provision to downstream services

### 18.2 What This Service Does NOT Do

❌ **Out of Scope**:
- Prompt processing (done by Behavior Resolution Service)
- User authentication/authorization (done by User Management)
- Drift detection (done by Drift Detection Service)
- LLM response generation (done by LLM Orchestration)
- Content recommendation (done by Recommendation Engine)
- Dynamic profile creation (separate Dynamic Profiling Service)

---

## 19. Summary

The **Predefined Profile Assignment Service** is a sophisticated behavioral classification system that:

1. **Receives** extracted behavioral data from users
2. **Analyzes** patterns using weighted multi-factor algorithms
3. **Assigns** users to one of six predefined profiles
4. **Adapts** to behavioral drift through fallback mechanisms
5. **Publishes** assignment events to downstream services
6. **Tracks** domain expertise and temporal ranking evolution

**Key Strengths**:
- Cold-start optimization for new users
- Drift resilience with fallback mode
- Event-driven architecture for loose coupling
- Comprehensive ranking state tracking
- AI context provision for LLM personalization

**Technology Highlights**:
- FastAPI for high-performance async HTTP
- SQLAlchemy for robust database operations
- Redis Streams for reliable event processing
- Docker for containerized deployment
- Multi-stage builds for secure production images

This system forms a critical component of an adaptive AI personalization platform, enabling downstream services to tailor their behavior based on user profiles while continuously adapting to changing user needs.

---

**End of Deep System Analysis**

*This document provides complete understanding of the Predefined Profile Assignment Service architecture, implementation, and operational characteristics. Any LLM reading this document should have 100% clarity on the system's design, behavior, and integration points.*
