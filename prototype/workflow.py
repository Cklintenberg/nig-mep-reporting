"""Coordinates parsing, calculations, drafting, and evidence checks."""
from datetime import timedelta
from hashlib import sha256
import json
import time
from pathlib import Path
from schemas import Evidence, Finding, Issue, Narrative, SourcePack
from metrics import calculate_metrics
from ai import generate_narrative, PROMPT, prompt_for

ROOT = Path(__file__).resolve().parent
SAMPLES = {
    "normal": "A normal reporting week",
    "missing_data": "Missing reliability metrics",
    "conflicting_dates": "A requested date, not a commitment",
    "duplicate_feedback": "Duplicate partner feedback",
    "untrusted_note": "An instruction hidden in a source note",
}


def load_sample(name):
    if name not in SAMPLES:
        raise ValueError("Unknown sample week.")
    folder = ROOT / "sample_data" / name
    return (folder / "metrics.csv").read_bytes(), (folder / "sources.json").read_bytes()


def validate_inputs(metrics_bytes, sources_bytes):
    if len(sources_bytes) > 250_000:
        raise ValueError("Source notes exceed the 250 KB prototype limit.")
    try:
        pack = SourcePack.model_validate_json(sources_bytes)
    except Exception as exc:
        raise ValueError("Invalid sources.json. Use the sample structure, unique source IDs, and a Monday week_start. " + str(exc)[:350]) from None
    if metrics_bytes is None and not pack.sources:
        raise ValueError("Upload a metrics spreadsheet, meeting material, or both.")
    if metrics_bytes is not None:
        metrics, issues = calculate_metrics(metrics_bytes, pack)
    else:
        metrics, issues = [], [Issue(severity="warning", code="no_metrics", message="No platform spreadsheet supplied. This report contains meeting evidence only; no KPIs are inferred.")]
    if not pack.sources:
        issues.append(Issue(severity="warning", code="no_notes", message="No meeting material supplied. This report contains calculated figures only; reasons and commitments are unknown."))
    end = pack.week_start + timedelta(days=6)
    for source in pack.sources:
        if source.date is not None and source.date > end:
            issues.append(Issue(severity="warning", code="future_source", message=f"{source.id} is dated after the reporting week. Review its relevance."))
    if any(source.date is None for source in pack.sources):
        issues.append(Issue(severity="warning", code="undated_sources", message="Some meeting dates were not supplied. Confirm that these notes belong in the selected reporting week; transcript timestamps are not calendar dates."))
    seen = {}
    for source in pack.sources:
        normalized = " ".join(source.text.lower().split())
        if normalized in seen:
            issues.append(Issue(severity="warning", code="duplicate_source", message=f"{source.id} repeats {seen[normalized]}. Treat as one piece of feedback."))
        else:
            seen[normalized] = source.id
    return pack, metrics, issues


def check_evidence(narrative, pack):
    """Mechanical checks only. A valid quote does not prove semantic support."""
    sources = {s.id: s.text for s in pack.sources}
    issues = []
    for index, finding in enumerate(narrative.findings, start=1):
        for evidence in finding.evidence:
            if evidence.source_id not in sources:
                issues.append(Issue(severity="error", code="unknown_source", message=f"Finding {index}: unknown source {evidence.source_id}."))
            elif evidence.quote not in sources[evidence.source_id]:
                issues.append(Issue(severity="error", code="invalid_quote", message=f"Finding {index}: quotation does not match {evidence.source_id}."))
        if finding.needs_review and not finding.review_reason:
            issues.append(Issue(severity="error", code="missing_review_reason", message=f"Finding {index} is flagged without an explanation."))
    return issues


def baseline_narrative(pack):
    """Non-AI comparison: verbatim source excerpts, no synthesis or deduplication."""
    mapping = {"partner": "partner feedback", "engineering": "engineering update", "action": "open action", "context": "source note"}
    return Narrative(findings=[Finding(
        category=mapping[s.kind], title=s.title[:120], summary=s.text[:600],
        evidence=[Evidence(source_id=s.id, quote=s.text[:600])],
        needs_review=True, review_reason="Verbatim excerpt. A human must interpret and reconcile this source.",
    ) for s in pack.sources[:10]], discussion_questions=[])


def input_fingerprint(metrics_bytes, sources_bytes, intake=None):
    payload = (metrics_bytes if metrics_bytes is not None else b"<no-metrics>") + b"\0" + sources_bytes
    if intake is not None:
        payload += b"\0" + json.dumps(intake, sort_keys=True).encode()
    return sha256(payload).hexdigest()


def build_report(metrics_bytes, sources_bytes, mode="baseline", model="gpt-6-luna", provider="OpenAI", intake=None):
    started = time.perf_counter()
    pack, metrics, issues = validate_inputs(metrics_bytes, sources_bytes)
    if mode not in {"live", "baseline"}:
        raise ValueError("Unsupported generation mode.")
    if not pack.sources:
        narrative = Narrative(findings=[], discussion_questions=[])
        usage = {"model": "none", "mode": "metrics only", "latency_seconds": 0,
                 "input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "estimated_cost_usd": 0}
    elif mode == "live":
        narrative, usage = generate_narrative(pack, model, provider)
        if not narrative.findings:
            raise ValueError("The model returned no findings for the supplied meeting material. Review the input and retry.")
    elif mode == "baseline":
        narrative = baseline_narrative(pack)
        usage = {"model": "none", "mode": "non-AI baseline", "latency_seconds": 0,
                 "input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "estimated_cost_usd": 0}
        if len(pack.sources) > 10:
            issues.append(Issue(severity="warning", code="baseline_truncated", message="Baseline displays only the first 10 sources. All originals remain available for review."))
    else:
        raise ValueError("Unsupported generation mode.")
    issues += check_evidence(narrative, pack)
    return {
        "pack": pack.model_dump(mode="json"), "metrics": [m.model_dump() for m in metrics],
        "narrative": narrative.model_dump(), "issues": [i.model_dump() for i in issues],
        "usage": usage, "elapsed_seconds": round(time.perf_counter() - started, 3),
        "metrics_csv": metrics_bytes.decode("utf-8-sig") if metrics_bytes is not None else None,
        "input_hash": input_fingerprint(metrics_bytes, sources_bytes, intake),
        "intake": intake,
        "schema_hash": sha256(json.dumps(Narrative.model_json_schema(), sort_keys=True).encode()).hexdigest(),
        "prompt_hash": sha256(prompt_for(pack).encode()).hexdigest(),
    }
