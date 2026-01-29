from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02"


class AddressType2Code(Enum):
    ADDR = "ADDR"
    PBOX = "PBOX"
    HOME = "HOME"
    BIZZ = "BIZZ"
    MLTO = "MLTO"
    DLVY = "DLVY"


class CashAccountType4Code(Enum):
    CASH = "CASH"
    CHAR = "CHAR"
    COMM = "COMM"
    TAXE = "TAXE"
    CISH = "CISH"
    TRAS = "TRAS"
    SACC = "SACC"
    CACC = "CACC"
    SVGS = "SVGS"
    ONDP = "ONDP"
    MGLD = "MGLD"
    NREX = "NREX"
    MOMA = "MOMA"
    LOAN = "LOAN"
    SLRY = "SLRY"
    ODFT = "ODFT"


class CashClearingSystem3Code(Enum):
    ABE = "ABE"
    ART = "ART"
    AVP = "AVP"
    AZM = "AZM"
    BAP = "BAP"
    BEL = "BEL"
    BOF = "BOF"
    BRL = "BRL"
    CAD = "CAD"
    CAM = "CAM"
    CBJ = "CBJ"
    CHP = "CHP"
    DKC = "DKC"
    RTP = "RTP"
    EBA = "EBA"
    ELS = "ELS"
    ERP = "ERP"
    XCT = "XCT"
    HRK = "HRK"
    HRM = "HRM"
    HUF = "HUF"
    LGS = "LGS"
    LVL = "LVL"
    MUP = "MUP"
    NOC = "NOC"
    PCH = "PCH"
    PDS = "PDS"
    PEG = "PEG"
    PNS = "PNS"
    PVE = "PVE"
    SEC = "SEC"
    SIT = "SIT"
    SLB = "SLB"
    SPG = "SPG"
    SSK = "SSK"
    TBF = "TBF"
    TGT = "TGT"
    TOP = "TOP"
    FDW = "FDW"
    BOJ = "BOJ"
    FEY = "FEY"
    ZEN = "ZEN"
    DDK = "DDK"
    AIP = "AIP"
    BCC = "BCC"
    BDS = "BDS"
    BGN = "BGN"
    BHS = "BHS"
    BIS = "BIS"
    BSP = "BSP"
    EPM = "EPM"
    EPN = "EPN"
    FDA = "FDA"
    GIS = "GIS"
    INC = "INC"
    JOD = "JOD"
    KPS = "KPS"
    LKB = "LKB"
    MEP = "MEP"
    MRS = "MRS"
    NAM = "NAM"
    PTR = "PTR"
    ROL = "ROL"
    ROS = "ROS"
    SCP = "SCP"
    STG = "STG"
    THB = "THB"
    TIS = "TIS"
    TTD = "TTD"
    UIS = "UIS"
    MOS = "MOS"
    ZET = "ZET"
    ZIS = "ZIS"
    CHI = "CHI"
    COP = "COP"


class ClearingChannel2Code(Enum):
    RTGS = "RTGS"
    RTNS = "RTNS"
    MPNS = "MPNS"
    BOOK = "BOOK"


@dataclass
class ClearingSystemMemberIdentification3Choice:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CurrencyAndAmount:
    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "required": True,
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Attribute",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )


@dataclass
class DateAndPlaceOfBirth:
    birth_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "BirthDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    prvc_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "PrvcOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    city_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "CityOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtryOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


class DocumentType2Code(Enum):
    MSIN = "MSIN"
    CNFA = "CNFA"
    DNFA = "DNFA"
    CINV = "CINV"
    CREN = "CREN"
    DEBN = "DEBN"
    HIRI = "HIRI"
    SBIN = "SBIN"
    CMCN = "CMCN"
    SOAC = "SOAC"
    DISP = "DISP"


class DocumentType3Code(Enum):
    RADM = "RADM"
    RPIN = "RPIN"
    FXDR = "FXDR"
    DISP = "DISP"
    PUOR = "PUOR"
    SCOR = "SCOR"


class Frequency1Code(Enum):
    YEAR = "YEAR"
    MNTH = "MNTH"
    QURT = "QURT"
    MIAN = "MIAN"
    WEEK = "WEEK"
    DAIL = "DAIL"
    ADHO = "ADHO"
    INDA = "INDA"


@dataclass
class GenericIdentification3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericIdentification4:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    id_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "IdTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class LocalInstrument1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


class PaymentCategoryPurpose1Code(Enum):
    CORT = "CORT"
    SALA = "SALA"
    TREA = "TREA"
    CASH = "CASH"
    DIVI = "DIVI"
    GOVT = "GOVT"
    INTE = "INTE"
    LOAN = "LOAN"
    PENS = "PENS"
    SECU = "SECU"
    SSBE = "SSBE"
    SUPP = "SUPP"
    TAXS = "TAXS"
    TRAD = "TRAD"
    VATX = "VATX"
    HEDG = "HEDG"
    INTC = "INTC"
    WHLD = "WHLD"


class PaymentMethod4Code(Enum):
    CHK = "CHK"
    TRF = "TRF"
    DD = "DD"
    TRA = "TRA"


class Priority2Code(Enum):
    HIGH = "HIGH"
    NORM = "NORM"


class SequenceType1Code(Enum):
    FRST = "FRST"
    RCUR = "RCUR"
    FNAL = "FNAL"
    OOFF = "OOFF"


class ServiceLevel1Code(Enum):
    SEPA = "SEPA"
    SDVA = "SDVA"
    PRPT = "PRPT"


class SettlementMethod1Code(Enum):
    INDA = "INDA"
    INGA = "INGA"
    COVE = "COVE"
    CLRG = "CLRG"


@dataclass
class SimpleIdentificationInformation2:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "min_length": 1,
            "max_length": 34,
        },
    )


class TransactionGroupStatus1Code(Enum):
    ACTC = "ACTC"
    RCVD = "RCVD"
    PART = "PART"
    RJCT = "RJCT"
    PDNG = "PDNG"
    ACCP = "ACCP"
    ACSP = "ACSP"
    ACSC = "ACSC"
    ACCR = "ACCR"
    ACWC = "ACWC"


class TransactionIndividualStatus1Code(Enum):
    ACTC = "ACTC"
    RJCT = "RJCT"
    PDNG = "PDNG"
    ACCP = "ACCP"
    ACSP = "ACSP"
    ACSC = "ACSC"
    ACCR = "ACCR"
    ACWC = "ACWC"


class TransactionRejectReason2Code(Enum):
    AC01 = "AC01"
    AC04 = "AC04"
    AC06 = "AC06"
    AM01 = "AM01"
    AM02 = "AM02"
    AM03 = "AM03"
    AM04 = "AM04"
    AM05 = "AM05"
    AM06 = "AM06"
    AM07 = "AM07"
    BE01 = "BE01"
    BE04 = "BE04"
    BE05 = "BE05"
    AG01 = "AG01"
    AG02 = "AG02"
    DT01 = "DT01"
    RF01 = "RF01"
    RC01 = "RC01"
    TM01 = "TM01"
    ED01 = "ED01"
    ED03 = "ED03"
    MS03 = "MS03"
    MS02 = "MS02"
    BE06 = "BE06"
    BE07 = "BE07"
    AM09 = "AM09"
    AM10 = "AM10"
    MD01 = "MD01"
    MD02 = "MD02"
    MD03 = "MD03"
    MD04 = "MD04"
    MD06 = "MD06"
    MD07 = "MD07"
    ED05 = "ED05"
    NARR = "NARR"


@dataclass
class AccountIdentification3Choice:
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[a-zA-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    bban: Optional[str] = field(
        default=None,
        metadata={
            "name": "BBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[a-zA-Z0-9]{1,30}",
        },
    )
    upic: Optional[str] = field(
        default=None,
        metadata={
            "name": "UPIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[0-9]{8,17}",
        },
    )
    prtry_acct: Optional[SimpleIdentificationInformation2] = field(
        default=None,
        metadata={
            "name": "PrtryAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class CashAccountType2:
    cd: Optional[CashAccountType4Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ClearingSystemIdentification1Choice:
    clr_sys_id: Optional[CashClearingSystem3Code] = field(
        default=None,
        metadata={
            "name": "ClrSysId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CreditorReferenceType1:
    cd: Optional[DocumentType3Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class EquivalentAmount:
    amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    ccy_of_trf: Optional[str] = field(
        default=None,
        metadata={
            "name": "CcyOfTrf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )


@dataclass
class NumberOfTransactionsPerStatus1:
    dtld_nb_of_txs: Optional[str] = field(
        default=None,
        metadata={
            "name": "DtldNbOfTxs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "pattern": r"[0-9]{1,15}",
        },
    )
    dtld_sts: Optional[TransactionIndividualStatus1Code] = field(
        default=None,
        metadata={
            "name": "DtldSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    dtld_ctrl_sum: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "DtldCtrlSum",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )


@dataclass
class OrganisationIdentification2:
    bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "BIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    ibei: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[A-Z]{2,2}[B-DF-HJ-NP-TV-XZ0-9]{7,7}[0-9]{1,1}",
        },
    )
    bei: Optional[str] = field(
        default=None,
        metadata={
            "name": "BEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    eangln: Optional[str] = field(
        default=None,
        metadata={
            "name": "EANGLN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[0-9]{13,13}",
        },
    )
    uschu: Optional[str] = field(
        default=None,
        metadata={
            "name": "USCHU",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"CH[0-9]{6,6}",
        },
    )
    duns: Optional[str] = field(
        default=None,
        metadata={
            "name": "DUNS",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[0-9]{9,9}",
        },
    )
    bk_pty_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "BkPtyId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry_id: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class PersonIdentification3:
    drvrs_lic_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "DrvrsLicNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cstmr_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "CstmrNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    scl_scty_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "SclSctyNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    aln_regn_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "AlnRegnNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pspt_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PsptNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    idnty_card_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "IdntyCardNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    mplyr_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "MplyrIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dt_and_plc_of_birth: Optional[DateAndPlaceOfBirth] = field(
        default=None,
        metadata={
            "name": "DtAndPlcOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    othr_id: Optional[GenericIdentification4] = field(
        default=None,
        metadata={
            "name": "OthrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class PostalAddress1:
    adr_tp: Optional[AddressType2Code] = field(
        default=None,
        metadata={
            "name": "AdrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "max_occurs": 5,
            "min_length": 1,
            "max_length": 70,
        },
    )
    strt_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "StrtNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class ReferredDocumentAmount1Choice:
    due_pybl_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "DuePyblAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    dscnt_apld_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "DscntApldAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    rmtd_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RmtdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdt_note_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CdtNoteAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    tax_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class ReferredDocumentType1:
    cd: Optional[DocumentType2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ServiceLevel2Choice:
    cd: Optional[ServiceLevel1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class StatusReason1Choice:
    cd: Optional[TransactionRejectReason2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class AmountType2Choice:
    instd_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "InstdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    eqvt_amt: Optional[EquivalentAmount] = field(
        default=None,
        metadata={
            "name": "EqvtAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class BranchData:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class CashAccount7:
    id: Optional[AccountIdentification3Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    tp: Optional[CashAccountType2] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class CreditorReferenceInformation1:
    cdtr_ref_tp: Optional[CreditorReferenceType1] = field(
        default=None,
        metadata={
            "name": "CdtrRefTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdtr_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "CdtrRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class FinancialInstitutionIdentification3:
    bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "BIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    clr_sys_mmb_id: Optional[ClearingSystemMemberIdentification3Choice] = (
        field(
            default=None,
            metadata={
                "name": "ClrSysMmbId",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            },
        )
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prtry_id: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class NameAndAddress7:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "min_length": 1,
            "max_length": 70,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )


@dataclass
class Party2Choice:
    org_id: Optional[OrganisationIdentification2] = field(
        default=None,
        metadata={
            "name": "OrgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prvt_id: list[PersonIdentification3] = field(
        default_factory=list,
        metadata={
            "name": "PrvtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "max_occurs": 4,
        },
    )


@dataclass
class PaymentTypeInformation6:
    instr_prty: Optional[Priority2Code] = field(
        default=None,
        metadata={
            "name": "InstrPrty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    svc_lvl: Optional[ServiceLevel2Choice] = field(
        default=None,
        metadata={
            "name": "SvcLvl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    clr_chanl: Optional[ClearingChannel2Code] = field(
        default=None,
        metadata={
            "name": "ClrChanl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    lcl_instrm: Optional[LocalInstrument1Choice] = field(
        default=None,
        metadata={
            "name": "LclInstrm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    seq_tp: Optional[SequenceType1Code] = field(
        default=None,
        metadata={
            "name": "SeqTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    ctgy_purp: Optional[PaymentCategoryPurpose1Code] = field(
        default=None,
        metadata={
            "name": "CtgyPurp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class ReferredDocumentInformation1:
    rfrd_doc_tp: Optional[ReferredDocumentType1] = field(
        default=None,
        metadata={
            "name": "RfrdDocTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    rfrd_doc_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "RfrdDocNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class FinancialInstitutionIdentification5Choice:
    bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "BIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    clr_sys_mmb_id: Optional[ClearingSystemMemberIdentification3Choice] = (
        field(
            default=None,
            metadata={
                "name": "ClrSysMmbId",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            },
        )
    )
    nm_and_adr: Optional[NameAndAddress7] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    prtry_id: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cmbnd_id: Optional[FinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "CmbndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class PartyIdentification8:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    id: Optional[Party2Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    ctry_of_res: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtryOfRes",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class BranchAndFinancialInstitutionIdentification3:
    fin_instn_id: Optional[FinancialInstitutionIdentification5Choice] = field(
        default=None,
        metadata={
            "name": "FinInstnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    brnch_id: Optional[BranchData] = field(
        default=None,
        metadata={
            "name": "BrnchId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class StatusReasonInformation1:
    sts_orgtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "StsOrgtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    sts_rsn: Optional[StatusReason1Choice] = field(
        default=None,
        metadata={
            "name": "StsRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    addtl_sts_rsn_inf: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AddtlStsRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 105,
        },
    )


@dataclass
class StructuredRemittanceInformation6:
    rfrd_doc_inf: Optional[ReferredDocumentInformation1] = field(
        default=None,
        metadata={
            "name": "RfrdDocInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    rfrd_doc_rltd_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "RfrdDocRltdDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    rfrd_doc_amt: list[ReferredDocumentAmount1Choice] = field(
        default_factory=list,
        metadata={
            "name": "RfrdDocAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdtr_ref_inf: Optional[CreditorReferenceInformation1] = field(
        default=None,
        metadata={
            "name": "CdtrRefInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    invcr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "Invcr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    invcee: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "Invcee",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    addtl_rmt_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlRmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class AmendmentInformationDetails1:
    orgnl_mndt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlMndtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_cdtr_schme_id: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "OrgnlCdtrSchmeId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    orgnl_cdtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlCdtrAgt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            },
        )
    )
    orgnl_cdtr_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "OrgnlCdtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    orgnl_dbtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "OrgnlDbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    orgnl_dbtr_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "OrgnlDbtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    orgnl_dbtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlDbtrAgt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            },
        )
    )
    orgnl_dbtr_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "OrgnlDbtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    orgnl_fnl_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "OrgnlFnlColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    orgnl_frqcy: Optional[Frequency1Code] = field(
        default=None,
        metadata={
            "name": "OrgnlFrqcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class ChargesInformation1:
    chrgs_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "ChrgsAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    chrgs_pty: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "ChrgsPty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )


@dataclass
class GroupHeader5:
    msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    cre_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "CreDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    initg_pty: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "InitgPty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    fwdg_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "FwdgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    dbtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "DbtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "CdtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    instg_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "InstgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    instd_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "InstdAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class OriginalGroupInformation1:
    orgnl_msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlMsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ntwk_file_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "NtwkFileNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_msg_nm_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlMsgNmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_cre_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "OrgnlCreDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    file_orgtr: Optional[str] = field(
        default=None,
        metadata={
            "name": "FileOrgtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_nb_of_txs: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlNbOfTxs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "pattern": r"[0-9]{1,15}",
        },
    )
    orgnl_ctrl_sum: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "OrgnlCtrlSum",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    grp_sts: Optional[TransactionGroupStatus1Code] = field(
        default=None,
        metadata={
            "name": "GrpSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    sts_rsn_inf: list[StatusReasonInformation1] = field(
        default_factory=list,
        metadata={
            "name": "StsRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    nb_of_txs_per_sts: list[NumberOfTransactionsPerStatus1] = field(
        default_factory=list,
        metadata={
            "name": "NbOfTxsPerSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class RemittanceInformation1:
    ustrd: list[str] = field(
        default_factory=list,
        metadata={
            "name": "Ustrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 140,
        },
    )
    strd: list[StructuredRemittanceInformation6] = field(
        default_factory=list,
        metadata={
            "name": "Strd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class SettlementInformation3:
    sttlm_mtd: Optional[SettlementMethod1Code] = field(
        default=None,
        metadata={
            "name": "SttlmMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    sttlm_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "SttlmAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    clr_sys: Optional[ClearingSystemIdentification1Choice] = field(
        default=None,
        metadata={
            "name": "ClrSys",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    instg_rmbrsmnt_agt: Optional[
        BranchAndFinancialInstitutionIdentification3
    ] = field(
        default=None,
        metadata={
            "name": "InstgRmbrsmntAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    instg_rmbrsmnt_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "InstgRmbrsmntAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    instd_rmbrsmnt_agt: Optional[
        BranchAndFinancialInstitutionIdentification3
    ] = field(
        default=None,
        metadata={
            "name": "InstdRmbrsmntAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    instd_rmbrsmnt_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "InstdRmbrsmntAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    thrd_rmbrsmnt_agt: Optional[
        BranchAndFinancialInstitutionIdentification3
    ] = field(
        default=None,
        metadata={
            "name": "ThrdRmbrsmntAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    thrd_rmbrsmnt_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "ThrdRmbrsmntAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class MandateRelatedInformation1:
    mndt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MndtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dt_of_sgntr: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "DtOfSgntr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    amdmnt_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "AmdmntInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    amdmnt_inf_dtls: Optional[AmendmentInformationDetails1] = field(
        default=None,
        metadata={
            "name": "AmdmntInfDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    elctrnc_sgntr: Optional[str] = field(
        default=None,
        metadata={
            "name": "ElctrncSgntr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 1025,
        },
    )
    frst_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FrstColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    fnl_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FnlColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    frqcy: Optional[Frequency1Code] = field(
        default=None,
        metadata={
            "name": "Frqcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class OriginalTransactionReference1:
    intr_bk_sttlm_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "IntrBkSttlmAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    amt: Optional[AmountType2Choice] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    intr_bk_sttlm_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "IntrBkSttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    reqd_exctn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ReqdExctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    reqd_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ReqdColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdtr_schme_id: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "CdtrSchmeId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    sttlm_inf: Optional[SettlementInformation3] = field(
        default=None,
        metadata={
            "name": "SttlmInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    pmt_tp_inf: Optional[PaymentTypeInformation6] = field(
        default=None,
        metadata={
            "name": "PmtTpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    pmt_mtd: Optional[PaymentMethod4Code] = field(
        default=None,
        metadata={
            "name": "PmtMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    mndt_rltd_inf: Optional[MandateRelatedInformation1] = field(
        default=None,
        metadata={
            "name": "MndtRltdInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    rmt_inf: Optional[RemittanceInformation1] = field(
        default=None,
        metadata={
            "name": "RmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    ultmt_dbtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "UltmtDbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    dbtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "Dbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    dbtr_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "DbtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    dbtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "DbtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    dbtr_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "DbtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "CdtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdtr_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "CdtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "Cdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    cdtr_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "CdtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    ultmt_cdtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "UltmtCdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class PaymentTransactionInformation1:
    sts_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "StsId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_pmt_inf_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlPmtInfId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_end_to_end_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlEndToEndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tx_sts: Optional[TransactionIndividualStatus1Code] = field(
        default=None,
        metadata={
            "name": "TxSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    sts_rsn_inf: list[StatusReasonInformation1] = field(
        default_factory=list,
        metadata={
            "name": "StsRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    chrgs_inf: list[ChargesInformation1] = field(
        default_factory=list,
        metadata={
            "name": "ChrgsInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    accptnc_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "AccptncDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    instg_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "InstgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    instd_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "InstdAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )
    orgnl_tx_ref: Optional[OriginalTransactionReference1] = field(
        default=None,
        metadata={
            "name": "OrgnlTxRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class Pacs00200102:
    class Meta:
        name = "pacs.002.001.02"

    grp_hdr: Optional[GroupHeader5] = field(
        default=None,
        metadata={
            "name": "GrpHdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    orgnl_grp_inf_and_sts: Optional[OriginalGroupInformation1] = field(
        default=None,
        metadata={
            "name": "OrgnlGrpInfAndSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
            "required": True,
        },
    )
    tx_inf_and_sts: list[PaymentTransactionInformation1] = field(
        default_factory=list,
        metadata={
            "name": "TxInfAndSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:pacs.002.001.02"

    pacs_002_001_02: Optional[Pacs00200102] = field(
        default=None,
        metadata={
            "name": "pacs.002.001.02",
            "type": "Element",
            "required": True,
        },
    )
