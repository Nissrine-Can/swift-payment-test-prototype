"""Validate a sample ISO 20022 pacs.008 payment message.

Usage:
    python check_payment.py payment.xml

Exit code 0 if every check passes, 1 if any check fails.
"""
import re
import sys
import xml.etree.ElementTree as ET

NS = {"p": "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"}
ALLOWED_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CHF"}
BIC_PATTERN = re.compile(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$")
UETR_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def text(tree, path):
    element = tree.find(path, NS)
    return element.text.strip() if element is not None and element.text else None


def check_amount(tree):
    amount = tree.find(".//p:IntrBkSttlmAmt", NS)
    if amount is None:
        return False, "amount is missing"
    try:
        value = float(amount.text)
    except (TypeError, ValueError):
        return False, f"amount is not a number: {amount.text!r}"
    if value <= 0:
        return False, f"amount must be positive, got {value}"
    return True, f"amount {value:.2f}"


def check_currency(tree):
    amount = tree.find(".//p:IntrBkSttlmAmt", NS)
    currency = amount.get("Ccy") if amount is not None else None
    if currency not in ALLOWED_CURRENCIES:
        return False, f"unexpected currency {currency!r}"
    return True, f"currency {currency}"


def check_uetr(tree):
    uetr = text(tree, ".//p:PmtId/p:UETR")
    if not uetr or not UETR_PATTERN.match(uetr):
        return False, f"UETR missing or not a valid UUID v4: {uetr!r}"
    return True, f"UETR {uetr}"


def check_bics(tree):
    problems = []
    for role in ("DbtrAgt", "CdtrAgt"):
        bic = text(tree, f".//p:{role}/p:FinInstnId/p:BICFI")
        if not bic or not BIC_PATTERN.match(bic):
            problems.append(f"{role} BIC invalid: {bic!r}")
    if problems:
        return False, "; ".join(problems)
    return True, "debtor and creditor agent BICs valid"


def check_structured_addresses(tree):
    problems = []
    for party in ("Dbtr", "Cdtr"):
        town = text(tree, f".//p:{party}/p:PstlAdr/p:TwnNm")
        country = text(tree, f".//p:{party}/p:PstlAdr/p:Ctry")
        if not town or not country:
            problems.append(f"{party} address not structured (needs TwnNm and Ctry)")
    if problems:
        return False, "; ".join(problems)
    return True, "debtor and creditor addresses structured"


CHECKS = [
    ("Amount", check_amount),
    ("Currency", check_currency),
    ("UETR", check_uetr),
    ("BICs", check_bics),
    ("Structured address", check_structured_addresses),
]


def main(path):
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as error:
        print(f"FAIL  could not read {path}: {error}")
        return 1

    failures = 0
    print(f"Checking {path}")
    for name, check in CHECKS:
        passed, detail = check(tree)
        print(f"  {'PASS' if passed else 'FAIL'}  {name}: {detail}")
        failures += not passed

    print(f"Result: {len(CHECKS) - failures}/{len(CHECKS)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_payment.py <payment.xml>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
