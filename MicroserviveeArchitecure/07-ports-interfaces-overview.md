# Services, Ports, and Interactions Overview

```mermaid
%%{init: {"theme": "default", "flowchart": {"nodeSpacing": 70, "rankSpacing": 90}, "themeVariables": {"fontSize": "16px"}}}%%
flowchart LR
    subgraph SERVICES[Services]
        direction LR

        subgraph APIGW[API Gateway Service]
            direction TB
            APIGW_IN[Inbound: HTTP REST, WebSocket]
            APIGW_OUT[Outbound: RoutingPort]
        end

        subgraph CHAT[Chat Orchestrator Service]
            direction TB
            CHAT_IN[Inbound: ChatPort HTTP Webhook]
            CHAT_OUT1[Outbound: SearchPort]
            CHAT_OUT2[Outbound: ConvertPort]
            CHAT_OUT3[Outbound: StoragePort]
        end

        subgraph SEARCH[Search Service]
            direction TB
            SEARCH_IN[Inbound: SearchPort HTTP REST]
            SEARCH_OUT1[Outbound: YouTubePort]
            SEARCH_OUT2[Outbound: CachePort]
        end

        subgraph CONV[Conversion Service]
            direction TB
            CONV_IN1[Inbound: ConvertPort HTTP REST]
            CONV_IN2[Inbound: QueuePort Job Queue]
            CONV_OUT1[Outbound: DownloadPort]
            CONV_OUT2[Outbound: ConvertPort]
            CONV_OUT3[Outbound: StoragePort]
            CONV_OUT4[Outbound: QueuePort]
        end

        subgraph STORE[Storage and Delivery Service]
            direction TB
            STORE_IN[Inbound: StoragePort HTTP REST]
            STORE_OUT1[Outbound: FileStorePort]
            STORE_OUT2[Outbound: LinkPort]
        end
    end

    subgraph EXTERNAL[External Systems]
        direction LR
        YT[YouTube Data API]
        CACHE[(Cache)]
        FF[FFmpeg and yt-dlp]
        QUEUE[(Job Queue)]
        FS[File Storage]
        CDN[(Download Link/CDN)]
    end

    %% Fan-out routers to reduce overlapping edges
    APIGW_ROUTER((API Routing))
    CHAT_ROUTER((Chat Routing))

    %% Interactions with ports and APIs
    APIGW_OUT -->|HTTP REST| APIGW_ROUTER
    APIGW_ROUTER -->|HTTP REST| CHAT_IN
    APIGW_ROUTER -->|HTTP REST| SEARCH_IN
    APIGW_ROUTER -->|HTTP REST| CONV_IN1
    APIGW_ROUTER -->|HTTP REST| STORE_IN

    CHAT_OUT1 -->|HTTP REST via SearchPort| CHAT_ROUTER
    CHAT_OUT2 -->|HTTP REST via ConvertPort| CHAT_ROUTER
    CHAT_OUT3 -->|HTTP REST via StoragePort| CHAT_ROUTER
    CHAT_ROUTER -->|HTTP REST| SEARCH_IN
    CHAT_ROUTER -->|HTTP REST| CONV_IN1
    CHAT_ROUTER -->|HTTP REST| STORE_IN

    SEARCH_OUT1 -->|YouTube Data API| YT
    SEARCH_OUT2 -->|Cache API| CACHE

    CONV_OUT1 -->|yt-dlp API| FF
    CONV_OUT2 -->|FFmpeg API| FF
    CONV_OUT3 -->|HTTP REST via StoragePort| STORE_IN
    CONV_OUT4 -->|Queue API| QUEUE

    STORE_OUT1 -->|File API| FS
    STORE_OUT2 -->|Link API| CDN
```
