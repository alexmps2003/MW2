import asyncio
import json


packages: dict[str, dict[str, str]] = {}


async def handle_wms(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """Accept one newline-terminated proprietary WMS message per connection."""
    try:
        line = (await reader.readline()).decode().strip()
        parts = line.split("|", 3)

        if len(parts) != 4 or parts[0] != "REGISTER":
            response = "ERROR|INVALID_MESSAGE\n"
        else:
            _, order_id, package_id, address = parts
            if order_id not in packages:
                packages[order_id] = {
                    "package_id": package_id,
                    "address": address,
                    "status": "REGISTERED",
                }
                response = f"ACK|{order_id}|PACKAGE_REGISTERED\n"
            else:
                response = f"ACK|{order_id}|ALREADY_REGISTERED\n"

        writer.write(response.encode())
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def handle_health(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        request_line = (await reader.readline()).decode(errors="replace").strip()
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break

        if request_line.startswith("GET /health"):
            body = json.dumps({"status": "healthy", "packages": len(packages)}).encode()
            status_line = b"HTTP/1.1 200 OK\r\n"
        else:
            body = b'{"detail":"not found"}'
            status_line = b"HTTP/1.1 404 Not Found\r\n"

        headers = (
            status_line
            + b"Content-Type: application/json\r\n"
            + f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode()
        )
        writer.write(headers + body)
        await writer.drain()
    finally:
        writer.close()
        await writer.wait_closed()


async def main() -> None:
    wms_server = await asyncio.start_server(handle_wms, "0.0.0.0", 9003)
    health_server = await asyncio.start_server(handle_health, "0.0.0.0", 8003)
    print("Mock WMS TCP server listening on 9003", flush=True)
    print("Mock WMS health endpoint listening on 8003", flush=True)

    async with wms_server, health_server:
        await asyncio.gather(wms_server.serve_forever(), health_server.serve_forever())


if __name__ == "__main__":
    asyncio.run(main())

