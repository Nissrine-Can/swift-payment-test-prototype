"""Mock payment API: receives a pacs.008 XML payment and answers ACK or NACK in XML."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from flask import Flask, Response, request

# Reuse the validation rules from scripts/check_payment.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from check_payment import CHECKS, text  # noqa: E402

app = Flask(__name__)


def xml_response(msg_id, status, reasons, code):
    root = ET.Element("PaymentStatus")
    ET.SubElement(root, "MsgId").text = msg_id or ""
    ET.SubElement(root, "Status").text = status
    reasons_element = ET.SubElement(root, "Reasons")
    for reason in reasons:
        ET.SubElement(reasons_element, "Reason").text = reason
    body = ET.tostring(root, encoding="unicode")+ "\n"
    return Response(body, status=code, mimetype="application/xml")


@app.get("/health")
def health():
    return Response("<Health><Status>UP</Status></Health>\n", mimetype="application/xml")


@app.post("/payments")
def receive_payment():
    try:
        tree = ET.fromstring(request.get_data())
    except ET.ParseError as error:
        return xml_response(None, "NACK", [f"invalid XML: {error}"], 400)

    msg_id = text(tree, ".//p:GrpHdr/p:MsgId")
    reasons = []
    for name, check in CHECKS:
        passed, detail = check(tree)
        if not passed:
            reasons.append(f"{name}: {detail}")

    if reasons:
        return xml_response(msg_id, "NACK", reasons, 400)
    return xml_response(msg_id, "ACK", [], 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)