import socket

from ..config import get_settings
from ..models import Order


def register_package(order: Order) -> str:
    settings = get_settings()
    address = order.delivery_address.replace("|", "/").replace("\n", " ")
    message = f"REGISTER|{order.id}|PKG-{order.id[:8]}|{address}\n"

    with socket.create_connection((settings.wms_host, settings.wms_port), timeout=3.0) as connection:
        connection.sendall(message.encode())
        response = connection.recv(1024).decode().strip()

    if not response.startswith("ACK|"):
        raise RuntimeError(f"WMS rejected the package: {response}")
    return response

