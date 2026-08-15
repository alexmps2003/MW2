# External System Contracts

The middleware will use one internal order model and convert it at each external-system boundary. This keeps protocol details inside adapters.

## CMS SOAP/XML

- WSDL: `http://localhost:8001/?wsdl`
- Operation: `create_order(order_id, client_id, recipient_name, delivery_address, priority)`
- Result: `CREATED:<order-id>` or `ALREADY_EXISTS:<order-id>`
- Operation: `get_order_status(order_id)`
- Result: `REGISTERED` or `NOT_FOUND`

## ROS REST/JSON

### Request

`POST http://localhost:8002/routes`

```json
{
  "order_id": "order UUID",
  "delivery_address": "42 Galle Road, Colombo 03",
  "priority": "NORMAL",
  "available_vehicles": ["VAN-01", "BIKE-02"]
}
```

### Response

```json
{
  "order_id": "order UUID",
  "vehicle": "VAN-01",
  "stops": ["Swift Logistics Warehouse", "42 Galle Road, Colombo 03"],
  "estimated_minutes": 40
}
```

### Failure simulation

`PUT http://localhost:8002/admin/failure`

```json
{
  "enabled": true,
  "delay_seconds": 0.2
}
```

When enabled, route requests return HTTP 503.

## WMS TCP/IP

- TCP port: `9003`
- Encoding: UTF-8
- Framing: one newline-terminated message per connection
- Delimiter: `|`

Request:

```text
REGISTER|<order-id>|<package-id>|<delivery-address>\n
```

Successful responses:

```text
ACK|<order-id>|PACKAGE_REGISTERED\n
ACK|<order-id>|ALREADY_REGISTERED\n
```

Invalid requests receive:

```text
ERROR|INVALID_MESSAGE\n
```

The repeated-order response is intentional: it demonstrates idempotent behaviour when middleware retries a message.
