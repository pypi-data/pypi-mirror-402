from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01"


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


class ChargeBearerType1Code(Enum):
    DEBT = "DEBT"
    CRED = "CRED"
    SHAR = "SHAR"
    SLEV = "SLEV"


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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    prvc_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "PrvcOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    city_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "CityOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


class Grouping1Code(Enum):
    SNGL = "SNGL"
    GRPD = "GRPD"
    MIXD = "MIXD"


@dataclass
class LocalInstrument1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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


@dataclass
class PaymentIdentification1:
    instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "InstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    end_to_end_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "EndToEndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


class PaymentMethod2Code(Enum):
    DD = "DD"


class Priority2Code(Enum):
    HIGH = "HIGH"
    NORM = "NORM"


@dataclass
class Purpose1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class RegulatoryAuthority:
    authrty_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuthrtyNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    authrty_ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuthrtyCtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[A-Z]{2,2}",
        },
    )


class RegulatoryReportingType1Code(Enum):
    CRED = "CRED"
    DEBT = "DEBT"
    BOTH = "BOTH"


class RemittanceLocationMethod1Code(Enum):
    FAXI = "FAXI"
    EDIC = "EDIC"
    URID = "URID"
    EMAL = "EMAL"
    POST = "POST"


class SequenceType1Code(Enum):
    FRST = "FRST"
    RCUR = "RCUR"
    FNAL = "FNAL"
    OOFF = "OOFF"


class ServiceLevel2Code(Enum):
    SEPA = "SEPA"
    SDVA = "SDVA"


@dataclass
class SimpleIdentificationInformation2:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 34,
        },
    )


@dataclass
class AccountIdentification3Choice:
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[a-zA-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    bban: Optional[str] = field(
        default=None,
        metadata={
            "name": "BBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[a-zA-Z0-9]{1,30}",
        },
    )
    upic: Optional[str] = field(
        default=None,
        metadata={
            "name": "UPIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[0-9]{8,17}",
        },
    )
    prtry_acct: Optional[SimpleIdentificationInformation2] = field(
        default=None,
        metadata={
            "name": "PrtryAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class CashAccountType2:
    cd: Optional[CashAccountType4Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class OrganisationIdentification2:
    bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "BIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    ibei: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[A-Z]{2,2}[B-DF-HJ-NP-TV-XZ0-9]{7,7}[0-9]{1,1}",
        },
    )
    bei: Optional[str] = field(
        default=None,
        metadata={
            "name": "BEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    eangln: Optional[str] = field(
        default=None,
        metadata={
            "name": "EANGLN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[0-9]{13,13}",
        },
    )
    uschu: Optional[str] = field(
        default=None,
        metadata={
            "name": "USCHU",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"CH[0-9]{6,6}",
        },
    )
    duns: Optional[str] = field(
        default=None,
        metadata={
            "name": "DUNS",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[0-9]{9,9}",
        },
    )
    bk_pty_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "BkPtyId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry_id: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class PersonIdentification3:
    drvrs_lic_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "DrvrsLicNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cstmr_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "CstmrNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    scl_scty_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "SclSctyNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    aln_regn_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "AlnRegnNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pspt_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PsptNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    idnty_card_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "IdntyCardNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    mplyr_id_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "MplyrIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dt_and_plc_of_birth: Optional[DateAndPlaceOfBirth] = field(
        default=None,
        metadata={
            "name": "DtAndPlcOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    othr_id: Optional[GenericIdentification4] = field(
        default=None,
        metadata={
            "name": "OthrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    dscnt_apld_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "DscntApldAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    rmtd_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RmtdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    cdt_note_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CdtNoteAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    tax_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class ReferredDocumentType1:
    cd: Optional[DocumentType2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ServiceLevel3Choice:
    cd: Optional[ServiceLevel2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class StructuredRegulatoryReporting2:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 3,
        },
    )
    amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "Inf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    taxbl_base_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TaxblBaseAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class BranchData:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class CashAccount7:
    id: Optional[AccountIdentification3Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    tp: Optional[CashAccountType2] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    cdtr_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "CdtrRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    clr_sys_mmb_id: Optional[ClearingSystemMemberIdentification3Choice] = (
        field(
            default=None,
            metadata={
                "name": "ClrSysMmbId",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            },
        )
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    prtry_id: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class NameAndAddress3:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )


@dataclass
class NameAndAddress7:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    prvt_id: list[PersonIdentification3] = field(
        default_factory=list,
        metadata={
            "name": "PrvtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "max_occurs": 4,
        },
    )


@dataclass
class PaymentTypeInformation2:
    instr_prty: Optional[Priority2Code] = field(
        default=None,
        metadata={
            "name": "InstrPrty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    svc_lvl: Optional[ServiceLevel3Choice] = field(
        default=None,
        metadata={
            "name": "SvcLvl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    clr_chanl: Optional[ClearingChannel2Code] = field(
        default=None,
        metadata={
            "name": "ClrChanl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    lcl_instrm: Optional[LocalInstrument1Choice] = field(
        default=None,
        metadata={
            "name": "LclInstrm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    seq_tp: Optional[SequenceType1Code] = field(
        default=None,
        metadata={
            "name": "SeqTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    ctgy_purp: Optional[PaymentCategoryPurpose1Code] = field(
        default=None,
        metadata={
            "name": "CtgyPurp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class ReferredDocumentInformation1:
    rfrd_doc_tp: Optional[ReferredDocumentType1] = field(
        default=None,
        metadata={
            "name": "RfrdDocTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    rfrd_doc_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "RfrdDocNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class RegulatoryReporting2:
    dbt_cdt_rptg_ind: Optional[RegulatoryReportingType1Code] = field(
        default=None,
        metadata={
            "name": "DbtCdtRptgInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    authrty: Optional[RegulatoryAuthority] = field(
        default=None,
        metadata={
            "name": "Authrty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    rgltry_dtls: Optional[StructuredRegulatoryReporting2] = field(
        default=None,
        metadata={
            "name": "RgltryDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class TaxDetails:
    cert_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CertId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_tp: Optional[TaxType] = field(
        default=None,
        metadata={
            "name": "TaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class FinancialInstitutionIdentification5Choice:
    bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "BIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    clr_sys_mmb_id: Optional[ClearingSystemMemberIdentification3Choice] = (
        field(
            default=None,
            metadata={
                "name": "ClrSysMmbId",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            },
        )
    )
    nm_and_adr: Optional[NameAndAddress7] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    prtry_id: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    cmbnd_id: Optional[FinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "CmbndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class PartyIdentification8:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pstl_adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    id: Optional[Party2Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    ctry_of_res: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtryOfRes",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class RemittanceLocation1:
    rmt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "RmtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rmt_lctn_mtd: Optional[RemittanceLocationMethod1Code] = field(
        default=None,
        metadata={
            "name": "RmtLctnMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    rmt_lctn_elctrnc_adr: Optional[str] = field(
        default=None,
        metadata={
            "name": "RmtLctnElctrncAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 256,
        },
    )
    rmt_lctn_pstl_adr: Optional[NameAndAddress3] = field(
        default=None,
        metadata={
            "name": "RmtLctnPstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class TaxInformation2:
    cdtr_tax_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CdtrTaxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cdtr_tax_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "CdtrTaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dbtr_tax_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "DbtrTaxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_ref_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxRefNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )
    ttl_taxbl_base_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlTaxblBaseAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    ttl_tax_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlTaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    tax_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "TaxDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    tax_tp_inf: list[TaxDetails] = field(
        default_factory=list,
        metadata={
            "name": "TaxTpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class BranchAndFinancialInstitutionIdentification3:
    fin_instn_id: Optional[FinancialInstitutionIdentification5Choice] = field(
        default=None,
        metadata={
            "name": "FinInstnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    brnch_id: Optional[BranchData] = field(
        default=None,
        metadata={
            "name": "BrnchId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class StructuredRemittanceInformation6:
    rfrd_doc_inf: Optional[ReferredDocumentInformation1] = field(
        default=None,
        metadata={
            "name": "RfrdDocInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    rfrd_doc_rltd_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "RfrdDocRltdDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    rfrd_doc_amt: list[ReferredDocumentAmount1Choice] = field(
        default_factory=list,
        metadata={
            "name": "RfrdDocAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    cdtr_ref_inf: Optional[CreditorReferenceInformation1] = field(
        default=None,
        metadata={
            "name": "CdtrRefInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    invcr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "Invcr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    invcee: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "Invcee",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    addtl_rmt_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlRmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_cdtr_schme_id: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "OrgnlCdtrSchmeId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    orgnl_cdtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlCdtrAgt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            },
        )
    )
    orgnl_cdtr_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "OrgnlCdtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    orgnl_dbtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "OrgnlDbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    orgnl_dbtr_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "OrgnlDbtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    orgnl_dbtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlDbtrAgt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            },
        )
    )
    orgnl_dbtr_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "OrgnlDbtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    orgnl_fnl_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "OrgnlFnlColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    orgnl_frqcy: Optional[Frequency1Code] = field(
        default=None,
        metadata={
            "name": "OrgnlFrqcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class GroupHeader1:
    msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    authstn: list[str] = field(
        default_factory=list,
        metadata={
            "name": "Authstn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "max_occurs": 2,
            "min_length": 1,
            "max_length": 128,
        },
    )
    btch_bookg: Optional[bool] = field(
        default=None,
        metadata={
            "name": "BtchBookg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    nb_of_txs: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfTxs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
            "pattern": r"[0-9]{1,15}",
        },
    )
    ctrl_sum: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "CtrlSum",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    grpg: Optional[Grouping1Code] = field(
        default=None,
        metadata={
            "name": "Grpg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    initg_pty: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "InitgPty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    fwdg_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "FwdgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class RemittanceInformation1:
    ustrd: list[str] = field(
        default_factory=list,
        metadata={
            "name": "Ustrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )
    strd: list[StructuredRemittanceInformation6] = field(
        default_factory=list,
        metadata={
            "name": "Strd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class MandateRelatedInformation1:
    mndt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MndtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dt_of_sgntr: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "DtOfSgntr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    amdmnt_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "AmdmntInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    amdmnt_inf_dtls: Optional[AmendmentInformationDetails1] = field(
        default=None,
        metadata={
            "name": "AmdmntInfDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    elctrnc_sgntr: Optional[str] = field(
        default=None,
        metadata={
            "name": "ElctrncSgntr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 1025,
        },
    )
    frst_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FrstColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    fnl_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FnlColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    frqcy: Optional[Frequency1Code] = field(
        default=None,
        metadata={
            "name": "Frqcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class DirectDebitTransaction1:
    mndt_rltd_inf: Optional[MandateRelatedInformation1] = field(
        default=None,
        metadata={
            "name": "MndtRltdInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    cdtr_schme_id: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "CdtrSchmeId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    pre_ntfctn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PreNtfctnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pre_ntfctn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "PreNtfctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class DirectDebitTransactionInformation1:
    pmt_id: Optional[PaymentIdentification1] = field(
        default=None,
        metadata={
            "name": "PmtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    pmt_tp_inf: Optional[PaymentTypeInformation2] = field(
        default=None,
        metadata={
            "name": "PmtTpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    instd_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "InstdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    chrg_br: Optional[ChargeBearerType1Code] = field(
        default=None,
        metadata={
            "name": "ChrgBr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    drct_dbt_tx: Optional[DirectDebitTransaction1] = field(
        default=None,
        metadata={
            "name": "DrctDbtTx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    ultmt_cdtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "UltmtCdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    dbtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "DbtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    dbtr_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "DbtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    dbtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "Dbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    dbtr_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "DbtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    ultmt_dbtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "UltmtDbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    instr_for_cdtr_agt: Optional[str] = field(
        default=None,
        metadata={
            "name": "InstrForCdtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )
    purp: Optional[Purpose1Choice] = field(
        default=None,
        metadata={
            "name": "Purp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    rgltry_rptg: list[RegulatoryReporting2] = field(
        default_factory=list,
        metadata={
            "name": "RgltryRptg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "max_occurs": 10,
        },
    )
    tax: Optional[TaxInformation2] = field(
        default=None,
        metadata={
            "name": "Tax",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    rltd_rmt_inf: list[RemittanceLocation1] = field(
        default_factory=list,
        metadata={
            "name": "RltdRmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "max_occurs": 10,
        },
    )
    rmt_inf: Optional[RemittanceInformation1] = field(
        default=None,
        metadata={
            "name": "RmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )


@dataclass
class PaymentInstructionInformation2:
    pmt_inf_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PmtInfId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pmt_mtd: Optional[PaymentMethod2Code] = field(
        default=None,
        metadata={
            "name": "PmtMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    pmt_tp_inf: Optional[PaymentTypeInformation2] = field(
        default=None,
        metadata={
            "name": "PmtTpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    reqd_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ReqdColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    cdtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "Cdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    cdtr_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "CdtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    cdtr_agt: Optional[BranchAndFinancialInstitutionIdentification3] = field(
        default=None,
        metadata={
            "name": "CdtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    cdtr_agt_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "CdtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    ultmt_cdtr: Optional[PartyIdentification8] = field(
        default=None,
        metadata={
            "name": "UltmtCdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    chrg_br: Optional[ChargeBearerType1Code] = field(
        default=None,
        metadata={
            "name": "ChrgBr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    chrgs_acct: Optional[CashAccount7] = field(
        default=None,
        metadata={
            "name": "ChrgsAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
        },
    )
    chrgs_acct_agt: Optional[BranchAndFinancialInstitutionIdentification3] = (
        field(
            default=None,
            metadata={
                "name": "ChrgsAcctAgt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            },
        )
    )
    drct_dbt_tx_inf: list[DirectDebitTransactionInformation1] = field(
        default_factory=list,
        metadata={
            "name": "DrctDbtTxInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_occurs": 1,
        },
    )


@dataclass
class Pain00800101:
    class Meta:
        name = "pain.008.001.01"

    grp_hdr: Optional[GroupHeader1] = field(
        default=None,
        metadata={
            "name": "GrpHdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "required": True,
        },
    )
    pmt_inf: list[PaymentInstructionInformation2] = field(
        default_factory=list,
        metadata={
            "name": "PmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01",
            "min_occurs": 1,
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:pain.008.001.01"

    pain_008_001_01: Optional[Pain00800101] = field(
        default=None,
        metadata={
            "name": "pain.008.001.01",
            "type": "Element",
            "required": True,
        },
    )
