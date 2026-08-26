"use client";

import React, { useState } from "react";
import { useNOCStore } from "@/store/useNOCStore";
import { RiskLevel } from "@/types/vat";
import {
  Activity,
  AlertOctagon,
  AlertTriangle,
  CheckCircle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clock,
  Copy,
  FileCode,
  Layers,
  RotateCcw,
  Shield,
  ShieldAlert,
  Terminal,
  Zap,
} from "lucide-react";

export function RunbookCanvas() {
  const activeIncident = useNOCStore((state) => state.activeIncident);
  const activeRunbook = useNOCStore((state) => state.activeRunbook);
  const isAnalyzing = useNOCStore((state) => state.isAnalyzing);
  const progress = useNOCStore((state) => state.progress);

  const [copiedStep, setCopiedStep] = useState<string | null>(null);

  const copyToClipboard = (text: string, identifier: string) => {
    navigator.clipboard.writeText(text);
    setCopiedStep(identifier);
    setTimeout(() => setCopiedStep(null), 2000);
  };

  const getRiskPill = (riskLevel: RiskLevel | string) => {
    switch (riskLevel?.toUpperCase()) {
      case "HIGH":
        return {
          bg: "bg-red-950/80 text-red-300 border-red-700/60",
          icon: <AlertOctagon className="w-3.5 h-3.5 text-red-400" />,
          label: "HIGH BLAST RADIUS",
        };
      case "MEDIUM":
        return {
          bg: "bg-amber-950/80 text-amber-300 border-amber-700/60",
          icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />,
          label: "MEDIUM BLAST RADIUS",
        };
      default:
        return {
          bg: "bg-emerald-950/80 text-emerald-300 border-emerald-700/60",
          icon: <Shield className="w-3.5 h-3.5 text-emerald-400" />,
          label: "LOW BLAST RADIUS (SAFE)",
        };
    }
  };

  if (isAnalyzing) {
    return (
      <main className="flex-1 bg-obsidian-950 flex flex-col items-center justify-center p-8 font-mono space-y-4">
        <div className="w-12 h-12 rounded-full border-2 border-brand-cyan border-t-transparent animate-spin" />
        <div className="text-sm text-cyan-300 font-bold tracking-wider">
          SYNTHESIZING CARRIER REMEDIATION RUNBOOK
        </div>
        <div className="text-xs text-obsidian-400 max-w-md text-center">
          {progress.message || "Executing pgvector HNSW + BM25 RRF search against official TAC manuals..."}
        </div>
        <div className="flex items-center space-x-2 text-[11px] text-obsidian-500 pt-4">
          <span className="animate-pulse">● STAGE: {progress.stage.toUpperCase()}</span>
        </div>
      </main>
    );
  }

  if (!activeRunbook) {
    return (
      <main className="flex-1 bg-obsidian-950 flex flex-col items-center justify-center p-8 font-mono text-center text-obsidian-500">
        <Terminal className="w-12 h-12 mb-3 text-obsidian-700" />
        <div className="text-sm font-semibold text-obsidian-300 mb-1">
          No Incident Selected
        </div>
        <div className="text-xs max-w-sm">
          Select a telemetry event from the live stream or paste custom telemetry to generate a grounded 4-stage operational runbook.
        </div>
      </main>
    );
  }

  const riskInfo = getRiskPill(activeRunbook.risk_assessment?.risk_level || "LOW");

  return (
    <main className="flex-1 bg-obsidian-950 overflow-y-auto flex flex-col h-full">
      {/* 1. Diagnostic Summary Card */}
      <section className="p-4 border-b border-obsidian-800 bg-gradient-to-b from-obsidian-900 to-obsidian-950 shrink-0">
        <div className="max-w-4xl mx-auto space-y-3">
          {/* Top Meta Strip */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-mono uppercase bg-blue-950 text-blue-300 px-2 py-0.5 rounded border border-blue-700/50 font-bold">
                {activeRunbook.vendor} &bull; {activeRunbook.protocol}
              </span>
              <span className="text-xs font-mono text-obsidian-400">
                HOST: <span className="text-white font-semibold">{activeRunbook.device_id || "Target-Device"}</span>
              </span>
            </div>

            {/* Risk Assessment Pill */}
            <div
              className={`flex items-center space-x-1.5 text-xs font-mono px-2.5 py-1 rounded border font-semibold ${riskInfo.bg}`}
            >
              {riskInfo.icon}
              <span>{riskInfo.label}</span>
            </div>
          </div>

          {/* Diagnosis Headline */}
          <div>
            <h2 className="text-base font-semibold text-white leading-snug">
              {activeRunbook.diagnosis}
            </h2>
            <p className="text-xs text-obsidian-300 mt-1 leading-relaxed">
              <span className="text-brand-cyan font-semibold font-mono">ROOT CAUSE:</span>{" "}
              {activeRunbook.root_cause_hypothesis}
            </p>
          </div>

          {/* Operational Risk Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-obsidian-800 text-[11px] font-mono">
            <div className="bg-obsidian-900/90 p-2 rounded border border-obsidian-800">
              <div className="text-obsidian-500">BLAST RADIUS</div>
              <div className="text-white font-semibold truncate">
                {activeRunbook.risk_assessment?.blast_radius_scope || "Single Interface"}
              </div>
            </div>
            <div className="bg-obsidian-900/90 p-2 rounded border border-obsidian-800">
              <div className="text-obsidian-500">EST. DOWNTIME</div>
              <div className="text-white font-semibold">
                {activeRunbook.risk_assessment?.estimated_downtime_sec || 0} SECONDS
              </div>
            </div>
            <div className="bg-obsidian-900/90 p-2 rounded border border-obsidian-800">
              <div className="text-obsidian-500">CONFIDENCE</div>
              <div className="text-emerald-400 font-bold">
                {(activeRunbook.confidence_score * 100).toFixed(0)}% (TAC GROUNDED)
              </div>
            </div>
            <div className="bg-obsidian-900/90 p-2 rounded border border-obsidian-800">
              <div className="text-obsidian-500">SYNTHESIS ENGINE</div>
              <div className="text-cyan-400 font-semibold truncate">
                {activeRunbook.model_used}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. 4-Stage Operational Runbook Body */}
      <div className="p-4 space-y-6 max-w-4xl mx-auto w-full flex-1">
        {/* ── STAGE 1: PRE-CHECKS ───────────────────────────────────────────── */}
        <section className="space-y-2">
          <div className="flex items-center space-x-2 border-b border-obsidian-800 pb-1.5">
            <span className="text-xs font-mono font-bold text-obsidian-400 bg-obsidian-800 px-2 py-0.5 rounded">
              STAGE 01
            </span>
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
              NON-DESTRUCTIVE PRE-CHECKS (READ-ONLY)
            </h3>
          </div>

          <div className="space-y-2.5">
            {activeRunbook.pre_checks.map((pre, idx) => (
              <div key={idx} className="glass-panel p-3 rounded-md space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-obsidian-300 font-semibold">
                    Step {pre.step}: {pre.description}
                  </span>
                  <button
                    onClick={() => copyToClipboard(pre.command, `pre-${idx}`)}
                    className="text-[11px] text-obsidian-400 hover:text-cyan-300 flex items-center space-x-1"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copiedStep === `pre-${idx}` ? "COPIED" : "COPY CLI"}</span>
                  </button>
                </div>
                <div className="cli-box">{pre.command}</div>
                <div className="text-[11px] font-mono text-obsidian-400 bg-obsidian-900/60 p-2 rounded border border-obsidian-800/80">
                  <span className="text-obsidian-500 font-bold">EXPECTED DIAGNOSTIC:</span>{" "}
                  {pre.expected_output}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── STAGE 2: REMEDIATION CLI ─────────────────────────────────────── */}
        <section className="space-y-2">
          <div className="flex items-center space-x-2 border-b border-blue-900/60 pb-1.5">
            <span className="text-xs font-mono font-bold text-blue-300 bg-blue-950 px-2 py-0.5 rounded border border-blue-700/50">
              STAGE 02
            </span>
            <h3 className="text-sm font-mono font-bold text-blue-200 uppercase tracking-wider">
              DETERMINISTIC REMEDIATION CLI COMMANDS
            </h3>
          </div>

          <div className="space-y-3">
            {activeRunbook.remediation_commands.map((rem, idx) => (
              <div
                key={idx}
                className="bg-obsidian-900 border border-blue-900/50 p-3.5 rounded-md space-y-2.5 ring-1 ring-blue-500/20"
              >
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center space-x-2">
                    <span className="text-white font-bold">
                      Step {rem.step}: {rem.action}
                    </span>
                    <span className="text-[10px] bg-blue-900/60 text-blue-300 px-1.5 py-0.2 rounded border border-blue-700/50 uppercase">
                      MODE: {rem.config_mode}
                    </span>
                  </div>

                  <button
                    onClick={() => copyToClipboard(rem.command, `rem-${idx}`)}
                    className="text-[11px] bg-blue-950 hover:bg-blue-900 text-cyan-300 border border-blue-700/60 px-2 py-0.5 rounded flex items-center space-x-1"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copiedStep === `rem-${idx}` ? "COPIED" : "COPY CONFIG"}</span>
                  </button>
                </div>

                <div className="cli-box whitespace-pre">{rem.command}</div>

                <div className="text-[11px] text-obsidian-300 bg-blue-950/30 p-2 rounded border border-blue-900/40 leading-relaxed font-sans">
                  <span className="font-mono text-blue-400 font-bold">RATIONALE:</span>{" "}
                  {rem.explanation}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── STAGE 3: POST-CHECKS ─────────────────────────────────────────── */}
        <section className="space-y-2">
          <div className="flex items-center space-x-2 border-b border-emerald-900/60 pb-1.5">
            <span className="text-xs font-mono font-bold text-emerald-300 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-700/50">
              STAGE 03
            </span>
            <h3 className="text-sm font-mono font-bold text-emerald-200 uppercase tracking-wider">
              EMPIRICAL VALIDATION & CONVERGENCE POST-CHECKS
            </h3>
          </div>

          <div className="space-y-2.5">
            {activeRunbook.post_checks.map((post, idx) => (
              <div key={idx} className="glass-panel p-3 rounded-md space-y-2 border-emerald-900/30">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-emerald-300 font-semibold">
                    Step {post.step}: Validation Query
                  </span>
                  <button
                    onClick={() => copyToClipboard(post.command, `post-${idx}`)}
                    className="text-[11px] text-obsidian-400 hover:text-emerald-300 flex items-center space-x-1"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copiedStep === `post-${idx}` ? "COPIED" : "COPY CLI"}</span>
                  </button>
                </div>
                <div className="cli-box text-emerald-300">{post.command}</div>
                <div className="text-[11px] font-mono text-emerald-400 bg-emerald-950/40 p-2 rounded border border-emerald-800/40">
                  <span className="text-emerald-500 font-bold">SUCCESS CRITERIA:</span>{" "}
                  {post.validation_criteria}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── STAGE 4: ROLLBACK PLAYBOOK ───────────────────────────────────── */}
        <section className="space-y-2 pb-6">
          <div className="flex items-center space-x-2 border-b border-amber-900/60 pb-1.5">
            <span className="text-xs font-mono font-bold text-amber-300 bg-amber-950 px-2 py-0.5 rounded border border-amber-700/50">
              STAGE 04
            </span>
            <h3 className="text-sm font-mono font-bold text-amber-200 uppercase tracking-wider">
              SAFE REVERSION & ROLLBACK PLAYBOOK
            </h3>
          </div>

          <div className="space-y-2.5">
            {activeRunbook.rollback_playbook.map((rb, idx) => (
              <div key={idx} className="glass-panel p-3 rounded-md space-y-2 border-amber-900/30">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-amber-300 font-semibold">
                    Step {rb.step}: {rb.action}
                  </span>
                  <button
                    onClick={() => copyToClipboard(rb.command, `rb-${idx}`)}
                    className="text-[11px] text-obsidian-400 hover:text-amber-300 flex items-center space-x-1"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copiedStep === `rb-${idx}` ? "COPIED" : "COPY REVERT"}</span>
                  </button>
                </div>
                <div className="cli-box text-amber-300 whitespace-pre">{rb.command}</div>
                <div className="text-[11px] font-mono text-amber-400 bg-amber-950/40 p-2 rounded border border-amber-800/40">
                  <span className="text-amber-500 font-bold">TRIGGER CONDITION:</span>{" "}
                  {rb.trigger_condition}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
