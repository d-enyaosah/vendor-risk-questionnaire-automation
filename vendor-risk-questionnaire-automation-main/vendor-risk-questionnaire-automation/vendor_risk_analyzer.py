#!/usr/bin/env python3
"""Normalize a vendor security questionnaire and produce risk-review outputs."""

from __future__ import annotations

import argparse
import csv
import html
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


YES = {"yes", "y", "implemented", "complete", "compliant"}
PARTIAL = {"partial", "partially", "in progress", "planned"}
NO = {"no", "n", "not implemented", "non-compliant", "noncompliant"}
SEVERITY_WEIGHT = {"critical": 4, "high": 3, "medium": 2, "low": 1}


@dataclass(frozen=True)
class Review:
    control_id: str
    domain: str
    question: str
    response: str
    severity: str
    evidence: str
    owner: str
    status: str
    evidence_status: str
    risk_score: int
    risk_rating: str
    finding: str
    remediation: str


def clean(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def normalize_response(value: str) -> str:
    normalized = clean(value).lower()
    if normalized in YES:
        return "Yes"
    if normalized in PARTIAL:
        return "Partial"
    if normalized in NO:
        return "No"
    return "Unclear"


def rate(score: int) -> str:
    if score >= 10:
        return "Critical"
    if score >= 7:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"


def review_row(row: dict[str, str]) -> Review:
    response = normalize_response(row.get("response", ""))
    severity = clean(row.get("severity", "medium")).lower()
    if severity not in SEVERITY_WEIGHT:
        severity = "medium"
    evidence = clean(row.get("evidence", ""))
    evidence_required = clean(row.get("evidence_required", "yes")).lower() not in {"no", "n", "false", "0"}
    evidence_missing = evidence_required and not evidence

    response_factor = {"Yes": 0, "Partial": 2, "No": 3, "Unclear": 2}[response]
    score = min(12, SEVERITY_WEIGHT[severity] * response_factor + (2 if evidence_missing else 0))
    status = "Pass" if response == "Yes" and not evidence_missing else "Review Required"
    evidence_status = "Missing" if evidence_missing else ("Provided" if evidence else "Not Required")

    issues = []
    if response != "Yes":
        issues.append(f"control response is {response.lower()}")
    if evidence_missing:
        issues.append("required evidence is missing")
    finding = "; ".join(issues).capitalize() if issues else "No exception identified"
    remediation = (
        "Obtain and validate supporting evidence; confirm control ownership and a dated remediation plan."
        if status != "Pass"
        else "No action required; retain evidence for the assessment record."
    )

    return Review(
        control_id=clean(row.get("control_id", "")),
        domain=clean(row.get("domain", "Uncategorized")),
        question=clean(row.get("question", "")),
        response=response,
        severity=severity.title(),
        evidence=evidence,
        owner=clean(row.get("owner", "Unassigned")),
        status=status,
        evidence_status=evidence_status,
        risk_score=score,
        risk_rating=rate(score),
        finding=finding,
        remediation=remediation,
    )


def load_reviews(input_path: Path) -> list[Review]:
    with input_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"control_id", "domain", "question", "response", "severity", "evidence_required", "evidence", "owner"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
        return [review_row(row) for row in reader]


def write_csv(reviews: list[Review], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(Review.__dataclass_fields__)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: getattr(item, field) for field in fields} for item in reviews)


def write_dashboard(reviews: list[Review], output_path: Path, vendor_name: str) -> None:
    counts = Counter(item.risk_rating for item in reviews)
    exceptions = [item for item in reviews if item.status != "Pass"]
    missing_evidence = sum(item.evidence_status == "Missing" for item in reviews)
    rows = "".join(
        f"<tr><td>{html.escape(r.control_id)}</td><td>{html.escape(r.domain)}</td>"
        f"<td>{html.escape(r.response)}</td><td>{html.escape(r.evidence_status)}</td>"
        f"<td>{r.risk_score}</td><td><span class='pill {r.risk_rating.lower()}'>{r.risk_rating}</span></td>"
        f"<td>{html.escape(r.finding)}</td></tr>" for r in sorted(reviews, key=lambda x: x.risk_score, reverse=True)
    )
    cards = "".join(
        f"<div class='card'><b>{label}</b><strong>{value}</strong></div>" for label, value in [
            ("Controls", len(reviews)), ("Review Required", len(exceptions)),
            ("Missing Evidence", missing_evidence), ("High/Critical", counts["High"] + counts["Critical"])
        ]
    )
    document = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>{html.escape(vendor_name)} Vendor Risk Review</title><style>
body{{font-family:Arial,sans-serif;margin:32px;background:#f4f7fb;color:#172033}}h1{{margin-bottom:4px}}.sub{{color:#60708a}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}}.card{{background:white;border-radius:10px;padding:16px;box-shadow:0 2px 8px #dbe2ec}}
.card b{{display:block;color:#60708a;font-size:13px}}.card strong{{font-size:28px}}table{{width:100%;border-collapse:collapse;background:white}}
th,td{{padding:11px;border-bottom:1px solid #e5e9f0;text-align:left;font-size:14px}}th{{background:#172033;color:white}}.pill{{padding:4px 8px;border-radius:12px;font-weight:bold}}
.critical{{background:#ffd7d7;color:#8b0000}}.high{{background:#ffe2c2;color:#8a4500}}.medium{{background:#fff1b8;color:#6d5700}}.low{{background:#d9f2e3;color:#176b3a}}
@media(max-width:800px){{.cards{{grid-template-columns:repeat(2,1fr)}}}}</style></head><body>
<h1>Vendor Risk Review</h1><div class='sub'>{html.escape(vendor_name)} · Automated questionnaire assessment</div>
<div class='cards'>{cards}</div><table><thead><tr><th>Control</th><th>Domain</th><th>Response</th><th>Evidence</th><th>Score</th><th>Rating</th><th>Finding</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Vendor questionnaire CSV")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--vendor", default="Sample Vendor")
    args = parser.parse_args()
    reviews = load_reviews(args.input)
    write_csv(reviews, args.output_dir / "risk_review.csv")
    write_dashboard(reviews, args.output_dir / "risk_dashboard.html", args.vendor)
    print(f"Reviewed {len(reviews)} controls; outputs written to {args.output_dir}")


if __name__ == "__main__":
    main()
