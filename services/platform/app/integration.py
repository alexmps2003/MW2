import time

from sqlalchemy.orm import Session

from .adapters.cms import create_order as create_cms_order
from .adapters.ros import create_route
from .adapters.wms import register_package
from .config import get_settings
from .models import Order, OrderHistory, OrderStatus


def update_status(db: Session, order: Order, status: OrderStatus, detail: str) -> None:
    order.status = status
    db.add(OrderHistory(order_id=order.id, status=status, detail=detail))
    db.commit()


def _demo_delay() -> None:
    """Optionally slow visible workflow stages for an assessment demonstration."""
    delay = get_settings().workflow_demo_delay_seconds
    if delay > 0:
        time.sleep(delay)


def run_integration_preview(db: Session, order: Order) -> dict[str, str]:
    """Synchronously exercise all adapters before Phase 6 adds the worker queue."""
    update_status(db, order, OrderStatus.PROCESSING, "Synchronous adapter preview started")

    cms_response = create_cms_order(order)
    order.cms_done = True
    update_status(db, order, OrderStatus.CMS_CONFIRMED, f"CMS response: {cms_response}")

    wms_response = register_package(order)
    order.wms_done = True
    update_status(db, order, OrderStatus.WMS_ACCEPTED, f"WMS response: {wms_response}")

    route_summary = create_route(order)
    order.ros_done = True
    order.route_summary = route_summary
    update_status(db, order, OrderStatus.ROUTE_PLANNED, route_summary)

    update_status(db, order, OrderStatus.READY_FOR_DELIVERY, "All three systems completed successfully")
    return {
        "order_id": order.id,
        "cms_response": cms_response,
        "wms_response": wms_response,
        "route_summary": route_summary,
    }


def _mark_workflow_failed(db: Session, order: Order, step: str, exc: Exception) -> None:
    order.status = OrderStatus.PROCESSING_FAILED
    order.failure_step = step
    order.failure_reason = str(exc)[:1000]
    db.add(
        OrderHistory(
            order_id=order.id,
            status=OrderStatus.PROCESSING_FAILED,
            detail=f"Asynchronous workflow failed during {step}: {exc}",
        )
    )
    db.commit()


def run_order_workflow(db: Session, order: Order) -> None:
    """Process an order from a durable order.created message."""
    if order.status == OrderStatus.READY_FOR_DELIVERY:
        return

    if order.status != OrderStatus.PROCESSING:
        order.failure_step = None
        order.failure_reason = None
        _demo_delay()
        update_status(db, order, OrderStatus.PROCESSING, "Asynchronous worker started")

    _demo_delay()

    current_step = "CMS"
    try:
        if not order.cms_done:
            cms_response = create_cms_order(order)
            order.cms_done = True
            update_status(db, order, OrderStatus.CMS_CONFIRMED, f"CMS response: {cms_response}")
            _demo_delay()

        current_step = "WMS"
        if not order.wms_done:
            wms_response = register_package(order)
            order.wms_done = True
            update_status(db, order, OrderStatus.WMS_ACCEPTED, f"WMS response: {wms_response}")
            _demo_delay()

        current_step = "ROS"
        if not order.ros_done:
            route_summary = create_route(order)
            order.ros_done = True
            order.route_summary = route_summary
            update_status(db, order, OrderStatus.ROUTE_PLANNED, route_summary)
            _demo_delay()

        order.failure_step = None
        order.failure_reason = None
        update_status(db, order, OrderStatus.READY_FOR_DELIVERY, "All three systems completed successfully")
    except Exception as exc:
        _mark_workflow_failed(db, order, current_step, exc)
        raise
