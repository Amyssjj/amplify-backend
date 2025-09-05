# Amplify Backend

## Overview

The Amplify Backend is a FastAPI-based web service designed to provide AI-powered story enhancement capabilities. The application enables users to submit stories for analysis and enhancement using generative AI, with additional features for text-to-speech audio generation and user authentication. The system is structured as a REST API with comprehensive endpoint coverage for story processing, audio generation, authentication, and system health monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
The application is built on FastAPI, chosen for its automatic API documentation generation, built-in data validation through Pydantic, and high performance with async/await support. The framework provides excellent developer experience with automatic OpenAPI schema generation and type safety.

### Application Structure
The codebase follows a layered architecture pattern with clear separation of concerns:

- **API Layer**: Contains versioned endpoints (v1) organized by feature domains (enhancement, audio, auth, health)
- **Schema Layer**: Pydantic models for request/response validation and serialization
- **Service Layer**: Business logic implementation (planned for future development)
- **Core Layer**: Application configuration, security utilities, and shared dependencies

### Request/Response Handling
All API endpoints use Pydantic schemas for automatic request validation and response serialization. The system includes standardized error handling and response models for consistency across all endpoints.

### Authentication System
JWT-based authentication is configured using python-jose for token generation and validation. The system includes password hashing capabilities through passlib with bcrypt support, though the actual implementation is pending.

### AI Integration Architecture
The application is designed to integrate with Google's Gemini AI API for story enhancement capabilities. The enhancement system supports different types of analysis (plot, character, dialogue, setting) and provides structured insights and suggestions.

### CORS Configuration
Cross-origin resource sharing is configured to allow all origins during development, with provisions for production-specific domain restrictions.

## External Dependencies

### AI Services
- **Google Generative AI (Gemini)**: Primary AI service for story analysis and enhancement
- **Text-to-Speech API**: Planned integration for audio generation from enhanced stories

### Authentication & Security
- **python-jose**: JWT token creation and validation
- **passlib**: Password hashing and verification with bcrypt

### Web Framework
- **FastAPI**: Core web framework with automatic documentation
- **Uvicorn**: ASGI server for running the FastAPI application
- **Pydantic**: Data validation and settings management

### Development & Testing
- **pytest**: Testing framework
- **httpx**: HTTP client for testing API endpoints

### Configuration Management
Environment-based configuration through Pydantic settings, supporting API keys for external services, database URLs, and security settings through environment variables or .env files.