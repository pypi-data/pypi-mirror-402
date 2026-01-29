import importlib.resources
from lxml import etree

def validate_invoice_xml(xml_string: str) -> bool:
    schema_path = importlib.resources.files("pyslog.eslog2.schemas").joinpath("eSLOG20_INVOIC_v200.xsd")
    
    with schema_path.open("rb") as f:
        schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)
    
    parser = etree.XMLParser(schema=schema)
    try:
        etree.fromstring(xml_string.encode("utf-8"), parser)
        return True
    except etree.XMLSyntaxError:
        return False
