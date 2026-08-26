/**
 * TypeScript Type Definitions for VAT Enterprise Platform
 * Strictly matched to Backend Pydantic v2 Models & DTOs
 */

export type VendorPlatform =
  | "cisco"
  | "juniper"
  | "velocloud"
  | "arista"
  | "nokia"
  | "huawei"
  | "generic";

export type ProtocolType =
  | "bgp"
  | "ospf"
  | "ipsec"
  | "evpn"
  | "interface"
  | "general";

export type SeverityLevel = "CRITICAL" | "ERROR" | "WARNING" | "INFO";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export type ConfigMode =
  | "interface"
  | "router bgp"
  | "router ospf"
  | "set"
  | "system"
  | "cli";

export interface ParsedTelemetry {
  raw_log: string;
  vendor: VendorPlatform;
  device_id: string;
  event_code?: string | null;
  protocol?: ProtocolType | string | null;
  interface?: string | null;
  peer_ip?: string | null;
  severity: SeverityLevel;
  category: string;
  extracted_keywords: string[];
}

export interface TelemetryEvent {
  event_id: string;
  timestamp_epoch: number;
  telemetry: ParsedTelemetry;
}

export interface PreCheckCommand {
  step: number;
  command: string;
  description: string;
  expected_output: string;
}

export interface RemediationCommand {
  step: number;
  action: string;
  command: string;
  config_mode: ConfigMode | string;
  explanation: string;
}

export interface PostCheckCommand {
  step: number;
  command: string;
  validation_criteria: string;
}

export interface RollbackCommand {
  step: number;
  action: string;
  command: string;
  trigger_condition: string;
}

export interface RiskAssessment {
  risk_level: RiskLevel;
  estimated_downtime_sec: number;
  blast_radius_scope: string;
  impacted_services: string[];
}

export interface VendorDocCitation {
  source_url: string;
  title: string;
  vendor: string;
  similarity_score: number;
  excerpt: string;
}

export interface ResolutionStepDTO {
  step_number: number;
  action: string;
  command?: string | null;
  expected_output?: string | null;
  explanation: string;
}

export interface TroubleshootResponseDTO {
  incident_id?: string | null;
  device_id?: string | null;
  generated_at: string;
  vendor: VendorPlatform | string;
  protocol: ProtocolType | string;
  diagnosis: string;
  root_cause_hypothesis: string;
  confidence_score: number;
  model_used: string;
  pre_checks: PreCheckCommand[];
  remediation_commands: RemediationCommand[];
  post_checks: PostCheckCommand[];
  rollback_playbook: RollbackCommand[];
  risk_assessment: RiskAssessment;
  resolution_steps: ResolutionStepDTO[];
  cited_vendor_docs: VendorDocCitation[];
}

export interface TroubleshootRequestDTO {
  incident_id?: string;
  device_id?: string;
  vendor?: string;
  protocol?: string;
  raw_logs: string;
  context?: Record<string, any>;
}

export interface TelemetryIngestBatchRequestDTO {
  logs: string[];
  device_hint?: string;
  auto_troubleshoot?: boolean;
}

export interface TelemetryIngestResponseDTO {
  total_received: number;
  parsed_events: ParsedTelemetry[];
  troubleshooting_reports: TroubleshootResponseDTO[];
}

export interface StepCommand {
  step?: number;
  command: string;
  description?: string;
  expected_output?: string;
  mode?: string;
}

export interface GroundedCitationSource {
  title: string;
  vendor: string;
  url?: string;
  similarity_score: number;
  excerpt: string;
}

export interface RunbookStage {
  failure_diagnosis: string;
  root_cause_hypothesis: string;
  blast_radius: string;
  estimated_downtime_seconds: number;
  confidence_score: number;
  synthesis_engine: string;
  runbook_pre_checks: StepCommand[];
  runbook_remediation: StepCommand[];
  runbook_post_checks: StepCommand[];
  runbook_rollback: StepCommand[];
  grounded_sources: GroundedCitationSource[];
}

export interface AuditLedgerEntry {
  id?: number;
  incident_id?: string | null;
  device_id: string;
  vendor: string;
  raw_logs: string;
  diagnosis: string;
  root_cause: string;
  risk_level: string;
  remediation_steps: Record<string, any>[];
  rollback_steps: Record<string, any>[];
  cited_sources: Record<string, any>[];
  confidence_score: number;
  model_used: string;
  executed_by?: string;
  created_at: string;
  // Aliases for unified presentation
  failure_diagnosis?: string;
  blast_radius?: string;
  runbook_pre_checks?: any[];
  runbook_remediation?: any[];
  runbook_rollback?: any[];
}

export type AuditRecord = AuditLedgerEntry;

export interface HealthResponse {
  status: "healthy" | "degraded";
  service: string;
  database_connected: boolean;
  version: string;
  timestamp: string;
}

export type SynthesisStage =
  | "idle"
  | "parsing"
  | "parsed"
  | "retrieval"
  | "retrieved_citations"
  | "synthesizing"
  | "completed"
  | "error";

export interface ProgressState {
  stage: SynthesisStage;
  message?: string;
  vendor?: string;
  protocol?: string;
  severity?: string;
  citationsCount?: number;
}
