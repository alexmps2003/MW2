# SwiftTrack Final Demonstration Script

This script is the recommended order for a short assessment demonstration. It shows the normal workflow, protocol integration, asynchronous processing, resilience, and driver actions.

## 1. Start the system

From the `swifttrack` directory:

If `.env` does not already exist, create it from the template, then start the stack:

```bash
cp .env.example .env
docker compose up -d --build
```

Do not overwrite an existing `.env` unless you intentionally want to reset your local configuration.

If status transitions are too fast to capture during the live-tracking demonstration, add `WORKFLOW_DEMO_DELAY_SECONDS=3` to `.env` and recreate only the worker:

```bash
docker compose up -d --build worker
```

This is an optional evidence-capture setting. Return it to `0` afterward.

Open the client portal at `http://localhost:5173` and RabbitMQ Management at `http://localhost:15672` when queue evidence is required. Use the credentials in `.env`.

## 2. Normal order workflow

1. Submit an order from the SwiftTrack client portal.
2. Record the generated order UUID.
3. Show that the browser receives `RECEIVED` immediately.
4. Keep the page open and show the live timeline progressing through:
   - `PROCESSING`
   - `CMS_CONFIRMED`
   - `WMS_ACCEPTED`
   - `ROUTE_PLANNED`
   - `READY_FOR_DELIVERY`
5. Point out the **Live tracking connected** indicator.
6. Select **Accept for delivery** and show `OUT_FOR_DELIVERY`.
7. Select **Mark delivered** and show `DELIVERED`.

This demonstrates the browser, API, database, RabbitMQ worker, protocol adapters, and WebSocket status stream working together.

## 3. Protocol translation preview

For a direct adapter demonstration, use a ready order or a separate demo order:

```bash
curl -X POST http://localhost:8000/api/orders/<order-id>/integration-preview
```

The response should show:

- a CMS response produced through the SOAP/XML adapter;
- a WMS acknowledgement produced through the TCP adapter;
- a ROS route summary produced through the REST/JSON adapter.

## 4. Idempotency demonstration

Submit the same order twice using the same `Idempotency-Key`. The second request should return the existing order rather than creating a second order.

Record the repeated responses or show that both responses contain the same order UUID.

## 5. Resilience and dead-letter demonstration

Use a new idempotency key for this scenario. Enable the ROS failure switch:

```bash
curl -X PUT http://localhost:8002/admin/failure \
  -H "Content-Type: application/json" \
  -d '{"enabled":true,"delay_seconds":0.2}'
```

Create a new order and query it after the worker has exhausted its attempts:

```bash
curl http://localhost:8000/api/orders/<failed-order-id>
```

Show that:

- CMS and WMS completed once;
- ROS failed with HTTP 503;
- the worker retried the event;
- the final state is `PROCESSING_FAILED`;
- `failure_step` is `ROS`.

In RabbitMQ Management, open `swifttrack.order-processing.dlq` and show the retained message. Do not purge it until the evidence has been captured.

Restore ROS after the evidence is captured:

```bash
curl -X PUT http://localhost:8002/admin/failure \
  -H "Content-Type: application/json" \
  -d '{"enabled":false,"delay_seconds":0}'
```

## 6. Driver failure demonstration

For a separate ready order:

1. Track the order in the portal.
2. Select **Accept for delivery**.
3. Enter a reason such as `Recipient was unavailable`.
4. Select **Report failure**.
5. Show the final `DELIVERY_FAILED` state and the recorded reason in the timeline.

## 7. Evidence to capture

Capture only the clearest screenshots or terminal responses for:

1. Docker Compose services running.
2. Normal order creation and live status progression.
3. CMS/WMS/ROS integration response.
4. Same idempotency key returning the same UUID.
5. ROS failure, retries, and `PROCESSING_FAILED`.
6. RabbitMQ dead-letter queue containing the failed message.
7. Driver acceptance and successful delivery.
8. Driver-reported delivery failure.

Do not include `.env` or any credentials in screenshots or in the repository.
