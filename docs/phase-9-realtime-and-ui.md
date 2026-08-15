# Phase 9: Real-Time Tracking and Web Interface

## Goal

Phase 9 provides a small client/driver interface and a live status stream. The browser can submit an order, follow its state without refreshing, and perform the driver actions from Phase 8.

## Real-time contract

Connect to:

```text
ws://localhost:8000/ws/orders/<order-id>
```

The API sends a JSON snapshot immediately and sends another snapshot whenever the persisted order changes:

```json
{
  "id": "order UUID",
  "status": "READY_FOR_DELIVERY",
  "route_summary": "VAN-01 via ...",
  "failure_step": null,
  "failure_reason": null,
  "updated_at": "UTC timestamp",
  "history": []
}
```

The prototype uses a short database poll behind the WebSocket. This keeps the API and worker independently deployable while ensuring that worker-written status changes are visible to connected browsers. A production version could replace the poll with a dedicated status-event consumer.

## Frontend responsibilities

The React/Vite frontend at `http://localhost:5173` contains:

- A client form for submitting a delivery order.
- An order lookup field for an existing order UUID.
- A live lifecycle progress strip and status history.
- Driver actions for dispatch, successful delivery, and failed delivery.
- A visible connection state and error message.

The browser calls the API at `http://localhost:8000` and opens the WebSocket at `ws://localhost:8000`.

## Owner verification checkpoint

Build and start the frontend manually:

```bash
docker compose up -d --build frontend
```

Open [http://localhost:5173](http://localhost:5173), submit an order, and observe that the status changes from `RECEIVED` through the worker workflow without refreshing the page. When the order becomes `READY_FOR_DELIVERY`, use the driver controls to dispatch and complete it.

For a stronger demonstration, keep the browser open on an order while using the ROS failure switch or driver API from another terminal. The timeline should update when the persisted status changes.

## Slower evidence capture mode

The worker supports an optional demonstration delay between visible workflow stages. This makes the `RECEIVED`, `PROCESSING`, adapter, and `READY_FOR_DELIVERY` states easier to capture without changing the normal default behavior.

In the local `.env` file, add:

```text
WORKFLOW_DEMO_DELAY_SECONDS=3
```

Then recreate the worker:

```bash
docker compose up -d --build worker
```

Use `0` when the slower demonstration mode is no longer needed.
