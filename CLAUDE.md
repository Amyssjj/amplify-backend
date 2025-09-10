# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Activate virtual environment first
source venv/bin/activate

# Start development server with auto-reload
python main.py

# Or using uvicorn directly (port 8000 locally, 5000 on Replit)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test types using markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e           # End-to-end tests only
pytest -m contract      # Contract tests only
pytest -m "not slow"    # Skip slow tests

# Run single test file
pytest tests/unit/test_gemini_service.py -v
```

### Code Quality
```bash
# Format code (if black is installed)
black app/ tests/ --line-length 88

# Sort imports (if isort is installed)  
isort app/ tests/ --profile black

# Type checking (if mypy is installed)
mypy app/ --python-version 3.11
```

### Database Operations
```bash
# Initialize database tables
python init_db.py

# The application auto-creates tables on startup via the lifespan manager
```

## Architecture Overview

### Core Structure
This is a FastAPI-based backend service for AI-powered story enhancement with the following layered architecture:

- **API Layer** (`app/api/v1/`): REST endpoints organized by feature domains
- **Services Layer** (`app/services/`): Business logic and external service integrations
- **Models Layer** (`app/models/`): SQLAlchemy database models
- **Schemas Layer** (`app/schemas/`): Pydantic models for request/response validation
- **Core Layer** (`app/core/`): Configuration, database, and authentication utilities

### Key Components

#### Enhancement Flow (Two-Stage Process)
1. **Stage 1 (POST /api/v1/enhancements)**: Photo + transcript → AI analysis → enhanced text
2. **Stage 2 (GET /api/v1/enhancements/{id}/audio)**: Enhanced text → TTS audio generation

#### AI Services Integration
- **Gemini Service** (`app/services/gemini_service.py`): Google Gemini API for story enhancement with vision capabilities
- **TTS Service** (`app/services/tts_service.py`): Text-to-speech with multiple provider support (OpenAI, ElevenLabs, mock)
- **Prompt Manager** (`app/services/prompt_manager.py`): Dynamic prompt loading from YAML files in `app/prompts/`

#### Authentication & User Management
- JWT-based authentication with Google OAuth integration
- Anonymous user support for unauthenticated usage
- User-scoped data access for enhancements and history

#### Database Architecture
- SQLAlchemy ORM with PostgreSQL support
- Enhancement model tracks full workflow: original → enhanced → audio status
- Graceful fallback when database is unavailable (continues without persistence)

### Service Dependencies

#### External APIs
- **Google Gemini**: Story enhancement with photo analysis (requires `GEMINI_API_KEY`)
- **OpenAI**: Text-to-speech generation (requires `OPENAI_API_KEY`)  
- **ElevenLabs**: Alternative TTS provider (requires `ELEVENLABS_API_KEY`)
- **Google OAuth**: User authentication (requires `GOOGLE_OAUTH_CLIENT_ID`)

#### Environment Configuration
The app uses Pydantic Settings with `.env` file support. Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini API access
- `TTS_PROVIDER`: Choose "openai", "elevenlabs", or "mock"
- `SECRET_KEY`: JWT signing key
- `DEBUG`: Development mode toggle

### Error Handling Strategy
- Service-specific exceptions (`GeminiError`, `TTSError`) for external API failures
- Graceful degradation: continues operation when non-critical services fail
- Database failure tolerance: logs errors but doesn't block requests
- Comprehensive error logging with request context

### Testing Architecture
- **Unit Tests**: Isolated component testing with mocks
- **Integration Tests**: Service-to-service interaction testing  
- **Contract Tests**: OpenAPI specification compliance
- **End-to-End Tests**: Complete user workflow validation
- Test configuration in `pytest.ini` with custom markers for test categorization

### Deployment Configuration
- **Local Development**: Runs on port 8000 (avoiding macOS AirPlay port conflict)
- **Replit Deployment**: Uses port 5000 (Replit requirement, configurable via PORT env var)
- Docker-ready with requirements.txt and virtual environment
- CORS configured for cross-origin requests (configured for development - restrict in production)
- Health check endpoints at `/` and `/health`