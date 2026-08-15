# SwiftTrack Evidence Log

This log maps captured demonstration evidence to the assignment acceptance criteria. Screenshots should be saved separately with the matching evidence ID; do not include `.env` or credentials.

## Captured evidence

### E01 — Docker Compose startup

- **Requirement:** The complete system starts through Docker Compose.
- **Evidence:** Startup screenshot supplied by the project owner: `Screenshot 2026-08-15 at 19.22.52.png`.
- **Observed result:** Compose started `8/8` containers. PostgreSQL, RabbitMQ, CMS mock, ROS mock, WMS mock, and API were healthy; worker and frontend were running. Exposed ports were visible for the API, frontend, mocks, and RabbitMQ Management.
- **Status:** Captured.

### E02 — Order creation and immediate acceptance

- **Requirement:** A client submits a valid order and immediately receives an order ID and `RECEIVED` status.
- **Evidence:** Terminal screenshot supplied by the project owner: `Screenshot 2026-08-15 at 19.28.29.png`.
- **Observed result:** The POST request used the new idempotency key `evidence-order-shan-001` and returned order UUID `a2713441-85c2-4bd3-bd3c-216cdc899671` with status `RECEIVED` and the initial order-history entry.
- **Status:** Captured.

### E03 — Normal asynchronous processing

- **Requirement:** The middleware processes the order asynchronously through CMS, WMS, and ROS and exposes the resulting status.
- **Evidence:** Terminal and browser captures supplied by the project owner: `Screenshot 2026-08-15 at 19.32.06.png` and `Screenshot 2026-08-15 at 19.32.27.png`.
- **Order:** `a2713441-85c2-4bd3-bd3c-216cdc899671`.
- **Observed result:** The order reached `READY_FOR_DELIVERY`. Its history contains `PROCESSING`, `CMS_CONFIRMED`, `WMS_ACCEPTED`, `ROUTE_PLANNED`, and the final successful-completion entry. The route summary is `VAN-01 via Swift Logistics Warehouse -> 50 Galle Road, Colombo 03 (40 min)`.
- **Status:** Captured.

### E04 — Idempotent duplicate submission

- **Requirement:** Reusing an idempotency key must not create a duplicate order.
- **Evidence:** Terminal and browser captures supplied by the project owner: `Screenshot 2026-08-15 at 19.37.00.png` and `Screenshot 2026-08-15 at 19.37.19.png`.
- **Command:** A second `POST /api/orders` used the same key `evidence-order-shan-001` and the same order payload as E02.
- **Observed result:** The response returned the existing UUID `a2713441-85c2-4bd3-bd3c-216cdc899671`, with the same idempotency key and order details. No new UUID was created.
- **Status:** Captured.

### E05 — Live WebSocket tracking

- **Requirement:** The browser receives status changes without a manual refresh.
- **Evidence:** Frontend captures supplied by the project owner: `Screenshot 2026-08-15 at 20.02.09.png`, `Screenshot 2026-08-15 at 20.02.26.png`, and `Screenshot 2026-08-15 at 20.03.33.png`.
- **Order:** `dac233f9-98e2-41f7-bad9-10c2fe973cae`, created for `E05 WebSocket Customer` at `60 Galle Road, Colombo 03`.
- **Observed result:** E05-0 shows the prepared client form before submission. E05-A shows the same page receiving the order at `RECEIVED` with `Live tracking connected`. E05-B shows the same UUID progressing automatically to `READY_FOR_DELIVERY`, with `PROCESSING`, `CMS_CONFIRMED`, `WMS_ACCEPTED`, `ROUTE_PLANNED`, and `READY_FOR_DELIVERY` visible in the timeline.
- **Status:** Captured.

### E06 — ROS failure, retry, and terminal failure state

- **Requirement:** A downstream ROS failure is recorded, retried, and surfaced without losing the earlier CMS/WMS results.
- **Evidence:** Terminal response supplied by the project owner after the fresh E06 run.
- **Order:** `deeac335-fd09-47e2-8257-ec630ffc7ad6`, created with idempotency key `e06-ros-failure-shan-001`.
- **Observed result:** CMS and WMS completed once. ROS returned HTTP `503 Service Unavailable`. The response history shows the initial attempt plus three retries, and the final state is `PROCESSING_FAILED` with `failure_step=ROS` and the ROS URL in `failure_reason`.
- **Status:** Captured.

### E07 — RabbitMQ dead-letter queue

- **Requirement:** A message that exhausts processing retries is retained in a durable dead-letter queue.
- **Evidence:** RabbitMQ Management captures supplied by the project owner: `Screenshot 2026-08-15 at 21.33.54.png` and `Screenshot 2026-08-15 at 21.34.08.png`.
- **Order:** `deeac335-fd09-47e2-8257-ec630ffc7ad6`, the fresh E06 ROS-failure order.
- **Observed result:** `swifttrack.order-processing.dlq` contains one ready message, zero unacknowledged messages, and one total message. The queue is bound from `swifttrack.events` using routing key `order.processing.dead`.
- **Status:** Captured.

### E08 — Driver acceptance

- **Requirement:** A ready order can be accepted by a driver and moved to `OUT_FOR_DELIVERY`.
- **Evidence:** Frontend capture supplied by the project owner: `Screenshot 2026-08-15 at 20.18.27.png`.
- **Order:** `dac233f9-98e2-41f7-bad9-10c2fe973cae`, the same order used for E05.
- **Observed result:** The live UI shows `OUT_FOR_DELIVERY`, the same order UUID, the completed middleware timeline, and the message `Driver accepted the order.`
- **Status:** Captured.

### E09 — Driver-reported delivery failure

- **Requirement:** A driver can report a delivery failure with a reason.
- **Evidence:** Frontend capture supplied by the project owner: `Screenshot 2026-08-15 at 20.18.53.png`.
- **Order:** `dac233f9-98e2-41f7-bad9-10c2fe973cae`, continuing from E08.
- **Observed result:** The live UI shows `DELIVERY_FAILED`, the same UUID, the `OUT_FOR_DELIVERY` history step, and the confirmation message `Delivery failure recorded.`
- **Status:** Captured.

### E10 — GitHub repository and reproducible source

- **Requirement:** The completed project source and documentation are maintained in a version-controlled repository.
- **Evidence:** GitHub repository capture supplied by the project owner: `Screenshot 2026-08-15 at 21.50.39.png`.
- **Repository:** [github.com/alexmps2003/MW2](https://github.com/alexmps2003/MW2), public repository on the `main` branch.
- **Observed result:** The repository root visibly contains `docs/`, `frontend/`, `scripts/`, `services/`, `tests/`, `README.md`, `.env.example`, and `docker-compose.yml`; the README preview identifies the SwiftTrack Middleware Prototype.
- **Status:** Captured.

### E11 — Successful driver delivery

- **Requirement:** A driver can complete a ready order, and the client receives the final `DELIVERED` update.
- **Evidence:** Frontend capture supplied by the project owner: `Screenshot 2026-08-15 at 21.58.09.png`.
- **Order:** `a2713441-85c2-4bd3-bd3c-216cdc899671`, the normal-flow order used in E02–E04.
- **Observed result:** The live portal shows `DELIVERED`, the same order UUID, all lifecycle progress stages completed, `Live tracking connected`, and the confirmation message `Delivery completed.`
- **Status:** Captured.

## Pending evidence

All planned evidence items are captured.
