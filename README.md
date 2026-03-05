# Predefined Profile Assignment Service

An intelligent user profiling and behavioral analysis system that automatically assigns users to predefined behavioral profiles based on their interactions with AI/LLM applications. The service uses multi-factor scoring algorithms to analyze user behavior patterns and adapt to behavioral changes over time.

## 🎯 Overview

This FastAPI-based service provides an AI-powered profile assignment system designed for adaptive user profiling in LLM applications. It tracks user interactions, analyzes behavioral patterns (intents, interests, complexity, and consistency), and automatically classifies users into one of six predefined behavioral profiles.

### Key Features

- **🤖 Intelligent Profile Matching**: Weighted multi-factor scoring algorithm matching users to 6 predefined behavioral profiles
- **🚀 Cold-Start Support**: Simplified matching for new users with limited interaction history
- **📊 Drift Detection**: Identifies and responds to behavioral changes with automatic reassignment
- **🎓 Domain Expertise Tracking**: Monitors user expertise levels across different interest domains
- **📈 Temporal Ranking**: Maintains historical profile ranking evolution for trend analysis
- **� Adaptive Profiling**: Multiple user modes (COLD_START, HYBRID, DYNAMIC_ONLY, DRIFT_FALLBACK)
- **🌐 Microservice Architecture**: Integrates with external User Management Service for user data

## 📋 Predefined Profiles

| Profile | Name | Primary Intent | Description |
|---------|------|----------------|-------------|
| **P1** | Knowledge Seeker | LEARNING | Learns concepts and seeks explanations |
| **P2** | Productivity Professional | TASK_COMPLETION | Uses LLMs for efficient task completion |
| **P3** | Technical Problem Solver | PROBLEM_SOLVING | Solves technical and engineering problems |
| **P4** | Creative Generator | EXPLORATION | Generates creative ideas and content |
| **P5** | Lifestyle Advisor Seeker | GUIDANCE | Seeks personal and lifestyle guidance |
| **P6** | Casual Explorer | ENGAGEMENT | Uses LLMs casually for curiosity or fun |

## 🏗️ Architecture

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│           API Layer (FastAPI)               │
│  - Profile Assignment Routes                │
│  - Ranking State Routes                     │
│  - Domain Expertise Routes                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Service Layer                       │
│  - Profile Assigner                         │
│  - Profile Matcher                          │
│  - User Management Client (HTTP)            │
│  - Complexity Calculator                    │
│  - Consistency Calculator                   │
│  - Domain Expertise Service                 │
│  - Ranking State Service                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      Repository Layer                       │
│  - Predefined Profile Repository            │
│  - Ranking State Repository                 │
│  - User Domain State Repository             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      Database Layer (PostgreSQL)            │
│  - SQLAlchemy ORM Models                    │
└─────────────────────────────────────────────┘
                    ↓
          External Dependencies
┌─────────────────────────────────────────────┐
│    User Management Service (HTTP API)       │
│  - User profile data and mode tracking      │
└─────────────────────────────────────────────┘
```

### Project Structure

```
predefined_profile_assignment/
├── app/
│   ├── api/                    # RESTful API route handlers
│   │   ├── predefined_profile_routes.py
│   │   ├── ranking_state_routes.py
│   │   └── domain_expertise_routes.py
│   ├── core/                   # Core configuration & utilities
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── constants.py
│   │   └── db_init.py
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── profile.py
│   │   ├── user_profile_ranking_state.py
│   │   ├── user_domain_state.py
│   │   └── ...
│   ├── repositories/           # Data access layer
│   │   ├── predefined_profile_repo.py
│   │   └── ranking_state_repo.py
│   ├── schemas/               # Pydantic DTOs
│   │   ├── predefined_profile_dto.py
│   │   └── ranking_state_dto.py
│   ├── services/              # Business logic layer
│   │   ├── profile_assigner.py
│   │   ├── profile_matcher.py
│   │   ├── user_management_client.py
│   │   ├── complexity_calculator.py
│   │   └── consistency_calculator.py
│   └── main.py                # Application entry point
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd predefined_profile_assignment
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Unix/MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   # Database Configuration
   DATABASE_URL=postgresql://username:password@localhost:5432/profile_db
   
   # Application Settings
   APP_NAME=Predefined Profile Assignment Service
   ENVIRONMENT=development
   DEBUG=False
   LOG_LEVEL=INFO
   
   # Redis Configuration (Docker uses shared-redis:6379/0)
   REDIS_URL=redis://localhost:6379/0
   
   # External Services
   BEHAVIOR_RESOLUTION_BASE_URL=http://localhost:8001
   USER_MANAGEMENT_SERVICE_URL=http://localhost:8080
   DRIFT_FALLBACK_BEHAVIOR_LIMIT=10
   
   # Profile Assignment Algorithm Parameters
   MIN_PROMPTS_COLD_START=3
   MIN_PROMPTS_FALLBACK=5
   COLD_START_THRESHOLD=0.60
   FALLBACK_THRESHOLD=0.70
   HIGH_CONFIDENCE_THRESHOLD=0.70
   ```

5. **Set up the database**
   
   The application will automatically initialize the database schema and seed reference data on startup.

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

7. **Access API documentation**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## 📚 API Endpoints

### Health Check
- **GET** `/` - Service health check
- **GET** `/health` - Detailed health check with component status

### Profile Assignment
- **GET** `/api/predefined-profiles/user/{user_id}` - Get profile assignment status
- **POST** `/api/predefined-profiles/assign-profile` - Assign profile based on behavior data

### Ranking State Management
- **POST** `/api/ranking-states/` - Create ranking state
- **GET** `/api/ranking-states/{state_id}` - Get ranking state
- **GET** `/api/ranking-states/user/{user_id}` - Get all states for user
- **GET** `/api/ranking-states/user/{user_id}/profile/{profile_id}` - Get specific user-profile state
- **PUT** `/api/ranking-states/{state_id}` - Update ranking state
- **DELETE** `/api/ranking-states/{state_id}` - Delete ranking state
- **POST** `/api/ranking-states/{state_id}/update-score` - Add score observation
- **GET** `/api/ranking-states/user/{user_id}/top-profiles` - Get top-ranked profiles
- **GET** `/api/ranking-states/user/{user_id}/stats` - Get ranking statistics
- **GET** `/api/ranking-states/user/{user_id}/detect-drift` - Detect behavioral drift

### Domain Expertise
- **POST** `/api/domain-expertise/` - Create domain expertise state
- **GET** `/api/domain-expertise/{user_id}/{interest_id}` - Get expertise for domain
- **GET** `/api/domain-expertise/user/{user_id}` - Get all expertise for user
- **PUT** `/api/domain-expertise/{user_id}/{interest_id}` - Update domain expertise
- **DELETE** `/api/domain-expertise/{user_id}/{interest_id}` - Delete domain expertise

## 🔧 Usage Example

### Prerequisites
- User must exist in the User Management Service
- User Management Service must be running and accessible

### 1. Assign Profile Based on Behavior

```bash
curl -X POST "http://localhost:8000/api/predefined-profiles/assign-profile" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-uuid-here",
    "behavior": {
      "intent": "LEARNING",
      "interests": ["AI", "DATA_SCIENCE"],
      "behavior_level": "INTERMEDIATE",
      "behavior_signals": ["DEEP_REASONING", "ITERATIVE"],
      "output_preference": "DETAILED",
      "interaction_tone": "PROFESSIONAL"
    }
  }'
```

### 3. Get Profile Assignment Status

```bash
curl -X GET "http://localhost:8000/api/predefined-profiles/user/{user_id}"
```

## 🧮 Matching Algorithm

The service uses a sophisticated multi-factor scoring algorithm:

### Standard Matching Weights (Normal Operation)
- **Intent**: 35%
- **Interest**: 25%
- **Complexity**: 15%
- **Style**: 15%
- **Consistency**: 10%

### Cold-Start Matching Weights (New Users)
- **Intent**: 60%
- **Interest**: 40%

### Assignment Criteria

**Cold-Start Mode:**
- Minimum 5 prompts required
- Average score ≥ 0.60
- 2+ consecutive top rankings

**Drift-Fallback Mode:**
- Average score ≥ 0.70
- 3+ consecutive top rankings

## 🌟 User Profile Modes

1. **COLD_START**: Initial phase for new users (0-4 prompts)
2. **HYBRID**: Normal operation with assigned profile + growing dynamic profile
3. **DYNAMIC_ONLY**: Mature users with high-confidence dynamic profiles
4. **DRIFT_FALLBACK**: Behavioral change detection and reassignment

## 🔍 Behavioral Dimensions

### Intents
- LEARNING - Cognitive support, gaining knowledge
- TASK_COMPLETION - Completing tasks efficiently
- PROBLEM_SOLVING - Solving technical problems
- EXPLORATION - Generating ideas and creative outputs
- GUIDANCE - Seeking personal/lifestyle advice
- ENGAGEMENT - Entertainment, casual use

### Interest Areas
- AI, DATA_SCIENCE, WRITING, PROGRAMMING, CREATIVE, HEALTH, PERSONAL_GROWTH, ENTERTAINMENT

### Behavior Levels
- BASIC - Simple prompts, low iteration
- INTERMEDIATE - Moderate complexity, task-based
- ADVANCED - Structured prompts, iterative workflows

### Behavior Signals
- DEEP_REASONING, GOAL_ORIENTED, MULTI_STEP, ITERATIVE, CASUAL

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.110.0
- **Database**: PostgreSQL with SQLAlchemy 2.0.27 ORM
- **Validation**: Pydantic 2.5.0
- **Server**: Uvicorn 0.27.1
- **HTTP Client**: httpx 0.27.0 (for external service communication)
- **Message Broker**: Redis 5.0.1 (for event streaming)

## 📊 Database Schema

### Core Tables

- **profile** - Predefined behavioral profiles
- **user_profile_ranking_state** - Temporal profile-user matching scores (references external user_id)
- **user_domain_state** - User expertise tracking per domain (references external user_id)

**Note**: User data is managed by the external User Management Service

### Reference Tables

- **intent** - User intent taxonomy
- **interest_area** - Domain interest taxonomy
- **behavior_level** - Complexity sophistication levels
- **behavior_signal** - Interaction pattern indicators
- **domain_expertise_level** - Expertise level taxonomy
- **standard_matching_factor** - Weights for full behavioral analysis
- **cold_start_matching_factor** - Weights for cold-start mode

## 📝 License

This project is part of a research initiative at SLIIT (Sri Lanka Institute of Information Technology).

## 📧 Contact

For questions or support, please contact the development team.

## 🙏 Acknowledgments

- Built with FastAPI for high-performance async capabilities
- PostgreSQL for robust relational data management
- SQLAlchemy for elegant ORM abstractions
- Research conducted at SLIIT

---

**Note**: This is a research project focused on adaptive user profiling in AI/LLM applications. The service is designed for integration with conversational AI systems to provide personalized user experiences based on behavioral analysis.
