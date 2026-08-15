from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from xml.etree import ElementTree


orders: dict[str, dict[str, str]] = {}

SOAP_ENV = "http://schemas.xmlsoap.org/soap/envelope/"
CMS_NS = "swiftlogistics.cms"

WSDL = f'''<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/"
 xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
 xmlns:tns="{CMS_NS}" targetNamespace="{CMS_NS}" name="ClientManagementService">
  <types>
    <xsd:schema targetNamespace="{CMS_NS}">
      <xsd:element name="create_order">
        <xsd:complexType><xsd:sequence>
          <xsd:element name="order_id" type="xsd:string"/>
          <xsd:element name="client_id" type="xsd:string"/>
          <xsd:element name="recipient_name" type="xsd:string"/>
          <xsd:element name="delivery_address" type="xsd:string"/>
          <xsd:element name="priority" type="xsd:string"/>
        </xsd:sequence></xsd:complexType>
      </xsd:element>
      <xsd:element name="create_orderResponse"><xsd:complexType><xsd:sequence>
        <xsd:element name="create_orderResult" type="xsd:string"/>
      </xsd:sequence></xsd:complexType></xsd:element>
      <xsd:element name="get_order_status"><xsd:complexType><xsd:sequence>
        <xsd:element name="order_id" type="xsd:string"/>
      </xsd:sequence></xsd:complexType></xsd:element>
      <xsd:element name="get_order_statusResponse"><xsd:complexType><xsd:sequence>
        <xsd:element name="get_order_statusResult" type="xsd:string"/>
      </xsd:sequence></xsd:complexType></xsd:element>
    </xsd:schema>
  </types>
  <message name="create_orderRequest"><part name="parameters" element="tns:create_order"/></message>
  <message name="create_orderResponse"><part name="parameters" element="tns:create_orderResponse"/></message>
  <message name="get_order_statusRequest"><part name="parameters" element="tns:get_order_status"/></message>
  <message name="get_order_statusResponse"><part name="parameters" element="tns:get_order_statusResponse"/></message>
  <portType name="ClientManagementPortType">
    <operation name="create_order"><input message="tns:create_orderRequest"/><output message="tns:create_orderResponse"/></operation>
    <operation name="get_order_status"><input message="tns:get_order_statusRequest"/><output message="tns:get_order_statusResponse"/></operation>
  </portType>
  <binding name="ClientManagementBinding" type="tns:ClientManagementPortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="create_order"><soap:operation soapAction="create_order"/><input><soap:body use="literal"/></input><output><soap:body use="literal"/></output></operation>
    <operation name="get_order_status"><soap:operation soapAction="get_order_status"/><input><soap:body use="literal"/></input><output><soap:body use="literal"/></output></operation>
  </binding>
  <service name="ClientManagementService"><port name="ClientManagementPort" binding="tns:ClientManagementBinding"><soap:address location="http://cms-mock:8001/"/></port></service>
</definitions>'''


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def soap_response(operation: str, result: str) -> bytes:
    envelope = ElementTree.Element(f"{{{SOAP_ENV}}}Envelope")
    body = ElementTree.SubElement(envelope, f"{{{SOAP_ENV}}}Body")
    response = ElementTree.SubElement(body, f"{{{CMS_NS}}}{operation}Response")
    result_element = ElementTree.SubElement(response, f"{{{CMS_NS}}}{operation}Result")
    result_element.text = result
    return ElementTree.tostring(envelope, encoding="utf-8", xml_declaration=True)


class CmsHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        print(f"CMS {self.address_string()} - {format % args}", flush=True)

    def send_xml(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if urlparse(self.path).query.lower() == "wsdl":
            self.send_xml(200, WSDL.encode())
        else:
            self.send_xml(200, b"<service>Client Management SOAP service</service>")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        root = ElementTree.fromstring(self.rfile.read(length))
        operation_element = next(
            (child for child in root.iter() if local_name(child.tag) not in {"Envelope", "Body"}),
            None,
        )
        if operation_element is None:
            self.send_xml(400, soap_response("fault", "Missing SOAP operation"))
            return

        operation = local_name(operation_element.tag)
        values = {local_name(child.tag): child.text or "" for child in operation_element}
        if operation == "create_order":
            order_id = values["order_id"]
            if order_id in orders:
                result = f"ALREADY_EXISTS:{order_id}"
            else:
                orders[order_id] = values | {"status": "REGISTERED"}
                result = f"CREATED:{order_id}"
        elif operation == "get_order_status":
            order_id = values.get("order_id", "")
            result = orders.get(order_id, {}).get("status", "NOT_FOUND")
        else:
            self.send_xml(500, soap_response("fault", f"Unknown operation: {operation}"))
            return

        self.send_xml(200, soap_response(operation, result))


if __name__ == "__main__":
    print("Mock CMS SOAP/XML server listening on 8001", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8001), CmsHandler).serve_forever()


class CmsService(ServiceBase):
    """Small SOAP/XML stand-in for the legacy Client Management System."""

    @rpc(Unicode, Unicode, Unicode, Unicode, Unicode, _returns=Unicode)
    def create_order(
        ctx,
        order_id: str,
        client_id: str,
        recipient_name: str,
        delivery_address: str,
        priority: str,
    ) -> str:
        if order_id in orders:
            return f"ALREADY_EXISTS:{order_id}"

        orders[order_id] = {
            "client_id": client_id,
            "recipient_name": recipient_name,
            "delivery_address": delivery_address,
            "priority": priority,
            "status": "REGISTERED",
        }
        return f"CREATED:{order_id}"

    @rpc(Unicode, _returns=Unicode)
    def get_order_status(ctx, order_id: str) -> str:
        order = orders.get(order_id)
        return order["status"] if order else "NOT_FOUND"


soap_application = Application(
    [CmsService],
    tns="swiftlogistics.cms",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

application = WsgiApplication(soap_application)
