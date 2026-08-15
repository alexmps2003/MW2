import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .database import SessionLocal, create_tables, get_db
from .integration import run_integration_preview
from .messaging import publish_order_created
from .models import Order, OrderHistory, OrderStatus
from .schemas import DeliveryUpdate, IntegrationPreviewResponse, OrderCreate, OrderResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="SwiftTrack API Gateway",
    version="1.0.0",
    description="Client-facing boundary for the SwiftLogistics middleware prototype.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def order_query():
    return select(Order).options(selectinload(Order.history))


def find_order(db: Session, order_id: str) -> Order:
    order = db.scalar(
        order_query()
        .where(Order.id == order_id)
        .execution_options(populate_existing=True)
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def order_snapshot(order_id: str) -> dict | None:
    """Read the small payload sent to a live tracking WebSocket."""
    db = SessionLocal()
    try:
        order = db.scalar(order_query().where(Order.id == order_id))
        if not order:
            return None
        return {
            "id": order.id,
            "status": order.status.value,
            "route_summary": order.route_summary,
            "failure_step": order.failure_step,
            "failure_reason": order.failure_reason,
            "updated_at": order.updated_at.isoformat(),
            "history": [
                {
                    "status": entry.status.value,
                    "detail": entry.detail,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in order.history
            ],
        }
    finally:
        db.close()


def enqueue_order(order: Order) -> None:
    try:
        publish_order_created(order.id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Order was saved but could not be queued; retry with the same Idempotency-Key",
        ) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "swifttrack-api"}


@app.websocket("/ws/orders/{order_id}")
async def order_status_socket(websocket: WebSocket, order_id: str) -> None:
    """Stream persisted order changes without requiring browser refreshes."""
    await websocket.accept()
    last_revision: tuple[str, int] | None = None
    try:
        while True:
            snapshot = await asyncio.to_thread(order_snapshot, order_id)
            if snapshot is None:
                await websocket.close(code=4404, reason="Order not found")
                return

            revision = (snapshot["updated_at"], len(snapshot["history"]))
            if revision != last_revision:
                await websocket.send_json(snapshot)
                last_revision = revision
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return


@app.post("/api/orders", response_model=OrderResponse, status_code=status.HTTP_202_ACCEPTED)
def create_order(
    request: OrderCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=100),
    db: Session = Depends(get_db),
) -> Order:
    existing = db.scalar(order_query().where(Order.idempotency_key == idempotency_key))
    if existing:
        if existing.status == OrderStatus.RECEIVED:
            enqueue_order(existing)
        return existing

    order = Order(idempotency_key=idempotency_key, **request.model_dump())
    db.add(order)
    db.flush()
    db.add(OrderHistory(order_id=order.id, status=OrderStatus.RECEIVED, detail="Order accepted by SwiftTrack"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(order_query().where(Order.idempotency_key == idempotency_key))
        if existing:
            return existing
        raise

    accepted_order = find_order(db, order.id)
    enqueue_order(accepted_order)
    return accepted_order


@app.get("/api/orders", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db)) -> list[Order]:
    return list(db.scalars(order_query().order_by(Order.created_at.desc())).unique())


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(get_db)) -> Order:
    return find_order(db, order_id)


@app.post("/api/orders/{order_id}/dispatch", response_model=OrderResponse)
def dispatch_order(order_id: str, db: Session = Depends(get_db)) -> Order:
    """Move a ready order into the driver's active delivery route."""
    order = find_order(db, order_id)
    if order.status == OrderStatus.OUT_FOR_DELIVERY:
        return order
    if order.status != OrderStatus.READY_FOR_DELIVERY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only READY_FOR_DELIVERY orders can be dispatched",
        )

    order.status = OrderStatus.OUT_FOR_DELIVERY
    db.add(
        OrderHistory(
            order_id=order.id,
            status=OrderStatus.OUT_FOR_DELIVERY,
            detail="Driver accepted the order for delivery",
        )
    )
    db.commit()
    return find_order(db, order.id)


@app.post("/api/orders/{order_id}/delivery", response_model=OrderResponse)
def update_delivery(
    order_id: str,
    request: DeliveryUpdate,
    db: Session = Depends(get_db),
) -> Order:
    """Record the driver's final delivery outcome."""
    order = find_order(db, order_id)
    target_status = OrderStatus(request.outcome)

    if order.status == target_status:
        return order
    if order.status in {OrderStatus.DELIVERED, OrderStatus.DELIVERY_FAILED}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A completed delivery cannot be changed",
        )
    if order.status != OrderStatus.OUT_FOR_DELIVERY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only OUT_FOR_DELIVERY orders can be completed",
        )

    order.status = target_status
    if target_status == OrderStatus.DELIVERED:
        order.failure_step = None
        order.failure_reason = None
        detail = "Driver confirmed successful delivery"
    else:
        order.failure_step = "DELIVERY"
        order.failure_reason = request.reason
        detail = f"Driver reported delivery failure: {request.reason}"

    db.add(OrderHistory(order_id=order.id, status=target_status, detail=detail))
    db.commit()
    return find_order(db, order.id)


@app.post(
    "/api/orders/{order_id}/integration-preview",
    response_model=IntegrationPreviewResponse,
)
def integration_preview(order_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    order = find_order(db, order_id)
    if order.status == OrderStatus.READY_FOR_DELIVERY:
        raise HTTPException(status_code=409, detail="Order has already completed integration")

    try:
        return run_integration_preview(db, order)
    except Exception as exc:
        order.status = OrderStatus.PROCESSING_FAILED
        order.failure_reason = str(exc)[:1000]
        db.add(
            OrderHistory(
                order_id=order.id,
                status=OrderStatus.PROCESSING_FAILED,
                detail=f"Synchronous integration preview failed: {exc}",
            )
        )
        db.commit()
        raise HTTPException(status_code=502, detail="An external system failed during integration") from exc
