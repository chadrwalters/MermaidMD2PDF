# System Architecture Documentation

This document demonstrates how to create a comprehensive system architecture documentation using MermaidMD2PDF.

## System Overview

Our system is a distributed microservices architecture that handles document processing and PDF generation.

```mermaid
graph TB
    subgraph Client
        UI[Web UI]
        CLI[CLI Tool]
    end

    subgraph Services
        API[API Gateway]
        Auth[Auth Service]
        Doc[Document Service]
        PDF[PDF Service]
    end

    subgraph Storage
        DB[(Database)]
        Cache[(Redis Cache)]
        S3[(S3 Storage)]
    end

    UI --> API
    CLI --> API
    API --> Auth
    API --> Doc
    Doc --> PDF
    Doc --> DB
    Doc --> Cache
    PDF --> S3
```

## Authentication Flow

The system uses OAuth2 for authentication. Here's the flow:

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant Auth
    participant API
    participant Service

    User->>UI: Login Request
    UI->>Auth: OAuth2 Request
    Auth->>User: Login Page
    User->>Auth: Credentials
    Auth->>Auth: Validate
    Auth->>UI: Access Token
    UI->>API: API Request + Token
    API->>Auth: Validate Token
    Auth->>API: Token Valid
    API->>Service: Process Request
    Service->>API: Response
    API->>UI: Response
    UI->>User: Show Result
```

## Data Model

The system uses a relational database with the following core entities:

```mermaid
erDiagram
    User ||--o{ Document : creates
    Document ||--o{ Version : has
    Version ||--o{ Diagram : contains
    Diagram ||--o{ Image : generates
    Document ||--o{ PDF : produces

    User {
        string id PK
        string email
        string name
        datetime created_at
    }

    Document {
        string id PK
        string title
        string content
        string user_id FK
        datetime created_at
    }

    Version {
        string id PK
        string document_id FK
        string content
        datetime created_at
    }

    Diagram {
        string id PK
        string version_id FK
        string content
        string type
        datetime created_at
    }

    Image {
        string id PK
        string diagram_id FK
        string url
        datetime created_at
    }

    PDF {
        string id PK
        string document_id FK
        string url
        datetime created_at
    }
```

## Deployment Architecture

The system is deployed using Kubernetes:

```mermaid
graph TB
    subgraph K8s Cluster
        subgraph Ingress
            IG[Ingress Gateway]
        end

        subgraph Services
            API[API Gateway]
            Auth[Auth Service]
            Doc[Document Service]
            PDF[PDF Service]
        end

        subgraph Storage
            DB[(PostgreSQL)]
            Redis[(Redis)]
            MinIO[(MinIO)]
        end
    end

    IG --> API
    API --> Auth
    API --> Doc
    Doc --> PDF
    Doc --> DB
    Doc --> Redis
    PDF --> MinIO
```

## State Management

The document processing workflow follows this state machine:

```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> Validating
    Validating --> Valid
    Validating --> Invalid
    Invalid --> Draft
    Valid --> Processing
    Processing --> Complete
    Processing --> Failed
    Failed --> Draft
    Complete --> [*]
```

## Performance Considerations

The system implements caching at multiple levels:

```mermaid
graph LR
    subgraph Client
        Browser[Browser Cache]
        CDN[CDN Cache]
    end

    subgraph Server
        Redis[Redis Cache]
        Memory[In-Memory Cache]
    end

    Browser --> CDN
    CDN --> Redis
    Redis --> Memory
```

## Security Architecture

The security model follows a defense-in-depth approach:

```mermaid
graph TB
    subgraph External
        WAF[Web Application Firewall]
        DDoS[DDoS Protection]
    end

    subgraph Application
        Auth[Authentication]
        Authz[Authorization]
        Input[Input Validation]
    end

    subgraph Data
        Encrypt[Encryption]
        Audit[Audit Logging]
    end

    WAF --> DDoS
    DDoS --> Auth
    Auth --> Authz
    Authz --> Input
    Input --> Encrypt
    Input --> Audit
```
