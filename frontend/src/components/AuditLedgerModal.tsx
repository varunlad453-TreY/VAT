"use client";

import React, { useEffect, useState } from "react";
import { useNOCStore } from "@/store/useNOCStore";
import { AuditLedgerEntry } from "@/types/vat";
import { Clock, Database, History, RefreshCw, Shield, Terminal, X } from "lucide-react";

interface AuditLedgerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuditLedgerModal({ isOpen, onClose }: AuditLedgerModalProps) {
  const auditHistory = useNOCStore((state) => state.auditHistory);
  const fetchAuditHistory = useNOCStore((state) => state.fetchAuditHistory);
  const [selectedRecord, setSelectedRecord] = useState<AuditLedgerEntry | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchAuditHistory();
    }
  }, [isOpen, fetchAuditHistory]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-obsidian-900 border border-obsidian-700 rounded-lg w-full max-w-5xl h-[80vh] flex flex-col shadow-2xl overflow-hidden font-mono">
        {/* Modal Header */}
        <div className="p-3.5 border-b border-obsidian-700 bg-obsidian-850 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-brand-cyan" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              PERMANENT TROUBLESHOOTING AUDIT LEDGER (POSTGRESQL)
            </h3>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => fetchAuditHistory()}
              className="text-xs text-obsidian-400 hover:text-white p-1 rounded hover:bg-obsidian-800"
              title="Refresh Audit History"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onClose}
              className="text-obsidian-400 hover:text-white p-1 rounded hover:bg-obsidian-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left List */}
          <div className="w-1/2 border-r border-obsidian-800 overflow-y-auto divide-y divide-obsidian-800/80">
            {auditHistory.length === 0 ? (
              <div className="p-8 text-center text-xs text-obsidian-500">
                No audit records found in PostgreSQL ledger.
              </div>
            ) : (
              auditHistory.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedRecord(item)}
                  className={`p-3 cursor-pointer transition text-xs ${
                    selectedRecord?.id === item.id
                      ? "bg-blue-950/50 border-l-2 border-brand-cyan"
                      : "hover:bg-obsidian-850"
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="font-bold text-white uppercase">
                      {item.vendor} &bull; {item.device_id}
                    </span>
                    <span className="text-obsidian-500 text-[10px]">
                      {new Date(item.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-obsidian-300 line-clamp-2">{item.diagnosis}</div>
                  <div className="flex items-center justify-between mt-2 text-[10px] text-obsidian-500">
                    <span>RISK: {item.risk_level}</span>
                    <span>CONFIDENCE: {(item.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Right Detail Pane */}
          <div className="w-1/2 p-4 overflow-y-auto bg-obsidian-950 text-xs space-y-4">
            {selectedRecord ? (
              <>
                <div>
                  <div className="text-[10px] text-obsidian-500">DIAGNOSIS</div>
                  <div className="text-white font-semibold mt-0.5 leading-snug">
                    {selectedRecord.diagnosis}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-obsidian-500">ROOT CAUSE</div>
                  <div className="text-cyan-300 mt-0.5 leading-relaxed">
                    {selectedRecord.root_cause}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-obsidian-500 mb-1">REMEDIATION COMMANDS</div>
                  <div className="space-y-1.5">
                    {selectedRecord.remediation_steps.map((r: any, i: number) => (
                      <div key={i} className="cli-box">
                        {r.command || JSON.stringify(r)}
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-obsidian-500 mb-1">ROLLBACK PLAYBOOK</div>
                  <div className="space-y-1.5">
                    {selectedRecord.rollback_steps.map((rb: any, i: number) => (
                      <div key={i} className="cli-box text-amber-300">
                        {rb.command || JSON.stringify(rb)}
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-obsidian-600 text-xs">
                Select an audit record to inspect details.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
