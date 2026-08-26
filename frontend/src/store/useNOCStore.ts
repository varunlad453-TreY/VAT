/**
 * Zustand State Store for VAT Enterprise NOC Console
 */

import { create } from "zustand";
import { api } from "@/lib/api";
import {
  AuditLedgerEntry,
  ParsedTelemetry,
  ProgressState,
  TroubleshootResponseDTO,
  VendorDocCitation,
} from "@/types/vat";

interface NOCState {
  // Real-time telemetry feed
  telemetryFeed: ParsedTelemetry[];
  activeIncident: ParsedTelemetry | null;
  activeRunbook: TroubleshootResponseDTO | null;
  citations: VendorDocCitation[];
  auditHistory: AuditLedgerEntry[];

  // Progress & Status
  progress: ProgressState;
  isAnalyzing: boolean;
  wsConnected: boolean;

  // Filters & Tabs
  filterVendor: string;
  filterSeverity: string;
  searchQuery: string;
  activeTab: "runbook" | "citations" | "audit";

  // Actions
  setWsConnected: (connected: boolean) => void;
  addTelemetryLog: (log: ParsedTelemetry) => void;
  selectIncident: (incident: ParsedTelemetry) => void;
  setRunbook: (runbook: TroubleshootResponseDTO) => void;
  setProgress: (progress: ProgressState) => void;
  setFilterVendor: (vendor: string) => void;
  setFilterSeverity: (severity: string) => void;
  setSearchQuery: (query: string) => void;
  setActiveTab: (tab: "runbook" | "citations" | "audit") => void;

  // Asynchronous Operations
  troubleshootIncident: (log: string, deviceId?: string, vendor?: string) => Promise<void>;
  fetchAuditHistory: (vendor?: string) => Promise<void>;
  loadInitialSampleData: () => void;
  clearFeed: () => void;
}

const SAMPLE_INCIDENTS: ParsedTelemetry[] = [
  {
    raw_log: "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent, hold time expired",
    vendor: "cisco",
    device_id: "Core-Router-01",
    event_code: "%BGP-5-ADJCHANGE",
    protocol: "bgp",
    interface: "GigabitEthernet0/0/1",
    peer_ip: "10.10.10.1",
    severity: "CRITICAL",
    category: "routing",
    extracted_keywords: ["bgp", "10.10.10.1", "%BGP-5-ADJCHANGE"],
  },
  {
    raw_log: "rpd[4210]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 (External AS 65001) changed state from Established to Idle",
    vendor: "juniper",
    device_id: "Juniper-MX960-01",
    event_code: "RPD_BGP_NEIGHBOR_STATE_CHANGED",
    protocol: "bgp",
    interface: "ge-0/1/0",
    peer_ip: "172.16.1.1",
    severity: "CRITICAL",
    category: "routing",
    extracted_keywords: ["bgp", "172.16.1.1", "RPD_BGP_NEIGHBOR_STATE_CHANGED"],
  },
  {
    raw_log: "EDGE_LINK_DEGRADATION: WAN link GE3 packet loss 18.4% PMTUD_BLACKHOLE",
    vendor: "velocloud",
    device_id: "Edge-SDWAN-Branch-04",
    event_code: "EDGE_LINK_DEGRADATION",
    protocol: "ipsec",
    interface: "GE3",
    peer_ip: "198.51.100.2",
    severity: "ERROR",
    category: "sdwan",
    extracted_keywords: ["sdwan", "GE3", "EDGE_LINK_DEGRADATION"],
  },
  {
    raw_log: "%MLAG-4-SPLIT_BRAIN: MLAG peer link Port-Channel 10 down on Leaf-01; secondary nodes isolated",
    vendor: "arista",
    device_id: "Arista-Leaf-01",
    event_code: "%MLAG-4-SPLIT_BRAIN",
    protocol: "evpn",
    interface: "Port-Channel 10",
    peer_ip: "10.0.0.2",
    severity: "CRITICAL",
    category: "switching",
    extracted_keywords: ["mlag", "Port-Channel 10", "%MLAG-4-SPLIT_BRAIN"],
  },
  {
    raw_log: "%OSPF-5-ADJCHG: Process 1, Nbr 192.168.1.2 on GigabitEthernet0/0/2 from EXSTART to DOWN",
    vendor: "cisco",
    device_id: "Dist-Router-02",
    event_code: "%OSPF-5-ADJCHG",
    protocol: "ospf",
    interface: "GigabitEthernet0/0/2",
    peer_ip: "192.168.1.2",
    severity: "WARNING",
    category: "routing",
    extracted_keywords: ["ospf", "192.168.1.2", "%OSPF-5-ADJCHG"],
  },
];

export const useNOCStore = create<NOCState>((set, get) => ({
  telemetryFeed: [],
  activeIncident: null,
  activeRunbook: null,
  citations: [],
  auditHistory: [],

  progress: { stage: "idle" },
  isAnalyzing: false,
  wsConnected: false,

  filterVendor: "all",
  filterSeverity: "all",
  searchQuery: "",
  activeTab: "runbook",

  setWsConnected: (connected) => set({ wsConnected: connected }),

  addTelemetryLog: (log) =>
    set((state) => ({
      telemetryFeed: [log, ...state.telemetryFeed.slice(0, 99)],
    })),

  selectIncident: (incident) => {
    set({ activeIncident: incident });
    get().troubleshootIncident(incident.raw_log, incident.device_id, incident.vendor);
  },

  setRunbook: (runbook) =>
    set({
      activeRunbook: runbook,
      citations: runbook.cited_vendor_docs || [],
      progress: { stage: "completed" },
      isAnalyzing: false,
    }),

  setProgress: (progress) => set({ progress }),
  setFilterVendor: (filterVendor) => set({ filterVendor }),
  setFilterSeverity: (filterSeverity) => set({ filterSeverity }),
  setSearchQuery: (searchQuery) => set({ searchQuery }),
  setActiveTab: (activeTab) => set({ activeTab }),

  troubleshootIncident: async (log, deviceId, vendor) => {
    set({
      isAnalyzing: true,
      progress: { stage: "parsing", message: "Parsing multi-vendor telemetry tokens..." },
      activeTab: "runbook",
    });

    try {
      // Simulate quick progress state transition
      setTimeout(() => {
        set({
          progress: {
            stage: "retrieval",
            message: `Searching pgvector HNSW + BM25 RRF for ${vendor || "vendor"} TAC docs...`,
          },
        });
      }, 300);

      const runbook = await api.troubleshoot({
        raw_logs: log,
        device_id: deviceId,
        vendor: vendor,
      });

      set({
        activeRunbook: runbook,
        citations: runbook.cited_vendor_docs || [],
        progress: { stage: "completed" },
        isAnalyzing: false,
      });

      // Refresh audit history in background
      get().fetchAuditHistory();
    } catch (err: any) {
      set({
        progress: { stage: "error", message: err.message || "Synthesis failed" },
        isAnalyzing: false,
      });
    }
  },

  fetchAuditHistory: async (vendor) => {
    try {
      const records = await api.getAuditHistory({
        limit: 30,
        vendor: vendor === "all" ? undefined : vendor,
      });
      set({ auditHistory: records });
    } catch (err) {
      console.error("Failed to fetch audit history:", err);
    }
  },

  loadInitialSampleData: () => {
    const state = get();
    if (state.telemetryFeed.length === 0) {
      set({ telemetryFeed: SAMPLE_INCIDENTS });
      if (!state.activeIncident) {
        state.selectIncident(SAMPLE_INCIDENTS[0]);
      }
    }
  },

  clearFeed: () => set({ telemetryFeed: [] }),
}));
