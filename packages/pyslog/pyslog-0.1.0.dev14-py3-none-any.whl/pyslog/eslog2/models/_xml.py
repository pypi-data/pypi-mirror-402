from pydantic_xml import BaseXmlModel, element, attr
import enum

class ESLOG_C_S009(BaseXmlModel, tag="C_S009"):
    D_0065: str = element(name="D_0065")
    D_0052: str = element(name="D_0052")
    D_0054: str = element(name="D_0054")
    D_0051: str = element(name="D_0051")

class ESLOG_S_UNH(BaseXmlModel, tag="S_UNH"):
    D_0062: str = element(name="D_0062")
    C_S009: ESLOG_C_S009 = element(tag="C_S009")

class ESLOG_C_C002(BaseXmlModel, tag="C_C002"):
    D_1001: str = element(name="D_1001")

class ESLOG_C_C106(BaseXmlModel, tag="C_C106"):
    D_1004: str = element(name="D_1004")

class ESLOG_S_BGM(BaseXmlModel, tag="S_BGM"):
    C_C002: ESLOG_C_C002 = element(tag="C_C002")
    C_C106: ESLOG_C_C106 = element(tag="C_C106")

class ESLOG_C_C507(BaseXmlModel, tag="C_C507", skip_empty=True):
    D_2005: str = element(name="D_2005")
    D_2380: str | None = element(name="D_2380", default=None)

class ESLOG_S_DTM(BaseXmlModel, tag="S_DTM"):
    C_C507: ESLOG_C_C507 = element(tag="C_C507")

class ESLOG_C_C107(BaseXmlModel, tag="C_C107"):
    D_4441: str = element(name="D_4441")

class ESLOG_C_C108(BaseXmlModel, tag="C_C108", skip_empty=True):
    D_4440: str = element(name="D_4440")
    D_4440_2: str | None = element(name="D_4440_2", default=None)
    D_4440_3: str | None = element(name="D_4440_3", default=None)
    D_4440_4: str | None = element(name="D_4440_4", default=None)
    D_4440_5: str | None = element(name="D_4440_5", default=None)

class ESLOG_S_FTX(BaseXmlModel, tag="S_FTX", skip_empty=True):
    D_4451: str = element(name="D_4451")  # Text subject code qualifier
    C_C107: ESLOG_C_C107 | None = element(tag="C_C107", default=None)
    C_C108: ESLOG_C_C108 = element(tag="C_C108")

class ESLOG_C_C506(BaseXmlModel, tag="C_C506"):
    D_1153: str = element(name="D_1153")
    D_1154: str = element(name="D_1154")

class ESLOG_S_RFF(BaseXmlModel, tag="S_RFF"):
    C_C506: ESLOG_C_C506 = element(tag="C_C506")

class ESLOG_G_SG1(BaseXmlModel, tag="G_SG1"):
    S_RFF: ESLOG_S_RFF = element(tag="S_RFF")

class ESLOG_C_C082(BaseXmlModel, tag="C_C082", skip_empty=True):
    D_3039: str = element(name="D_3039")
    D_1131: str | None = element(name="D_1131", default=None)

class ESLOG_C_C080(BaseXmlModel, tag="C_C080", skip_empty=True):
    D_3036: str = element(name="D_3036")
    D_3036_2: str | None = element(name="D_3036_2", default=None)

class ESLOG_C_C059(BaseXmlModel, tag="C_C059", skip_empty=True):
    D_3042: str = element(name="D_3042")
    D_3042_2: str | None = element(name="D_3042_2", default=None)
    D_3042_3: str | None = element(name="D_3042_3", default=None)

class ESLOG_C_C819(BaseXmlModel, tag="C_C819"):
    D_3228: str = element(name="D_3228")

class ESLOG_S_NAD(BaseXmlModel, tag="S_NAD", skip_empty=True):
    D_3035: str = element(name="D_3035")
    C_C082: ESLOG_C_C082 | None = element(tag="C_C082", default=None)
    C_C080: ESLOG_C_C080 = element(tag="C_C080")
    C_C059: ESLOG_C_C059 | None = element(tag="C_C059", default=None)
    D_3164: str | None = element(name="D_3164", default=None)
    C_C819: ESLOG_C_C819 | None = element(tag="C_C819", default=None)
    D_3251: str | None = element(name="D_3251", default=None)
    D_3207: str = element(name="D_3207")

class ESLOG_C_C078(BaseXmlModel, tag="C_C078"):
    D_3194: str = element(name="D_3194")

class ESLOG_C_C088(BaseXmlModel, tag="C_C088"):
    D_3433: str = element(name="D_3433")

class ESLOG_S_FII(BaseXmlModel, tag="S_FII"):
    D_3035: str = element(name="D_3035")
    C_C078: ESLOG_C_C078 = element(tag="C_C078")
    C_C088: ESLOG_C_C088 = element(tag="C_C088")

class ESLOG_G_SG3(BaseXmlModel, tag="G_SG3"):
    S_RFF: ESLOG_S_RFF = element(tag="S_RFF")

class ESLOG_C_C056(BaseXmlModel, tag="C_C056"):
    D_3412: str = element(name="D_3412")

class ESLOG_S_CTA(BaseXmlModel, tag="S_CTA"):
    D_3139: str = element(name="D_3139")
    C_C056: ESLOG_C_C056 = element(tag="C_C056")

class ESLOG_G_SG5(BaseXmlModel, tag="G_SG5"):
    S_CTA: ESLOG_S_CTA = element(tag="S_CTA")

class ESLOG_G_SG2(BaseXmlModel, tag="G_SG2", skip_empty=True):
    S_NAD: ESLOG_S_NAD = element(tag="S_NAD")
    S_FII: ESLOG_S_FII | None = element(tag="S_FII", default=None)
    G_SG3: list[ESLOG_G_SG3] | None = element(tag="G_SG3", default=None)
    G_SG5: list[ESLOG_G_SG5] | None = element(tag="G_SG5", default=None)

class ESLOG_C_C504(BaseXmlModel, tag="C_C504"):
    D_6347: str = element(name="D_6347")
    D_6345: str = element(name="D_6345")

class ESLOG_S_CUX(BaseXmlModel, tag="S_CUX"):
    C_C504: ESLOG_C_C504 = element(tag="C_C504")

class ESLOG_G_SG7(BaseXmlModel, tag="G_SG7"):
    S_CUX: ESLOG_S_CUX = element(tag="S_CUX")

class ESLOG_S_PAT(BaseXmlModel, tag="S_PAT"):
    D_4279: str = element(name="D_4279")

class ESLOG_C_C534(BaseXmlModel, tag="C_C534"):
    D_4461: str = element(name="D_4461")

class ESLOG_S_PAI(BaseXmlModel, tag="S_PAI"):
    C_C534: ESLOG_C_C534 = element(tag="C_C534")

class ESLOG_G_SG8(BaseXmlModel, tag="G_SG8"):
    S_PAT: ESLOG_S_PAT = element(tag="S_PAT")
    S_DTM: list[ESLOG_S_DTM] = element(tag="S_DTM")
    S_PAI: ESLOG_S_PAI | None = element(tag="S_PAI", default=None)

class ESLOG_C_C212(BaseXmlModel, tag="C_C212"):
    D_7140: str = element(name="D_7140")
    D_7143: str = element(name="D_7143")

class ESLOG_S_LIN(BaseXmlModel, tag="S_LIN"):
    D_1082: str = element(name="D_1082")
    C_C212: ESLOG_C_C212 = element(tag="C_C212")

class ESLOG_S_PIA(BaseXmlModel, tag="S_PIA"):
    D_4347: str = element(name="D_4347")
    C_C212: ESLOG_C_C212 = element(tag="C_C212")

class ESLOG_C_C273(BaseXmlModel, tag="C_C273"):
    D_7008: str = element(name="D_7008")
    
class ESLOG_S_IMD(BaseXmlModel, tag="S_IMD"):
    D_7077: str = element(name="D_7077")
    C_C273: ESLOG_C_C273 = element(tag="C_C273")

class ESLOG_C_C186(BaseXmlModel, tag="C_C186"):
    D_6063: str = element(name="D_6063")
    D_6060: str = element(name="D_6060")
    D_6411: str = element(name="D_6411")

class ESLOG_S_QTY(BaseXmlModel, tag="S_QTY"):
    C_C186: ESLOG_C_C186 = element(tag="C_C186")

class ESLOG_S_ALI(BaseXmlModel, tag="S_ALI"):
    D_3239: str = element(name="D_3239")

class ESLOG_C_C516(BaseXmlModel, tag="C_C516"):
    D_5025: str = element(name="D_5025")
    D_5004: str = element(name="D_5004")

class ESLOG_S_MOA(BaseXmlModel, tag="S_MOA"):
    C_C516: ESLOG_C_C516 = element(tag="C_C516")

class ESLOG_G_SG27(BaseXmlModel, tag="G_SG27"):
    S_MOA: ESLOG_S_MOA = element(tag="S_MOA")
    
class ESLOG_C_C509(BaseXmlModel, tag="C_C509", skip_empty=True):
    D_5125: str = element(name="D_5125")
    D_5118: str = element(name="D_5118")
    D_5284: str | None = element(default=None, name="D_5284")
    D_6411: str | None = element(default=None, name="D_6411")
            
class ESLOG_S_PRI(BaseXmlModel, tag="S_PRI"):
    C_C509: ESLOG_C_C509 = element(tag="C_C509")

class ESLOG_G_SG29(BaseXmlModel, tag="G_SG29"):
    S_PRI: ESLOG_S_PRI = element(tag="S_PRI")

class ESLOG_G_SG30(BaseXmlModel, tag="G_SG30"):
    S_RFF: ESLOG_S_RFF = element(tag="S_RFF")

class ESLOG_C_C241(BaseXmlModel, tag="C_C241"):
    D_5153: str = element(name="D_5153")

class ESLOG_C_C243(BaseXmlModel, tag="C_C243"):
    D_5278: str = element(name="D_5278")

class ESLOG_S_TAX(BaseXmlModel, tag="S_TAX"):
    D_5283: str = element(name="D_5283")
    C_C241: ESLOG_C_C241 = element(tag="C_C241")
    C_C243: ESLOG_C_C243 = element(tag="C_C243")
    D_5305: str = element(name="D_5305")

class ESLOG_G_SG34(BaseXmlModel, tag="G_SG34"):
    S_TAX: ESLOG_S_TAX = element(tag="S_TAX")
    S_MOA: list[ESLOG_S_MOA] = element(tag="S_MOA")

class ESLOG_C_C552(BaseXmlModel, tag="C_C552"):
    D_5189: str = element(name="D_5189")

class ESLOG_S_ALC(BaseXmlModel, tag="S_ALC"):
    D_5463: str = element(name="D_5463")
    C_C552: ESLOG_C_C552 = element(tag="C_C552")

class ESLOG_C_C501(BaseXmlModel, tag="C_C501"):
    D_5245: str = element(name="D_5245")
    D_5482: str = element(name="D_5482")

class ESLOG_S_PCD(BaseXmlModel, tag="S_PCD"):
    C_C501: ESLOG_C_C501 = element(tag="C_C501")

class ESLOG_G_SG41(BaseXmlModel, tag="G_SG41"):
    S_PCD: ESLOG_S_PCD = element(tag="S_PCD")

class ESLOG_G_SG42(BaseXmlModel, tag="G_SG42"):
    S_MOA: ESLOG_S_MOA = element(tag="S_MOA")

class ESLOG_G_SG39(BaseXmlModel, tag="G_SG39"):
    S_ALC: ESLOG_S_ALC = element(tag="S_ALC")
    G_SG41: ESLOG_G_SG41 | None = element(tag="G_SG41", default=None)
    G_SG42: list[ESLOG_G_SG42] = element(tag="G_SG42")

class ESLOG_G_SG26(BaseXmlModel, tag="G_SG26", skip_empty=True):
    S_LIN: ESLOG_S_LIN = element(tag="S_LIN")
    S_PIA: list[ESLOG_S_PIA] = element(tag="S_PIA")
    S_IMD: list[ESLOG_S_IMD] = element(tag="S_IMD")
    S_QTY: ESLOG_S_QTY = element(tag="S_QTY")
    S_ALI: ESLOG_S_ALI | None = element(tag="S_ALI", default=None)
    S_DTM: list[ESLOG_S_DTM] = element(tag="S_DTM")
    S_FTX: list[ESLOG_S_FTX] = element(tag="S_FTX")
    G_SG27: list[ESLOG_G_SG27] = element(tag="G_SG27")
    G_SG29: list[ESLOG_G_SG29] = element(tag="G_SG29")
    G_SG30: list[ESLOG_G_SG30] = element(tag="G_SG30")
    G_SG34: list[ESLOG_G_SG34] = element(tag="G_SG34")
    G_SG39: list[ESLOG_G_SG39] = element(tag="G_SG39")
    
    
class ESLOG_S_UNS(BaseXmlModel, tag="S_UNS"):
    D_0081: str = element(name="D_0081")


class ESLOG_G_SG50(BaseXmlModel, tag="G_SG50"):
    S_MOA: ESLOG_S_MOA = element(tag="S_MOA")

class ESLOG_G_SG52(BaseXmlModel, tag="G_SG52"):
    S_TAX: ESLOG_S_TAX = element(tag="S_TAX")
    S_MOA: list[ESLOG_S_MOA] = element(tag="S_MOA")

class ESLOG_M_INVOIC(BaseXmlModel, tag="M_INVOIC"):
    """
    Invoice metadata wrapper
    """
    Id: str = attr(name="Id") # Always the same? Check xsd
    UNH: ESLOG_S_UNH = element(tag="S_UNH")
    BGM: ESLOG_S_BGM = element(tag="S_BGM")
    DTM: list[ESLOG_S_DTM] = element(tag="S_DTM")
    FTX: list[ESLOG_S_FTX] = element(tag="S_FTX")
    SG1: list[ESLOG_G_SG1] = element(tag="G_SG1")
    SG2: list[ESLOG_G_SG2] = element(tag="G_SG2")
    SG7: list[ESLOG_G_SG7] = element(tag="G_SG7")
    SG8: list[ESLOG_G_SG8] = element(tag="G_SG8")
    SG26: list[ESLOG_G_SG26] = element(tag="G_SG26")
    UNS: ESLOG_S_UNS = element(tag="S_UNS")
    SG50: list[ESLOG_G_SG50] = element(tag="G_SG50")
    SG52: list[ESLOG_G_SG52] = element(tag="G_SG52")

class ESLOG_Invoice(BaseXmlModel, tag="Invoice", nsmap={"": "urn:eslog:2.00", "xsi": "http://www.w3.org/2001/XMLSchema-instance"}):
    """
    Base invoice class
    """
    M_INVOIC: ESLOG_M_INVOIC = element(tag="M_INVOIC")
