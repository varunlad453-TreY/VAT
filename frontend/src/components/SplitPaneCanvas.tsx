"use client";

import React, { useState } from "react";
import { TelemetryFeed } from "@/components/TelemetryFeed";
import { RunbookCanvas } from "@/components/RunbookCanvas";
import { GroundedCitations } from "@/components/GroundedCitations";
import { AuditLedgerModal } from "@/components/AuditLedgerModal";
import { HeaderBar } from "@/components/HeaderBar";
import { useTelemetryWS } from "@/hooks/useTelemetryWS";

export function SplitPaneCanvas() {
  // Initialize real-time WebSocket connection
  useTelemetryWS();

  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-obsidian-950">
      {/* 1. Header Bar */}
      <HeaderBar onOpenAudit={() => setIsAuditModalOpen(true)} />

      {/* 2. High-Density 3-Column Split-Pane Canvas */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Pane: Live Telemetry Feed */}
        <TelemetryFeed />

        {/* Center Canvas: 4-Stage Operational Runbook */}
        <RunbookCanvas />

        {/* Right Pane: Grounded TAC Manual Citations */}
        <GroundedCitations />
      </div>

      {/* 3. Bottom Status Bar */}
      <footer className="h-6 bg-obsidian-900 border-t border-obsidian-800 px-3 flex items-center justify-between text-[10px] font-mono text-obsidian-400 select-none shrink-0">
        <div className="flex items-center space-x-3">
          <span>VAT ENGINE: v2.0.0 (CLEAN ARCHITECTURE)</span>
          <span className="text-obsidian-600">|</span>
          <span className="text-emerald-400">STATUS: CARRIER-GRADE NOC READY</span>
        </div>

        <div className="flex items-center space-x-4">
          <span>HYBRID VECTOR SEARCH: 0.65 HNSW + 0.35 BM25</span>
          <span className="text-obsidian-600">|</span>
          <span className="text-cyan-400">PORT: 8000 (FASTAPI) &bull; 3000 (NEXT.JS)</span>
        </div>
      </footer>

      {/* 4. Audit Ledger History Modal */}
      <AuditLedgerModal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
      />
    </div>
  );
}
