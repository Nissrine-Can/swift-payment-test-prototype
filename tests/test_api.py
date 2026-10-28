"""API tests for the mock payment gateway (api/app.py)."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "api"))
from app import app  # noqa: E402

DATA = ROOT / "data"


@pytest.fixture
def client():
    return app.test_client()


def post_payment(client, body):
    response = client.post("/payments", data=body, content_type="application/xml")
    return response, ET.fromstring(response.data)


def test_health_is_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert ET.fromstring(response.data).findtext("Status") == "UP"


def test_valid_payment_is_acked(client):
    response, result = post_payment(client, (DATA / "payment.xml").read_bytes())
    assert response.status_code == 200
    assert result.findtext("Status") == "ACK"
    assert result.findtext("MsgId") == "MSG-2026-0001"
    assert len(result.find("Reasons")) == 0


def test_invalid_payment_is_nacked_with_all_reasons(client):
    response, result = post_payment(client, (DATA / "payment_bad.xml").read_bytes())
    assert response.status_code == 400
    assert result.findtext("Status") == "NACK"
    assert len(result.findall("Reasons/Reason")) == 5


@pytest.mark.parametrize("body", [b"hello", b"", b"<Document>"], ids=["text", "empty", "broken-xml"])
def test_body_that_is_not_xml_is_rejected(client, body):
    response, result = post_payment(client, body)
    assert response.status_code == 400
    assert result.findtext("Status") == "NACK"
    assert result.findtext("Reasons/Reason").startswith("invalid XML")


@pytest.mark.parametrize(
    "old, new, check",
    [
        ('Ccy="USD">5000.00<', 'Ccy="USD">0<', "Amount"),
        ('Ccy="USD"', 'Ccy="XYZ"', "Currency"),
        ("<BICFI>AAAAUS33</BICFI>", "<BICFI>AAAAUS3</BICFI>", "BICs"),
        ("<TwnNm>Manassas</TwnNm>", "", "Structured address"),
    ],
    ids=["amount-zero", "currency-xyz", "bic-7-chars", "no-town"],
)
def test_one_broken_field_gives_one_reason(client, old, new, check):
    body = (DATA / "payment.xml").read_text().replace(old, new)
    response, result = post_payment(client, body)
    assert response.status_code == 400
    reasons = [reason.text for reason in result.findall("Reasons/Reason")]
    assert len(reasons) == 1
    assert reasons[0].startswith(check)


@pytest.mark.parametrize(
    "old, new",
    [
        ('Ccy="USD">5000.00<', 'Ccy="USD">0.01<'),
        ('Ccy="USD"', 'Ccy="EUR"'),
        ("<BICFI>AAAAUS33</BICFI>", "<BICFI>AAAAUS33XXX</BICFI>"),
    ],
    ids=["amount-0.01", "currency-eur", "bic-11-chars"],
)
def test_valid_variations_are_acked(client, old, new):
    body = (DATA / "payment.xml").read_text().replace(old, new)
    response, result = post_payment(client, body)
    assert response.status_code == 200
    assert result.findtext("Status") == "ACK"

@pytest.mark.xfail(reason="Known gap: API does not check Content-Type; should return 415")
def test_wrong_content_type_is_rejected(client):
    response = client.post(
        "/payments",
        data=(DATA / "payment.xml").read_bytes(),
        content_type="text/plain",
    )
    assert response.status_code == 415

