# Component Architecture (Clean + Hexagonal)

```mermaid
flowchart TB
    subgraph UI[Frontend]
        UI1[Web App Shell]
        UI2[Chat UI]
        UI3[Search Results UI]
        UI4[Conversion Status UI]
    end

    subgraph API[API Gateway]
        APIGW[Gateway: Auth, Rate Limit, Validation]
    end

    subgraph Core[Domain Core]
        UC1[Use Case: Search]
        UC2[Use Case: Convert]
        UC3[Use Case: Deliver]
        ENT[Entities + Policies]
    end

    subgraph Ports[Ports (Interfaces)]
        P1[SearchPort]
        P2[ConvertPort]
        P3[StoragePort]
        P4[ChatPort]
    end

    subgraph Adapters[Adapters]
        A1[YouTube API Adapter]
        A2[MP3 Module Adapter]
        A3[Storage Adapter]
        A4[Chat Model Adapter]
        A5[Notification Adapter]
    end

    UI --> APIGW
    APIGW --> Core
    Core --> Ports
    Ports --> Adapters

    A1 --> YT[YouTube Data API]
    A2 --> MOD[MP3 Conversion Module]
    A3 --> STORE[File Storage]
```
