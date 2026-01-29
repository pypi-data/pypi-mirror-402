import json
from pathlib import Path

from pic_standard.evidence import EvidenceSystem, apply_verified_ids_to_provenance
from pic_standard.verifier import ActionProposal

ROOT = Path(__file__).resolve().parents[1]


def test_evidence_hash_ok_verifies_and_upgrades_provenance():
    proposal_path = ROOT / "examples" / "financial_hash_ok.json"
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

    report = EvidenceSystem().verify_all(proposal, base_dir=proposal_path.parent)
    assert report.ok
    assert "invoice_123" in report.verified_ids

    upgraded = apply_verified_ids_to_provenance(proposal, report.verified_ids)
    # Should pass verifier after upgrade (money requires TRUSTED evidence)
    ActionProposal(**upgraded)


def test_evidence_hash_bad_fails():
    proposal_path = ROOT / "examples" / "failing" / "financial_hash_bad.json"
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))

    report = EvidenceSystem().verify_all(proposal, base_dir=proposal_path.parent)
    assert not report.ok
    assert report.results
    assert any((not r.ok) for r in report.results)
