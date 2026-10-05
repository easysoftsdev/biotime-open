/**
 * WebSocket client for live punch feed.
 */

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export type WsMessage =
  | { type: "punch"; employee_name: string; employee_id: string; event_time: string; verify_type: number; status: string; device_serial: string }
  | { type: "device_status"; device_id: string; serial: string; status: string }
  | { type: "connected"; message: string }
  | { type: "pong" };

export class LiveFeedSocket {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private handlers: Array<(msg: WsMessage) => void> = [];
  private pingInterval: ReturnType<typeof setInterval> | null = null;

  connect(token: string) {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.ws = new WebSocket(`${WS_BASE}/ws/live?token=${token}`);

    this.ws.onopen = () => {
      this.pingInterval = setInterval(() => {
        this.ws?.send(JSON.stringify({ type: "ping" }));
      }, 30_000);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WsMessage;
        this.handlers.forEach((h) => h(msg));
      } catch {}
    };

    this.ws.onclose = () => {
      this._cleanup();
      // Auto-reconnect after 3s
      this.reconnectTimer = setTimeout(() => {
        this.connect(token);
      }, 3_000);
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  onMessage(handler: (msg: WsMessage) => void) {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  disconnect() {
    this._cleanup();
    this.ws?.close();
    this.ws = null;
  }

  private _cleanup() {
    if (this.pingInterval) clearInterval(this.pingInterval);
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
  }
}

export const liveFeedSocket = new LiveFeedSocket();
