"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import {
  AuditLedgerEntry,
  HealthResponse,
  TroubleshootRequestDTO,
  TroubleshootResponseDTO,
  VendorDocCitation,
} from "@/types/vat";

/**
 * Lightweight Stale-While-Revalidate Query Hook for Real-Time NOC Health
 */
export function useHealthQuery(intervalMs: number = 10000) {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  const refetch = useCallback(async () => {
    try {
      const res = await api.getHealth();
      setData(res);
      setIsError(false);
    } catch {
      setIsError(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
    const interval = setInterval(refetch, intervalMs);
    return () => clearInterval(interval);
  }, [refetch, intervalMs]);

  return { data, isLoading, isError, refetch };
}

/**
 * Query Hook for TAC Audit History
 */
export function useAuditHistoryQuery(vendor?: string) {
  const [data, setData] = useState<AuditLedgerEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refetch = useCallback(async () => {
    setIsLoading(true);
    try {
      const records = await api.getAuditHistory({
        limit: 50,
        vendor: vendor === "all" ? undefined : vendor,
      });
      setData(records);
    } catch (err) {
      console.debug("Failed to fetch audit records:", err);
    } finally {
      setIsLoading(false);
    }
  }, [vendor]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, isLoading, refetch };
}

/**
 * Mutation Hook for Real-Time Multi-Vendor RAG Troubleshooting
 */
export function useTroubleshootMutation() {
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<TroubleshootResponseDTO | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const mutateAsync = async (req: TroubleshootRequestDTO) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.troubleshoot(req);
      setData(result);
      return result;
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return { mutateAsync, data, isLoading, error };
}
