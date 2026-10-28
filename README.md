# Swift Payment Test Prototype

![Tests](https://github.com/Nissrine-Can/swift-payment-test-prototype/actions/workflows/tests.yml/badge.svg)

A small test-automation project for ISO 20022 payment messages (pacs.008), built in GitHub Codespaces on Ubuntu Linux to practice API testing, Bash scripting and CI.

All payment data is made up for practice.

## What it does

- **Validates payment messages** with a Python validator: amount, currency, UETR, BIC format and structured addresses.
- **Mock payment gateway API** (Flask): accepts pacs.008 XML at `POST /payments` and answers ACK (200) or NACK (400) with the reasons, like a simplified pacs.002 status report.
- **Tests the API** with a curl smoke script and a pytest suite (positive, negative and boundary cases).
- **Analyzes a gateway log** with Bash and grep.
- **Runs everything in CI** with GitHub Actions on every push and pull request.

## Project structure

| Folder / file | Purpose |
|---|---|
| `data/` | Valid and invalid payment messages, and a simplified XSD |
| `scripts/check_payment.py` | Validator with 5 checks (reused by the API) |
| `scripts/run_checks.sh` | Runs the validator on every XML file in `data/` |
| `scripts/analyze_logs.sh` | Summarizes the gateway log: payments, ACKs, NACKs, warnings, rejection reasons |
| `scripts/smoke_test.sh` | curl smoke tests against the running API |
| `api/app.py` | Mock payment gateway API |
| `tests/test_api.py` | pytest API tests |
| `logs/server.log` | Sample payment gateway log |
| `.github/workflows/tests.yml` | CI pipeline |

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the pytest suite (no server needed, uses Flask's test client):

```bash
pytest -v
```

Run the API and the smoke tests (two terminals):

```bash
python3 api/app.py
./scripts/smoke_test.sh
```

Other scripts:

```bash
./scripts/run_checks.sh      # validate the XML files in data/
./scripts/analyze_logs.sh    # summarize logs/server.log
```

## Test design

| Test | Technique |
|---|---|
| Valid payment is accepted | Positive |
| Invalid payment is rejected with all 5 reasons | Negative |
| Body that is not XML (text, empty, broken) | Negative, invalid format |
| One broken field at a time (amount 0, currency XYZ, 7-character BIC, missing town) | Negative, one variable at a time |
| Amount 0.01, currency EUR, 11-character BIC are accepted | Boundary values |
| Wrong Content-Type should return 415 | Known gap, marked `xfail` |

## Findings

- The API does not check the `Content-Type` header (a request sent as `text/plain` is still processed). A production API should return 415 Unsupported Media Type. Documented as an `xfail` test.
- API responses originally had no final newline; fixed (Content-Length went from 90 to 91).

## Tools

Python 3.14, Flask, pytest, Bash, curl, grep, Git, GitHub Codespaces, GitHub Actions.
