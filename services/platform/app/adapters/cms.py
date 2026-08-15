import httpx
from xml.etree import ElementTree

from ..config import get_settings
from ..models import Order

SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
CMS_NS = "swiftlogistics.cms"


def _soap_request(operation: str, values: dict[str, str]) -> str:
    envelope = ElementTree.Element(f"{{{SOAP_ENV}}}Envelope")
    body = ElementTree.SubElement(envelope, f"{{{SOAP_ENV}}}Body")
    operation_element = ElementTree.SubElement(body, f"{{{CMS_NS}}}{operation}")
    for name, value in values.items():
        child = ElementTree.SubElement(operation_element, f"{{{CMS_NS}}}{name}")
        child.text = value
    return ElementTree.tostring(envelope, encoding="unicode", xml_declaration=True)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _result(xml: bytes) -> str:
    root = ElementTree.fromstring(xml)
    for element in root.iter():
        if _local_name(element.tag).endswith("Result"):
            return element.text or ""
    raise RuntimeError("CMS SOAP response did not contain a result")


def create_order(order: Order) -> str:
    body = _soap_request(
        "create_order",
        {
            "order_id": order.id,
            "client_id": order.client_id,
            "recipient_name": order.recipient_name,
            "delivery_address": order.delivery_address,
            "priority": order.priority,
        },
    )
    response = httpx.post(
        get_settings().cms_url,
        content=body.encode(),
        headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": "create_order"},
        timeout=3.0,
    )
    response.raise_for_status()
    return _result(response.content)

