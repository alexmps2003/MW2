import httpx

from ..config import get_settings
from ..models import Order


def create_route(order: Order) -> str:
    response = httpx.post(
        f"{get_settings().ros_url}/routes",
        json={
            "order_id": order.id,
            "delivery_address": order.delivery_address,
            "priority": order.priority,
            "available_vehicles": ["VAN-01", "BIKE-02"],
        },
        timeout=3.0,
    )
    response.raise_for_status()
    route = response.json()
    return f"{route['vehicle']} via {' -> '.join(route['stops'])} ({route['estimated_minutes']} min)"

