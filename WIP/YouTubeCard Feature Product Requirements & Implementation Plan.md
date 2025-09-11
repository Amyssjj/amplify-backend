### YouTubeCard Feature: Product Requirements & Implementation Plan**

This document outlines the vision, requirements, technical design, and TDD implementation strategy for introducing the "Share Your Take" (YouTubeCard) feature into the Amplify application.

### **1. Problem, Vision & User Value**

*   **Problem:** The current Amplify experience is centered on personal, creative storytelling sparked by user photos. While valuable, this limits the scope of practice. Our target persona, "The Aspiring Communicator," also needs to hone analytical and summarization skills crucial for professional settings like meetings, presentations, and client interactions. The app needs a way to prevent practice from becoming repetitive and to expand the user's communication toolkit.

*   **Vision:** To evolve Amplify from a personal storytelling coach into a comprehensive communication training tool. By introducing curated, external content, we provide users with structured exercises that simulate real-world professional scenarios, helping them become more versatile and confident speakers.

*   **User Value Proposition:**
    *   **Skill Diversification:** Users can move beyond creative expression to practice the critical skills of listening, analysis, summarization, and rephrasing—directly applicable to their careers.
    *   **Increased Engagement:** A constantly refreshed feed of new, interesting content provides a compelling reason for users to return to the app daily.
    *   **Real-World Simulation:** The "listen, then summarize" flow directly mimics the common professional task of providing a takeaway after a presentation or discussion, making practice highly relevant.
    *   **Structured Learning:** Curated clips provide focused, bite-sized learning opportunities on topics relevant to communication and leadership.

### **2. User Journey**

1.  **Discovery:** The user opens the Amplify app and lands on the Home Screen. Below the familiar "Say It Your Way" photo prompt, they see a new "Share Your Take" section with a horizontally scrolling carousel of `YouTubeCards`. Each card displays a video thumbnail, title, and clip duration.
2.  **Selection:** The user browses the carousel and taps on a `YouTubeCard` that interests them.
3.  **Immersion:** The user is navigated to a dedicated `InsightRecordingScreen`. The YouTube video clip automatically plays from its specified start time to its end time, allowing the user to focus solely on the content.
4.  **Response:** After listening, the user taps the "Record" button at the bottom of the screen to capture their summary, insights, or personal take on the clip's message.
5.  **Amplification:** Upon finishing the recording, the user is taken to the results screen where their take is enhanced and analyzed by the AI, which uses the original clip's transcript for context.
6.  **Review:** The user reviews their amplified text, listens to the improved audio, and explores the "Framework," "Phrasing," and "Synthesis & Clarity" feedback modules.
7.  **History:** The completed session appears in the user's enhancement history list, correctly displaying the YouTube video's thumbnail, title, and the duration of their enhanced audio take.

### **3. APIs Design**

The feature will be implemented using the finalized OpenAPI v2.1 specification. The key components are:

*   **New Endpoint (`GET /api/v1/youtube-cards`):** A dedicated endpoint to fetch the list of active `YouTubeCards`. Each card object in the response will contain `id`, `title`, `youtube_video_id`, `thumbnail_url`, `duration_seconds`, `start_time_seconds`, `end_time_seconds`, and `clip_transcript`.

*   **Modified Endpoint (`POST /api/v1/enhancements`):** This core endpoint will be generalized using a `discriminator` on a `type` field.
    *   If `type` is `"photo"`, the request body will require `photo_base64` and `transcript`.
    *   If `type` is `"youtube"`, the request body will require `source_transcript` (the `clip_transcript` from the `YouTubeCard`) and `transcript` (the user's recording).

*   **Modified Response Schemas:**
    *   `EnhancementSummary`: Will now include `prompt_type`, `prompt_title`, `prompt_thumbnail_url` (for YouTube), `prompt_photo_thumbnail_base64` (for Photo), and `audio_duration_seconds` to correctly populate the history list for both types.
    *   `EnhancementDetails`: Will be updated with the same fields to provide full context when viewing a single past enhancement.

### **4. TDD Implementation Details for Backend (Python/pytest)**

The backend will be developed following a strict Red-Green-Refactor TDD cycle.

**Module 1: `GET /api/v1/youtube-cards` Endpoint**
1.  **RED:** Write a `pytest` test `test_get_youtube_cards_returns_200_ok` that calls the (not-yet-existing) endpoint and asserts a `200 OK` status. The test fails.
2.  **GREEN:** Create the basic route and a controller function that returns an empty JSON array `[]` and a `200 OK` status. The test passes.
3.  **RED:** Write a test `test_get_youtube_cards_returns_correct_schema` that mocks the database response and asserts that the JSON body of a successful response matches the `YouTubeCard` schema (contains all required fields). The test fails.
4.  **GREEN:** Implement the database query logic to fetch active cards and serialize them into the correct JSON structure. The test passes.
5.  **REFACTOR:** Clean up the controller and serialization logic. Ensure all tests still pass.

**Module 2: `POST /api/v1/enhancements` Modification**
1.  **RED:** Write a test `test_enhancement_fails_with_invalid_type` that sends a request with `type: "invalid_type"` and asserts a `400 Bad Request` response. The test fails.
2.  **GREEN:** Add validation logic to the request handler that checks for `type` being either `"photo"` or `"youtube"`. The test passes.
3.  **RED:** Write a test `test_youtube_enhancement_succeeds` that sends a valid `type: "youtube"` payload. The test should assert that the request is routed to a new (mocked) `process_youtube_enhancement` service function. The test fails.
4.  **GREEN:** Implement the dispatcher logic in the main controller that calls the appropriate service function based on the `type` field. The test passes.
5.  **RED:** Write a test `test_photo_enhancement_still_works` to ensure the original photo flow continues to work as expected. The test fails as the request model has changed.
6.  **GREEN:** Adjust the dispatcher to correctly handle the legacy photo flow. The test passes.
7.  **REFACTOR:** Clean up the controller and service routing logic.

**Module 3: Data Persistence**
1.  **RED:** Write an end-to-end test that first creates a YouTube enhancement and then calls `GET /api/v1/enhancements/{id}`. Assert that the response body contains the correct `prompt_type: "youtube"` and `source_transcript`. The test fails.
2.  **GREEN:** Modify the database saving logic within the enhancement service to persist the new contextual fields (`prompt_type`, `source_transcript`, `prompt_thumbnail_url`, etc.). The test passes.
3.  **REFACTOR:** Ensure the database models are clean and efficient.

### **5. TDD Implementation Details for iOS App (Swift/XCTest)**

The iOS app will also follow a TDD approach, focusing on the ViewModel and Service layers.

**Module 1: Data & Networking Layer**
1.  **RED:** Write an `XCTest` `test_decoding_youtube_card_from_json` that attempts to decode a sample valid JSON string into a `YouTubeCard` model. The test fails because the model doesn't exist.
2.  **GREEN:** Create the `YouTubeCard` struct conforming to `Codable`. The test passes.
3.  **RED:** Write a test for a `YouTubeCardService` that asserts a successful fetch and decoding of cards from a mocked network client. The test fails.
4.  **GREEN:** Implement the `fetchYouTubeCards()` method in the service that uses the network client. The test passes.
5.  **REFACTOR:** Clean up the service logic.

**Module 2: Home Screen (`HomeScreenViewModel`)**
1.  **RED:** Write a test `test_home_screen_vm_fetches_cards_on_init` that initializes the ViewModel and asserts that its `youtubeCards` published property receives values from a mocked service. The test fails.
2.  **GREEN:** Implement the `init()` method of the ViewModel to call the service's `fetchYouTubeCards()` function and assign the result to the property. The test passes.
3.  **RED:** Write a test `test_selecting_card_triggers_navigation` that calls a `viewModel.didSelectCard(at: 0)` method and asserts that a delegate or coordinator function `navigateToInsight(with: card)` is called. The test fails.
4.  **GREEN:** Implement the selection logic. The test passes.
5.  **REFACTOR:** Clean up the ViewModel.

**Module 3: Submission Logic (`EnhancementService`)**
1.  **RED:** Write a test `test_submitting_youtube_enhancement_builds_correct_body` for the `EnhancementService`. The test will call a `submitEnhancement(for: youtubePrompt)` method and use a mocked network client to capture the outgoing request body, asserting it matches the new JSON structure with `type: "youtube"`. The test fails.
2.  **GREEN:** Implement the logic inside the `submitEnhancement` function to check the prompt type and construct the correct request body before sending it. The test passes.
3.  **REFACTOR:** Ensure the submission logic is clean and reusable.

### **6. Success Metrics**

The "Definition of Done" for this feature is primarily technical, ensuring a high-quality and bug-free release.

*   **Primary Success Metric (Definition of Done):**
    *   **100% Pass Rate for Backend Tests:** All `pytest` unit and integration tests for the new and modified endpoints must pass in the CI/CD pipeline.
    *   **100% Pass Rate for iOS Tests:** All `XCTest` unit tests for the ViewModels, Services, and data models related to the feature must pass.

*   **Secondary Success Metrics (Post-Launch Monitoring):**
    *   **Feature Adoption:** At least 20% of Daily Active Users (DAU) engage with a `YouTubeCard` (tap to view) within the first week of launch.
    *   **Engagement:** The ratio of completed `youtube` enhancements to `photo` enhancements reaches at least 1:4 within the first month.
    *   **Stability:** Zero feature-specific crashes reported through crashlytics.