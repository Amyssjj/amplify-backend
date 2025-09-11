openapi: 3.1.0
info:
  title: Amplify AI Coach API (v2.1 - With YouTube Feature)
  description: |
    AI-powered storytelling enhancement for a pre-MVP demo.
    This API uses a two-stage flow designed for a seamless user experience:
    1. A fast `POST` request returns text analysis (enhanced story, insights) immediately.
    2. The client app then automatically makes a `GET` request to generate the audio in the background.
    Metadata is persisted in a server-side database, while audio assets are sent to the client for local storage.
  version: 2.1.0
  contact:
    name: Amplify Team
    email: support@amplify.app
  license:
    name: MIT

servers:
  - url: http://localhost:8000
    description: Local development
  - url: https://amplify-backend.repl.co
    description: Production (Replit)

tags:
  - name: Health
    description: Service health monitoring
  - name: Enhancement
    description: Story enhancement with Gemini + TTS
  - name: Auth
    description: Google OAuth authentication

paths:
  # --- UNCHANGED Paths ---
  /health:
    get:
      tags: [Health]
      summary: Basic health check
      operationId: getHealth
      security: []
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, example: healthy }
                  timestamp: { type: string, format: date-time }
                required: [status, timestamp]
  /health/ready:
    get:
      tags: [Health]
      summary: Readiness check
      operationId: getReadiness
      security: []
      responses:
        '200':
          description: All services ready
          content: { application/json: { schema: { $ref: '#/components/schemas/ReadinessResponse' } } }
        '503':
          description: Services not ready
          content: { application/json: { schema: { $ref: '#/components/schemas/ErrorResponse' } } }

  # --- NEW Path for YouTube Cards ---
  /api/v1/youtube-cards:
    get:
      tags: [Enhancement]
      summary: Get available YouTube practice cards
      operationId: getYouTubeCards
      description: Returns a list of curated YouTube video clips for users to practice with.
      responses:
        '200':
          description: A list of YouTube cards was retrieved successfully.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/YouTubeCard'
        '401': { $ref: '#/components/responses/Unauthorized' }

  # --- MODIFIED Enhancement Flow ---
  /api/v1/enhancements:
    post:
      tags: [Enhancement]
      summary: Create enhancement (Stage 1 - Text)
      operationId: createEnhancement
      description: |
        Performs Gemini analysis on a user transcript based on a specific prompt 
        context (either a photo or a YouTube insight). Responds quickly with 
        text-based results. The client app should immediately call 
        `GET /api/v1/enhancements/{id}/audio` in the background to complete the flow.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EnhancementRequest'
      responses:
        '200':
          description: Text enhancement successful.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnhancementTextResponse'
        '400': { $ref: '#/components/responses/BadRequest' }
        '401': { $ref: '#/components/responses/Unauthorized' }

    get:
      tags: [Enhancement]
      summary: Get enhancement history
      operationId: getEnhancements
      description: Returns a paginated list of the user's past enhancements, including audio status.
      parameters:
        - { name: limit, in: query, schema: { type: integer, default: 20, minimum: 1, maximum: 50 } }
        - { name: offset, in: query, schema: { type: integer, default: 0, minimum: 0 } }
      responses:
        '200':
          description: History retrieved successfully.
          content:
            application/json:
              schema:
                type: object
                required: [total, items]
                properties:
                  total: { type: integer }
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/EnhancementSummary'
        '401': { $ref: '#/components/responses/Unauthorized' }

  /api/v1/enhancements/{enhancement_id}:
    get:
      tags: [Enhancement]
      summary: Get enhancement details
      operationId: getEnhancementById
      description: Returns the full persisted details of a specific enhancement, including its audio status.
      parameters:
        - { name: enhancement_id, in: path, required: true, schema: { type: string, pattern: '^enh_[a-zA-Z0-9]+$' } }
      responses:
        '200':
          description: Enhancement details retrieved.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnhancementDetails'
        '401': { $ref: '#/components/responses/Unauthorized' }
        '404': { $ref: '#/components/responses/NotFound' }

  # --- UNCHANGED Paths ---
  /api/v1/enhancements/{enhancement_id}/audio:
    get:
      tags: [Enhancement]
      summary: Generate or retrieve audio (Stage 2 - Audio)
      operationId: getEnhancementAudio
      description: |
        Generates TTS audio for the given enhancement. This is a synchronous, idempotent endpoint.
        The client app should call this in the background immediately after Stage 1 succeeds.
        The response contains the Base64 audio data for the client to save locally.
      parameters:
        - { name: enhancement_id, in: path, required: true, schema: { type: string, pattern: '^enh_[a-zA-Z0-9]+$' } }
      responses:
        '200':
          description: Audio generated or retrieved successfully.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/EnhancementAudioResponse'
        '401': { $ref: '#/components/responses/Unauthorized' }
        '404': { $ref: '#/components/responses/NotFound' }
        '503':
          description: TTS service unavailable.
          content: { application/json: { schema: { $ref: '#/components/schemas/ErrorResponse' } } }
  /api/v1/auth/google:
    post:
      tags: [Auth]
      summary: Authenticate with Google
      operationId: googleAuth
      description: Exchange a Google ID token for a service-specific JWT access token.
      security: []
      requestBody:
        required: true
        content: { application/json: { schema: { $ref: '#/components/schemas/GoogleAuthRequest' } } }
      responses:
        '200':
          description: Authentication successful.
          content: { application/json: { schema: { $ref: '#/components/schemas/AuthResponse' } } }
        '401':
          description: Invalid Google token.
          content: { application/json: { schema: { $ref: '#/components/schemas/ErrorResponse' } } }

components:
  schemas:
    # --- NEW Schema for the YouTube Card List ---
    YouTubeCard:
      type: object
      required: [id, title, youtube_video_id, thumbnail_url, clip_transcript, duration_seconds]
      properties:
        id: { type: string, description: "Unique identifier for the YouTube card", example: "ytc_12345" }
        title: { type: string, description: "The title of the video clip" }
        youtube_video_id: { type: string, description: "The 11-character YouTube video ID" }
        thumbnail_url:
          type: string
          format: uri
          description: "The direct URL to the video thumbnail image."
        duration_seconds:
          type: integer
          description: "The duration of the video clip in seconds."
        start_time_seconds: { type: integer, nullable: true, description: "Optional start time for the clip in seconds" }
        end_time_seconds: { type: integer, nullable: true, description: "Optional end time for the clip in seconds" }
        clip_transcript: { type: string, description: "The transcript corresponding to the clip's duration" }

    # --- MODIFIED Request Schemas ---
    EnhancementRequest:
      oneOf:
        - $ref: '#/components/schemas/PhotoEnhancementRequest'
        - $ref: '#/components/schemas/YouTubeEnhancementRequest'
      discriminator:
        propertyName: type
        mapping:
          photo: '#/components/schemas/PhotoEnhancementRequest'
          youtube: '#/components/schemas/YouTubeEnhancementRequest'
    
    PhotoEnhancementRequest:
      type: object
      required: [type, photo_base64, transcript]
      properties:
        type: { type: string, enum: [photo], description: "The type of the enhancement prompt." }
        photo_base64: { type: string, format: byte, description: "Base64 encoded JPEG or PNG image (max 10MB)" }
        transcript: { type: string, description: "User's original story transcript", minLength: 1, maxLength: 5000 }
        language: { type: string, pattern: '^[a-z]{2}$', default: en }
    
    YouTubeEnhancementRequest:
      type: object
      required: [type, source_transcript, transcript]
      properties:
        type: { type: string, enum: [youtube], description: "The type of the enhancement prompt." }
        source_transcript: { type: string, description: "The original transcript from the YouTube video clip." }
        transcript: { type: string, description: "User's original summary or takeaway transcript", minLength: 1, maxLength: 5000 }
        language: { type: string, pattern: '^[a-z]{2}$', default: en }
    
    # --- MODIFIED Response Schemas ---
    EnhancementSummary:
      type: object
      required: [enhancement_id, created_at, prompt_type, prompt_title, transcript_preview, audio_status]
      properties:
        enhancement_id: { type: string }
        created_at: { type: string, format: date-time }
        prompt_type: 
          type: string
          enum: [photo, youtube]
        prompt_title:
          type: string
        prompt_thumbnail_url:
          type: string
          format: uri
          nullable: true
          description: "The thumbnail URL for the prompt. Only present if prompt_type is 'youtube'."
        prompt_photo_thumbnail_base64:
          type: string
          format: byte
          nullable: true
          description: "A small, Base64 encoded thumbnail of the original photo. Only present if prompt_type is 'photo'."
        transcript_preview: { type: string, maxLength: 100 }
        audio_status:
          type: string
          enum: [not_generated, ready]
        audio_duration_seconds:
          type: integer
          nullable: true
          description: "The duration of the generated audio in seconds. Null if audio_status is 'not_generated'."
    
    EnhancementDetails:
      type: object
      required: [enhancement_id, created_at, prompt_type, user_transcript, enhanced_transcript, insights, audio_status]
      properties:
        enhancement_id: { type: string }
        created_at: { type: string, format: date-time }
        prompt_type: 
          type: string
          enum: [photo, youtube]
        prompt_thumbnail_url:
          type: string
          format: uri
          nullable: true
          description: "The thumbnail URL for the prompt, if applicable (e.g., for YouTube prompts)."
        source_photo_base64:
          type: string
          format: byte
          nullable: true
          description: "Original photo data. Only present if prompt_type is 'photo'."
        source_transcript:
          type: string
          nullable: true
          description: "Original YouTube clip transcript. Only present if prompt_type is 'youtube'."
        user_transcript: { type: string, description: "The user's original transcript." }
        enhanced_transcript: { type: string }
        insights: { type: object, additionalProperties: { type: string } }
        audio_status:
          type: string
          enum: [not_generated, ready]
        audio_duration_seconds:
          type: integer
          nullable: true
          description: "The duration of the generated audio in seconds. Null if audio_status is 'not_generated'."
    
    # --- UNCHANGED Schemas ---
    GoogleAuthRequest:
      type: object
      required: [id_token]
      properties:
        id_token: { type: string, description: "Google ID token obtained from the iOS client" }
    EnhancementTextResponse:
      type: object
      required: [enhancement_id, enhanced_transcript, insights]
      properties:
        enhancement_id: { type: string, pattern: '^enh_[a-zA-Z0-9]+$', description: "Unique ID for the new enhancement" }
        enhanced_transcript: { type: string, description: "The AI-enhanced version of the story" }
        insights: { type: object, additionalProperties: { type: string }, description: "Dynamic, key-value insights from Gemini analysis" }
    EnhancementAudioResponse:
      type: object
      required: [audio_base64, audio_format]
      properties:
        audio_base64: { type: string, format: byte, description: "Base64 encoded MP3 audio data" }
        audio_format: { type: string, enum: [mp3], description: "The format of the audio data" }
    AuthResponse:
      type: object
      required: [access_token, token_type, user]
      properties:
        access_token: { type: string, description: "The JWT token for authenticating subsequent API requests" }
        token_type: { type: string, enum: [bearer], default: bearer }
        expires_in: { type: integer, example: 3600, description: "Token expiry time in seconds" }
        user:
          type: object
          required: [user_id, email]
          properties:
            user_id: { type: string, description: "Unique internal user ID" }
            email: { type: string, format: email }
            name: { type: string, description: "User's full name from Google" }
            picture: { type: string, format: uri, description: "URL to user's profile picture from Google" }
    ReadinessResponse:
      type: object
      required: [status, services]
      properties:
        status: { type: string, enum: [ready, not_ready] }
        services:
          type: object
          properties:
            gemini: { type: boolean }
            tts: { type: boolean }
            database: { type: boolean }
    ErrorResponse:
      type: object
      required: [error, message]
      properties:
        error: { type: string, description: "A machine-readable error code" }
        message: { type: string, description: "A human-readable error message" }
    ValidationErrorResponse:
      type: object
      required: [error, message, validation_errors]
      properties:
        error: { type: string, enum: [VALIDATION_ERROR] }
        message: { type: string }
        validation_errors:
          type: array
          items:
            type: object
            required: [field, message]
            properties:
              field: { type: string }
              message: { type: string }

  responses:
    BadRequest:
      description: The request body is invalid or missing required fields.
      content: { application/json: { schema: { $ref: '#/components/schemas/ValidationErrorResponse' } } }
    Unauthorized:
      description: The JWT is missing, invalid, or expired.
      content: { application/json: { schema: { $ref: '#/components/schemas/ErrorResponse' } } }
    NotFound:
      description: The requested enhancement does not exist.
      content: { application/json: { schema: { $ref: '#/components/schemas/ErrorResponse' } } }

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: "A JWT obtained from the `/api/v1/auth/google` endpoint."

security:
  - BearerAuth: []