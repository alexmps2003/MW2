# SwiftTrack Technology Stack

## Chosen Technologies

| Concern | Technology | Why it is appropriate |
|---|---|---|
| Client and driver interface | React with Vite | A small, responsive single-page web interface for the prototype. |
| Client-facing API | Python FastAPI | Clear REST API development, validation, automatic OpenAPI documentation, and WebSocket support. |
| Workflow persistence | PostgreSQL | Reliable relational persistence for orders, status history, idempotency records, and outbox events. |
| Asynchronous middleware | RabbitMQ | Durable queues, topic-based publish/subscribe, retries, acknowledgements, and dead-letter queues. |
| CMS integration | Python standard-library SOAP/XML mock and XML-over-HTTP client | Demonstrates actual SOAP/XML service integration without coupling the mock to a framework. |
| ROS integration | Python standard-library HTTP mock and HTTPX client | Demonstrates REST/JSON communication while keeping the external mock lightweight. |
| WMS integration | Python `asyncio` TCP server and socket client | Demonstrates a custom TCP/IP protocol. |
| Service packaging | Docker and Docker Compose | Reproducible local deployment using open-source tools. |
| Automated tests | Pytest and HTTPX | Unit and integration tests for adapters and workflow behaviour. |

## Why RabbitMQ Instead of Direct Calls

RabbitMQ decouples order acceptance from slow background work. The client API persists an order and records an event, then returns immediately. A worker processes that event later and can retry it safely if CMS, ROS, or WMS is unavailable.

## Why PostgreSQL Instead of In-Memory State

An accepted order must survive a service restart. PostgreSQL stores the authoritative SwiftTrack workflow state, including the current order status and every status transition. External CMS, ROS, and WMS data remains owned by those systems.

## Deployment Boundaries

The final Docker Compose deployment will contain:

```text
postgres       SwiftTrack order and workflow data
rabbitmq       queues, publish/subscribe events, retry and DLQ
cms-mock       SOAP/XML legacy-system simulation
ros-mock       REST/JSON route-system simulation
wms-mock       TCP/IP warehouse-system simulation
api            client-facing FastAPI gateway and order API
worker         asynchronous Saga orchestration
frontend       React client and driver views
```

This is a prototype deployment. In production, API and worker replicas could be independently scaled behind a load balancer, while a managed PostgreSQL cluster and RabbitMQ cluster provide high availability.
