"use client";

import React, { useRef, useState, useEffect, useMemo } from "react";
import { useNOCStore } from "@/store/useNOCStore";
import { ParsedTelemetry, SeverityLevel } from "@/types/vat";
import {
  ChevronRight,
  Filter,
  Inbox,
  Pause,
  Play,
  Plus,
  Radio,
  RotateCcw,
  Search,
  Send,
  Zap,
} from "lucide-react";

const ROW_HEIGHT = 86; // Height in pixels for virtualized row calculation
const OVERSCAN = 5;

export function TelemetryFeed() {
  const telemetryFeed = useNOCStore((state) => state.telemetryFeed);
  const activeIncident = useNOCStore((state) => state.activeIncident);
  const selectIncident = useNOCStore((state) => state.selectIncident);
  const filterVendor = useNOCStore((state) => state.filterVendor);
  const setFilterVendor = useNOCStore((state) => state.setFilterVendor);
  const filterSeverity = useNOCStore((state) => state.filterSeverity);
  const setFilterSeverity = useNOCStore((state) => state.setFilterSeverity);
  const searchQuery = useNOCStore((state) => state.searchQuery);
  const setSearchQuery = useNOCStore((state) => state.setSearchQuery);
  const troubleshootIncident = useNOCStore((state) => state.troubleshootIncident);
  const loadDemoFixtures = useNOCStore((state) => state.loadDemoFixtures);
  const clearFeed = useNOCStore((state) => state.clearFeed);

  const [customLogInput, setCustomLogInput] = useState("");
  const [customDevice, setCustomDevice] = useState("");
  const [showIngestBox, setShowIngestBox] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [scrollTop, setScrollTop] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);

  const handleManualIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customLogInput.trim()) return;

    await troubleshootIncident(
      customLogInput,
      customDevice.trim() ? customDevice.trim() : undefined
    );
    setCustomLogInput("");
    setCustomDevice("");
    setShowIngestBox(false);
  };

  const filteredLogs = useMemo(() => {
    return telemetryFeed.filter((item) => {
      if (filterVendor !== "all" && item.vendor.toLowerCase() !== filterVendor.toLowerCase()) {
        return false;
      }
      if (filterSeverity !== "all" && item.severity.toUpperCase() !== filterSeverity.toUpperCase()) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          item.raw_log.toLowerCase().includes(q) ||
          item.device_id.toLowerCase().includes(q) ||
          (item.event_code && item.event_code.toLowerCase().includes(q)) ||
          (item.protocol && item.protocol.toLowerCase().includes(q))
        );
      }
      return true;
    });
  }, [telemetryFeed, filterVendor, filterSeverity, searchQuery]);

  // Virtual Window Calculation
  const totalItems = filteredLogs.length;
  const containerHeight = 600; // default estimated container height
  const startIndex = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - OVERSCAN);
  const endIndex = Math.min(
    totalItems,
    Math.ceil((scrollTop + containerHeight) / ROW_HEIGHT) + OVERSCAN
  );

  const visibleItems = useMemo(() => {
    return filteredLogs.slice(startIndex, endIndex).map((item, index) => ({
      item,
      index: startIndex + index,
      top: (startIndex + index) * ROW_HEIGHT,
    }));
  }, [filteredLogs, startIndex, endIndex]);

  const onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  const getSeverityBorderColor = (severity: SeverityLevel) => {
    switch (severity) {
      case "CRITICAL":
        return "border-l-red-500 text-red-400";
      case "ERROR":
        return "border-l-amber-500 text-amber-400";
      case "WARNING":
        return "border-l-yellow-500 text-yellow-400";
      default:
        return "border-l-blue-500 text-blue-400";
    }
  };

  const getSeverityDot = (severity: SeverityLevel) => {
    switch (severity) {
      case "CRITICAL":
        return "text-red-400";
      case "ERROR":
        return "text-amber-400";
      case "WARNING":
        return "text-yellow-400";
      default:
        return "text-blue-400";
    }
  };

  return (
    <aside className="w-80 md:w-96 bg-[#070b12] border-r border-[#172236] flex flex-col h-full shrink-0 font-mono text-xs select-none">
      {/* Pane Header */}
      <div className="h-10 px-3 border-b border-[#172236] bg-[#090e18] flex items-center justify-between">
        <div className="flex items-center space-x-2 text-slate-300 font-semibold tracking-wider text-[11px] uppercase">
          <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
          <span>TELEMETRY STREAM</span>
          <span className="bg-[#111c2e] text-cyan-400 px-1.5 py-0.2 rounded text-[10px]">
            {filteredLogs.length}
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`text-[11px] flex items-center space-x-0.5 px-1.5 py-0.5 rounded border ${
              isPaused
                ? "bg-amber-950/40 border-amber-600/40 text-amber-400"
                : "border-[#1e2c45] text-slate-400 hover:text-slate-200"
            }`}
            title={isPaused ? "Resume Stream" : "Pause Stream"}
          >
            {isPaused ? <Play className="w-2.5 h-2.5" /> : <Pause className="w-2.5 h-2.5" />}
          </button>

          <button
            onClick={() => setShowIngestBox(!showIngestBox)}
            className="text-[11px] bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 px-2 py-0.5 flex items-center space-x-0.5"
            title="Submit Live Raw Telemetry"
          >
            <Plus className="w-3 h-3" />
            <span>INGEST</span>
          </button>
        </div>
      </div>

      {/* Manual Ingestion Input Area */}
      {showIngestBox && (
        <form onSubmit={handleManualIngest} className="p-3 border-b border-[#172236] bg-[#090d16] space-y-2">
          <input
            type="text"
            placeholder="Device ID (optional, e.g. Core-RT-01)"
            value={customDevice}
            onChange={(e) => setCustomDevice(e.target.value)}
            className="w-full bg-[#05080e] border border-[#1e2c45] rounded-none px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          />
          <textarea
            rows={3}
            placeholder="Paste raw syslog line..."
            value={customLogInput}
            onChange={(e) => setCustomLogInput(e.target.value)}
            className="w-full bg-[#05080e] border border-[#1e2c45] rounded-none p-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          />
          <div className="flex justify-end space-x-2 text-[11px]">
            <button
              type="button"
              onClick={() => setShowIngestBox(false)}
              className="text-slate-400 hover:text-white px-2 py-0.5"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-0.5 font-medium flex items-center space-x-1"
            >
              <Send className="w-2.5 h-2.5" />
              <span>Diagnose</span>
            </button>
          </div>
        </form>
      )}

      {/* Filters & Search Toolbar */}
      <div className="p-2.5 border-b border-[#172236] bg-[#080d16] space-y-2">
        {/* Search */}
        <div className="relative">
          <Search className="w-3 h-3 absolute left-2 top-2 text-slate-500" />
          <input
            type="text"
            placeholder="Filter by keyword, IP, code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#04070d] border border-[#172236] rounded-none pl-7 pr-2 py-1 text-[11px] text-slate-200 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Flat Text Filter Tabs */}
        <div className="flex items-center space-x-3 text-[10px] text-slate-400 pt-0.5 overflow-x-auto">
          <span className="text-slate-600 font-semibold uppercase">Vendor:</span>
          {["all", "cisco", "juniper", "velocloud", "arista"].map((v) => (
            <button
              key={v}
              onClick={() => setFilterVendor(v)}
              className={`capitalize transition ${
                filterVendor === v
                  ? "text-cyan-400 font-bold border-b border-cyan-400 pb-0.5"
                  : "hover:text-slate-200 pb-0.5"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Virtualized Stream Viewport (Renders only ~30 active DOM rows for 100k+ scale) */}
      <div
        ref={containerRef}
        onScroll={onScroll}
        className="flex-1 overflow-y-auto relative"
        style={{ height: "100%" }}
      >
        {filteredLogs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-500 space-y-2">
            <Inbox className="w-6 h-6 text-slate-700" />
            <div className="text-slate-400 font-medium text-xs">
              Live Stream Awaiting Telemetry
            </div>
            <p className="text-[10px] text-slate-600 max-w-xs leading-relaxed">
              No telemetry received yet. Stream live multi-vendor syslogs via Vector / Redpanda or click <b>INGEST</b>.
            </p>
            <button
              onClick={loadDemoFixtures}
              className="mt-2 text-[10px] text-amber-400 hover:text-amber-300 underline"
            >
              Load Multi-Vendor Fixtures
            </button>
          </div>
        ) : (
          <div style={{ height: `${totalItems * ROW_HEIGHT}px`, position: "relative" }}>
            {visibleItems.map(({ item, index, top }) => {
              const isSelected = activeIncident?.raw_log === item.raw_log;

              return (
                <div
                  key={index}
                  onClick={() => selectIncident(item)}
                  style={{
                    position: "absolute",
                    top: `${top}px`,
                    left: 0,
                    right: 0,
                    height: `${ROW_HEIGHT}px`,
                  }}
                  className={`p-3 cursor-pointer transition border-l-2 border-b border-[#121927] ${getSeverityBorderColor(
                    item.severity
                  )} ${
                    isSelected
                      ? "bg-[#0f1729] text-white"
                      : "hover:bg-[#0b101c] text-slate-300"
                  }`}
                >
                  {/* Meta Header */}
                  <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
                    <div className="flex items-center space-x-1.5 font-semibold">
                      <span className="text-slate-200 uppercase">{item.vendor}</span>
                      <span className="text-slate-600">·</span>
                      <span className="text-slate-300">{item.device_id}</span>
                    </div>

                    <div className="flex items-center space-x-1">
                      <span className={`font-bold ${getSeverityDot(item.severity)}`}>
                        ● {item.severity}
                      </span>
                    </div>
                  </div>

                  {/* Raw Log Line */}
                  <div className="text-[11px] leading-relaxed line-clamp-1 text-slate-300 font-mono">
                    {item.raw_log}
                  </div>

                  {/* Meta Footer */}
                  <div className="flex items-center justify-between text-[10px] text-slate-500 mt-1">
                    <div className="flex items-center space-x-2">
                      {item.protocol && (
                        <span className="uppercase text-cyan-500 font-medium">
                          {item.protocol}
                        </span>
                      )}
                      {item.peer_ip && <span>IP: {item.peer_ip}</span>}
                    </div>

                    {isSelected && (
                      <span className="text-cyan-400 font-semibold flex items-center">
                        Inspecting <ChevronRight className="w-2.5 h-2.5 ml-0.5" />
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
}
