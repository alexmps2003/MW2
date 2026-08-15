# SwiftTrack Submission Checklist

## Final documentation package

- [Final technical report](final-report.md)
- [Evidence log](evidence-log.md)
- [Final demonstration script](final-demo-script.md)

## Implementation

- [x] Client order portal is implemented.
- [x] FastAPI gateway and PostgreSQL persistence are implemented.
- [x] CMS SOAP/XML, ROS REST/JSON, and WMS TCP adapters are implemented.
- [x] RabbitMQ event processing and background worker are implemented.
- [x] Retry queue and dead-letter queue are implemented.
- [x] Driver delivery lifecycle is implemented.
- [x] WebSocket live tracking and React/Vite interface are implemented.
- [x] Docker Compose starts the complete local system.

## Acceptance evidence

| Requirement | Evidence to include |
|---|---|
| Order is accepted with an ID and `RECEIVED` status | Portal or terminal capture of order creation |
| Order is persisted before processing | Creation response followed by worker history |
| Three external protocols are integrated | Integration preview response and contract documentation |
| Status changes appear without manual refresh | Portal timeline plus **Live tracking connected** indicator |
| Idempotency prevents duplicates | Two requests with one idempotency key and one UUID |
| ROS failure is retried safely | Failed order history showing repeated ROS attempts |
| Dead-letter handling is visible | RabbitMQ `swifttrack.order-processing.dlq` screenshot |
| Driver can complete or fail delivery | `DELIVERED` and `DELIVERY_FAILED` portal captures |
| Complete system is reproducible | README and Docker Compose startup command |

## Report sections

The existing documentation can be assembled into the final report in this order:

1. Problem, scope, and requirements — `requirements.md`
2. Architecture alternatives and selected design — `architecture-alternatives.md`
3. Technology choices — `technology-stack.md`
4. External contracts and protocol translation — `contracts.md`
5. Asynchronous processing — `phase-6-event-driven.md`
6. Retry and dead-letter resilience — `phase-7-resilience.md`
7. Driver delivery lifecycle — `phase-8-delivery-lifecycle.md`
8. Real-time interface — `phase-9-realtime-and-ui.md`
9. Demonstration evidence — `final-demo-script.md` and captured evidence
10. Limitations and future improvements

## Security and hygiene before submission

- [ ] `.env` remains uncommitted.
- [ ] No passwords, tokens, or private credentials appear in screenshots.
- [ ] Temporary files and university notes are outside the project repository.
- [ ] GitHub repository is private unless the submission instructions require public access.
- [ ] The final README explains how to start the system.
- [ ] The final GitHub commit contains the code and documentation used in the demonstration.
