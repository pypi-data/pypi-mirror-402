from enum import Enum


class VATCategoryCode(str, Enum):
    """
    VAT Category Code

    S = Standard rate
    Z = Zero rated goods
    E = Exempt from tax
    AE = VAT Reverse Charge
    K = VAT exempt for EEA intra-community supply of goods and services
    G = Free export item, tax not charged
    O = Services outside scope of tax
    L = Canary Islands general indirect tax
    M = Tax for production, services and importation in Ceuta and Melilla
    """

    STANDARD_RATE = "S"
    ZERO_RATED_GOODS = "Z"
    EXEMPT_FROM_TAX = "E"
    VAT_REVERSE_CHARGE = "AE"
    VAT_EXEMPT_FOR_EEA_INTRA_COMMUNITY_SUPPLY_OF_GOODS_AND_SERVICES = "K"
    FREE_EXPORT_ITEM = "G"
    SERVICES_OUTSIDE_SCOPE_OF_TAX = "O"
    CANARY_ISLANDS_GENERAL_INDIRECT_TAX = "L"
    TAX_FOR_PRODUCTION_SERVICES_AND_IMPORTATION_IN_CEUTA_AND_MELILLA = "M"
