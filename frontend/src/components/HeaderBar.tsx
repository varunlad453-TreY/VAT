"use client";

import React from "react";
import { useNOCStore } from "@/store/useNOCStore";
import {
  Activity,
  AlertCircle,
  Database,
  Layers,
  Radio,
  RefreshCw,
  Server,
  ShieldAlert,
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
    <header className="h-14 bg-obsidian-900 border-b border-obsidian-700/80 px-4 flex items-center justify-between shrink-0 select-none">
      {/* Left: Brand Identity & Tier-1 Indicator */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 bg-gradient-to-r from-blue-900/50 to-obsidian-800 border border-blue-600/40 px-2.5 py-1 rounded">
          <ShieldAlert className="w-4 h-4 text-brand-cyan" />
          <span className="font-bold tracking-wider text-sm text-white font-mono">
            VAT<span className="text-brand-cyan">.ENTERPRISE</span>
          </span>
          <span className="text-[10px] bg-blue-500/20 text-blue-300 font-semibold px-1.5 py-0.5 rounded border border-blue-500/30">
            NOC TIER-1
          </span>
        </div>

        {/* Vendor Platform Badges */}
        <div className="hidden lg:flex items-center space-x-1.5 pl-3 border-l border-obsidian-700/60">
          <span className="text-[11px] font-mono text-obsidian-400">ENGINES:</span>
          {["CISCO", "JUNIPER", "VELOCLOUD", "ARISTA"].map((vendor) => (
            <span
              key={vendor}
              className="text-[10px] font-mono bg-obsidian-800 text-obsidian-300 px-2 py-0.5 rounded border border-obsidian-700 font-medium"
            >
              {vendor}
            </span>
          ))}
        </div>

        {/* Demo Mode Visual Flag */}
        {isDemoMode && (
          <div className="flex items-center space-x-1 bg-amber-950/80 border border-amber-600/60 text-amber-300 text-[10px] font-mono px-2 py-0.5 rounded">
            <span>[DEMO FIXTURES ACTIVE]</span>
            <button
              onClick={clearFeed}
              className="ml-1 text-amber-200 hover:text-white underline"
            >
              Clear
            </button>
          </div>
        )}
      </div>

      {/* Center: Real-Time Stream Status & Stats */}
      <div className="hidden md:flex items-center space-x-4 text-xs font-mono">
        <div className="flex items-center space-x-1.5 text-obsidian-300 bg-obsidian-850 px-2.5 py-1 rounded border border-obsidian-700/60">
          <Layers className="w-3.5 h-3.5 text-brand-sky" />
          <span>EVENTS:</span>
          <span className="text-white font-bold">{telemetryCount}</span>
        </div>

        {/* Dynamic Database Health State */}
        <div className="flex items-center space-x-1.5 text-obsidian-300 bg-obsidian-850 px-2.5 py-1 rounded border border-obsidian-700/60">
          <Database
            className={`w-3.5 h-3.5 ${
              isDbConnected ? "text-brand-emerald" : "text-amber-400"
            }`}
          />
          <span>PGVECTOR:</span>
          <span
            className={`font-bold ${
              isDbConnected ? "text-brand-emerald" : "text-amber-400"
            }`}
          >
            {isDbConnected ? "ONLINE (HNSW+RRF)" : "AIR-GAPPED (OFFLINE)"}
          </span>
        </div>

        {activeRunbook && (
          <div className="flex items-center space-x-1.5 text-obsidian-300 bg-obsidian-850 px-2.5 py-1 rounded border border-obsidian-700/60">
            <Activity className="w-3.5 h-3.5 text-brand-cyan" />
            <span>CONFIDENCE:</span>
            <span className="text-cyan-400 font-bold">
              {(activeRunbook.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {/* Right: Actions & Live WS Indicator */}
      <div className="flex items-center space-x-2.5">
        <button
          onClick={loadDemoFixtures}
          title="Load Isolated QA Test Scenarios for Demonstration"
          className="flex items-center space-x-1 text-xs font-mono bg-obsidian-800 hover:bg-obsidian-700 text-obsidian-300 px-2.5 py-1.5 rounded border border-obsidian-700 transition"
        >
          <Zap className="w-3 h-3 text-amber-400" />
          <span className="hidden sm:inline">LOAD DEMO FIXTURES</span>
        </button>

        <button
          onClick={onOpenAudit}
          className="flex items-center space-x-1 text-xs font-mono bg-blue-950/80 hover:bg-blue-900 text-blue-200 border border-blue-700/60 px-2.5 py-1.5 rounded transition"
        >
          <Terminal className="w-3.5 h-3.5 text-brand-cyan" />
          <span>AUDIT LEDGER</span>
        </button>

        {/* Live WS Pill */}
        <div
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full border text-[11px] font-mono font-medium ${
            wsConnected
              ? "bg-emerald-950/60 text-emerald-300 border-emerald-600/50"
              : "bg-amber-950/60 text-amber-300 border-amber-600/50"
          }`}
        >
          <div
            className={`w-2 h-2 rounded-full ${
              wsConnected ? "bg-emerald-400 live-indicator" : "bg-amber-400"
            }`}
          />
          <span>{wsConnected ? "LIVE STREAM" : "OFFLINE"}</span>
        </div>
      </div>
    </header>
  );
}
