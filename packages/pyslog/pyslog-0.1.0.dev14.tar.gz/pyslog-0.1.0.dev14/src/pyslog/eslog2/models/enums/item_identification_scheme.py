from enum import Enum


class ItemIdentificationScheme(str, Enum):
    GTIN = "0160"
    EAN = "0088"
