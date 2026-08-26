"use client";

import React from "react";
import { useNOCStore } from "@/store/useNOCStore";
import {
  Activity,
  Database,
  Layers,
  RefreshCw,
  Shield,
  Terminal,
  Zap,
} from "lucide-react";

interface HeaderBarProps {
  onOpenAudit: () => void;
}

export function HeaderBar({ onOpenAudit }: HeaderBarProps) {
  const wsConnected = useNOCStore((state) => state.wsConnected);
  const health = useNOCStore((state) => state.health);
  const activeRunbook = useNOCStore((state) => state.activeRunbook);
  const telemetryCount = useNOCStore((state) => state.telemetryFeed.length);
  const isDemoMode = useNOCStore((state) => state.isDemoMode);
  const loadDemoFixtures = useNOCStore((state) => state.loadDemoFixtures);
  const clearFeed = useNOCStore((state) => state.clearFeed);

  const isDbConnected = health?.database_connected ?? false;

  return (
    <header className="h-11 bg-[#090d16] border-b border-[#172236] px-4 flex items-center justify-between shrink-0 select-none text-xs font-mono">
      {/* Left: Brand Identity & Supported Multi-Vendor Engines */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-white">
          <span className="font-bold tracking-wider text-sm">
            VAT<span className="text-cyan-400"> // NOC</span>
          </span>
          <span className="text-[10px] text-slate-500 font-normal">
            TIER-1 REMEDIATION
          </span>
        </div>

        <span className="text-slate-700">|</span>

        <div className="hidden lg:flex items-center space-x-2 text-[11px] text-slate-400">
          <span className="text-slate-500">ENGINES:</span>
          <span>Cisco</span>
          <span className="text-slate-700">·</span>
          <span>Juniper</span>
          <span className="text-slate-700">·</span>
          <span>VeloCloud</span>
          <span className="text-slate-700">·</span>
          <span>Arista</span>
        </div>
      </div>

      {/* Center: Inline Real-Time Status & Metrics */}
      <div className="hidden md:flex items-center space-x-4 text-[11px] text-slate-400">
        <div>
          <span className="text-slate-500">EVENTS:</span>{" "}
          <span className="text-slate-200 font-semibold">{telemetryCount}</span>
        </div>

        <span className="text-slate-700">·</span>

        <div>
          <span className="text-slate-500">PGVECTOR:</span>{" "}
          <span className={isDbConnected ? "text-emerald-400 font-medium" : "text-amber-400 font-medium"}>
            {isDbConnected ? "ONLINE (HNSW+RRF)" : "AIR-GAPPED"}
          </span>
        </div>

        {activeRunbook && (
          <>
            <span className="text-slate-700">·</span>
            <div>
              <span className="text-slate-500">CONFIDENCE:</span>{" "}
              <span className="text-cyan-400 font-semibold">
                {(activeRunbook.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </>
        )}

        {isDemoMode && (
          <>
            <span className="text-slate-700">·</span>
            <div className="text-amber-400 flex items-center space-x-1">
              <span>[DEMO FIXTURES]</span>
              <button
                onClick={clearFeed}
                className="text-slate-400 hover:text-white underline ml-1"
              >
                Clear
              </button>
            </div>
          </>
        )}
      </div>

      {/* Right: Operational Controls & Live Connection State */}
      <div className="flex items-center space-x-3 text-[11px]">
        <button
          onClick={loadDemoFixtures}
          title="Load Isolated QA Test Scenarios"
          className="text-slate-400 hover:text-amber-300 transition flex items-center space-x-1"
        >
          <Zap className="w-3 h-3 text-amber-400" />
          <span className="hidden sm:inline">DEMO FIXTURES</span>
        </button>

        <button
          onClick={onOpenAudit}
          className="text-slate-400 hover:text-cyan-300 transition flex items-center space-x-1"
        >
          <Terminal className="w-3 h-3 text-cyan-400" />
          <span>AUDIT LEDGER</span>
        </button>

        <span className="text-slate-700">|</span>

        {/* Live Status Indicator */}
        <div className="flex items-center space-x-1.5 font-medium">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              wsConnected ? "bg-emerald-400 live-dot" : "bg-amber-400"
            }`}
          />
          <span className={wsConnected ? "text-emerald-400" : "text-amber-400"}>
            {wsConnected ? "STREAM ACTIVE" : "OFFLINE"}
          </span>
        </div>
      </div>
    </header>
  );
}
