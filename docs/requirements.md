# SwiftTrack Prototype Requirements

## 1. Purpose

SwiftTrack is a middleware prototype for Swift Logistics. It connects three independent systems that use incompatible communication methods:

- Client Management System (CMS): SOAP/XML
- Route Optimisation System (ROS): REST/JSON
- Warehouse Management System (WMS): proprietary TCP/IP messages

The prototype must demonstrate protocol translation, asynchronous order processing, safe recovery from partial failures, and real-time order-status updates.

## 2. Why Middleware Is Needed

The client portal cannot communicate directly with every back-end system because each one uses a different protocol and data format. SwiftTrack is the integration layer: it accepts a normal order request, translates that request for each system, coordinates processing, and reports progress back to the client.

## 3. Users

| User | Goal in the prototype |
|---|---|
| E-commerce client | Submit an order and follow its delivery status in real time. |
| Driver | View an assigned delivery and mark it delivered or failed. |
| System operator | Observe queued orders and demonstrate recovery when a back-end system fails. |

## 4. In-Scope Features

The prototype will include:

- A client portal that submits delivery orders and displays order progress.
- A small driver view that completes or fails a delivery with a reason.
- A mock CMS that receives SOAP/XML requests.
- A mock ROS that receives REST/JSON requests and returns a simple route.
- A mock WMS that receives proprietary TCP/IP messages.
- Middleware adapters that translate one internal order model into the three external protocols.
- Asynchronous order processing, so the portal does not wait for CMS, ROS, and WMS.
- Persistent order and workflow state, so an accepted order is not silently lost.
- Real-time status updates in the client interface.
- A controlled ROS failure scenario that demonstrates retry and safe failure handling.
- Duplicate-submission protection using an idempotency key.

## 5. Out-of-Scope Features

The following are intentionally represented only as future work or architecture notes:

- A real route-optimisation algorithm.
- Real billing, contracts, and invoicing.
- Native Android or iOS applications.
- Actual signature or photo storage for proof of delivery.
- A production cloud deployment or Kubernetes cluster.
- A commercial push-notification service.
- Production-grade identity-provider integration.

Keeping these out of scope lets the team prove the middleware architecture thoroughly within the assignment timeframe.

## 6. Order Lifecycle

```text
RECEIVED
  -> PROCESSING
  -> CMS_CONFIRMED
  -> WMS_ACCEPTED
  -> ROUTE_PLANNED
  -> READY_FOR_DELIVERY
  -> OUT_FOR_DELIVERY
  -> DELIVERED

An order can also become PROCESSING_FAILED or DELIVERY_FAILED.
```

`PROCESSING_FAILED` means that CMS, WMS, or ROS could not complete a middleware step after retries. `DELIVERY_FAILED` means the driver attempted delivery but could not complete it, for example because the recipient was unavailable.

## 7. Acceptance Criteria

The prototype is complete when all of the following can be demonstrated:

1. A client submits a valid order and immediately receives an order ID and `RECEIVED` status.
2. The order is persisted before the system acknowledges it.
3. The middleware sends the order to CMS through SOAP/XML, WMS through TCP/IP, and ROS through REST/JSON.
4. The client sees each status change without manually refreshing the page.
5. A repeated request with the same idempotency key does not create a duplicate order.
6. When ROS is unavailable, processing retries safely and the accepted order remains visible with a useful failure state.
7. A failed message can be inspected in a Dead-Letter Queue after retries are exhausted.
8. A driver can mark a ready order as delivered or failed, and the client receives the update.
9. The complete system starts with one documented Docker Compose command.

## 8. Key Quality Goals

- Reliability: an accepted order is not silently lost.
- Resilience: one unavailable back-end system does not freeze the client portal.
- Scalability: portal/API instances and background workers can scale independently.
- Security: validate input, restrict user actions by role, keep secrets out of source code, and document secure production communication.
- Observability: record order history, correlation IDs, health checks, and meaningful logs.
- Portability: use only open-source technologies and run locally through Docker Compose.
