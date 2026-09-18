# Vendor Risk Questionnaire Automation

[![Python tests](https://github.com/d-enyaosah/vendor-risk-questionnaire-automation/actions/workflows/tests.yml/badge.svg)](https://github.com/d-enyaosah/vendor-risk-questionnaire-automation/actions/workflows/tests.yml)

A transparent Python workflow that converts vendor security questionnaires into normalized risk-review data and a self-contained HTML dashboard. This personal portfolio project demonstrates practical third-party risk management (TPRM), evidence review, rules-based risk scoring, exception identification, remediation guidance, and stakeholder reporting.

## What it does

- Normalizes inconsistent answers such as `Y`, `implemented`, `partial`, and `in progress`.
- Flags required evidence that is missing.
- Scores each control using response quality and business severity.
- Generates findings and remediation guidance.
- Produces `risk_review.csv` for analysis and `risk_dashboard.html` for stakeholder review.
- Requires no third-party packages.

## Run it

```bash
python3 vendor_risk_analyzer.py data/sample_vendor_questionnaire.csv \
  --output-dir output --vendor "Acme Cloud Services"
```

Open `output/risk_dashboard.html` in a browser. The scoring model is intentionally transparent and easy to adapt to an organization's risk methodology.

## Example results

The included sample questionnaire contains eight controls across access control, data protection, incident response, business continuity, vulnerability management, and third-party risk. Running the tool creates:

- `output/risk_review.csv`: normalized control results, evidence status, findings, remediation guidance, and risk ratings.
- `output/risk_dashboard.html`: a responsive summary showing total controls, review-required items, missing evidence, and high/critical risks.

## Expected input columns

`control_id`, `domain`, `question`, `response`, `severity`, `evidence_required`, `evidence`, `owner`

Supported severity values: `Critical`, `High`, `Medium`, `Low`.

## Test it

```bash
python3 -m unittest discover -s tests -v
```

The same test command runs automatically through GitHub Actions on pushes and pull requests.

## Repository structure

```text
.
├── data/sample_vendor_questionnaire.csv
├── output/risk_dashboard.html
├── output/risk_review.csv
├── tests/test_vendor_risk_analyzer.py
├── vendor_risk_analyzer.py
├── PROJECT_ENTRY.md
└── requirements.txt
```

## Portfolio positioning

This is a personal project and does not represent sample results, production data, or employer outcomes.

## Security and data handling

The repository contains only synthetic sample data. We do not commit confidential vendor questionnaires, assurance reports, credentials, personal data, or employer information.

## Suggested next extensions

- Mapping questionnaire controls to NIST CSF, ISO 27001, or SOC 2 criteria.
- Adding configurable scoring weights through JSON.
- Importing XLSX files and exporting a Power BI-ready dataset.
- Adding reviewer decisions, residual-risk acceptance, and remediation due dates.
- Connecting a ticketing or GRC platform only after implementing and testing the integration.

## License

Released under the MIT License.
