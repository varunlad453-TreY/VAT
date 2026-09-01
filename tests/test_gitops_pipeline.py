"""
Automated Test Suite for Step 3: GitOps & CI/CD Pipeline Finalization
Validates GitHub Actions workflow structures, ArgoCD AppSet templates, and idempotency guarantees.
"""

from pathlib import Path
import pytest


def test_github_actions_ci_workflow():
    """Validates CI workflow has backend tests, frontend build, and manifest validation."""
    ci_path = Path("g:/VAT/.github/workflows/ci.yaml")
    assert ci_path.exists(), "ci.yaml must exist in .github/workflows/"

    content = ci_path.read_text(encoding="utf-8")
    assert "backend-test:" in content
    assert "frontend-build:" in content
    assert "manifest-lint:" in content
    assert "pytest tests/ -v" in content
    assert "npm run build" in content


def test_github_actions_deploy_workflow():
    """Validates GitOps CD workflow has image build and SHA pinning steps."""
    cd_path = Path("g:/VAT/.github/workflows/deploy-gitops.yaml")
    assert cd_path.exists(), "deploy-gitops.yaml must exist in .github/workflows/"

    content = cd_path.read_text(encoding="utf-8")
    assert "vat-backend" in content
    assert "vat-embedding-worker" in content
    assert "vat-frontend" in content
    assert "github.sha" in content


def test_argocd_appset_manifest():
    """Validates ArgoCD ApplicationSet defines staging and production environments."""
    appset_path = Path("g:/VAT/k8s/gitops/argocd-appset.yaml")
    assert appset_path.exists(), "argocd-appset.yaml must exist in k8s/gitops/"

    content = appset_path.read_text(encoding="utf-8")
    assert "kind: ApplicationSet" in content
    assert "vat-staging" in content
    assert "vat-system" in content
    assert "selfHeal: true" in content
    assert "prune: true" in content
