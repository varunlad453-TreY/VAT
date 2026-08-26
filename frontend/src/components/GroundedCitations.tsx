"use client";

import React from "react";
import { useNOCStore } from "@/store/useNOCStore";
import { BookOpen, ExternalLink, FileText, Sparkles } from "lucide-react";

export function GroundedCitations() {
  const citations = useNOCStore((state) => state.citations);
  const activeRunbook = useNOCStore((state) => state.activeRunbook);

  if (!citations || citations.length === 0) {
    return (
      <aside className="w-80 md:w-96 bg-obsidian-900 border-l border-obsidian-700/80 p-4 flex flex-col items-center justify-center text-center font-mono text-obsidian-500 shrink-0">
        <BookOpen className="w-8 h-8 mb-2 text-obsidian-700" />
        <span className="text-xs">No vendor citations available.</span>
      </aside>
    );
  }

  return (
    <aside className="w-80 md:w-96 bg-obsidian-900 border-l border-obsidian-700/80 flex flex-col h-full shrink-0">
      {/* Header */}
      <div className="p-3 border-b border-obsidian-700/60 bg-obsidian-850 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-brand-cyan" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-white">
            GROUNDED TAC CITATIONS
          </span>
        </div>
        <span className="text-[10px] font-mono bg-blue-950 text-blue-300 px-2 py-0.5 rounded border border-blue-700/50">
          {citations.length} SOURCES
        </span>
      </div>

      {/* Citations List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {citations.map((cite, idx) => (
          <div
            key={idx}
            className="glass-panel p-3 rounded-md space-y-2 border-obsidian-700/60 hover:border-obsidian-600 transition"
          >
            {/* Title & External Link */}
            <div className="flex items-start justify-between gap-2">
              <h4 className="text-xs font-semibold text-white leading-snug">
                {cite.title}
              </h4>
              {cite.source_url && (
                <a
                  href={cite.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cyan-400 hover:text-cyan-300 p-1 rounded bg-obsidian-800 border border-obsidian-700 shrink-0"
                  title="Open Official Vendor TAC Document"
                >
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>

            {/* Vendor & Similarity Match Score */}
            <div className="flex items-center justify-between text-[10px] font-mono text-obsidian-400">
              <span className="uppercase font-bold text-obsidian-300">
                VENDOR: {cite.vendor}
              </span>
              <span className="text-emerald-400 font-bold bg-emerald-950/80 px-1.5 py-0.2 rounded border border-emerald-700/50">
                {(cite.similarity_score * 100).toFixed(0)}% MATCH
              </span>
            </div>

            {/* Excerpt */}
            <div className="text-[11px] font-mono text-obsidian-300 bg-obsidian-950/80 p-2.5 rounded border border-obsidian-800/80 leading-relaxed max-h-36 overflow-y-auto">
              {cite.excerpt}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
