# pyslog - A modern Python library for generating eSLOG invoices

[![PyPI version](https://badge.fury.io/py/pyslog.svg)](https://badge.fury.io/py/pyslog)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!CAUTION]
> This library is in its early stages. 
> The current implementation focuses on **eSLOG 2.0 Invoices**. Other document types and certain niche fields are not yet supported.
> Please double-check generated XML files against official validators before production use.

## Overview

`pyslog` is designed to provide a clean, Pythonic interface for generating standard-compliant eSLOG 2.0 documents. By separating the complex, segment-based XML logic from simple Pydantic models, we allow developers to focus on their data rather than the intricacies of the eSLOG specification.

## Usage

### Installation

```bash
# Using uv
uv add pyslog

# Using pip
pip install pyslog
```

### Basic Example

```python
from pyslog.eslog2.models import Invoice, BusinessEntity, Item, BusinessProcessType, VATCategoryCode
from pyslog.eslog2.generator import generate_eslog_invoice

# 1. Define the Buyer and Seller
buyer = BusinessEntity(
    name="Buyer Corp",
    address_line_1="Industrial Road 1",
    city="Ljubljana",
    post_code="1000",
    country_code="SI",
    vat_registration_number="SI12345678"
)

seller = BusinessEntity(
    name="Seller Ltd",
    address_line_1="Tech Park 5",
    city="Ljubljana",
    post_code="1000",
    country_code="SI",
    iban="SI5600000000000",
    bic="BANKSI2X",
    vat_registration_number="SI87654321",
    maticna="1234567000"
)

# 2. Define Items
item = Item(
    standard_identifier="1234567890123",
    standard_identifier_identification_scheme_identifier="0088", # EAN
    sellers_item_identifier="SKU-001",
    name="Consulting Services",
    quantity="10",
    quantity_unit_of_measure="HUR", # Hours
    total_monetary_amount="1000.00",
    item_net_price="100.00",
    vat_rate="22",
    vat_category_code=VATCategoryCode.STANDARD_RATE
)

# 3. Create the Invoice
invoice = Invoice(
    invoice_number="INV-2026-001",
    invoice_issue_date="2026-01-13",
    #business_process_type=BusinessProcessType.INVOICING_BASED_ON_CONTRACT,
    buyer=buyer,
    seller=seller,
    items=[item],
    sum_of_invoice_line_net_amount="1000.00",
    invoice_total_amount_without_vat="1000.00",
    invoice_total_amount_with_vat="1220.00",
    amount_due_for_payment="1220.00"
)

# 4. Generate XML string
xml_output = generate_eslog_invoice(invoice)

with open("invoice.xml", "w") as f:
    f.write(xml_output)
```

## Roadmap

- [x] Base eSLOG 2.0 Invoice Model
- [x] Pydantic integration for type safety
- [ ] Field-level validation (ISO codes, IBAN, etc.)
- [ ] eSLOG 2.0 Order & Order Confirmation
- [ ] eSLOG 2.0 Delivery Note (Dobavnica)
- [ ] Comprehensive documentation site
- [ ] Comprehensive tests

## Acknowledgements

Inspired by the early work of [python-eracun](https://github.com/boris-savic/python-eracun).

## License

MIT License - see [LICENSE](LICENSE) file for details.
