# Predefined Profile Assignment Service - Complete System Analysis

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture](#3-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Data Models](#5-data-models)
6. [API Endpoints](#6-api-endpoints)
7. [Core Services](#7-core-services)
8. [Profile Matching Algorithm](#8-profile-matching-algorithm)
9. [Event-Driven Architecture](#9-event-driven-architecture)
10. [Domain Expertise Tracking](#10-domain-expertise-tracking)
11. [Configuration & Constants](#11-configuration--constants)
12. [Deployment](#12-deployment)
13. [Integration Points](#13-integration-points)
14. [Data Flow Diagrams](#14-data-flow-diagrams)
15. [Security Considerations](#15-security-considerations)
16. [Performance Considerations](#16-performance-considerations)

---

## 1. Executive Summary

### 1.1 Purpose
The **Predefined Profile Assignment Service** is an AI-powered microservice designed to automatically classify users into one of six predefined behavioral profiles based on their interactions with LLM (Large Language Model) applications. It uses multi-factor scoring algorithms to analyze user behavior patterns and adapts to behavioral changes over time.

### 1.2 Key Capabilities
| Capability | Description |
|------------|-------------|
| **Intelligent Profile Matching** | Weighted multi-factor scoring algorithm matching users to 6 predefined profiles |
| **Cold-Start Support** | Simplified matching for new users with limited interaction history |
| **Drift Detection** | Identifies and responds to behavioral changes with automatic reassignment |
| **Domain Expertise Tracking** | Monitors user expertise levels across different interest domains |
| **Temporal Ranking** | Maintains historical profile ranking evolution for trend analysis |
| **OAuth Integration** | Supports Google and GitHub authentication |
| **Adaptive Profiling** | Multiple user modes (COLD_START, HYBRID, DYNAMIC_ONLY, DRIFT_FALLBACK) |

### 1.3 Service Identification
- **Service Name**: Predefined Profile Assignment Service
- **Port**: 8002 (external), 8000 (internal)
- **Version**: 1.0.0
- **Framework**: FastAPI

---

## 2. System Overview

### 2.1 The Six Predefined Profiles

| Profile ID | Name | Primary Intent | Description | AI Guidance |
|------------|------|----------------|-------------|-------------|
| **P1** | Knowledge Seeker | LEARNING | Learns concepts and seeks explanations | "Respond as a tutor. Prioritize explanation and understanding." |
| **P2** | Productivity Professional | TASK_COMPLETION | Uses LLMs for efficient task completion | "Respond as an assistant focused on execution and efficiency." |
| **P3** | Technical Problem Solver | PROBLEM_SOLVING | Solves technical and engineering problems | "Respond as a technical expert. Prioritize correctness and depth." |
| **P4** | Creative Generator | EXPLORATION | Generates creative ideas and content | "Respond creatively. Prioritize originality and idea generation." |
| **P5** | Lifestyle Advisor Seeker | GUIDANCE | Seeks personal and lifestyle guidance | "Respond as a supportive advisor, not a command-giver." |
| **P6** | Casual Explorer | ENGAGEMENT | Uses LLMs casually for curiosity or fun | "Respond casually and keep things engaging and simple." |

### 2.2 User Assignment Modes

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        User Profile Modes                               │
├─────────────────────────────────────────────────────────────────────────┤
│ COLD_START      │ Initial phase with limited behavioral data           │
│                 │ Uses simplified matching (Intent + Interest only)     │
│                 │ First 5 prompts use cold-start weights               │
├─────────────────────────────────────────────────────────────────────────┤
│ HYBRID          │ Uses both predefined and dynamic profiles            │
│                 │ Transitional mode after cold-start                   │
├─────────────────────────────────────────────────────────────────────────┤
│ DYNAMIC_ONLY    │ Uses only dynamically generated profiles             │
│                 │ For users with rich behavioral history               │
├─────────────────────────────────────────────────────────────────────────┤
│ DRIFT_FALLBACK  │ Fallback mode when behavior drift detected           │
│                 │ Re-evaluates using recent behavior batch             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Architecture

### 3.1 Layered Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI Routers)                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │
│  │ Profile Routes  │ │  User Routes    │ │ Ranking Routes  │          │
│  │ /api/predefined │ │  /api/users     │ │ /api/ranking-   │          │
│  │    -profiles    │ │                 │ │     states      │          │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘          │
│  ┌─────────────────┐                                                   │
│  │ Domain Routes   │                                                   │
│  │ /api/domain-    │                                                   │
│  │    expertise    │                                                   │
│  └─────────────────┘                                                   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Orchestration Layer                                 │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                   IntakeOrchestrator                            │   │
│  │  - Routes requests to ProfileAssigner                          │   │
│  │  - Publishes events via ProfilePublisher                       │   │
│  │  - Handles both sync and async processing                      │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Service Layer                                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │
│  │ ProfileAssigner │ │ ProfileMatcher  │ │ RankingState    │          │
│  │   Orchestrates  │ │  Scores/ranks   │ │   Service       │          │
│  │   assignment    │ │    profiles     │ │ Tracks stats    │          │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │
│  │ Complexity      │ │ Consistency     │ │ DomainExpertise │          │
│  │  Calculator     │ │  Calculator     │ │    Service      │          │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘          │
│  ┌─────────────────┐                                                   │
│  │  UserService    │                                                   │
│  │  Auth & CRUD    │                                                   │
│  └─────────────────┘                                                   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Repository Layer                                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐          │
│  │ PredefinedProf  │ │  UserRepo       │ │ RankingState    │          │
│  │    ileRepo      │ │                 │ │     Repo        │          │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘          │
│  ┌─────────────────┐                                                   │
│  │ UserDomainState │                                                   │
│  │      Repo       │                                                   │
│  └─────────────────┘                                                   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Database Layer                                     │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL (Supabase)                        │   │
│  │  - 18+ tables for profiles, users, rankings, expertise         │   │
│  │  - SQLAlchemy ORM with eager loading                           │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Event-Driven Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Event-Driven Architecture                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────┐        drift.events       ┌─────────────────┐       │
│   │   Drift     │ ─────────────────────────▶│ DriftEvent      │       │
│   │  Detection  │        Redis Stream       │   Consumer      │       │
│   │  Service    │                           └─────────────────┘       │
│   └─────────────┘                                    │                 │
│                                                      ▼                 │
│                                            ┌─────────────────┐        │
│                                            │ DriftEvent      │        │
│                                            │   Handler       │        │
│                                            └─────────────────┘        │
│                                                      │                 │
│                                                      ▼                 │
│                                            ┌─────────────────┐        │
│                                            │   Intake        │        │
│                                            │  Orchestrator   │        │
│                                            └─────────────────┘        │
│                                                      │                 │
│                                                      ▼                 │
│   ┌─────────────┐       profile.assigned   ┌─────────────────┐       │
│   │    LLM      │ ◀────────────────────────│   Profile       │       │
│   │Orchestration│        Redis Stream      │   Publisher     │       │
│   │   Service   │                          └─────────────────┘       │
│   └─────────────┘                                                     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

### 4.1 Core Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | FastAPI | 0.110.0 | Async REST API |
| **Server** | Uvicorn | 0.27.1 | ASGI server |
| **ORM** | SQLAlchemy | 2.0.27 | Database abstraction |
| **Database** | PostgreSQL | - | Primary data store |
| **Validation** | Pydantic | 2.5.0 | Data validation & DTOs |
| **Message Queue** | Redis | 5.0.1 | Stream messaging |
| **HTTP Client** | HTTPX | 0.27.0 | Async HTTP requests |
| **Auth** | PyJWT | 2.8.0 | JWT tokens |
| **Password** | bcrypt | 4.1.2 | Password hashing |
| **Python** | Python | 3.11 | Runtime |

### 4.2 Database Drivers
- `psycopg2-binary` (v2.9.9) - Sync PostgreSQL driver
- `psycopg[binary]` (v3.3.2) - Modern PostgreSQL driver
- `asyncpg` (v0.29.0) - Async PostgreSQL driver

### 4.3 Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose
- **Redis**: redis:7-alpine

---

## 5. Data Models

### 5.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CORE ENTITIES                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌───────────────┐     1:N     ┌─────────────────────────────┐
│     User      │ ◀──────────│ UserProfileRankingState     │
├───────────────┤             ├─────────────────────────────┤
│ user_id (PK)  │             │ id (PK)                     │
│ username      │             │ user_id (FK)                │
│ email         │             │ profile_id (FK)             │
│ password_hash │             │ cumulative_score            │
│ provider      │             │ average_score               │
│ provider_id   │             │ max_score                   │
│ profile_mode  │             │ observation_count           │
│ predefined_   │             │ last_rank                   │
│   profile_id  │             │ consecutive_top_count       │
│ dynamic_      │             │ consecutive_drop_count      │
│   profile_id  │             │ updated_at                  │
│ fallback_     │             └─────────────────────────────┘
│   profile_id  │
│ created_at    │
│ last_active_at│
│ status        │
└───────────────┘
       │
       │ 1:N
       ▼
┌─────────────────┐
│ UserDomainState │
├─────────────────┤
│ user_id (PK,FK) │
│ interest_id     │
│   (PK, FK)      │
│ expertise_      │
│   level_id (FK) │
│ confidence_score│
│ last_updated    │
└─────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         PROFILE ENTITIES                                │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │     Profile     │
                              ├─────────────────┤
                              │ profile_id (PK) │
                              │ profile_name    │
                              │ description     │
                              │ context_        │
                              │   statement     │
                              │ assumptions     │
                              │ ai_guidance     │
                              │ preferred_      │
                              │   response_style│
                              │ context_        │
                              │   injection_    │
                              │   prompt        │
                              │ created_at      │
                              └─────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐    ┌─────────────────┐
    │  ProfileIntent  │     │ ProfileInterest │    │ProfileBehavior  │
    ├─────────────────┤     ├─────────────────┤    │     Level       │
    │ profile_id (FK) │     │ profile_id (FK) │    ├─────────────────┤
    │ intent_id (FK)  │     │ interest_id(FK) │    │ profile_id (FK) │
    │ is_primary      │     │ weight          │    │ behavior_       │
    │ weight          │     └─────────────────┘    │   level_id (FK) │
    └─────────────────┘              │              └─────────────────┘
              │                      │                       │
              ▼                      ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐    ┌─────────────────┐
    │     Intent      │     │  InterestArea   │    │  BehaviorLevel  │
    ├─────────────────┤     ├─────────────────┤    ├─────────────────┤
    │ intent_id (PK)  │     │ interest_id (PK)│    │ behavior_       │
    │ intent_name     │     │ interest_name   │    │   level_id (PK) │
    │ description     │     │ description     │    │ level_name      │
    └─────────────────┘     └─────────────────┘    │ description     │
                                                   └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       ADDITIONAL ENTITIES                               │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐  ┌────────────────────────┐
│   BehaviorSignal       │  │    OutputPreference    │
├────────────────────────┤  ├────────────────────────┤
│ signal_id (PK)         │  │ output_pref_id (PK)    │
│ signal_name            │  │ format_name            │
│ description            │  │ description            │
└────────────────────────┘  └────────────────────────┘

┌────────────────────────┐  ┌────────────────────────┐
│   InteractionTone      │  │  DomainExpertiseLevel  │
├────────────────────────┤  ├────────────────────────┤
│ tone_id (PK)           │  │ expertise_level_id(PK) │
│ tone_name              │  │ level_name             │
│ description            │  │ description            │
└────────────────────────┘  └────────────────────────┘

┌────────────────────────┐  ┌────────────────────────┐
│ StandardMatchingFactor │  │ColdStartMatchingFactor │
├────────────────────────┤  ├────────────────────────┤
│ factor_id (PK)         │  │ factor_id (PK)         │
│ factor_name            │  │ factor_name            │
│ weight                 │  │ weight                 │
└────────────────────────┘  └────────────────────────┘
```

### 5.2 Reference Data (Seed Values)

#### Intents
| ID | Name | Description |
|----|------|-------------|
| 1 | LEARNING | Cognitive support, gaining knowledge |
| 2 | TASK_COMPLETION | Completing tasks efficiently |
| 3 | PROBLEM_SOLVING | Solving technical problems |
| 4 | EXPLORATION | Generating creative ideas |
| 5 | GUIDANCE | Seeking personal advice |
| 6 | ENGAGEMENT | Entertainment, casual use |

#### Behavior Levels
| ID | Name | Description |
|----|------|-------------|
| 1 | BASIC | Simple prompts, low iteration |
| 2 | INTERMEDIATE | Moderate complexity, task-based |
| 3 | ADVANCED | Structured prompts, iterative workflows |

#### Interest Areas
| ID | Name | Description |
|----|------|-------------|
| 1 | AI | Artificial Intelligence |
| 2 | DATA_SCIENCE | Data analysis and science |
| 3 | WRITING | Drafting, editing, summarizing |
| 4 | PROGRAMMING | Coding, debugging, algorithms |
| 5 | CREATIVE | Stories, scripts, ideation |
| 6 | HEALTH | Well-being, diet, exercise |
| 7 | PERSONAL_GROWTH | Career, life guidance |
| 8 | ENTERTAINMENT | Games, quizzes, leisure |

#### Behavior Signals
| ID | Name | Description |
|----|------|-------------|
| 1 | DEEP_REASONING | Curiosity-driven queries |
| 2 | GOAL_ORIENTED | Command-based prompts |
| 3 | MULTI_STEP | Multi-constraint prompts |
| 4 | ITERATIVE | Repeated refinements |
| 5 | CASUAL | Short, entertainment-focused |

---

## 6. API Endpoints

### 6.1 Profile Assignment Routes (`/api/predefined-profiles`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Get all profiles with full context |
| `GET` | `/{profile_id}` | Get single profile by ID |
| `GET` | `/user/{user_id}` | Get assignment status (no new scoring) |
| `POST` | `/assign-profile` | **Async** - Assign profile with event publishing |
| `POST` | `/assign-profile/sync` | **Sync** - Legacy backward compatibility |

#### Request/Response Examples

**POST /api/predefined-profiles/assign-profile**
```json
// Request
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "mode": "COLD_START",
  "extracted_behavior": {
    "intents": {"LEARNING": 0.8, "PROBLEM_SOLVING": 0.2},
    "interests": {"PROGRAMMING": 0.7, "AI": 0.5},
    "behavior_level": "INTERMEDIATE",
    "signals": {"DEEP_REASONING": 0.6, "ITERATIVE": 0.4},
    "complexity": 0.65,
    "consistency": 0.72
  },
  "trigger_event_id": null
}

// Response
{
  "status": "ASSIGNED",
  "confidence_level": "HIGH",
  "user_mode": "COLD_START",
  "prompt_count": 5,
  "assigned_profile_id": "P3",
  "aggregated_rankings": [
    {
      "profile_code": "P3",
      "average_score": 0.7234,
      "cumulative_score": 3.617,
      "max_score": 0.78,
      "observations": 5,
      "last_rank": 1,
      "consecutive_top_count": 3,
      "consecutive_drop_count": 0,
      "updated_at": "2026-02-26T10:30:00Z"
    }
    // ... more profiles
  ]
}
```

### 6.2 User Routes (`/api/users`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/register` | Register new user |
| `POST` | `/login` | Authenticate user |
| `POST` | `/oauth/login` | OAuth login/register |
| `POST` | `/oauth/github/callback` | GitHub OAuth callback |
| `GET` | `/` | List all users (paginated) |
| `GET` | `/{user_id}` | Get user by ID |
| `PUT` | `/{user_id}` | Update user |
| `DELETE` | `/{user_id}` | Delete user |
| `PUT` | `/{user_id}/activate` | Activate user |
| `PUT` | `/{user_id}/suspend` | Suspend user |
| `PUT` | `/{user_id}/fallback` | Manage fallback profile |

### 6.3 Ranking State Routes (`/api/ranking-states`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create ranking state |
| `GET` | `/{state_id}` | Get by ID |
| `GET` | `/user/{user_id}/profile/{profile_id}` | Get by user-profile pair |
| `GET` | `/user/{user_id}` | Get all for user |
| `PUT` | `/{state_id}` | Update ranking state |
| `DELETE` | `/{state_id}` | Delete ranking state |
| `POST` | `/{state_id}/observe` | Add score observation |
| `GET` | `/user/{user_id}/top` | Get top profiles for user |
| `GET` | `/user/{user_id}/stats` | Get user statistics summary |
| `GET` | `/user/{user_id}/drift` | Detect behavioral drift |
| `GET` | `/user/{user_id}/history` | Get ranking history |
| `POST` | `/batch/update` | Batch update rankings |
| `GET` | `/analytics/profile/{profile_id}/distribution` | Score distribution |
| `GET` | `/analytics/top-converters` | Top converting profiles |
| `DELETE` | `/user/{user_id}` | Delete all user states |

### 6.4 Domain Expertise Routes (`/api/domain-expertise`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/update` | Update domain expertise |
| `GET` | `/user/{user_id}/domain/{interest_id}` | Get specific domain state |
| `GET` | `/user/{user_id}` | Get all domain states |
| `POST` | `/initialize` | Initialize cold-start state |
| `POST` | `/decay` | Apply expertise decay |

---

## 7. Core Services

### 7.1 ProfileAssigner

**Purpose**: Orchestrates the complete profile assignment workflow.

**Key Methods**:
```python
class ProfileAssigner:
    def get_assignment_status(user_id: str) -> dict
    def should_assign_profile(user_id, user_mode, ...) -> Tuple[bool, str, float]
    def assign(extracted_behavior, user_id) -> dict
```

**Assignment Flow**:
1. Fetch user and verify user mode
2. Validate behavior format for mode
3. Load profiles and matching factors
4. Process behaviors through ProfileMatcher
5. Update ranking states
6. Determine if assignment criteria met
7. Persist assignment if applicable

### 7.2 ProfileMatcher

**Purpose**: Scores and ranks profiles against behavioral data.

**Scoring Formula**:
```
Profile Score = (INTENT × intent_score) +
                (INTEREST × interest_score) +
                (COMPLEXITY × complexity) +
                (STYLE × signal_score) +
                (CONSISTENCY × consistency)
```

**Weight Configurations**:

| Factor | Standard Mode | Cold-Start Mode |
|--------|---------------|-----------------|
| INTENT | 0.35 | 0.60 |
| INTEREST | 0.25 | 0.40 |
| COMPLEXITY | 0.15 | 0.00 |
| STYLE | 0.15 | 0.00 |
| CONSISTENCY | 0.10 | 0.00 |

### 7.3 ComplexityCalculator

**Purpose**: Computes task complexity (0-1) from prompt analysis.

**Complexity Factors**:
| Factor | Max Score | Per-Keyword Score |
|--------|-----------|-------------------|
| Length | 0.20 | Scaled 0.05-0.20 |
| Constraints | 0.70 | 0.23 |
| Multi-step | 0.60 | 0.20 |
| Structure | 0.12 | 0.04 |
| Examples | 0.08 | 0.027 |

**Keyword Categories**:
- **Constraints**: must, should, require, restrict, exactly...
- **Multi-step**: first, then, next, finally, step, sequence...
- **Structure**: format, template, list, table, json, code...
- **Examples**: example, like, such as, demonstrate...

### 7.4 ConsistencyCalculator

**Purpose**: Computes behavioral consistency (0-1) across session history.

**Consistency Components**:
| Component | Weight |
|-----------|--------|
| Intent Repetition | 0.40 |
| Domain Stability | 0.40 |
| Temporal Consistency | 0.20 |
| Signal Consistency | 0.10 (optional) |

### 7.5 DomainExpertiseService

**Purpose**: Tracks user expertise levels per interest domain.

**Expertise Levels**:
| Level | Confidence Range |
|-------|------------------|
| BEGINNER | 0.00 - 0.39 |
| INTERMEDIATE | 0.40 - 0.74 |
| ADVANCED | 0.75 - 1.00 |

**Signal Weights**:
| Signal | Confidence Delta |
|--------|------------------|
| Correct Terminology | +0.10 |
| Multi-step Prompt | +0.15 |
| Iterative Refinement | +0.20 |
| Explicit Advanced Request | +0.25 |
| Beginner Question | -0.10 |
| Definition Request | -0.10 |

---

## 8. Profile Matching Algorithm

### 8.1 Complete Algorithm Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PROFILE MATCHING ALGORITHM                         │
└─────────────────────────────────────────────────────────────────────────┘

Input: extracted_behavior = {
    intents: {INTENT_NAME: score, ...},
    interests: {INTEREST_NAME: score, ...},
    behavior_level: "BASIC" | "INTERMEDIATE" | "ADVANCED",
    signals: {SIGNAL_NAME: score, ...},
    complexity: 0.0 - 1.0,
    consistency: 0.0 - 1.0
}

┌─────────────────────────────────────────────────────────────────────────┐
│ Step 1: Select Weights Based on Mode                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   if is_cold_start:                                                    │
│       weights = cold_start_weights  # Intent=0.60, Interest=0.40      │
│   else:                                                                │
│       weights = standard_weights    # Full 5-factor weights           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 2: Calculate Component Scores for Each Profile                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   For each profile P in profiles:                                      │
│                                                                         │
│   intent_score = Σ(user_intent[i] × profile_intent_weight[i])         │
│   interest_score = Σ(user_interest[i] × profile_interest_weight[i])   │
│   behavior_score = 1.0 if level matches, else 0.5                     │
│   signal_score = Σ(user_signal[i] × profile_signal_weight[i])         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 3: Calculate Weighted Raw Score                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   raw_score[P] = (weights.INTENT × intent_score) +                     │
│                  (weights.INTEREST × interest_score) +                 │
│                  (weights.COMPLEXITY × complexity) +                   │
│                  (weights.STYLE × signal_score) +                      │
│                  (weights.CONSISTENCY × consistency)                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 4: Normalize Scores                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   total = Σ(raw_score[P])                                              │
│   For each profile P:                                                  │
│       normalized_score[P] = raw_score[P] / total                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 5: Rank Profiles and Return Results                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ranked_profiles = sort_descending(normalized_score)                  │
│                                                                         │
│   Return {                                                             │
│       ranked_profiles: [(profile_id, score), ...],                    │
│       best_profile: ranked_profiles[0].profile_id,                    │
│       confidence: ranked_profiles[0].score                            │
│   }                                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Assignment Decision Logic

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ASSIGNMENT DECISION LOGIC                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ COLD_START Mode Assignment Criteria                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ASSIGN if ALL conditions met:                                        │
│   ✓ observation_count >= MIN_PROMPTS_COLD_START (5)                   │
│   ✓ average_score >= COLD_START_THRESHOLD (0.60)                      │
│   ✓ consecutive_top_count >= 2                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ DRIFT_FALLBACK Mode Assignment Criteria                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ASSIGN if ALL conditions met:                                        │
│   ✓ average_score >= FALLBACK_THRESHOLD (0.70)                        │
│   ✓ consecutive_top_count >= 3                                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ Confidence Level Determination                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   HIGH:   average_score >= 0.70                                        │
│   MEDIUM: average_score >= 0.50 and < 0.70                            │
│   LOW:    average_score < 0.50                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Event-Driven Architecture

### 9.1 Redis Streams

#### Stream: `drift.events` (Consumer)
**Purpose**: Receives behavioral drift notifications from Drift Detection Service.

**Message Schema**:
```json
{
  "drift_event_id": "drift-evt-abc123",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "severity": "STRONG"  // WEAK | MODERATE | STRONG
}
```

**Processing Logic**:
- Only `MODERATE` and `STRONG` severities trigger action
- Fetches recent behaviors from Behavior Resolution Service
- Processes through IntakeOrchestrator in DRIFT_FALLBACK mode

#### Stream: `profile.assigned` (Publisher)
**Purpose**: Notifies downstream services of profile assignments.

**Message Schema**:
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

### 9.2 Consumer Group Configuration
- **Group Name**: `predefined-profile-service`
- **Consumer Name**: `profile-worker-1`
- **Block Time**: 5000ms
- **Max Messages**: 10 per read

---

## 10. Domain Expertise Tracking

### 10.1 Expertise Update Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DOMAIN EXPERTISE UPDATE FLOW                        │
└─────────────────────────────────────────────────────────────────────────┘

           User Prompt
               │
               ▼
    ┌──────────────────────┐
    │ should_update_       │──────▶ NO: Skip (greeting, too short)
    │ expertise(prompt)    │
    └──────────────────────┘
               │ YES
               ▼
    ┌──────────────────────┐
    │ detect_expertise_    │
    │ signals(prompt)      │
    └──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Signals Detected:    │
    │ • BEGINNER_QUESTION  │
    │ • CORRECT_TERMINOLOGY│
    │ • MULTI_STEP         │
    │ • ITERATIVE          │
    │ • ASSUME_KNOWLEDGE   │
    │ • EXPLICIT_ADVANCED  │
    └──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ calculate_new_       │
    │ confidence()         │
    │                      │
    │ new = old + Σsignals │
    │ clamp(0.0, 1.0)     │
    └──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ determine_expertise_ │
    │ level(confidence)    │
    │                      │
    │ 0.00-0.39: BEGINNER  │
    │ 0.40-0.74: INTERMED. │
    │ 0.75-1.00: ADVANCED  │
    └──────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Persist to          │
    │ user_domain_state   │
    └──────────────────────┘
```

### 10.2 Keyword Detection

**Beginner Indicators**:
- "what is", "what are", "define", "explain"
- "how to", "tutorial", "basics", "introduction"
- "beginner", "step by step", "simple", "easy way"

**Advanced Indicators**:
- "optimize", "performance", "edge case"
- "scalability", "architecture", "best practice"
- "assume I know", "skip basics", "advanced"
- "deep dive", "implementation details"

---

## 11. Configuration & Constants

### 11.1 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `JWT_SECRET_KEY` | JWT signing key | (development default) |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | 30 |
| `ENVIRONMENT` | Environment name | `development` |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `BEHAVIOR_RESOLUTION_BASE_URL` | External service URL | `http://localhost:8001` |
| `DRIFT_FALLBACK_BEHAVIOR_LIMIT` | Behaviors to fetch for fallback | 10 |

### 11.2 Assignment Thresholds

| Threshold | Value | Description |
|-----------|-------|-------------|
| `MIN_PROMPTS_COLD_START` | 3 | Minimum prompts before cold-start check |
| `MIN_PROMPTS_FALLBACK` | 5 | Minimum prompts for profile assignment |
| `COLD_START_THRESHOLD` | 0.60 | Score threshold for cold-start |
| `FALLBACK_THRESHOLD` | 0.70 | Score threshold for fallback |
| `HIGH_CONFIDENCE_THRESHOLD` | 0.70 | High confidence classification |
| `COLD_START_CONSECUTIVE_TOP` | 2 | Required consecutive tops (cold-start) |
| `FALLBACK_CONSECUTIVE_TOP` | 3 | Required consecutive tops (fallback) |

---

## 12. Deployment

### 12.1 Dockerfile Analysis

```dockerfile
# Multi-stage build for optimized production image

Stage 1: Builder
├── Base: python:3.11-slim
├── Install build dependencies (build-essential, libpq-dev)
└── Install Python packages from requirements.txt

Stage 2: Production
├── Base: python:3.11-slim
├── Install runtime dependencies only (libpq5)
├── Create non-root user (appuser)
├── Copy installed packages from builder
├── Copy application code
├── Switch to non-root user
├── Expose port 8000
├── Health check every 30s
└── CMD: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 12.2 Docker Compose Services

| Service | Image | Internal Port | External Port |
|---------|-------|---------------|---------------|
| `app` | Built from Dockerfile | 8000 | 8002 |
| `redis` | redis:7-alpine | 6379 | 6380 |
| `redis-commander` | redis-commander | 8081 | 8083 |

### 12.3 Networks & Volumes

**Network**: `profile-network` (bridge mode)

**Volumes**:
- `redis_data` - Persists Redis AOF data

---

## 13. Integration Points

### 13.1 External Service Dependencies

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL INTEGRATIONS                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐                    ┌─────────────────┐
│   Behavior      │  GET /api/         │   Predefined    │
│   Resolution    │  behaviors/{id}/   │     Profile     │
│   Service       │◀─────────────────▶│    Service      │
│  (Port 8001)    │     recent         │  (Port 8002)    │
└─────────────────┘                    └─────────────────┘
                                              ▲
                                              │
                    drift.events             │
┌─────────────────┐    (Redis)      ┌───────┴───────┐
│     Drift       │────────────────▶│ DriftEvent    │
│   Detection     │                 │   Consumer    │
│   Service       │                 └───────────────┘
└─────────────────┘

                    profile.assigned
┌─────────────────┐    (Redis)      ┌───────────────┐
│     LLM         │◀────────────────│   Profile     │
│  Orchestration  │                 │   Publisher   │
│   Service       │                 └───────────────┘
└─────────────────┘
```

### 13.2 API Contracts

**Behavior Resolution API Call**:
```
GET {BEHAVIOR_RESOLUTION_BASE_URL}/api/behaviors/{user_id}/recent?limit=10

Response:
{
  "behaviors": [
    {
      "intents": {"LEARNING": 0.8},
      "interests": {"PROGRAMMING": 0.7},
      "behavior_level": "INTERMEDIATE",
      "signals": {"DETAILED_EXPLANATION": 0.5},
      "complexity": 0.65,
      "consistency": 0.72
    }
  ]
}
```

---

## 14. Data Flow Diagrams

### 14.1 Cold-Start Assignment Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COLD-START ASSIGNMENT FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

    User                   Behavior               Predefined           LLM
  Interaction              Resolution              Profile         Orchestration
      │                     Service                Service            Service
      │                        │                      │                  │
      │  1. User prompt        │                      │                  │
      │───────────────────────▶│                      │                  │
      │                        │                      │                  │
      │                        │  2. POST /assign-    │                  │
      │                        │     profile          │                  │
      │                        │─────────────────────▶│                  │
      │                        │                      │                  │
      │                        │                      │ 3. Profile       │
      │                        │                      │    Matching      │
      │                        │                      │    Algorithm     │
      │                        │                      │                  │
      │                        │                      │ 4. Update        │
      │                        │                      │    Ranking       │
      │                        │                      │    State         │
      │                        │                      │                  │
      │                        │                      │ 5. Check         │
      │                        │                      │    Assignment    │
      │                        │                      │    Criteria      │
      │                        │                      │                  │
      │                        │  6. Response         │                  │
      │                        │◀─────────────────────│                  │
      │                        │                      │                  │
      │                        │                      │ 7. publish       │
      │                        │                      │    profile.      │
      │                        │                      │    assigned      │
      │                        │                      │─────────────────▶│
      │                        │                      │  (if assigned)   │
      │                        │                      │                  │
```

### 14.2 Drift Fallback Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      DRIFT FALLBACK FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

    Drift              Predefined              Behavior              LLM
  Detection             Profile              Resolution         Orchestration
   Service              Service                Service             Service
      │                    │                      │                   │
      │ 1. drift.events    │                      │                   │
      │   (MODERATE/STRONG)│                      │                   │
      │───────────────────▶│                      │                   │
      │                    │                      │                   │
      │                    │ 2. GET /behaviors/   │                   │
      │                    │    {user_id}/recent  │                   │
      │                    │─────────────────────▶│                   │
      │                    │                      │                   │
      │                    │ 3. [behaviors]       │                   │
      │                    │◀─────────────────────│                   │
      │                    │                      │                   │
      │                    │ 4. Process batch     │                   │
      │                    │    of behaviors      │                   │
      │                    │    (DRIFT_FALLBACK)  │                   │
      │                    │                      │                   │
      │                    │ 5. Update rankings   │                   │
      │                    │    for each behavior │                   │
      │                    │                      │                   │
      │                    │ 6. Check reassignment│                   │
      │                    │    criteria          │                   │
      │                    │                      │                   │
      │                    │ 7. profile.assigned  │                   │
      │                    │    (if reassigned)   │                   │
      │                    │──────────────────────────────────────────▶│
      │                    │                      │                   │
```

---

## 15. Security Considerations

### 15.1 Authentication & Authorization
- **JWT Tokens**: Used for API authentication
- **OAuth Support**: Google and GitHub providers
- **Password Hashing**: bcrypt with automatic salting
- **Non-root Container**: Application runs as `appuser`

### 15.2 Security Best Practices Implemented
- ✅ Environment-based configuration (no hardcoded secrets)
- ✅ Input validation via Pydantic schemas
- ✅ SQL injection prevention via SQLAlchemy ORM
- ✅ CORS configuration (configurable origins)
- ✅ Health check endpoints for monitoring
- ✅ Non-root Docker user

### 15.3 Areas for Enhancement
- ⚠️ Rate limiting not implemented
- ⚠️ API key authentication for service-to-service calls
- ⚠️ Audit logging for sensitive operations

---

## 16. Performance Considerations

### 16.1 Database Optimizations
- **Eager Loading**: `joinedload` prevents N+1 queries
- **Indexes**: Composite indexes on frequently queried columns
- **Connection Pooling**: SQLAlchemy engine with configurable pool

### 16.2 Caching Opportunities
- Profile configurations (rarely change)
- Matching factors (static after initialization)
- User expertise levels (per-session caching)

### 16.3 Async Processing
- Redis Stream consumer runs as background asyncio task
- Event publishing is asynchronous
- Database operations support both sync and async modes

### 16.4 Scaling Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| API Server | Horizontal (multiple uvicorn workers) |
| Redis Consumer | Horizontal (consumer groups) |
| Database | Vertical + Read replicas |
| Redis | Redis Cluster for high availability |

---

## Appendix A: File Structure Summary

```
predefined_profile_assignment/
├── docker-compose.yml          # Container orchestration
├── Dockerfile                  # Multi-stage build
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── SYSTEM_ANALYSIS.md          # This document
└── app/
    ├── main.py                 # FastAPI application entry
    ├── __init__.py
    │
    ├── api/                    # REST API endpoints
    │   ├── predefined_profile_routes.py
    │   ├── user_routes.py
    │   ├── ranking_state_routes.py
    │   └── domain_expertise_routes.py
    │
    ├── consumer/               # Redis Stream consumers
    │   ├── redis_consumer.py   # DriftEventConsumer
    │   └── drift_event_handler.py
    │
    ├── publisher/              # Redis Stream publishers
    │   └── profile_publisher.py
    │
    ├── core/                   # Core utilities
    │   ├── config.py           # Settings management
    │   ├── constants.py        # Application constants
    │   ├── database.py         # DB connection management
    │   ├── db_init.py          # Schema initialization
    │   ├── initial_seed.sql    # Reference data
    │   ├── intake_orchestrator.py
    │   ├── jwt_utils.py        # JWT handling
    │   ├── logging_config.py
    │   ├── utils.py
    │   └── exceptions.py
    │
    ├── models/                 # SQLAlchemy ORM models
    │   ├── user.py
    │   ├── profile.py
    │   ├── user_profile_ranking_state.py
    │   ├── user_domain_state.py
    │   ├── intent.py
    │   ├── interest_area.py
    │   ├── behavior_level.py
    │   ├── behavior_signal.py
    │   ├── standard_matching_factor.py
    │   ├── cold_start_matching_factor.py
    │   ├── domain_expertise_level.py
    │   ├── output_preference.py
    │   ├── interaction_tone.py
    │   ├── profile_intent.py
    │   ├── profile_interest.py
    │   ├── profile_behavior_level.py
    │   ├── profile_behavior_signal.py
    │   ├── profile_output_preference.py
    │   └── profile_tone.py
    │
    ├── repositories/           # Data access layer
    │   ├── predefined_profile_repo.py
    │   ├── user_repo.py
    │   ├── ranking_state_repo.py
    │   └── user_domain_state_repo.py
    │
    ├── schemas/                # Pydantic DTOs
    │   ├── predefined_profile_dto.py
    │   ├── user_dto.py
    │   ├── ranking_state_dto.py
    │   └── domain_expertise_dto.py
    │
    └── services/               # Business logic
        ├── profile_assigner.py
        ├── profile_matcher.py
        ├── complexity_calculator.py
        ├── consistency_calculator.py
        ├── ranking_state_service.py
        ├── domain_expertise_service.py
        └── user_service.py
```

---

## Appendix B: API Quick Reference

### Profile Assignment
```bash
# Assign profile (async)
POST /api/predefined-profiles/assign-profile

# Get assignment status
GET /api/predefined-profiles/user/{user_id}

# Get all profiles
GET /api/predefined-profiles/
```

### User Management
```bash
# Register
POST /api/users/register

# Login
POST /api/users/login

# OAuth Login
POST /api/users/oauth/login
```

### Ranking States
```bash
# Get user's top profiles
GET /api/ranking-states/user/{user_id}/top

# Detect drift
GET /api/ranking-states/user/{user_id}/drift
```

### Domain Expertise
```bash
# Update expertise
POST /api/domain-expertise/update

# Get user's expertise
GET /api/domain-expertise/user/{user_id}
```

---

*Document Generated: February 26, 2026*
*Version: 1.0.0*
