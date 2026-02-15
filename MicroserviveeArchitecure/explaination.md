# CS 331 Assignment 4 - Architecture Explanation

## I. Software Architecture Style

**Microservices (system-level) + Hexagonal (service-level)**

### A. Justification of category by granularity

- **System-level granularity (Microservices):**
  - The system is split into independent, deployable services aligned to business capabilities.
  - Each service has its own API boundary and can be deployed, scaled, and maintained separately.
  - Services communicate via HTTP/REST and queues, not by sharing internal code.
- **Service-level granularity (Hexagonal inside each service):**
  - Each service has a business logic core (use cases + entities).
  - Ports define stable interfaces for inputs/outputs.
  - Adapters implement those ports for concrete technologies (YouTube API, FFmpeg, storage, etc.).
  - This makes each service a clean, testable unit with clear boundaries.

### B. Why this is the best choice for this project

- **Scalability:**
  - Conversion is CPU-heavy and can scale independently without scaling chat or search.
  - Workers can be added for peak demand without affecting other services.
- **Maintainability:**
  - Changes in external tools (yt-dlp, FFmpeg, storage) are isolated to adapters.
  - Each service has a focused responsibility, reducing code complexity.
- **Performance:**
  - Asynchronous job queue prevents blocking the user interface.
  - Heavy workloads are offloaded to conversion workers.
- **Reliability:**
  - A failure in one service does not bring down the entire system.
  - Services can be restarted or replaced independently.
- **Extensibility:**
  - New features (playlists, multiple qualities, new UI clients) can be added by new services or adapters.

## II. Application Components

- **API Gateway Service:** auth, validation, routing
- **Chat Orchestrator Service:** intent parsing, conversation state, workflow routing
- **Search Service:** YouTube search and ranking
- **Conversion Service:** download, convert, job status
- **Storage and Delivery Service:** file storage, download links, cleanup
- **Job Queue:** async task distribution
- **Web UI:** chat interface, results view, status updates
- **External systems and tools:**
  - YouTube Data API
  - yt-dlp
  - FFmpeg
  - File storage / CDN
  - Observability (logs/metrics)
