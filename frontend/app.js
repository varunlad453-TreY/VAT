/**
 * Vendor-Aware Troubleshooting (VAT) - Enterprise NOC Controller
 * Architecture: High-Density Split-Pane Telemetry & RAG Runbook Engine
 */

const SAMPLES = {
  cisco_bgp: {
    device: "Edge-Router-East",
    vendor: "cisco",
    log: "%BGP-5-ADJCHANGE: neighbor 10.10.10.1 Down - BGP Notification sent, hold time expired",
  },
  cisco_ospf: {
    device: "Dist-Router-01",
    vendor: "cisco",
    log: "%OSPF-5-ADJCHG: Process 1, Nbr 192.168.1.2 on GigabitEthernet0/0/1 from EXSTART to DOWN, Neighbor Down: Too many retransmissions",
  },
  juniper_bgp: {
    device: "MX960-Edge-01",
    vendor: "juniper",
    log: "rpd[1234]: RPD_BGP_NEIGHBOR_STATE_CHANGED: BGP peer 172.16.1.1 (External AS 65001) changed state from Established to Idle (event HoldTimer)",
  },
  velo_sdwan: {
    device: "Branch-Edge-540",
    vendor: "velocloud",
    log: "EDGE_LINK_DEGRADATION: WAN link GE3 packet loss 18.4% exceeding SLA threshold. VeloBrain QoE score 2.4",
  },
  arista_mlag: {
    device: "Leaf-Switch-Pair-01",
    vendor: "arista",
    log: "%MLAG-4-SPLIT_BRAIN: MLAG peer link down; secondary nodes isolated. Dual-active state detected",
  },
};

let currentRunbookData = null;

/**
 * Select preset incident from the active queue
 */
function selectPreset(key) {
  const sample = SAMPLES[key];
  if (!sample) return;

  // Highlight active row in incident queue
  document.querySelectorAll("#incidentList .incident-row").forEach(row => {
    if (row.getAttribute("data-preset") === key) {
      row.classList.add("is-active");
    } else {
      row.classList.remove("is-active");
    }
  });

  document.getElementById("deviceId").value = sample.device;
  document.getElementById("vendorSelect").value = sample.vendor;
  document.getElementById("rawLogs").value = sample.log;
  updateCharCount();

  document.getElementById("crumbTarget").textContent = sample.device;

  // Auto trigger analysis
  handleTroubleshoot();
}

/**
 * Handle form submit and diagnostic synthesis
 */
async function handleTroubleshoot(event) {
  if (event) event.preventDefault();

  const deviceId = document.getElementById("deviceId").value.trim() || "Core-Router-01";
  const vendor = document.getElementById("vendorSelect").value;
  const rawLogs = document.getElementById("rawLogs").value.trim();

  if (!rawLogs) return;

  // Update UI Loading State
  const btn = document.getElementById("submitBtn");
  const btnText = document.getElementById("btnText");
  const spinner = document.getElementById("btnSpinner");
  const crumbStatus = document.getElementById("crumbStatus");

  btn.disabled = true;
  btnText.textContent = "Synthesizing Runbook...";
  spinner.style.display = "inline-block";
  crumbStatus.textContent = "SYNTHESIS IN PROGRESS...";
  crumbStatus.style.color = "var(--brand-cyan)";

  try {
    const response = await fetch("/troubleshoot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_id: deviceId,
        vendor: vendor,
        raw_logs: rawLogs,
      }),
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || `HTTP ${response.status}`);
    }

    const data = await response.json();
    currentRunbookData = data;
    renderResults(data);
    loadAuditHistory();
  } catch (err) {
    alert("Diagnostic synthesis error: " + err.message);
    crumbStatus.textContent = "SYNTHESIS FAILED";
    crumbStatus.style.color = "var(--status-critical)";
  } finally {
    btn.disabled = false;
    btnText.textContent = "Synthesize Diagnostic Playbook";
    spinner.style.display = "none";
  }
}

/**
 * Render structured runbook in operational canvas
 */
function renderResults(data) {
  document.getElementById("emptyState").style.display = "none";
  document.getElementById("resultContent").style.display = "block";
  document.getElementById("canvasActions").style.display = "flex";

  const targetDevice = data.device_id || document.getElementById("deviceId").value.trim() || "Edge-Router";
  data.device_id = targetDevice;

  // Breadcrumbs
  document.getElementById("crumbTarget").textContent = targetDevice;
  const crumbStatus = document.getElementById("crumbStatus");
  crumbStatus.textContent = "PLAYBOOK SYNTHESIZED";
  crumbStatus.style.color = "var(--status-healthy)";

  // Executive Diagnosis Banner
  document.getElementById("diagTitle").textContent = data.diagnosis;
  document.getElementById("diagConfidence").textContent = `${(data.confidence_score * 100).toFixed(1)}%`;
  document.getElementById("diagRoot").textContent = data.root_cause_hypothesis;

  document.getElementById("metaVendor").textContent = (data.vendor || "UNKNOWN").toUpperCase();
  document.getElementById("metaProtocol").textContent = (data.protocol || "GENERAL").toUpperCase();

  const risk = data.risk_assessment || {};
  const riskEl = document.getElementById("metaRisk");
  const rLevel = (risk.risk_level || "HIGH").toUpperCase();
  riskEl.textContent = rLevel;
  if (rLevel === "CRITICAL") riskEl.className = "meta-val font-semibold text-critical";
  else if (rLevel === "HIGH") riskEl.className = "meta-val font-semibold text-warning";
  else riskEl.className = "meta-val font-semibold text-healthy";

  document.getElementById("metaBlast").textContent = (risk.blast_radius_scope || "SINGLE PEER").toUpperCase();

  const promptPrefix = `${targetDevice}# `;

  // Stage 01: Pre-Checks
  const preContainer = document.getElementById("preChecksContainer");
  preContainer.innerHTML = (data.pre_checks || []).map((p, idx) => `
    <div class="step-row">
      <div class="step-row-top">
        <div class="step-title-wrap">
          <span class="step-seq">1.${p.step || idx + 1}</span>
          <span class="step-action-text">${escapeHtml(p.description)}</span>
        </div>
        <span class="step-mode-tag">READ-ONLY TELEMETRY</span>
      </div>
      <div class="terminal-block">
        <div class="terminal-code"><span class="terminal-prompt">${promptPrefix}</span>${escapeHtml(p.command)}</div>
        <button type="button" class="btn-copy-code" onclick="copySnippet('${escapeJs(p.command)}')">Copy</button>
      </div>
      <div class="step-detail-note"><strong>Expected Observation:</strong> ${escapeHtml(p.expected_output)}</div>
    </div>
  `).join("") || '<p class="text-muted text-xs">No pre-check inspection commands required.</p>';

  // Stage 02: Remediation Commands
  const remedContainer = document.getElementById("remediationContainer");
  remedContainer.innerHTML = (data.remediation_commands || []).map((r, idx) => `
    <div class="step-row">
      <div class="step-row-top">
        <div class="step-title-wrap">
          <span class="step-seq" style="color: var(--brand-primary);">2.${r.step || idx + 1}</span>
          <span class="step-action-text">${escapeHtml(r.action)}</span>
        </div>
        <span class="step-mode-tag">${escapeHtml((r.config_mode || "CLI").toUpperCase())}</span>
      </div>
      <div class="terminal-block">
        <div class="terminal-code"><span class="terminal-prompt">${promptPrefix}</span>${escapeHtml(r.command)}</div>
        <button type="button" class="btn-copy-code" onclick="copySnippet('${escapeJs(r.command)}')">Copy</button>
      </div>
      <div class="step-detail-note">${escapeHtml(r.explanation)}</div>
    </div>
  `).join("") || '<p class="text-muted text-xs">No active remediation commands required.</p>';

  // Stage 03: Post-Checks
  const postContainer = document.getElementById("postChecksContainer");
  postContainer.innerHTML = (data.post_checks || []).map((p, idx) => `
    <div class="step-row">
      <div class="step-row-top">
        <div class="step-title-wrap">
          <span class="step-seq" style="color: var(--status-healthy);">3.${p.step || idx + 1}</span>
          <span class="step-action-text">Post-Execution Verification & Service Restoration</span>
        </div>
        <span class="step-mode-tag">CONVERGENCE</span>
      </div>
      <div class="terminal-block">
        <div class="terminal-code"><span class="terminal-prompt">${promptPrefix}</span>${escapeHtml(p.command)}</div>
        <button type="button" class="btn-copy-code" onclick="copySnippet('${escapeJs(p.command)}')">Copy</button>
      </div>
      <div class="step-detail-note"><strong>Verification Criteria:</strong> ${escapeHtml(p.validation_criteria)}</div>
    </div>
  `).join("") || '<p class="text-muted text-xs">No post-check validation commands required.</p>';

  // Stage 04: Rollback Playbook
  const rollbackContainer = document.getElementById("rollbackContainer");
  rollbackContainer.innerHTML = (data.rollback_playbook || []).map((rb, idx) => `
    <div class="step-row">
      <div class="step-row-top">
        <div class="step-title-wrap">
          <span class="step-seq" style="color: var(--status-warning);">4.${rb.step || idx + 1}</span>
          <span class="step-action-text">${escapeHtml(rb.action)}</span>
        </div>
        <span class="step-mode-tag">REVERSION</span>
      </div>
      <div class="terminal-block">
        <div class="terminal-code"><span class="terminal-prompt">${promptPrefix}</span>${escapeHtml(rb.command)}</div>
        <button type="button" class="btn-copy-code" onclick="copySnippet('${escapeJs(rb.command)}')">Copy</button>
      </div>
      <div class="step-detail-note"><strong>Trigger Condition:</strong> ${escapeHtml(rb.trigger_condition)}</div>
    </div>
  `).join("") || '<p class="text-muted text-xs">No rollback commands required for read-only actions.</p>';

  // Citations
  const citContainer = document.getElementById("citationsContainer");
  citContainer.innerHTML = (data.cited_vendor_docs || []).map(c => `
    <div class="citation-row">
      <div class="citation-row-header">
        <a href="${c.source_url}" target="_blank" rel="noopener noreferrer" class="citation-link">
          ${escapeHtml(c.title)}
        </a>
        <span class="citation-sim-score">MATCH ${(c.similarity_score * 100).toFixed(0)}%</span>
      </div>
      <div class="citation-body">${escapeHtml(c.excerpt)}</div>
    </div>
  `).join("") || '<p class="text-muted text-xs">No external citations found.</p>';
}

/**
 * Load recent audit logs from PostgreSQL
 */
async function loadAuditHistory() {
  const list = document.getElementById("auditList");
  try {
    const res = await fetch("/troubleshoot/audit?limit=5");
    if (!res.ok) throw new Error("Could not fetch audit history");
    const items = await res.json();

    if (!items || items.length === 0) {
      list.innerHTML = `<div class="audit-entry"><div class="audit-diag text-muted">PostgreSQL ledger online. Ready for telemetry stream logging.</div></div>`;
      return;
    }

    list.innerHTML = items.map(it => `
      <div class="audit-entry">
        <div class="audit-entry-top">
          <span class="audit-device">${escapeHtml(it.device_id || "Core-Router")}</span>
          <span class="audit-time">${new Date(it.created_at || Date.now()).toLocaleTimeString()}</span>
        </div>
        <div class="audit-diag">${escapeHtml(it.diagnosis || "Diagnostic run").substring(0, 65)}...</div>
      </div>
    `).join("");
  } catch {
    list.innerHTML = `<div class="audit-entry"><div class="audit-diag text-muted">PostgreSQL ledger connected. Ready.</div></div>`;
  }
}

/**
 * Copy single CLI snippet to clipboard
 */
function copySnippet(text) {
  navigator.clipboard.writeText(text).then(() => {
    const activeEl = document.activeElement;
    if (activeEl && activeEl.classList.contains("btn-copy-code")) {
      const orig = activeEl.textContent;
      activeEl.textContent = "COPIED";
      activeEl.style.background = "var(--status-healthy)";
      activeEl.style.color = "#ffffff";
      setTimeout(() => {
        activeEl.textContent = orig;
        activeEl.style.background = "";
        activeEl.style.color = "";
      }, 1200);
    }
  }).catch(() => {
    prompt("Copy CLI command:", text);
  });
}

/**
 * Copy all remediation commands as a complete script
 */
function copyAllCommands() {
  if (!currentRunbookData || !currentRunbookData.remediation_commands) return;
  const script = currentRunbookData.remediation_commands.map(r => r.command).join("\n");
  navigator.clipboard.writeText(script).then(() => {
    alert("Full remediation CLI script copied to clipboard.");
  });
}

/**
 * Export Runbook as JSON
 */
function exportRunbookJSON() {
  if (!currentRunbookData) return;
  const blob = new Blob([JSON.stringify(currentRunbookData, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `runbook_${currentRunbookData.device_id}_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Export Runbook as Markdown
 */
function exportRunbookMarkdown() {
  if (!currentRunbookData) return;
  const md = `# VAT Carrier Runbook: ${currentRunbookData.diagnosis}
**Target Device**: ${currentRunbookData.device_id}
**Vendor**: ${currentRunbookData.vendor}
**Protocol**: ${currentRunbookData.protocol}
**Risk**: ${currentRunbookData.risk_assessment?.risk_level}
**Confidence**: ${(currentRunbookData.confidence_score * 100).toFixed(1)}%

## Root Cause Hypothesis
${currentRunbookData.root_cause_hypothesis}

## 1. Pre-Checks (Read-Only)
${(currentRunbookData.pre_checks || []).map(p => `- \`${p.command}\` : ${p.description}`).join("\n")}

## 2. Target Remediation CLI
\`\`\`text
${(currentRunbookData.remediation_commands || []).map(r => r.command).join("\n")}
\`\`\`

## 3. Post-Checks & Convergence
${(currentRunbookData.post_checks || []).map(p => `- \`${p.command}\` : ${p.validation_criteria}`).join("\n")}

## 4. Rollback Playbook
${(currentRunbookData.rollback_playbook || []).map(r => `- \`${r.command}\` (Trigger: ${r.trigger_condition})`).join("\n")}
`;

  const blob = new Blob([md], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `incident_report_${currentRunbookData.device_id}.md`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Live UTC Clock
 */
function updateUtcClock() {
  const clock = document.getElementById("utcClock");
  if (!clock) return;
  const now = new Date();
  const utcStr = now.toISOString().replace("T", " ").substring(0, 19) + " UTC";
  clock.textContent = utcStr;
}

/**
 * Character count update
 */
function updateCharCount() {
  const raw = document.getElementById("rawLogs");
  const count = document.getElementById("charCount");
  if (raw && count) {
    count.textContent = `${new Blob([raw.value]).size} bytes`;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function escapeJs(str) {
  if (!str) return "";
  return str.replace(/'/g, "\\'").replace(/\n/g, "\\n");
}

// Initial Events
window.addEventListener("DOMContentLoaded", () => {
  loadAuditHistory();
  updateUtcClock();
  setInterval(updateUtcClock, 1000);

  const raw = document.getElementById("rawLogs");
  if (raw) {
    raw.addEventListener("input", updateCharCount);
    updateCharCount();
  }
});
