from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:xsd:pain.001.001.01"


class AddressType2Code(Enum):
    ADDR = "ADDR"
    PBOX = "PBOX"
    HOME = "HOME"
    BIZZ = "BIZZ"
    MLTO = "MLTO"
    DLVY = "DLVY"


class CashAccountType3Code(Enum):
    CASH = "CASH"
    CHAR = "CHAR"
    SACC = "SACC"
    CACC = "CACC"
    SVGS = "SVGS"


class CashClearingSystem2Code(Enum):
    RTG = "RTG"
    ACH = "ACH"
    CHI = "CHI"
    FDN = "FDN"


class ChargeBearer1Code(Enum):
    OUR = "OUR"
    BEN = "BEN"
    SHA = "SHA"


class ChequeDelivery1Code(Enum):
    MLDB = "MLDB"
    MLCD = "MLCD"
    MLFA = "MLFA"
    CRDB = "CRDB"
    CRCD = "CRCD"
    CRFA = "CRFA"
    PUDB = "PUDB"
    PUCD = "PUCD"
    PUFA = "PUFA"
    RGDB = "RGDB"
    RGCD = "RGCD"
    RGFA = "RGFA"


class ChequeType2Code(Enum):
    CCHQ = "CCHQ"
    CCCH = "CCCH"
    BCHQ = "BCHQ"
    DRFT = "DRFT"
    ELDR = "ELDR"


@dataclass
class ClearingSystemMemberIdentificationChoice:
    uschu: Optional[str] = field(
        default=None,
        metadata={
            "name": "USCHU",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"CH[0-9]{6,6}",
        },
    )
    nzncc: Optional[str] = field(
        default=None,
        metadata={
            "name": "NZNCC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"NZ[0-9]{6,6}",
        },
    )
    iensc: Optional[str] = field(
        default=None,
        metadata={
            "name": "IENSC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"IE[0-9]{6,6}",
        },
    )
    gbsc: Optional[str] = field(
        default=None,
        metadata={
            "name": "GBSC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"SC[0-9]{6,6}",
        },
    )
    usch: Optional[str] = field(
        default=None,
        metadata={
            "name": "USCH",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"CP[0-9]{4,4}",
        },
    )
    chbc: Optional[str] = field(
        default=None,
        metadata={
            "name": "CHBC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"SW[0-9]{3,5}",
        },
    )
    usfw: Optional[str] = field(
        default=None,
        metadata={
            "name": "USFW",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"FW[0-9]{9,9}",
        },
    )
    ptncc: Optional[str] = field(
        default=None,
        metadata={
            "name": "PTNCC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"PT[0-9]{8,8}",
        },
    )
    rucb: Optional[str] = field(
        default=None,
        metadata={
            "name": "RUCB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"RU[0-9]{9,9}",
        },
    )
    itncc: Optional[str] = field(
        default=None,
        metadata={
            "name": "ITNCC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"IT[0-9]{10,10}",
        },
    )
    atblz: Optional[str] = field(
        default=None,
        metadata={
            "name": "ATBLZ",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"AT[0-9]{5,5}",
        },
    )
    cacpa: Optional[str] = field(
        default=None,
        metadata={
            "name": "CACPA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"CA[0-9]{9,9}",
        },
    )
    chsic: Optional[str] = field(
        default=None,
        metadata={
            "name": "CHSIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"SW[0-9]{6,6}",
        },
    )
    deblz: Optional[str] = field(
        default=None,
        metadata={
            "name": "DEBLZ",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"BL[0-9]{8,8}",
        },
    )
    esncc: Optional[str] = field(
        default=None,
        metadata={
            "name": "ESNCC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"ES[0-9]{8,9}",
        },
    )
    zancc: Optional[str] = field(
        default=None,
        metadata={
            "name": "ZANCC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"ZA[0-9]{6,6}",
        },
    )
    hkncc: Optional[str] = field(
        default=None,
        metadata={
            "name": "HKNCC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"HK[0-9]{3,3}",
        },
    )
    aubsbx: Optional[str] = field(
        default=None,
        metadata={
            "name": "AUBSBx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"AU[0-9]{6,6}",
        },
    )
    aubsbs: Optional[str] = field(
        default=None,
        metadata={
            "name": "AUBSBs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"AU[0-9]{6,6}",
        },
    )


class CreditTransferType2Code(Enum):
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


class DocumentType1Code(Enum):
    MSIN = "MSIN"
    CNFA = "CNFA"
    DNFA = "DNFA"
    CINV = "CINV"
    CREN = "CREN"
    DEBN = "DEBN"
    HIRI = "HIRI"
    SBIN = "SBIN"
    RADM = "RADM"
    RPIN = "RPIN"
    CMCN = "CMCN"
    FXDR = "FXDR"
    SOAC = "SOAC"


@dataclass
class GenericIdentification3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
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
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
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
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
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
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


class Instruction3Code(Enum):
    CHQB = "CHQB"
    HOLD = "HOLD"
    PHOB = "PHOB"
    TELB = "TELB"


@dataclass
class PaymentIdentification:
    instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "InstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    end_to_end_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "EndToEndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    pmt_rmt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PmtRmtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


class PaymentMethod1Code(Enum):
    CHK = "CHK"
    TRF = "TRF"


class PaymentPurpose1Code(Enum):
    SALA = "SALA"
    TREA = "TREA"
    ADVA = "ADVA"
    AGRT = "AGRT"
    ALMY = "ALMY"
    BECH = "BECH"
    BENE = "BENE"
    BONU = "BONU"
    CASH = "CASH"
    CBFF = "CBFF"
    CHAR = "CHAR"
    COLL = "COLL"
    CMDT = "CMDT"
    COMC = "COMC"
    COMM = "COMM"
    COST = "COST"
    CPYR = "CPYR"
    DIVI = "DIVI"
    FREX = "FREX"
    GDDS = "GDDS"
    GOVT = "GOVT"
    IHRP = "IHRP"
    INTC = "INTC"
    INSU = "INSU"
    INTE = "INTE"
    LICF = "LICF"
    LOAN = "LOAN"
    LOAR = "LOAR"
    NETT = "NETT"
    PAYR = "PAYR"
    PENS = "PENS"
    REFU = "REFU"
    RENT = "RENT"
    ROYA = "ROYA"
    SCVE = "SCVE"
    SECU = "SECU"
    SSBE = "SSBE"
    SUBS = "SUBS"
    TAXS = "TAXS"
    VATX = "VATX"
    COMT = "COMT"
    DBTC = "DBTC"
    SUPP = "SUPP"
    HEDG = "HEDG"


class Priority2Code(Enum):
    HIGH = "HIGH"
    NORM = "NORM"


class RemittanceLocationMethod1Code(Enum):
    FAXI = "FAXI"
    EDIC = "EDIC"
    URID = "URID"
    EMAL = "EMAL"
    POST = "POST"


@dataclass
class SimpleIdentificationInformation:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class AccountIdentification1Choice:
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[a-zA-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    bban: Optional[str] = field(
        default=None,
        metadata={
            "name": "BBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[a-zA-Z0-9]{1,30}",
        },
    )
    upic: Optional[str] = field(
        default=None,
        metadata={
            "name": "UPIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[0-9]{8,17}",
        },
    )
    dmst_acct: Optional[SimpleIdentificationInformation] = field(
        default=None,
        metadata={
            "name": "DmstAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class EquivalentAmount:
    amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    ccy_of_trf: Optional[str] = field(
        default=None,
        metadata={
            "name": "CcyOfTrf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )


@dataclass
class InstructionForFinalAgent:
    cd: list[Instruction3Code] = field(
        default_factory=list,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "max_occurs": 2,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class NonFinancialInstitutionIdentification1:
    bei: Optional[str] = field(
        default=None,
        metadata={
            "name": "BEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    eangln: Optional[str] = field(
        default=None,
        metadata={
            "name": "EANGLN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[0-9]{13,13}",
        },
    )
    uschu: Optional[str] = field(
        default=None,
        metadata={
            "name": "USCHU",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"CH[0-9]{6,6}",
        },
    )
    duns: Optional[str] = field(
        default=None,
        metadata={
            "name": "DUNS",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[0-9]{9,9}",
        },
    )
    bk_pty_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "BkPtyId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry_id: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class PaymentSchemeChoice:
    cd: Optional[CashClearingSystem2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    prtry_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "PrtryInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class PersonIdentification2:
    drvrs_lic_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "DrvrsLicNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    scl_scty_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "SclSctyNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    aln_regn_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "AlnRegnNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pspt_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PsptNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    idnty_card_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "IdntyCardNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    mplyr_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "MplyrIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    othr_id: Optional[GenericIdentification4] = field(
        default=None,
        metadata={
            "name": "OthrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
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
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
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
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class PurposeChoice:
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cd: Optional[PaymentPurpose1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class ReferredDocumentAmount1Choice:
    due_pybl_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "DuePyblAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    dscnt_apld_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "DscntApldAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    rmtd_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RmtdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    cdt_note_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CdtNoteAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    tax_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class StructuredRegulatoryReporting2:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 3,
        },
    )
    amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "Inf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class TaxType:
    ctgy_desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtgyDesc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    taxbl_base_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TaxblBaseAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class AmountType1Choice:
    instd_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "InstdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    eqvt_amt: Optional[EquivalentAmount] = field(
        default=None,
        metadata={
            "name": "EqvtAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class BranchData:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class CashAccount3:
    id: Optional[AccountIdentification1Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    tp: Optional[CashAccountType3Code] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class FinancialInstitutionIdentification1:
    bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "BIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    clr_sys_mmb_id: Optional[ClearingSystemMemberIdentificationChoice] = field(
        default=None,
        metadata={
            "name": "ClrSysMmbId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    prtry_id: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class NameAndAddress3:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 70,
        },
    )
    adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "Adr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )


@dataclass
class Party1Choice:
    org_id: Optional[NonFinancialInstitutionIdentification1] = field(
        default=None,
        metadata={
            "name": "OrgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    prvt_id: list[PersonIdentification2] = field(
        default_factory=list,
        metadata={
            "name": "PrvtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "max_occurs": 2,
        },
    )


@dataclass
class SettlementPriorityChoice:
    prty: Optional[Priority2Code] = field(
        default=None,
        metadata={
            "name": "Prty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    pmt_schme: Optional[PaymentSchemeChoice] = field(
        default=None,
        metadata={
            "name": "PmtSchme",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class TaxDetails:
    cert_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CertId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_tp: Optional[TaxType] = field(
        default=None,
        metadata={
            "name": "TaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class BranchAndFinancialInstitutionIdentification:
    fin_instn_id: Optional[FinancialInstitutionIdentification1] = field(
        default=None,
        metadata={
            "name": "FinInstnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    brnch_id: Optional[BranchData] = field(
        default=None,
        metadata={
            "name": "BrnchId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class Cheque2:
    chq_tp: Optional[ChequeType2Code] = field(
        default=None,
        metadata={
            "name": "ChqTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    chq_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "ChqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    chq_fr: Optional[NameAndAddress3] = field(
        default=None,
        metadata={
            "name": "ChqFr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    dlvry_mtd: Optional[ChequeDelivery1Code] = field(
        default=None,
        metadata={
            "name": "DlvryMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    dlvr_to: Optional[NameAndAddress3] = field(
        default=None,
        metadata={
            "name": "DlvrTo",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    instr_prty: Optional[Priority2Code] = field(
        default=None,
        metadata={
            "name": "InstrPrty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    chq_mtrty_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ChqMtrtyDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    frms_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "FrmsCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    memo_fld: Optional[str] = field(
        default=None,
        metadata={
            "name": "MemoFld",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rgnl_clr_zone: Optional[str] = field(
        default=None,
        metadata={
            "name": "RgnlClrZone",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CreditTransferTypeIdentification:
    cd: Optional[CreditTransferType2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    lcl_instrm: Optional[str] = field(
        default=None,
        metadata={
            "name": "LclInstrm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    instr_prty: Optional[Priority2Code] = field(
        default=None,
        metadata={
            "name": "InstrPrty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    sttlm_prty: Optional[SettlementPriorityChoice] = field(
        default=None,
        metadata={
            "name": "SttlmPrty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class PartyIdentification1:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    id: Optional[Party1Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class TaxInformation1:
    cdtr_tax_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CdtrTaxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cdtr_tax_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "CdtrTaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dbtr_tax_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "DbtrTaxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_ref_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxRefNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )
    ttl_taxbl_base_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlTaxblBaseAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    ttl_tax_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlTaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    tax_tp_inf: list[TaxDetails] = field(
        default_factory=list,
        metadata={
            "name": "TaxTpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class GroupInformation1:
    grp_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "GrpId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
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
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    authstn: list[str] = field(
        default_factory=list,
        metadata={
            "name": "Authstn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "max_occurs": 2,
            "min_length": 1,
            "max_length": 128,
        },
    )
    ctrl_sum: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "CtrlSum",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    btch_bookg: Optional[bool] = field(
        default=None,
        metadata={
            "name": "BtchBookg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    nb_of_txs: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfTxs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[0-9]{1,15}",
        },
    )
    grpg: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Grpg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    initg_pty: Optional[PartyIdentification1] = field(
        default=None,
        metadata={
            "name": "InitgPty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    fwdg_agt: Optional[BranchAndFinancialInstitutionIdentification] = field(
        default=None,
        metadata={
            "name": "FwdgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class InstructionForFirstAgent:
    rmt_lctn_mtd: Optional[RemittanceLocationMethod1Code] = field(
        default=None,
        metadata={
            "name": "RmtLctnMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    rmt_lctn_elctrnc_adr: Optional[str] = field(
        default=None,
        metadata={
            "name": "RmtLctnElctrncAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 128,
        },
    )
    rmt_lctn_pstl_adr: Optional[NameAndAddress3] = field(
        default=None,
        metadata={
            "name": "RmtLctnPstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    dbt_purp: Optional[str] = field(
        default=None,
        metadata={
            "name": "DbtPurp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )
    tax: Optional[TaxInformation1] = field(
        default=None,
        metadata={
            "name": "Tax",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class StructuredRemittanceInformation2:
    rfrd_doc_tp: Optional[DocumentType1Code] = field(
        default=None,
        metadata={
            "name": "RfrdDocTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    rfrd_doc_rltd_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "RfrdDocRltdDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    rfrd_doc_amt: list[ReferredDocumentAmount1Choice] = field(
        default_factory=list,
        metadata={
            "name": "RfrdDocAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    doc_ref_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "DocRefNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cdtr_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "CdtrRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    invcr: Optional[PartyIdentification1] = field(
        default=None,
        metadata={
            "name": "Invcr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    invcee: Optional[PartyIdentification1] = field(
        default=None,
        metadata={
            "name": "Invcee",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class RemittanceInformation3Choice:
    ustrd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ustrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )
    strd: Optional[StructuredRemittanceInformation2] = field(
        default=None,
        metadata={
            "name": "Strd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class GenericPaymentTransaction3:
    pmt_id: Optional[PaymentIdentification] = field(
        default=None,
        metadata={
            "name": "PmtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    purp: Optional[PurposeChoice] = field(
        default=None,
        metadata={
            "name": "Purp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    amt: Optional[AmountType1Choice] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    chq_instr: Optional[Cheque2] = field(
        default=None,
        metadata={
            "name": "ChqInstr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    orgtg_pty: Optional[PartyIdentification1] = field(
        default=None,
        metadata={
            "name": "OrgtgPty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    intrmy_agt1: Optional[BranchAndFinancialInstitutionIdentification] = field(
        default=None,
        metadata={
            "name": "IntrmyAgt1",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    intrmy_agt2: Optional[BranchAndFinancialInstitutionIdentification] = field(
        default=None,
        metadata={
            "name": "IntrmyAgt2",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    cdtr: Optional[PartyIdentification1] = field(
        default=None,
        metadata={
            "name": "Cdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    cdtr_acct: Optional[CashAccount3] = field(
        default=None,
        metadata={
            "name": "CdtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    cdtr_ctry_of_res: Optional[str] = field(
        default=None,
        metadata={
            "name": "CdtrCtryOfRes",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[A-Z]{2,2}",
        },
    )
    fnl_agt: Optional[BranchAndFinancialInstitutionIdentification] = field(
        default=None,
        metadata={
            "name": "FnlAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    fnl_agt_acct: Optional[str] = field(
        default=None,
        metadata={
            "name": "FnlAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    fnl_pty: Optional[PartyIdentification1] = field(
        default=None,
        metadata={
            "name": "FnlPty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    chrg_br: Optional[ChargeBearer1Code] = field(
        default=None,
        metadata={
            "name": "ChrgBr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    xchg_ctrct_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "XchgCtrctRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rgltry_rptg: list[StructuredRegulatoryReporting2] = field(
        default_factory=list,
        metadata={
            "name": "RgltryRptg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "max_occurs": 3,
        },
    )
    instr_for_fnl_agt: Optional[InstructionForFinalAgent] = field(
        default=None,
        metadata={
            "name": "InstrForFnlAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    instr_for_frst_agt: Optional[InstructionForFirstAgent] = field(
        default=None,
        metadata={
            "name": "InstrForFrstAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    rmt_inf: list[RemittanceInformation3Choice] = field(
        default_factory=list,
        metadata={
            "name": "RmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )


@dataclass
class PaymentInformation6:
    reqd_exctn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ReqdExctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    pmt_mtd_by_frst_agt: Optional[PaymentMethod1Code] = field(
        default=None,
        metadata={
            "name": "PmtMtdByFrstAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    cdt_trf_tp_id: Optional[CreditTransferTypeIdentification] = field(
        default=None,
        metadata={
            "name": "CdtTrfTpId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    dbtr: Optional[PartyIdentification1] = field(
        default=None,
        metadata={
            "name": "Dbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    dbtr_ctry_of_res: Optional[str] = field(
        default=None,
        metadata={
            "name": "DbtrCtryOfRes",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "pattern": r"[A-Z]{2,2}",
        },
    )
    dbtr_acct: Optional[CashAccount3] = field(
        default=None,
        metadata={
            "name": "DbtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    frst_agt: Optional[BranchAndFinancialInstitutionIdentification] = field(
        default=None,
        metadata={
            "name": "FrstAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    chrgs_acct: Optional[CashAccount3] = field(
        default=None,
        metadata={
            "name": "ChrgsAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
        },
    )
    chrgs_acct_agt: Optional[BranchAndFinancialInstitutionIdentification] = (
        field(
            default=None,
            metadata={
                "name": "ChrgsAcctAgt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            },
        )
    )
    pmt_tx: list[GenericPaymentTransaction3] = field(
        default_factory=list,
        metadata={
            "name": "PmtTx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_occurs": 1,
        },
    )


@dataclass
class Pain00100101:
    class Meta:
        name = "pain.001.001.01"

    grp_hdr: Optional[GroupInformation1] = field(
        default=None,
        metadata={
            "name": "GrpHdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "required": True,
        },
    )
    pmt_inf: list[PaymentInformation6] = field(
        default_factory=list,
        metadata={
            "name": "PmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:xsd:pain.001.001.01",
            "min_occurs": 1,
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:xsd:pain.001.001.01"

    pain_001_001_01: Optional[Pain00100101] = field(
        default=None,
        metadata={
            "name": "pain.001.001.01",
            "type": "Element",
            "required": True,
        },
    )
