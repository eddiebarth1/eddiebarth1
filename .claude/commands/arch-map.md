Generate a comprehensive architectural map of this codebase. The goal is a precise, reference-quality understanding of how all the pieces fit together - the kind of knowledge a new senior engineer would need to confidently design new features or debug production incidents.

## Phase 1: System Boundaries

1. What type of system is this? (monolith, microservice, library, CLI tool, serverless, etc.)
2. What does it accept as input and produce as output?
3. What external systems does it depend on? (databases, caches, message queues, external APIs, storage)
4. What external systems depend on it? (consumers, clients, downstream services)
5. Draw a text-based system context diagram showing the boundaries

## Phase 2: Internal Structure

Map the internal architecture layers. Depending on the style, look for:

**Layered / N-tier architecture**:
- Presentation / API layer (routes, controllers, handlers)
- Business logic / service layer
- Data access / repository layer
- Domain model layer

**Hexagonal / Ports and Adapters**:
- Core domain (entities, use cases, domain services)
- Ports (interfaces the domain exposes or requires)
- Adapters (concrete implementations: HTTP, DB, MQ, etc.)

**Event-driven**:
- Event producers and where events originate
- Event consumers and what they do
- Event schemas and contracts

**Microservices / Modular monolith**:
- Module/service boundaries
- How modules communicate (direct calls, HTTP, events, shared DB)
- Shared vs. isolated data stores

Read the key directories and files to map these layers:

```bash
# Find all route/handler definitions
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" --include="*.rb" \
  -E "(router\.|app\.(get|post|put|delete|patch)|@app\.route|func.*Handler|http\.Handle)" . \
  | grep -v "node_modules\|vendor\|test" | head -50

# Find all database interaction points
grep -rn --include="*.js" --include="*.ts" --include="*.go" --include="*.py" \
  -E "(\.query\(|\.find\(|\.save\(|db\.|gorm\.|mongoose\.|sqlx\.|\.execute\()" . \
  | grep -v "node_modules\|vendor\|test" | head -30

# Find service/use-case layer
find . -type d -name "service*" -o -name "usecase*" -o -name "domain*" -o -name "business*" 2>/dev/null \
  | grep -v "node_modules\|vendor\|.git"
```

## Phase 3: Data Architecture

1. What are the primary data stores? (PostgreSQL, MySQL, MongoDB, Redis, S3, etc.)
2. Find and read all schema definitions, migrations, or ORM models
3. Map the key entities and their relationships
4. Identify caching layers and what they cache
5. Find any event/message schemas

```bash
# Find schema/migration files
find . -type f -name "*.sql" -o -name "*migration*" -o -name "*schema*" -o -name "*model*" 2>/dev/null \
  | grep -v "node_modules\|vendor\|.git" | head -30
```

## Phase 4: API Surface

For each type of interface the system exposes:

**HTTP/REST API**:
- List all endpoints with their HTTP method, path, and purpose
- Note authentication requirements
- Note request/response shapes for the most important ones

**GraphQL**: Map the schema types and resolvers

**gRPC/Protobuf**: Find and read all `.proto` files

**Message Queue**: Find all topics/queues consumed and produced

**CLI**: Map all commands and their flags

## Phase 5: Cross-Cutting Concerns

Identify how the following are handled across the entire system:
1. **Logging**: What library? What format? What is logged?
2. **Error handling**: Global error boundaries? Error types?
3. **Configuration**: How is config loaded and injected?
4. **Authentication**: Middleware? Where enforced?
5. **Observability**: Metrics, tracing, health checks?
6. **Concurrency**: Goroutines, async/await, worker pools?

## Phase 6: Synthesis

Produce a structured architectural document:

**System Context** (text diagram):
```
[External Consumer] → [This System] → [Database]
                                    → [External API]
                                    → [Message Queue]
```

**Internal Architecture** (text diagram of layers and their relationships)

**Key Components Table**:
| Component | Location | Responsibility | Depends On |

**Data Flow**: Step-by-step trace of a representative request through the system

**API Inventory**: All exposed interfaces with methods/endpoints

**Technology Stack**: Languages, frameworks, libraries, infrastructure

**Architectural Decisions**: Any patterns or choices that seem intentional and load-bearing

**Architectural Risks**: Places where the architecture creates fragility, tight coupling, or scaling problems

$ARGUMENTS
