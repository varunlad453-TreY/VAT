"""
Automated Test Suite for Step 2: Chaos Engineering & Carrier-Grade Resiliency Proving
Validates Chaos Mesh manifest structure, target namespace isolation, and recovery assertions.
"""

from pathlib import Path
import pytest


def test_redpanda_pod_kill_manifest():
    """Validates PodChaos manifest targeting Redpanda brokers in staging."""
    manifest_path = Path("g:/VAT/k8s/chaos/redpanda-pod-kill.yaml")
    assert manifest_path.exists(), "redpanda-pod-kill.yaml must exist in k8s/chaos/"

    content = manifest_path.read_text(encoding="utf-8")
    assert "kind: PodChaos" in content
    assert "action: pod-kill" in content
    assert "namespace: vat-staging" in content
    assert "app.kubernetes.io/name: vat-redpanda" in content


def test_clickhouse_network_partition_manifest():
    """Validates NetworkChaos manifest isolating ClickHouse from Redpanda in staging."""
    manifest_path = Path("g:/VAT/k8s/chaos/clickhouse-network-partition.yaml")
    assert manifest_path.exists(), "clickhouse-network-partition.yaml must exist in k8s/chaos/"

    content = manifest_path.read_text(encoding="utf-8")
    assert "kind: NetworkChaos" in content
    assert "action: partition" in content
    assert "direction: both" in content
    assert "vat-staging" in content
    assert "duration: \"60s\"" in content


def test_chaos_schedule_workflow_manifest():
    """Validates serial Chaos Mesh workflow schedule and cooldown steps."""
    manifest_path = Path("g:/VAT/k8s/chaos/chaos-schedule.yaml")
    assert manifest_path.exists(), "chaos-schedule.yaml must exist in k8s/chaos/"

    content = manifest_path.read_text(encoding="utf-8")
    assert "kind: Schedule" in content
    assert "carrier-resilience-proving-workflow" in content
    assert "recovery-cooldown-step" in content
    assert "templateType: Serial" in content
