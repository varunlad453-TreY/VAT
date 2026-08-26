/**
 * Typed REST API Client for VAT Enterprise Backend
 */

import {
  AuditLedgerEntry,
  HealthResponse,
  ParsedTelemetry,
  TelemetryIngestBatchRequestDTO,
  TelemetryIngestResponseDTO,
  TroubleshootRequestDTO,
  TroubleshootResponseDTO,
  VendorDocCitation,
} from "@/types/vat";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error ${res.status}: ${errorText || res.statusText}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  /** Synthesize 4-stage operational remediation runbook */
  async troubleshoot(req: TroubleshootRequestDTO): Promise<TroubleshootResponseDTO> {
    return fetchJson<TroubleshootResponseDTO>(`${API_BASE_URL}/troubleshoot`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  /** Query indexed vendor TAC documentation */
  async listSources(params?: {
    query?: string;
    vendor?: string;
    protocol?: string;
    limit?: number;
  }): Promise<VendorDocCitation[]> {
    const searchParams = new URLSearchParams();
    if (params?.query) searchParams.set("query", params.query);
    if (params?.vendor) searchParams.set("vendor", params.vendor);
    if (params?.protocol) searchParams.set("protocol", params.protocol);
    if (params?.limit) searchParams.set("limit", params.limit.toString());

    return fetchJson<VendorDocCitation[]>(
      `${API_BASE_URL}/troubleshoot/sources?${searchParams.toString()}`
    );
  },

  /** Retrieve permanent troubleshooting audit ledger history */
  async getAuditHistory(params?: {
    limit?: number;
    vendor?: string;
  }): Promise<AuditLedgerEntry[]> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.vendor) searchParams.set("vendor", params.vendor);

    return fetchJson<AuditLedgerEntry[]>(
      `${API_BASE_URL}/troubleshoot/audit?${searchParams.toString()}`
    );
  },

  /** Parse single raw telemetry log line */
  async parseLog(rawLog: string, deviceHint?: string): Promise<ParsedTelemetry> {
    const searchParams = new URLSearchParams();
    searchParams.set("raw_log", rawLog);
    if (deviceHint) searchParams.set("device_hint", deviceHint);

    return fetchJson<ParsedTelemetry>(
      `${API_BASE_URL}/telemetry/parse?${searchParams.toString()}`,
      { method: "POST" }
    );
  },

  /** Batch ingest telemetry syslog stream */
  async ingestBatch(
    req: TelemetryIngestBatchRequestDTO
  ): Promise<TelemetryIngestResponseDTO> {
    return fetchJson<TelemetryIngestResponseDTO>(`${API_BASE_URL}/telemetry/ingest`, {
      method: "POST",
      body: JSON.stringify(req),
    });
  },

  /** Service health probe */
  async getHealth(): Promise<HealthResponse> {
    return fetchJson<HealthResponse>(`${API_BASE_URL}/health`);
  },
};
