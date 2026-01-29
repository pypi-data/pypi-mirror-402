from enum import Enum


class VATPointDateCode(str, Enum):
    INVOICE_DATE_TIME = "3"
    DELIVERY_DATE_TIME_ACTUAL = "35"
    PAID_TO_DATE = "432"
