import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


failure_enabled = False
delay_seconds = 0.2


class RouteHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        print(f"ROS {self.address_string()} - {format % args}", flush=True)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length))

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(200, {"status": "healthy", "failure_mode": failure_enabled})
        else:
            self.send_json(404, {"detail": "not found"})

    def do_POST(self) -> None:
        if self.path != "/routes":
            self.send_json(404, {"detail": "not found"})
            return

        request = self.read_json()
        time.sleep(delay_seconds)
        if failure_enabled:
            self.send_json(503, {"detail": "ROS failure simulation is enabled"})
            return

        vehicles = request.get("available_vehicles", [])
        if not vehicles:
            self.send_json(409, {"detail": "No vehicles available"})
            return

        vehicle = vehicles[1] if request.get("priority") == "HIGH" and len(vehicles) > 1 else vehicles[0]
        self.send_json(
            200,
            {
                "order_id": request.get("order_id"),
                "vehicle": vehicle,
                "stops": ["Swift Logistics Warehouse", request.get("delivery_address")],
                "estimated_minutes": 25 if request.get("priority") == "HIGH" else 40,
            },
        )

    def do_PUT(self) -> None:
        if self.path != "/admin/failure":
            self.send_json(404, {"detail": "not found"})
            return

        mode = self.read_json()
        global failure_enabled, delay_seconds
        failure_enabled = bool(mode.get("enabled", False))
        delay_seconds = float(mode.get("delay_seconds", 0.2))
        self.send_json(200, {"failure_mode": failure_enabled, "delay_seconds": delay_seconds})


if __name__ == "__main__":
    print("Mock ROS REST server listening on 8002", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8002), RouteHandler).serve_forever()
