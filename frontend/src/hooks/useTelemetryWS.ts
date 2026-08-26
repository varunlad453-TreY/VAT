/**
 * Real-Time Telemetry & Synthesis WebSocket Hook
 */

import { useEffect, useRef } from "react";
import { useNOCStore } from "@/store/useNOCStore";
import { ParsedTelemetry } from "@/types/vat";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_BASE_URL || "ws://localhost:8000";

export function useTelemetryWS() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const addTelemetryLog = useNOCStore((state) => state.addTelemetryLog);
  const setWsConnected = useNOCStore((state) => state.setWsConnected);

  useEffect(() => {
    let isMounted = true;

    function connect() {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      try {
        const ws = new WebSocket(`${WS_BASE_URL}/ws/telemetry`);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          console.log("[VAT WS] Connected to live telemetry stream.");
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);
            if (data.type === "telemetry_event" && data.parsed) {
              addTelemetryLog(data.parsed as ParsedTelemetry);
            } else if (data.type === "telemetry_broadcast" && data.event) {
              addTelemetryLog(data.event as ParsedTelemetry);
            }
          } catch (e) {
            console.debug("[VAT WS] Raw message received:", event.data);
          }
        };

        ws.onclose = () => {
          if (!isMounted) return;
          console.log("[VAT WS] Disconnected. Attempting reconnect in 3s...");
          setWsConnected(false);
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        };

        ws.onerror = (err) => {
          console.debug("[VAT WS] Connection error:", err);
          ws.close();
        };
      } catch (err) {
        console.debug("[VAT WS] Setup error:", err);
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      }
    }

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [addTelemetryLog, setWsConnected]);

  const sendLog = (rawLog: string, deviceHint?: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ log: rawLog, device_hint: deviceHint }));
    }
  };

  return { sendLog };
}
