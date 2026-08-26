"use client";

import React, { useState } from "react";
import { useNOCStore } from "@/store/useNOCStore";
import { ParsedTelemetry, SeverityLevel, VendorPlatform } from "@/types/vat";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Filter,
  Flame,
  Plus,
  Radio,
  Search,
  Send,
  Terminal,
} from "lucide-react";

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

  const [customLogInput, setCustomLogInput] = useState("");
  const [customDevice, setCustomDevice] = useState("Border-RT-01");
  const [showIngestBox, setShowIngestBox] = useState(false);

  const handleManualIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customLogInput.trim()) return;

    await troubleshootIncident(customLogInput, customDevice);
    setCustomLogInput("");
    setShowIngestBox(false);
  };

  const filteredLogs = telemetryFeed.filter((item) => {
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

  const getSeverityBadge = (severity: SeverityLevel) => {
    switch (severity) {
      case "CRITICAL":
        return "bg-red-950/80 text-red-300 border-red-700/60";
      case "ERROR":
        return "bg-amber-950/80 text-amber-300 border-amber-700/60";
      case "WARNING":
        return "bg-yellow-950/80 text-yellow-300 border-yellow-700/60";
      default:
        return "bg-blue-950/80 text-blue-300 border-blue-700/60";
    }
  };

  const getVendorBadgeColor = (vendor: string) => {
    switch (vendor.toLowerCase()) {
      case "cisco":
        return "text-cyan-400 border-cyan-700/40 bg-cyan-950/40";
      case "juniper":
        return "text-purple-400 border-purple-700/40 bg-purple-950/40";
      case "velocloud":
        return "text-emerald-400 border-emerald-700/40 bg-emerald-950/40";
      case "arista":
        return "text-amber-400 border-amber-700/40 bg-amber-950/40";
      default:
        return "text-obsidian-300 border-obsidian-700 bg-obsidian-800";
    }
  };

  return (
    <aside className="w-80 md:w-96 bg-obsidian-900 border-r border-obsidian-700/80 flex flex-col h-full shrink-0">
      {/* Feed Header */}
      <div className="p-3 border-b border-obsidian-700/60 flex items-center justify-between bg-obsidian-850">
        <div className="flex items-center space-x-2">
          <Radio className="w-4 h-4 text-brand-cyan" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-white">
            TELEMETRY INGESTION STREAM
          </span>
        </div>
        <button
          onClick={() => setShowIngestBox(!showIngestBox)}
          className="text-xs bg-obsidian-800 hover:bg-obsidian-700 text-cyan-300 p-1.5 rounded border border-obsidian-700 flex items-center space-x-1"
          title="Paste Custom Telemetry"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="text-[10px] font-mono">INGEST</span>
        </button>
      </div>

      {/* Manual Log Ingestion Box */}
      {showIngestBox && (
        <form onSubmit={handleManualIngest} className="p-3 border-b border-obsidian-700 bg-obsidian-950 space-y-2">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              placeholder="Device ID (e.g. Core-RT-01)"
              value={customDevice}
              onChange={(e) => setCustomDevice(e.target.value)}
              className="text-xs bg-obsidian-900 border border-obsidian-700 rounded px-2 py-1 text-white font-mono w-full focus:outline-none focus:border-brand-sky"
            />
          </div>
          <textarea
            rows={3}
            placeholder="Paste raw syslog or telemetry event..."
            value={customLogInput}
            onChange={(e) => setCustomLogInput(e.target.value)}
            className="text-xs bg-obsidian-900 border border-obsidian-700 rounded p-2 text-white font-mono w-full focus:outline-none focus:border-brand-sky"
          />
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setShowIngestBox(false)}
              className="text-xs px-2.5 py-1 text-obsidian-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="text-xs bg-brand-blue hover:bg-blue-600 text-white font-mono px-3 py-1 rounded flex items-center space-x-1"
            >
              <Send className="w-3 h-3" />
              <span>Diagnose</span>
            </button>
          </div>
        </form>
      )}

      {/* Filters & Search */}
      <div className="p-2.5 border-b border-obsidian-700/60 bg-obsidian-900/90 space-y-2">
        {/* Search */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-obsidian-500" />
          <input
            type="text"
            placeholder="Filter logs by keyword, IP, code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-obsidian-950 border border-obsidian-700/80 rounded pl-8 pr-2 py-1 text-xs text-obsidian-200 font-mono focus:outline-none focus:border-brand-sky"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-[10px] font-mono">
          <span className="text-obsidian-500 font-bold">VENDOR:</span>
          {["all", "cisco", "juniper", "velocloud", "arista"].map((v) => (
            <button
              key={v}
              onClick={() => setFilterVendor(v)}
              className={`px-2 py-0.5 rounded border transition capitalize ${
                filterVendor === v
                  ? "bg-brand-blue text-white border-blue-500"
                  : "bg-obsidian-850 text-obsidian-400 border-obsidian-700 hover:text-white"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Live Stream List */}
      <div className="flex-1 overflow-y-auto divide-y divide-obsidian-800/80 p-2 space-y-2">
        {filteredLogs.length === 0 ? (
          <div className="p-8 text-center text-obsidian-500 font-mono text-xs">
            No telemetry matching active filters.
          </div>
        ) : (
          filteredLogs.map((item, idx) => {
            const isSelected = activeIncident?.raw_log === item.raw_log;

            return (
              <div
                key={idx}
                onClick={() => selectIncident(item)}
                className={`p-2.5 rounded-md cursor-pointer border transition ${
                  isSelected
                    ? "bg-blue-950/40 border-blue-500/80 ring-1 ring-blue-500/50"
                    : "bg-obsidian-850/70 border-obsidian-700/60 hover:bg-obsidian-800/80 hover:border-obsidian-600"
                }`}
              >
                {/* Meta Top: Vendor, Device, Severity */}
                <div className="flex items-center justify-between text-[11px] font-mono mb-1.5">
                  <div className="flex items-center space-x-1.5">
                    <span
                      className={`text-[10px] uppercase font-bold px-1.5 py-0.2 rounded border ${getVendorBadgeColor(
                        item.vendor
                      )}`}
                    >
                      {item.vendor}
                    </span>
                    <span className="text-obsidian-300 font-semibold truncate max-w-[130px]">
                      {item.device_id}
                    </span>
                  </div>

                  <span
                    className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded border ${getSeverityBadge(
                      item.severity
                    )}`}
                  >
                    {item.severity}
                  </span>
                </div>

                {/* Raw Log Preview */}
                <div className="text-xs font-mono text-obsidian-200 line-clamp-2 leading-relaxed mb-2">
                  {item.raw_log}
                </div>

                {/* Meta Bottom: Protocol, Event Code & Quick Action */}
                <div className="flex items-center justify-between text-[10px] font-mono text-obsidian-400 pt-1 border-t border-obsidian-700/40">
                  <div className="flex items-center space-x-2">
                    {item.protocol && (
                      <span className="uppercase text-cyan-400 font-medium">
                        [{item.protocol}]
                      </span>
                    )}
                    {item.peer_ip && (
                      <span className="text-obsidian-400">IP: {item.peer_ip}</span>
                    )}
                  </div>

                  <div className="flex items-center text-blue-400 font-semibold group">
                    <span>Synthesize</span>
                    <ArrowRight className="w-3 h-3 ml-0.5 group-hover:translate-x-0.5 transition" />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
