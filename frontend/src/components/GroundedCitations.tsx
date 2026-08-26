"use client";

import React from "react";
import { useNOCStore } from "@/store/useNOCStore";
import { BookOpen, ExternalLink, ShieldCheck } from "lucide-react";

export function GroundedCitations() {
  const activeRunbook = useNOCStore((state) => state.activeRunbook);
  const storeCitations = useNOCStore((state) => state.citations);

  // Use runbook-specific citations or globally queried citations
  const sources = activeRunbook?.cited_vendor_docs || storeCitations || [];

  return (
    <aside className="w-80 md:w-96 bg-[#070b12] border-l border-[#172236] flex flex-col h-full shrink-0 font-mono text-xs select-none">
      {/* Pane Header */}
      <div className="h-10 px-3 border-b border-[#172236] bg-[#090e18] flex items-center justify-between">
        <div className="flex items-center space-x-2 text-slate-300 font-semibold tracking-wider text-[11px] uppercase">
          <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
          <span>GROUNDED TAC CITATIONS</span>
        </div>

        <span className="text-[11px] text-slate-500 font-mono">
          {sources.length} {sources.length === 1 ? "SOURCE" : "SOURCES"}
        </span>
      </div>

      {/* Citations List (Flat Editorial Hierarchy, No Cards) */}
      <div className="flex-1 overflow-y-auto divide-y divide-[#141e30]">
        {sources.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-500 space-y-2">
            <ShieldCheck className="w-6 h-6 text-slate-700" />
            <div className="text-slate-400 font-medium text-xs font-sans">
              No Active Citations
            </div>
            <p className="text-[10px] text-slate-600 max-w-xs leading-relaxed font-sans">
              TAC manual citations with cosine similarity match scores will appear here when an incident is diagnosed.
            </p>
          </div>
        ) : (
          sources.map((src, idx) => {
            const matchScore = (src.similarity_score * 100).toFixed(0);

            return (
              <article key={idx} className="p-3.5 space-y-2 hover:bg-[#0b101c] transition">
                {/* Title & Link */}
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-xs text-slate-200 hover:text-cyan-300 transition leading-snug font-sans">
                    {src.source_url ? (
                      <a
                        href={src.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 hover:underline"
                      >
                        <span>{src.title}</span>
                        <ExternalLink className="w-2.5 h-2.5 shrink-0 opacity-70" />
                      </a>
                    ) : (
                      src.title
                    )}
                  </h3>
                </div>

                {/* Inline Typographic Metadata (No Badge Pills) */}
                <div className="flex items-center space-x-2 text-[10px] text-slate-400 font-mono">
                  <span className="uppercase text-slate-300 font-semibold">
                    {src.vendor}
                  </span>
                  <span className="text-slate-700">·</span>
                  <span className="text-emerald-400 font-bold">
                    {matchScore}% MATCH
                  </span>
                  <span className="text-slate-700">·</span>
                  <span className="text-slate-500">HNSW COSINE</span>
                </div>

                {/* Excerpt Text (Flat, Indented) */}
                <p className="text-[11px] text-slate-400 font-sans leading-relaxed pl-2.5 border-l-2 border-[#1e2d47]">
                  {src.excerpt}
                </p>
              </article>
            );
          })
        )}
      </div>
    </aside>
  );
}
