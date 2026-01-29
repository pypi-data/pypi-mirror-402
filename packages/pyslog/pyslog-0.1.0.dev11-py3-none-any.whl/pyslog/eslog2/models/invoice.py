from pydantic import BaseModel, Field
from .enums import (
    VATPointDateCode,
    BusinessProcessType,
    ItemIdentificationScheme,
    VATCategoryCode,
    PaymentMeansCode,
    AllowanceType,
)


class CEF_VAT_EXEMPTION(BaseModel):
    VAT_EXEMPTION_REASON_CODE: str = Field(description="VAT Exemption Reason (BT-121). Use vode list CEF VATEX — VAT exemption reason code")  # TODO Add validation
    VAT_EXEMPTION_REASON_TEXT: str = Field(description="VAT Exemption Reason (BT-120)")


class VATBreakdown(BaseModel):
    taxable_amount: str = Field(description="VAT category taxable amount (BT-116). The sum of all Invoice line net amounts that are subject to a specific VAT category code and VAT category rate, minus all allowances on document level, plus all charges on document level.")
    tax_amount: str = Field(description="VAT category tax amount (BT-117). The total VAT amount for a given VAT category.")
    vat_category_code: VATCategoryCode = Field(description="VAT category code (BT-118). The code that applies to the VAT category.")
    vat_category_rate: str = Field(default=None, description="VAT category rate (BT-119). The VAT rate, represented as a percentage that applies for the relevant VAT category.")


class Allowance(BaseModel):
    allowance_type: AllowanceType = Field(description="Allowance reason code (BT-140). Use code list UNTDID 51890")
    percentage: str = Field(description="Allowance percentage (BT-138)")
    amount: str = Field(description="Allowance amount (BT-136)")
    base_amount: str = Field(description="Allowance base amount (BT-137)")

class BusinessEntity(BaseModel):
    identifier: str | None = Field(default=None, description="Buyer identifier (BT-46)")
    identifier_identification_scheme_identifier: str | None = Field(default="0088", description="Buyer identifier identification scheme identifier (BT-46-1). The identification scheme identifier of the Buyer identifier. Use code list ISO/IEC 6523 — Identifier scheme code") # Todo validation?
    name: str = Field(description="Buyer name (BT-44). The full name of the buyer.")
    trading_name: str | None = Field(default=None, description="Buyer trading name (BT-45). A name by which the Buyer is known, other than Buyer name (also known as Business name).")
    address_line_1: str = Field(description="Buyer address line 1(BT-50). The main address line in an address.")
    address_line_2: str | None = Field(default=None, description="Buyer address line 2 (BT-51). An additional address line in an address that can be used to give further details supplementing the main line.")
    address_line_3: str | None = Field(default=None, description="Buyer address line 3 (BT-163). An additional address line in an address that can be used to give further details supplementing the main line.")
    city: str | None = Field(default=None, description="Buyer city (BT-52). The common name of the city, town or village, where the Buyer's address is located.")
    country_subdivision: str | None = Field(default=None, description="Buyer country subdivision (BT-54). The subdivision of a country.")
    post_code: str | None = Field(default=None, description="Buyer post code (BT-53). The identifier for an addressable group of properties according to the relevant postal service.")
    country_code: str = Field(description="Buyer country code (BT-55). A code that identifies the country. Use code list ISO 3166-1 — Country Codes")  # TODO: Validation
    iban: str | None = Field(default=None, description="Buyer IBAN (BT-84)")
    account_holder_name: str | None = Field(default=None, description="Buyer account holder name (BT-85)")
    bic: str | None = Field(default=None, description="Buyer BIC (BT-86)")
    vat_registration_number: str | None = Field(default=None, description="Buyer VAT registration number (BT-31)")
    maticna: str | None = Field(default=None, description="Buyer maticna (BT-30)")
    contact_person_name: str | None = Field(default=None, description="Buyer contact person name (BT-32)")


class Item(BaseModel):
    standard_identifier: str = Field(description="Item standard identifier(BT-157) An item identifier based on a registered scheme.")
    standard_identifier_identification_scheme_identifier: ItemIdentificationScheme = Field(description="Item standard identifier identification scheme identifier (BT-157-1). The identification scheme identifier of the Item standard identifier. Use code list ISO/IEC 6523 — Identifier scheme code")
    sellers_item_identifier: str = Field(description="Item sellers item identifier (BT-155). The identifier assigned by the Seller for the item.")
    name: str = Field(description="Item name (BT-153). The name of the item.")
    quantity: str  = Field(description="Invoiced quantity (BT-129). The quantity of items (goods or services) that is charged in the Invoice line.")
    quantity_unit_of_measure: str = Field(description="Invoiced quantity unit of measure (BT-130). The unit of measure that applies to the invoiced quantity. Use code list UN/ECE Recommendation N°20 and UN/ECE Recommendation N°21 — Unit codes")  ## TODO Validation, mapping
    total_monetary_amount: str = Field(description="Invoice line net amount (BT-131). The total amount of the Invoice line.")
    total_monetary_amount_including_vat: str | None = Field(default=None, description="Invoice line net amount including VAT (NBT-031). The total amount of the Invoice line including VAT.")
    item_net_price: str = Field(description="Item net price (BT-146). The price of an item, exclusive of VAT, after subtracting item price discount.")
    item_price_base_quantity: str | None = Field(default=None, description="Item price base quantity (BT-149). The number of item unity to which the price applies.")
    item_price_base_quantity_unit_of_measure_code: str | None = Field(default=None, description="Item price base quantity unit of measure code (BT-150). The unit of measure that applies to the item price base quantity. Use code list UN/ECE Recommendation N°20 and UN/ECE Recommendation N°21 — Unit codes")  ## TODO VALIDATING; MAPPING
    item_gross_price: str | None = Field(default=None, description="Item gross price (BT-148). The unit price, exclusive of VAT; before subtracting item price discount.")
    vat_rate: str = Field(description="Invoiced item VAT rate (BT-152). The VAR rate, represented as percentage that applies to the invoiced item.")
    vat_category_code: VATCategoryCode = Field(description="Invoiced item VAT category code (BT-151). The VAT category code for the invoiced item")
    allowance: Allowance | None = Field(default=None, description="Invoiced item allowance (BG-27)")


    

class Invoice(BaseModel):
    invoice_number: str
    invoice_issue_date: str
    value_added_tax_point_date: str | None = Field(default=None, description="Value added tax point date (BT-7). The date when the VAT becomes accountable for the Seller and for the Buyer in so far as that date can be determined and differs from the date of issue of the invoice, according to the VAT directive.")
    payment_due_date: str | None = Field(default=None, description="Payment due date (BT-9). The date on which the payment is due.")
    payment_means_code: PaymentMeansCode = Field(default=PaymentMeansCode.SEPA_CREDIT_TRANSFER, description="Payment means type code (BT-81). The means, expressed as code, for how a payment is expected to be or has been settled.")
    value_added_tax_point_date_code: VATPointDateCode | None = Field(default=None, description="Value added tax point date code (BT-8), DESC:The code of the date when the VAT becomes accountable for the Seller and for the Buyer.")
    actual_delivery_date: str | None = Field(default=None, description="Actual delivery date (BT-72). The date on which the delivery is made.")
    invoicing_period_start_date: str | None = Field(default=None, description="Invoicing period start date (BT-73). The date on which the invoicing period starts.")
    invoicing_period_end_date: str | None = Field(default=None, description="Invoicing period end date (BT-74). The date on which the invoicing period ends.")
    terms_of_payments: list[str] | None = Field(
        default=None,
        description="Payment terms (BT-20). A textual description of the payment terms that apply to the amount due for payment (Including description of possible penalties). Five lines of text possible.",
        max_length=5
    )
    seller_additional_legal_information: str | None = Field(
        default=None,
        description="Seller additional legal information (BT-33). Additional legal information relevant for the Seller."
    )
    invoice_note: str | None = Field(
        default=None,
        description="Invoice note (BT-22). A textual note that gives unstructured information that is relevant to the Invoice as a whole. A group of business terms providing textual notes that are relevant for the invoice, together with an indication of the note subject."
    )
    business_process_type: BusinessProcessType | None = Field(
        default=None,
        description="Business process type (BT-23). Identifies the business process context in which the transaction appears, to enable the Buyer to process the Invoice in an appropriate way."
    )
    payment_means_text: str | None = Field(
        default=None,
        description="Payment means text (BT-82). The means, expressed as text, for prepaid how a payment is expected to be or has been settled. Code AAT may be used for other than IATA."
    )
    vat_exemption_reason: CEF_VAT_EXEMPTION | None = Field(
        default=None,
    )
    buyer: BusinessEntity = Field(description="Buyer (BT-44, BT-45, BT-46, BT-46-1)")
    seller: BusinessEntity = Field(description="Seller")
    reference_currency_code: str = Field(default="EUR", description="Reference currency code (BT-5). The currency in which all Invoice amounts are given, except for the Total VAT amount in accounting currency. Use code list ISO 4217 — Currency codes")  # TODO validation
    items: list[Item] = Field(description="Items to include in the invoice. Will be automatically numbered starting from 1.")
    vat_breakdown: list[VATBreakdown] = Field(default_factory=list, description="VAT breakdown (BG-23). A group of business terms providing information about VAT breakdown by different categories, rates and exemption reasons.")
    
    # Monetary stuff
    sum_of_invoice_line_net_amount: str = Field(description="Sum of Invoice line net amount (BT-106). The sum of all Invoice line net amounts in the Invoice.")
    invoice_total_amount_without_vat: str = Field(description="Invoice total amount without VAT (BT-109). The total amount of the Invoice without VAT.")
    invoice_total_amount_with_vat: str = Field(description="Invoice total amount with VAT (BT-112). The total amount of the Invoice with VAT.")
    amount_due_for_payment: str = Field(description="Amount due for payment (BT-115). The outstanding amount that is requested to be paid.")
    sum_of_allowances_on_document_level: str | None = Field(default=None, description="Sum of allowances on document level (BT-107). The sum of all allowances on document level in the Invoice.")
    sum_of_charges_on_document_level: str | None = Field(default=None, description="Sum of charges on document level (BT-108). The sum of all charges on document level in the Invoice.")
    invoice_total_vat_amount_in_accounting_currency: str | None = Field(default=None, description="Invoice total VAT amount in accounting currency (BT-111). The VAT total amount expressed in the accounting currency accepted or required in the country of the Seller.")
    paid_amount: str | None = Field(default=None, description="Paid amount (BT-113). The sum of amounts which have been paid in advance.")
    rounding_amount: str | None = Field(default=None, description="Rounding amount (BT-114). The amount to be added to the invoice total to round the amount to be paid.")
    invoice_total_vat_amount: str | None = Field(default=None, description="Invoice total VAT amount (BT-110). The total VAT amount for the Invoice.")
