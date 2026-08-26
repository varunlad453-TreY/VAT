"""
Infrastructure Adapter: Resilient LLM AI Synthesizer
Uses AsyncOpenAI with tenacity retry/exponential backoff and fallback to DeterministicSynthesizer.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.application.dtos.troubleshoot_dto import (
    ResolutionStepDTO,
    TroubleshootRequestDTO,
    TroubleshootResponseDTO,
)
from backend.application.ports.ai_synthesizer import IAISynthesizer
from backend.domain.entities.citation import VendorDocCitation
from backend.domain.entities.remediation import (
    PostCheckCommand,
    PreCheckCommand,
    RemediationCommand,
    RiskAssessment,
    RollbackCommand,
)
from backend.domain.entities.telemetry import ParsedTelemetry
from backend.infrastructure.ai.deterministic_synthesizer import DeterministicSynthesizer
from config.settings import get_settings

logger = logging.getLogger(__name__)


class ResilientLLMAdapter(IAISynthesizer):
    """Resilient LLM Synthesizer with tenacity exponential backoff and circuit-breaker fallback."""

    def __init__(self, fallback_synthesizer: Optional[DeterministicSynthesizer] = None) -> None:
        self._fallback = fallback_synthesizer or DeterministicSynthesizer()

    async def synthesize_runbook(
        self,
        request: TroubleshootRequestDTO,
        parsed_telemetry: ParsedTelemetry,
        citations: List[VendorDocCitation],
        relevant_docs: List[Dict[str, Any]],
    ) -> TroubleshootResponseDTO:
        """Synthesize remediation runbook via LLM with automatic tenacity retry and fallback."""
        settings = get_settings()
        api_key = settings.github_token or settings.openai_api_key

        if not api_key:
            return await self._fallback.synthesize_runbook(
                request=request,
                parsed_telemetry=parsed_telemetry,
                citations=citations,
                relevant_docs=relevant_docs,
            )

        try:
            return await self._call_llm_with_retry(
                request=request,
                parsed_telemetry=parsed_telemetry,
                citations=citations,
                relevant_docs=relevant_docs,
            )
        except Exception as exc:
            logger.warning("LLM synthesis failed after retries (%s). Falling back to deterministic synthesizer.", exc)
            return await self._fallback.synthesize_runbook(
                request=request,
                parsed_telemetry=parsed_telemetry,
                citations=citations,
                relevant_docs=relevant_docs,
            )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _call_llm_with_retry(
        self,
        request: TroubleshootRequestDTO,
        parsed_telemetry: ParsedTelemetry,
        citations: List[VendorDocCitation],
        relevant_docs: List[Dict[str, Any]],
    ) -> TroubleshootResponseDTO:
        """Execute LLM call with exponential backoff."""
        from openai import AsyncOpenAI

        settings = get_settings()
        api_key = settings.github_token or settings.openai_api_key

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.ai_base_url if settings.github_token else None,
        )

        system_prompt = (
            "You are a Tier-3 Principal Network Architect for a carrier telecom network. "
            "Analyze the raw telemetry log strictly using the provided official vendor manuals. "
            "Structure your response with exact syntax for the target vendor (Cisco IOS-XE/XR, Junos CLI, VeloCloud, or Arista EOS). "
            "Evaluate blast radius, operational risk (LOW, MEDIUM, HIGH), and provide a safe Rollback Command. "
            "Respond with a valid JSON object matching this schema:\n"
            "{\n"
            '  "diagnosis": "Executive summary of failure",\n'
            '  "root_cause_hypothesis": "Root cause explanation",\n'
            '  "confidence_score": 0.96,\n'
            '  "risk_level": "LOW|MEDIUM|HIGH",\n'
            '  "estimated_downtime_sec": 0,\n'
            '  "blast_radius_scope": "Single Interface / Peer",\n'
            '  "pre_checks": [{"step": 1, "command": "show ...", "description": "...", "expected_output": "..."}],\n'
            '  "remediation_commands": [{"step": 1, "action": "...", "command": "...", "config_mode": "...", "explanation": "..."}],\n'
            '  "post_checks": [{"step": 1, "command": "show ...", "validation_criteria": "..."}],\n'
            '  "rollback_playbook": [{"step": 1, "action": "...", "command": "...", "trigger_condition": "..."}]\n'
            "}"
        )

        docs_context = "\n\n".join(
            [f"--- VENDOR DOC: {doc['title']} ({doc['source_url']}) ---\n{doc['chunk_text']}" for doc in relevant_docs]
        )

        effective_vendor = request.vendor or parsed_telemetry.vendor
        effective_protocol = request.protocol or parsed_telemetry.protocol
        effective_device = request.device_id or parsed_telemetry.device_id

        user_prompt = (
            f"LIVE NETWORK TELEMETRY:\n{request.raw_logs}\n\n"
            f"DEVICE: {effective_device}\n"
            f"VENDOR: {effective_vendor}\n"
            f"PROTOCOL: {effective_protocol}\n\n"
            f"OFFICIAL VENDOR DOCUMENTATION:\n{docs_context}\n\n"
            "Synthesize a strict, professional 4-stage remediation playbook in JSON format."
        )

        logger.info("Executing Enterprise LLM synthesis (%s) for %s...", settings.ai_model, effective_vendor)
        completion = await client.chat.completions.create(
            model=settings.ai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw_json = completion.choices[0].message.content or "{}"
        data = json.loads(raw_json)

        pre_checks = [PreCheckCommand(**p) for p in data.get("pre_checks", [])]
        remeds = [RemediationCommand(**r) for r in data.get("remediation_commands", [])]
        post_checks = [PostCheckCommand(**p) for p in data.get("post_checks", [])]
        rollbacks = [RollbackCommand(**r) for r in data.get("rollback_playbook", [])]

        risk = RiskAssessment(
            risk_level=data.get("risk_level", "LOW"),
            estimated_downtime_sec=data.get("estimated_downtime_sec", 0),
            blast_radius_scope=data.get("blast_radius_scope", "Single Interface / Peer"),
        )

        legacy_steps = [
            ResolutionStepDTO(
                step_number=r.step,
                action=r.action,
                command=r.command,
                explanation=r.explanation,
            )
            for r in remeds
        ]

        return TroubleshootResponseDTO(
            incident_id=request.incident_id,
            device_id=effective_device,
            generated_at=datetime.now(timezone.utc),
            vendor=effective_vendor,
            protocol=effective_protocol,
            diagnosis=data.get("diagnosis", "Diagnostic analysis completed."),
            root_cause_hypothesis=data.get("root_cause_hypothesis", "Identified anomaly from telemetry."),
            confidence_score=float(data.get("confidence_score", 0.95)),
            model_used=f"llm-{settings.ai_model}",
            pre_checks=pre_checks,
            remediation_commands=remeds,
            post_checks=post_checks,
            rollback_playbook=rollbacks,
            risk_assessment=risk,
            resolution_steps=legacy_steps,
            cited_vendor_docs=citations,
        )
