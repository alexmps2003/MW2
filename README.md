# SwiftTrack Middleware Prototype

SwiftTrack is the group prototype for the Middleware Architecture assignment. It integrates mock SOAP/XML, REST/JSON, and TCP/IP logistics systems through an event-driven middleware layer.

## Documentation

- [Requirements and scope](docs/requirements.md)
- [Architecture alternatives and final selection](docs/architecture-alternatives.md)
- [Technology stack](docs/technology-stack.md)
- [External system contracts](docs/contracts.md)
- [Phase 6: event-driven processing](docs/phase-6-event-driven.md)
- [Phase 7: resilience and recovery](docs/phase-7-resilience.md)
- [Phase 8: delivery lifecycle](docs/phase-8-delivery-lifecycle.md)
- [Phase 9: real-time tracking and web interface](docs/phase-9-realtime-and-ui.md)
- [Final demonstration script](docs/final-demo-script.md)
- [Submission checklist](docs/submission-checklist.md)

## Project Structure

```text
docs/                 Architecture, report material, API contracts, and demo notes
services/platform/    FastAPI gateway, order service, adapters, and worker
services/cms-mock/    SOAP/XML CMS mock
services/ros-mock/    REST/JSON ROS mock
services/wms-mock/    TCP/IP WMS mock
frontend/             React/Vite client and driver web interface
tests/                Automated tests written after core implementation
scripts/              Demo and helper scripts
```

## Local Infrastructure

Phase 3 supplies PostgreSQL and RabbitMQ through Docker Compose. Phase 4 adds the CMS, ROS, and WMS mock systems to the same Compose file. Phase 5 adds the FastAPI API Gateway, PostgreSQL order persistence, and protocol adapters. Phase 6 adds a durable RabbitMQ event and background worker. Phase 7 adds delayed retries and dead-letter handling. Phase 8 adds validated driver delivery actions. Phase 9 adds a React/Vite live-tracking interface. The mocks use the Python standard library so a temporary PyPI outage does not prevent the protocol demonstrations from starting.

Copy the local environment template once before running the stack:

```bash
cp .env.example .env
```

## Phase 5 Verification Checkpoint (run by project owner)

When asked to verify Phase 5, run:

```bash
docker compose up -d
docker compose ps
```

Expected result: `postgres`, `rabbitmq`, `cms-mock`, `ros-mock`, `wms-mock`, and `api` become healthy. RabbitMQ's management interface will be available at `http://localhost:15672` using the username and password from `.env`.

Phase 6 adds `worker`. New orders are persisted by `api`, published as `order.created`, and processed by `worker` without the client waiting for CMS, WMS, or ROS.
