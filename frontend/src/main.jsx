import { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

const lifecycle = [
  "RECEIVED",
  "PROCESSING",
  "CMS_CONFIRMED",
  "WMS_ACCEPTED",
  "ROUTE_PLANNED",
  "READY_FOR_DELIVERY",
  "OUT_FOR_DELIVERY",
  "DELIVERED",
];

function App() {
  const [order, setOrder] = useState(null);
  const [orderIdInput, setOrderIdInput] = useState("");
  const [recipientName, setRecipientName] = useState("Demo Customer");
  const [deliveryAddress, setDeliveryAddress] = useState("100 Galle Road, Colombo 03");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [failureReason, setFailureReason] = useState("Recipient was unavailable");
  const [liveConnected, setLiveConnected] = useState(false);

  useEffect(() => {
    if (!order?.id) {
      setLiveConnected(false);
      return undefined;
    }

    let disposed = false;
    let retryTimer;
    let socket;

    function connect() {
      socket = new WebSocket(`${WS_BASE}/ws/orders/${order.id}`);
      socket.onopen = () => {
        setLiveConnected(true);
        setError("");
      };
      socket.onmessage = (event) => {
        const update = JSON.parse(event.data);
        setLiveConnected(true);
        setError("");
        setOrder((current) => ({ ...current, ...update }));
      };
      socket.onerror = () => {
        setLiveConnected(false);
        setError("Live tracking connection failed; retrying...");
        socket.close();
      };
      socket.onclose = () => {
        setLiveConnected(false);
        if (!disposed) retryTimer = setTimeout(connect, 1000);
      };
    }

    connect();
    return () => {
      disposed = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, [order?.id]);

  const progressIndex = useMemo(() => {
    const displayStatus = order?.status === "DELIVERY_FAILED" ? "OUT_FOR_DELIVERY" : order?.status;
    const index = lifecycle.indexOf(displayStatus);
    return index < 0 ? 0 : index;
  }, [order?.status]);

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Request failed");
    return payload;
  }

  async function createOrder(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      const payload = await request("/api/orders", {
        method: "POST",
        headers: { "Idempotency-Key": `web-demo-${Date.now()}` },
        body: JSON.stringify({
          client_id: "WEB-DEMO",
          recipient_name: recipientName,
          delivery_address: deliveryAddress,
          priority: "NORMAL",
        }),
      });
      setOrder(payload);
      setOrderIdInput(payload.id);
      setNotice("Order accepted. Live tracking is connected.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function loadOrder(event) {
    event.preventDefault();
    setError("");
    setNotice("");
    try {
      const payload = await request(`/api/orders/${orderIdInput.trim()}`);
      setOrder(payload);
      setNotice("Order loaded. Live tracking is connected.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function dispatchOrder() {
    setError("");
    try {
      const payload = await request(`/api/orders/${order.id}/dispatch`, { method: "POST" });
      setOrder(payload);
      setNotice("Driver accepted the order.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function completeDelivery(outcome) {
    setError("");
    try {
      const payload = await request(`/api/orders/${order.id}/delivery`, {
        method: "POST",
        body: JSON.stringify({
          outcome,
          ...(outcome === "DELIVERY_FAILED" ? { reason: failureReason } : {}),
        }),
      });
      setOrder(payload);
      setNotice(outcome === "DELIVERED" ? "Delivery completed." : "Delivery failure recorded.");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <main className="shell">
      <header className="hero">
        <div>
          <p className="eyebrow">SWIFTLOGISTICS / MIDDLEWARE DEMO</p>
          <h1>SwiftTrack</h1>
          <p className="subtitle">One live view for order progress and driver actions.</p>
        </div>
        <div className={`connection ${liveConnected ? "connected" : ""}`}>
          <span className="dot" /> {liveConnected ? "Live tracking connected" : order ? "Connecting to live tracking..." : "No order selected"}
        </div>
      </header>

      <section className="grid">
        <div className="card form-card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">CLIENT PORTAL</p>
              <h2>Create an order</h2>
            </div>
          </div>
          <form onSubmit={createOrder}>
            <label>
              Recipient
              <input value={recipientName} onChange={(event) => setRecipientName(event.target.value)} required />
            </label>
            <label>
              Delivery address
              <input value={deliveryAddress} onChange={(event) => setDeliveryAddress(event.target.value)} required />
            </label>
            <button type="submit">Submit order</button>
          </form>

          <div className="divider"><span>or track an existing order</span></div>
          <form className="lookup" onSubmit={loadOrder}>
            <input
              value={orderIdInput}
              onChange={(event) => setOrderIdInput(event.target.value)}
              placeholder="Order UUID"
              required
            />
            <button className="secondary" type="submit">Track</button>
          </form>
        </div>

        <div className="card tracking-card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">LIVE TRACKING</p>
              <h2>{order ? order.status.replaceAll("_", " ") : "Waiting for an order"}</h2>
            </div>
            {order && <span className="status-pill">{order.status}</span>}
          </div>

          {order ? (
            <>
              <p className="order-id">{order.id}</p>
              <div className="progress">
                {lifecycle.map((state, index) => (
                  <div className={`progress-step ${index <= progressIndex ? "active" : ""}`} key={state}>
                    <span />
                    <small>{state.replaceAll("_", " ")}</small>
                  </div>
                ))}
              </div>
              <div className="timeline">
                {(order.history || []).map((entry) => (
                  <div className="timeline-entry" key={`${entry.status}-${entry.created_at}`}>
                    <span className="timeline-dot" />
                    <div>
                      <strong>{entry.status.replaceAll("_", " ")}</strong>
                      <p>{entry.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-state">Create an order to open a live WebSocket tracking stream.</div>
          )}
        </div>
      </section>

      {order && (order.status === "READY_FOR_DELIVERY" || order.status === "OUT_FOR_DELIVERY") && (
        <section className="card driver-card">
          <div className="card-heading">
            <div>
              <p className="eyebrow">DRIVER VIEW</p>
              <h2>Delivery actions</h2>
            </div>
          </div>
          {order.status === "READY_FOR_DELIVERY" && (
            <button onClick={dispatchOrder}>Accept for delivery</button>
          )}
          {order.status === "OUT_FOR_DELIVERY" && (
            <div className="action-row">
              <button onClick={() => completeDelivery("DELIVERED")}>Mark delivered</button>
              <input value={failureReason} onChange={(event) => setFailureReason(event.target.value)} />
              <button className="danger" onClick={() => completeDelivery("DELIVERY_FAILED")}>Report failure</button>
            </div>
          )}
        </section>
      )}

      {(notice || error) && <div className={`message ${error ? "error" : ""}`}>{error || notice}</div>}
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
