"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { AuditRecord } from "@/types/vat";
import { Clock, RefreshCw, Shield, Terminal, X } from "lucide-react";

interface AuditLedgerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuditLedgerModal({ isOpen, onClose }: AuditLedgerModalProps) {
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchAudit();
    }
  }, [isOpen]);

  const fetchAudit = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditHistory({ limit: 30 });
      setRecords(data);
    } catch (err) {
      console.error("Failed to load audit history:", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 select-none font-mono">
      <div className="bg-[#080d17] border border-[#172236] w-full max-w-4xl max-h-[85vh] flex flex-col text-xs shadow-2xl">
        {/* Header */}
        <div className="h-11 px-4 border-b border-[#172236] bg-[#0a0f1b] flex items-center justify-between">
          <div className="flex items-center space-x-2 text-slate-200 font-bold uppercase tracking-wider text-[11px]">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <span>POSTGRESQL AUDIT LEDGER // IMMUTABLE RUNBOOK HISTORY</span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={fetchAudit}
              disabled={loading}
              className="text-slate-400 hover:text-white p-1"
              title="Refresh Audit Records"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1"
              title="Close Dialog"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Table (Flat, Dense) */}
        <div className="flex-1 overflow-y-auto p-4">
          {records.length === 0 ? (
            <div className="py-12 text-center text-slate-500 font-sans">
              {loading ? "Querying PostgreSQL audit tables..." : "No permanent audit records logged yet."}
            </div>
          ) : (
            <div className="space-y-4">
              {records.map((rec, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-[#05080e] border-l-2 border-cyan-500 space-y-2"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <div className="flex items-center space-x-2 font-semibold text-slate-200">
                      <span className="uppercase text-cyan-400">{rec.vendor}</span>
                      <span className="text-slate-600">·</span>
                      <span>HOST: {rec.device_id}</span>
                      <span className="text-slate-600">·</span>
                      <span className="text-emerald-400 font-normal">
                        Confidence: {(rec.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="text-slate-500 text-[10px]">
                      {new Date(rec.created_at).toLocaleString()}
                    </div>
                  </div>

                  <div className="text-xs font-sans font-medium text-slate-300">
                    {rec.failure_diagnosis}
                  </div>

                  <div className="text-[11px] text-slate-500 font-mono">
                    <span className="text-slate-400">Blast Radius:</span> {rec.blast_radius} ·{" "}
                    <span className="text-slate-400">Pre-checks:</span> {rec.runbook_pre_checks?.length || 0} ·{" "}
                    <span className="text-slate-400">Remediations:</span> {rec.runbook_remediation?.length || 0} ·{" "}
                    <span className="text-slate-400">Rollbacks:</span> {rec.runbook_rollback?.length || 0}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="h-9 px-4 border-t border-[#172236] bg-[#0a0f1b] flex items-center justify-between text-[10px] text-slate-500">
          <span>Storage: PostgreSQL JSONB Partitioned Ledger</span>
          <span>Showing {records.length} recent records</span>
        </div>
      </div>
    </div>
  );
}
