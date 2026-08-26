"use client";

import React, { useState } from "react";
import { useNOCStore } from "@/store/useNOCStore";
import {
  PreCheckCommand,
  RemediationCommand,
  PostCheckCommand,
  RollbackCommand,
} from "@/types/vat";
import {
  Check,
  Copy,
  Play,
  Terminal,
  Zap,
} from "lucide-react";

export function RunbookCanvas() {
  const activeIncident = useNOCStore((state) => state.activeIncident);
  const activeRunbook = useNOCStore((state) => state.activeRunbook);
  const isAnalyzing = useNOCStore((state) => state.isAnalyzing);
  const troubleshootIncident = useNOCStore((state) => state.troubleshootIncident);
  const loadDemoFixtures = useNOCStore((state) => state.loadDemoFixtures);

  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(id);
    setTimeout(() => setCopiedIndex(null), 1800);
  };

  if (!activeIncident) {
    return (
      <main className="flex-1 bg-[#05080f] flex flex-col items-center justify-center p-8 text-center select-none font-mono">
        <div className="max-w-md space-y-4">
          <Terminal className="w-10 h-10 text-slate-700 mx-auto" />
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Operational Workspace Ready
          </h2>
          <p className="text-xs text-slate-500 leading-relaxed font-sans">
            Select an active telemetry event from the stream on the left or ingest a raw syslog line to generate a deterministic 4-stage remediation runbook.
          </p>
          <button
            onClick={loadDemoFixtures}
            className="inline-flex items-center space-x-1.5 text-xs text-amber-400 hover:text-amber-300 underline font-mono"
          >
            <Zap className="w-3.5 h-3.5" />
            <span>Load Demo Fixture Incidents</span>
          </button>
        </div>
      </main>
    );
  }

  const blastRadius = activeRunbook?.risk_assessment?.blast_radius_scope || "STANDARD";
  const downtimeSec = activeRunbook?.risk_assessment?.estimated_downtime_sec ?? 0;

  const getBlastRadiusColor = (blast: string) => {
    const b = blast.toUpperCase();
    if (b.includes("HIGH") || b.includes("CRITICAL") || b.includes("CHASSIS") || b.includes("PAIR")) {
      return "text-red-400";
    }
    if (b.includes("MEDIUM") || b.includes("CORE") || b.includes("ZONE")) {
      return "text-amber-400";
    }
    return "text-emerald-400";
  };

  return (
    <main className="flex-1 bg-[#05080f] flex flex-col h-full overflow-hidden select-none">
      {/* ────────────────────────────────────────────────────────────────────────
          1. INCIDENT DIAGNOSTIC BANNER (Flat Editorial Layout, No Metric Boxes)
          ──────────────────────────────────────────────────────────────────────── */}
      <div className="p-4 bg-[#080d17] border-b border-[#172236] shrink-0 space-y-3 font-mono">
        {/* Title & Metadata Ribbon */}
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-white font-bold tracking-wide uppercase">
              {activeIncident.vendor}
            </span>
            <span className="text-slate-600">·</span>
            {activeIncident.protocol && (
              <>
                <span className="text-cyan-400 uppercase font-medium">
                  {activeIncident.protocol}
                </span>
                <span className="text-slate-600">·</span>
              </>
            )}
            <span className="text-slate-300">HOST: {activeIncident.device_id}</span>
            {activeIncident.peer_ip && (
              <>
                <span className="text-slate-600">·</span>
                <span className="text-slate-400">PEER: {activeIncident.peer_ip}</span>
              </>
            )}
          </div>

          {activeRunbook && (
            <div className="flex items-center space-x-1 font-bold text-[11px]">
              <span className="text-slate-500">BLAST RADIUS:</span>
              <span className={getBlastRadiusColor(blastRadius)}>
                ● {blastRadius.toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* Diagnosis Statement */}
        <div>
          <h1 className="text-sm md:text-base font-semibold text-slate-100 font-sans tracking-tight leading-snug">
            {activeRunbook?.diagnosis || "Awaiting Runbook Synthesis..."}
          </h1>

          {activeRunbook?.root_cause_hypothesis && (
            <div className="mt-2 text-xs font-sans text-slate-300 bg-[#060a12] p-2.5 border-l-2 border-cyan-500">
              <span className="text-cyan-400 font-mono font-bold text-[11px] uppercase mr-2">
                ROOT CAUSE:
              </span>
              {activeRunbook.root_cause_hypothesis}
            </div>
          )}
        </div>

        {/* Inline Operational Metadata (Replaces the 4-Card Grid) */}
        {activeRunbook && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-400 pt-1 border-t border-[#121b2d]">
            <div>
              <span className="text-slate-500">EST. DOWNTIME:</span>{" "}
              <span className="text-slate-200">{downtimeSec}s</span>
            </div>
            <span className="text-slate-700">·</span>
            <div>
              <span className="text-slate-500">CONFIDENCE:</span>{" "}
              <span className="text-emerald-400 font-semibold">
                {(activeRunbook.confidence_score * 100).toFixed(0)}% (TAC GROUNDED)
              </span>
            </div>
            <span className="text-slate-700">·</span>
            <div>
              <span className="text-slate-500">SYNTHESIS ENGINE:</span>{" "}
              <span className="text-cyan-400">
                {activeRunbook.model_used || "deterministic-rag"}
              </span>
            </div>
          </div>
        )}

        {/* In-Progress Synthesis Action */}
        {!activeRunbook && (
          <div className="pt-2">
            <button
              onClick={() => troubleshootIncident(activeIncident.raw_log, activeIncident.device_id, activeIncident.vendor)}
              disabled={isAnalyzing}
              className="bg-blue-600 hover:bg-blue-500 text-white text-xs px-4 py-1.5 font-medium flex items-center space-x-2 transition disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>
                {isAnalyzing ? "Synthesizing Runbook..." : "Generate Deterministic Runbook"}
              </span>
            </button>
          </div>
        )}
      </div>

      {/* ────────────────────────────────────────────────────────────────────────
          2. CONTINUOUS 4-STAGE PLAYBOOK DOCUMENT (Flat, High-Density)
          ──────────────────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 font-mono text-xs">
        {activeRunbook ? (
          <>
            {/* Stage 1: Pre-checks */}
            <section className="space-y-3 pb-6 border-b border-[#141e30]">
              <div className="flex items-center justify-between pb-1.5 border-b border-[#141e30]">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold tracking-wider text-cyan-400">STAGE 01</span>
                    <span className="text-slate-600">·</span>
                    <span className="font-semibold text-slate-200 uppercase tracking-wide">
                      NON-DESTRUCTIVE PRE-CHECKS (READ-ONLY)
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 font-sans mt-0.5">
                    Collect baseline router state and telemetry validation before mutation
                  </p>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  {activeRunbook.pre_checks.length} COMMANDS
                </span>
              </div>

              <div className="space-y-4">
                {activeRunbook.pre_checks.map((cmd, idx) => (
                  <StepItem
                    key={idx}
                    index={idx + 1}
                    id={`pre-${idx}`}
                    title={cmd.description}
                    command={cmd.command}
                    expected={cmd.expected_output}
                    mode="EXEC"
                    copiedIndex={copiedIndex}
                    onCopy={handleCopy}
                  />
                ))}
              </div>
            </section>

            {/* Stage 2: Remediation */}
            <section className="space-y-3 pb-6 border-b border-[#141e30]">
              <div className="flex items-center justify-between pb-1.5 border-b border-[#141e30]">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold tracking-wider text-amber-400">STAGE 02</span>
                    <span className="text-slate-600">·</span>
                    <span className="font-semibold text-slate-200 uppercase tracking-wide">
                      DETERMINISTIC REMEDIATION CLI COMMANDS
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 font-sans mt-0.5">
                    Carrier-grade configuration changes grounded in official TAC resolution manuals
                  </p>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  {activeRunbook.remediation_commands.length} COMMANDS
                </span>
              </div>

              <div className="space-y-4">
                {activeRunbook.remediation_commands.map((cmd, idx) => (
                  <StepItem
                    key={idx}
                    index={idx + 1}
                    id={`rem-${idx}`}
                    title={cmd.action || cmd.explanation}
                    command={cmd.command}
                    mode={cmd.config_mode || "CONFIG"}
                    copiedIndex={copiedIndex}
                    onCopy={handleCopy}
                  />
                ))}
              </div>
            </section>

            {/* Stage 3: Post-checks */}
            <section className="space-y-3 pb-6 border-b border-[#141e30]">
              <div className="flex items-center justify-between pb-1.5 border-b border-[#141e30]">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold tracking-wider text-emerald-400">STAGE 03</span>
                    <span className="text-slate-600">·</span>
                    <span className="font-semibold text-slate-200 uppercase tracking-wide">
                      POST-REMEDIATION VERIFICATION
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 font-sans mt-0.5">
                    Assert state restoration, protocol convergence, and zero packet drops
                  </p>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  {activeRunbook.post_checks.length} COMMANDS
                </span>
              </div>

              <div className="space-y-4">
                {activeRunbook.post_checks.map((cmd, idx) => (
                  <StepItem
                    key={idx}
                    index={idx + 1}
                    id={`post-${idx}`}
                    title={cmd.validation_criteria}
                    command={cmd.command}
                    mode="VERIFY"
                    copiedIndex={copiedIndex}
                    onCopy={handleCopy}
                  />
                ))}
              </div>
            </section>

            {/* Stage 4: Rollback */}
            <section className="space-y-3 pb-6 border-b border-[#141e30] last:border-b-0">
              <div className="flex items-center justify-between pb-1.5 border-b border-[#141e30]">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold tracking-wider text-rose-400">STAGE 04</span>
                    <span className="text-slate-600">·</span>
                    <span className="font-semibold text-slate-200 uppercase tracking-wide">
                      AUTOMATED ROLLBACK CONTINGENCY
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 font-sans mt-0.5">
                    Deterministic rollback commands if verification assertions fail
                  </p>
                </div>
                <span className="text-[11px] text-slate-500 font-mono">
                  {activeRunbook.rollback_playbook.length} COMMANDS
                </span>
              </div>

              <div className="space-y-4">
                {activeRunbook.rollback_playbook.map((cmd, idx) => (
                  <StepItem
                    key={idx}
                    index={idx + 1}
                    id={`roll-${idx}`}
                    title={cmd.action || `Trigger: ${cmd.trigger_condition}`}
                    command={cmd.command}
                    mode="ROLLBACK"
                    copiedIndex={copiedIndex}
                    onCopy={handleCopy}
                  />
                ))}
              </div>
            </section>
          </>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500">
            {isAnalyzing ? (
              <div className="flex items-center space-x-3 text-cyan-400">
                <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                <span>RAG synthesis engine computing deterministic playbook...</span>
              </div>
            ) : (
              <span>Click Generate Deterministic Runbook above to view the 4-stage execution plan.</span>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

interface StepItemProps {
  index: number;
  id: string;
  title?: string;
  command: string;
  expected?: string;
  mode?: string;
  copiedIndex: string | null;
  onCopy: (text: string, id: string) => void;
}

function StepItem({
  index,
  id,
  title,
  command,
  expected,
  mode,
  copiedIndex,
  onCopy,
}: StepItemProps) {
  const isCopied = copiedIndex === id;

  return (
    <div className="space-y-1.5 group">
      {/* Title & Mode */}
      <div className="flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center space-x-2 font-medium font-sans">
          <span className="font-mono text-slate-500 text-[11px]">
            {String(index).padStart(2, "0")}.
          </span>
          <span>{title || command}</span>
        </div>

        <div className="flex items-center space-x-2">
          {mode && (
            <span className="text-[10px] text-slate-500 uppercase font-mono">
              MODE: {mode}
            </span>
          )}
          <button
            onClick={() => onCopy(command, id)}
            className="text-[11px] text-slate-400 hover:text-cyan-300 flex items-center space-x-1 px-1.5 py-0.5 transition"
            title="Copy CLI Syntax to Clipboard"
          >
            {isCopied ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-400">COPIED</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>COPY</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Monospace CLI Terminal Stream Line */}
      <pre className="font-mono text-xs bg-[#04070d] text-cyan-300 p-2.5 border-l-2 border-cyan-500/50 overflow-x-auto select-all leading-relaxed">
        <code>{command}</code>
      </pre>

      {/* Inline Expected Diagnostic Assertion (Flat, No Card) */}
      {expected && (
        <div className="text-[11px] text-slate-400 flex items-start space-x-1.5 pl-3 pt-0.5">
          <span className="text-slate-600 font-mono">↳</span>
          <div>
            <span className="text-slate-500 font-mono uppercase mr-1">
              EXPECTED:
            </span>
            <span className="text-slate-300 font-mono">{expected}</span>
          </div>
        </div>
      )}
    </div>
  );
}
