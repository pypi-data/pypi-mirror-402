from enum import Enum

class PaymentMeansCode(str, Enum):
    CREDIT_TRANSFER = "30"
    SEPA_CREDIT_TRANSFER = "58"
