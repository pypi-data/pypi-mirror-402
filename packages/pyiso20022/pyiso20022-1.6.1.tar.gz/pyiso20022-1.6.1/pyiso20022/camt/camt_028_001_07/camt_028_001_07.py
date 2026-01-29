from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07"


@dataclass
class AccountSchemeName1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ActiveOrHistoricCurrencyAndAmount:
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


class AddressType2Code(Enum):
    ADDR = "ADDR"
    PBOX = "PBOX"
    HOME = "HOME"
    BIZZ = "BIZZ"
    MLTO = "MLTO"
    DLVY = "DLVY"


@dataclass
class CashAccountType2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CategoryPurpose1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


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
class ClearingSystemIdentification2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 5,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ClearingSystemIdentification3Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 3,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


class CreditDebitCode(Enum):
    CRDT = "CRDT"
    DBIT = "DBIT"


@dataclass
class DateAndDateTimeChoice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class DateAndPlaceOfBirth:
    birth_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "BirthDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    prvc_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "PrvcOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    city_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "CityOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class DatePeriodDetails:
    fr_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FrDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    to_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )


@dataclass
class DiscountAmountType1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DocumentLineType1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


class DocumentType3Code(Enum):
    RADM = "RADM"
    RPIN = "RPIN"
    FXDR = "FXDR"
    DISP = "DISP"
    PUOR = "PUOR"
    SCOR = "SCOR"


class DocumentType6Code(Enum):
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
    BOLD = "BOLD"
    VCHR = "VCHR"
    AROI = "AROI"
    TSUT = "TSUT"
    PUOR = "PUOR"


@dataclass
class FinancialIdentificationSchemeName1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GarnishmentType1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


class Instruction3Code(Enum):
    CHQB = "CHQB"
    HOLD = "HOLD"
    PHOB = "PHOB"
    TELB = "TELB"


class Instruction4Code(Enum):
    PHOA = "PHOA"
    TELA = "TELA"


@dataclass
class LocalInstrument2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


class NamePrefix1Code(Enum):
    DOCT = "DOCT"
    MIST = "MIST"
    MISS = "MISS"
    MADM = "MADM"


@dataclass
class OrganisationIdentificationSchemeName1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class OriginalGroupInformation3:
    orgnl_msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlMsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_msg_nm_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlMsgNmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class PersonIdentificationSchemeName1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


class Priority2Code(Enum):
    HIGH = "HIGH"
    NORM = "NORM"


@dataclass
class Purpose2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


class SequenceType3Code(Enum):
    FRST = "FRST"
    RCUR = "RCUR"
    FNAL = "FNAL"
    OOFF = "OOFF"
    RPRE = "RPRE"


@dataclass
class ServiceLevel8Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


class SettlementMethod1Code(Enum):
    INDA = "INDA"
    INGA = "INGA"
    COVE = "COVE"
    CLRG = "CLRG"


@dataclass
class SupplementaryDataEnvelope1:
    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )


@dataclass
class TaxAmountType1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class TaxAuthorisation1:
    titl: Optional[str] = field(
        default=None,
        metadata={
            "name": "Titl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class TaxParty1:
    tax_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    regn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "RegnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


class TaxRecordPeriod1Code(Enum):
    MM01 = "MM01"
    MM02 = "MM02"
    MM03 = "MM03"
    MM04 = "MM04"
    MM05 = "MM05"
    MM06 = "MM06"
    MM07 = "MM07"
    MM08 = "MM08"
    MM09 = "MM09"
    MM10 = "MM10"
    MM11 = "MM11"
    MM12 = "MM12"
    QTR1 = "QTR1"
    QTR2 = "QTR2"
    QTR3 = "QTR3"
    QTR4 = "QTR4"
    HLF1 = "HLF1"
    HLF2 = "HLF2"


@dataclass
class UnderlyingGroupInformation1:
    orgnl_msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlMsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_msg_nm_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlMsgNmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    orgnl_msg_dlvry_chanl: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlMsgDlvryChanl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ClearingSystemMemberIdentification2:
    clr_sys_id: Optional[ClearingSystemIdentification2Choice] = field(
        default=None,
        metadata={
            "name": "ClrSysId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    mmb_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MmbId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ContactDetails2:
    nm_prfx: Optional[NamePrefix1Code] = field(
        default=None,
        metadata={
            "name": "NmPrfx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )
    phne_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PhneNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"\+[0-9]{1,3}-[0-9()+\-]{1,30}",
        },
    )
    mob_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "MobNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"\+[0-9]{1,3}-[0-9()+\-]{1,30}",
        },
    )
    fax_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "FaxNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"\+[0-9]{1,3}-[0-9()+\-]{1,30}",
        },
    )
    email_adr: Optional[str] = field(
        default=None,
        metadata={
            "name": "EmailAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 2048,
        },
    )
    othr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CreditorReferenceType1Choice:
    cd: Optional[DocumentType3Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DiscountAmountAndType1:
    tp: Optional[DiscountAmountType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )


@dataclass
class DocumentAdjustment1:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    rsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 4,
        },
    )
    addtl_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class DocumentLineType1:
    cd_or_prtry: Optional[DocumentLineType1Choice] = field(
        default=None,
        metadata={
            "name": "CdOrPrtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class EquivalentAmount2:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    ccy_of_trf: Optional[str] = field(
        default=None,
        metadata={
            "name": "CcyOfTrf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )


@dataclass
class GarnishmentType1:
    cd_or_prtry: Optional[GarnishmentType1Choice] = field(
        default=None,
        metadata={
            "name": "CdOrPrtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericAccountIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 34,
        },
    )
    schme_nm: Optional[AccountSchemeName1Choice] = field(
        default=None,
        metadata={
            "name": "SchmeNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericFinancialIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    schme_nm: Optional[FinancialIdentificationSchemeName1Choice] = field(
        default=None,
        metadata={
            "name": "SchmeNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericOrganisationIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    schme_nm: Optional[OrganisationIdentificationSchemeName1Choice] = field(
        default=None,
        metadata={
            "name": "SchmeNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericPersonIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    schme_nm: Optional[PersonIdentificationSchemeName1Choice] = field(
        default=None,
        metadata={
            "name": "SchmeNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class InstructionForCreditorAgent1:
    cd: Optional[Instruction3Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instr_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "InstrInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class InstructionForNextAgent1:
    cd: Optional[Instruction4Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instr_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "InstrInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class PaymentTypeInformation25:
    instr_prty: Optional[Priority2Code] = field(
        default=None,
        metadata={
            "name": "InstrPrty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    clr_chanl: Optional[ClearingChannel2Code] = field(
        default=None,
        metadata={
            "name": "ClrChanl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    svc_lvl: Optional[ServiceLevel8Choice] = field(
        default=None,
        metadata={
            "name": "SvcLvl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    lcl_instrm: Optional[LocalInstrument2Choice] = field(
        default=None,
        metadata={
            "name": "LclInstrm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    seq_tp: Optional[SequenceType3Code] = field(
        default=None,
        metadata={
            "name": "SeqTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ctgy_purp: Optional[CategoryPurpose1Choice] = field(
        default=None,
        metadata={
            "name": "CtgyPurp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class PostalAddress6:
    adr_tp: Optional[AddressType2Code] = field(
        default=None,
        metadata={
            "name": "AdrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dept: Optional[str] = field(
        default=None,
        metadata={
            "name": "Dept",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 70,
        },
    )
    sub_dept: Optional[str] = field(
        default=None,
        metadata={
            "name": "SubDept",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 70,
        },
    )
    strt_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "StrtNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"[A-Z]{2,2}",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "max_occurs": 7,
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class ReferredDocumentType3Choice:
    cd: Optional[DocumentType6Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class SupplementaryData1:
    plc_and_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlcAndNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )


@dataclass
class TaxAmountAndType1:
    tp: Optional[TaxAmountType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )


@dataclass
class TaxParty2:
    tax_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    regn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "RegnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    authstn: Optional[TaxAuthorisation1] = field(
        default=None,
        metadata={
            "name": "Authstn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class TaxPeriod1:
    yr: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Yr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    tp: Optional[TaxRecordPeriod1Code] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    fr_to_dt: Optional[DatePeriodDetails] = field(
        default=None,
        metadata={
            "name": "FrToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class UnderlyingPaymentInstruction3:
    orgnl_grp_inf: Optional[UnderlyingGroupInformation1] = field(
        default=None,
        metadata={
            "name": "OrgnlGrpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    orgnl_pmt_inf_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlPmtInfId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_end_to_end_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlEndToEndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_instd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "OrgnlInstdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    reqd_exctn_dt: Optional[DateAndDateTimeChoice] = field(
        default=None,
        metadata={
            "name": "ReqdExctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    reqd_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ReqdColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class UnderlyingPaymentTransaction2:
    orgnl_grp_inf: Optional[UnderlyingGroupInformation1] = field(
        default=None,
        metadata={
            "name": "OrgnlGrpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    orgnl_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_end_to_end_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlEndToEndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_intr_bk_sttlm_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlIntrBkSttlmAmt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
                "required": True,
            },
        )
    )
    orgnl_intr_bk_sttlm_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "OrgnlIntrBkSttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )


@dataclass
class UnderlyingStatementEntry1:
    orgnl_grp_inf: Optional[OriginalGroupInformation3] = field(
        default=None,
        metadata={
            "name": "OrgnlGrpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    orgnl_stmt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlStmtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    orgnl_ntry_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrgnlNtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class AccountIdentification4Choice:
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"[A-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    othr: Optional[GenericAccountIdentification1] = field(
        default=None,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class AmountType4Choice:
    instd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "InstdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    eqvt_amt: Optional[EquivalentAmount2] = field(
        default=None,
        metadata={
            "name": "EqvtAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class BranchData2:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )
    pstl_adr: Optional[PostalAddress6] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class CreditorReferenceType2:
    cd_or_prtry: Optional[CreditorReferenceType1Choice] = field(
        default=None,
        metadata={
            "name": "CdOrPrtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DocumentLineIdentification1:
    tp: Optional[DocumentLineType1] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rltd_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "RltdDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class FinancialInstitutionIdentification8:
    bicfi: Optional[str] = field(
        default=None,
        metadata={
            "name": "BICFI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    clr_sys_mmb_id: Optional[ClearingSystemMemberIdentification2] = field(
        default=None,
        metadata={
            "name": "ClrSysMmbId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )
    pstl_adr: Optional[PostalAddress6] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    othr: Optional[GenericFinancialIdentification1] = field(
        default=None,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class OrganisationIdentification8:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    othr: list[GenericOrganisationIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class PersonIdentification5:
    dt_and_plc_of_birth: Optional[DateAndPlaceOfBirth] = field(
        default=None,
        metadata={
            "name": "DtAndPlcOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    othr: list[GenericPersonIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class ReferredDocumentType4:
    cd_or_prtry: Optional[ReferredDocumentType3Choice] = field(
        default=None,
        metadata={
            "name": "CdOrPrtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class RemittanceAmount2:
    due_pybl_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "DuePyblAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dscnt_apld_amt: list[DiscountAmountAndType1] = field(
        default_factory=list,
        metadata={
            "name": "DscntApldAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    cdt_note_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CdtNoteAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    tax_amt: list[TaxAmountAndType1] = field(
        default_factory=list,
        metadata={
            "name": "TaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    adjstmnt_amt_and_rsn: list[DocumentAdjustment1] = field(
        default_factory=list,
        metadata={
            "name": "AdjstmntAmtAndRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    rmtd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RmtdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class RemittanceAmount3:
    due_pybl_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "DuePyblAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dscnt_apld_amt: list[DiscountAmountAndType1] = field(
        default_factory=list,
        metadata={
            "name": "DscntApldAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    cdt_note_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CdtNoteAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    tax_amt: list[TaxAmountAndType1] = field(
        default_factory=list,
        metadata={
            "name": "TaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    adjstmnt_amt_and_rsn: list[DocumentAdjustment1] = field(
        default_factory=list,
        metadata={
            "name": "AdjstmntAmtAndRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    rmtd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RmtdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class TaxRecordDetails1:
    prd: Optional[TaxPeriod1] = field(
        default=None,
        metadata={
            "name": "Prd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )


@dataclass
class UnderlyingTransaction3Choice:
    initn: Optional[UnderlyingPaymentInstruction3] = field(
        default=None,
        metadata={
            "name": "Initn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    intr_bk: Optional[UnderlyingPaymentTransaction2] = field(
        default=None,
        metadata={
            "name": "IntrBk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    stmt_ntry: Optional[UnderlyingStatementEntry1] = field(
        default=None,
        metadata={
            "name": "StmtNtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class BranchAndFinancialInstitutionIdentification5:
    fin_instn_id: Optional[FinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "FinInstnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    brnch_id: Optional[BranchData2] = field(
        default=None,
        metadata={
            "name": "BrnchId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class CashAccount24:
    id: Optional[AccountIdentification4Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    tp: Optional[CashAccountType2Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class CreditorReferenceInformation2:
    tp: Optional[CreditorReferenceType2] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ref",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DocumentLineInformation1:
    id: list[DocumentLineIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_occurs": 1,
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 2048,
        },
    )
    amt: Optional[RemittanceAmount3] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class Party11Choice:
    org_id: Optional[OrganisationIdentification8] = field(
        default=None,
        metadata={
            "name": "OrgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    prvt_id: Optional[PersonIdentification5] = field(
        default=None,
        metadata={
            "name": "PrvtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class TaxAmount1:
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    taxbl_base_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TaxblBaseAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ttl_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dtls: list[TaxRecordDetails1] = field(
        default_factory=list,
        metadata={
            "name": "Dtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class PartyIdentification43:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )
    pstl_adr: Optional[PostalAddress6] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    id: Optional[Party11Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ctry_of_res: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtryOfRes",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "pattern": r"[A-Z]{2,2}",
        },
    )
    ctct_dtls: Optional[ContactDetails2] = field(
        default=None,
        metadata={
            "name": "CtctDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class ReferredDocumentInformation7:
    tp: Optional[ReferredDocumentType4] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rltd_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "RltdDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    line_dtls: list[DocumentLineInformation1] = field(
        default_factory=list,
        metadata={
            "name": "LineDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class SettlementInstruction4:
    sttlm_mtd: Optional[SettlementMethod1Code] = field(
        default=None,
        metadata={
            "name": "SttlmMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    sttlm_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "SttlmAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    clr_sys: Optional[ClearingSystemIdentification3Choice] = field(
        default=None,
        metadata={
            "name": "ClrSys",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instg_rmbrsmnt_agt: Optional[
        BranchAndFinancialInstitutionIdentification5
    ] = field(
        default=None,
        metadata={
            "name": "InstgRmbrsmntAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instg_rmbrsmnt_agt_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "InstgRmbrsmntAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instd_rmbrsmnt_agt: Optional[
        BranchAndFinancialInstitutionIdentification5
    ] = field(
        default=None,
        metadata={
            "name": "InstdRmbrsmntAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instd_rmbrsmnt_agt_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "InstdRmbrsmntAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    thrd_rmbrsmnt_agt: Optional[
        BranchAndFinancialInstitutionIdentification5
    ] = field(
        default=None,
        metadata={
            "name": "ThrdRmbrsmntAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    thrd_rmbrsmnt_agt_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "ThrdRmbrsmntAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class TaxRecord1:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctgy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctgy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctgy_dtls: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtgyDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dbtr_sts: Optional[str] = field(
        default=None,
        metadata={
            "name": "DbtrSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cert_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CertId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    frms_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "FrmsCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prd: Optional[TaxPeriod1] = field(
        default=None,
        metadata={
            "name": "Prd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    tax_amt: Optional[TaxAmount1] = field(
        default=None,
        metadata={
            "name": "TaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    addtl_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class Garnishment1:
    tp: Optional[GarnishmentType1] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    grnshee: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "Grnshee",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    grnshmt_admstr: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "GrnshmtAdmstr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ref_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "RefNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    rmtd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RmtdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    fmly_mdcl_insrnc_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "FmlyMdclInsrncInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    mplyee_termntn_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "MplyeeTermntnInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class Party12Choice:
    pty: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "Pty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    agt: Optional[BranchAndFinancialInstitutionIdentification5] = field(
        default=None,
        metadata={
            "name": "Agt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class TaxInformation4:
    cdtr: Optional[TaxParty1] = field(
        default=None,
        metadata={
            "name": "Cdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dbtr: Optional[TaxParty2] = field(
        default=None,
        metadata={
            "name": "Dbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ultmt_dbtr: Optional[TaxParty2] = field(
        default=None,
        metadata={
            "name": "UltmtDbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    admstn_zone: Optional[str] = field(
        default=None,
        metadata={
            "name": "AdmstnZone",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ref_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "RefNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )
    mtd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Mtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ttl_taxbl_base_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlTaxblBaseAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ttl_tax_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlTaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    seq_nb: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "SeqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )
    rcrd: list[TaxRecord1] = field(
        default_factory=list,
        metadata={
            "name": "Rcrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class Case3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    cretr: Optional[Party12Choice] = field(
        default=None,
        metadata={
            "name": "Cretr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    reop_case_indctn: Optional[bool] = field(
        default=None,
        metadata={
            "name": "ReopCaseIndctn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class CaseAssignment3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    assgnr: Optional[Party12Choice] = field(
        default=None,
        metadata={
            "name": "Assgnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    assgne: Optional[Party12Choice] = field(
        default=None,
        metadata={
            "name": "Assgne",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    cre_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "CreDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )


@dataclass
class StructuredRemittanceInformation13:
    rfrd_doc_inf: list[ReferredDocumentInformation7] = field(
        default_factory=list,
        metadata={
            "name": "RfrdDocInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    rfrd_doc_amt: Optional[RemittanceAmount2] = field(
        default=None,
        metadata={
            "name": "RfrdDocAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    cdtr_ref_inf: Optional[CreditorReferenceInformation2] = field(
        default=None,
        metadata={
            "name": "CdtrRefInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    invcr: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "Invcr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    invcee: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "Invcee",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    tax_rmt: Optional[TaxInformation4] = field(
        default=None,
        metadata={
            "name": "TaxRmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    grnshmt_rmt: Optional[Garnishment1] = field(
        default=None,
        metadata={
            "name": "GrnshmtRmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    addtl_rmt_inf: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AddtlRmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "max_occurs": 3,
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class RemittanceInformation11:
    ustrd: list[str] = field(
        default_factory=list,
        metadata={
            "name": "Ustrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )
    strd: list[StructuredRemittanceInformation13] = field(
        default_factory=list,
        metadata={
            "name": "Strd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class PaymentComplementaryInformation6:
    instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "InstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    end_to_end_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "EndToEndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pmt_tp_inf: Optional[PaymentTypeInformation25] = field(
        default=None,
        metadata={
            "name": "PmtTpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    reqd_exctn_dt: Optional[DateAndDateTimeChoice] = field(
        default=None,
        metadata={
            "name": "ReqdExctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    reqd_colltn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ReqdColltnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    intr_bk_sttlm_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "IntrBkSttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    amt: Optional[AmountType4Choice] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    intr_bk_sttlm_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "IntrBkSttlmAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    chrg_br: Optional[ChargeBearerType1Code] = field(
        default=None,
        metadata={
            "name": "ChrgBr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ultmt_dbtr: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "UltmtDbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dbtr: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "Dbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dbtr_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "DbtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dbtr_agt: Optional[BranchAndFinancialInstitutionIdentification5] = field(
        default=None,
        metadata={
            "name": "DbtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    dbtr_agt_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "DbtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    sttlm_inf: Optional[SettlementInstruction4] = field(
        default=None,
        metadata={
            "name": "SttlmInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    intrmy_agt1: Optional[BranchAndFinancialInstitutionIdentification5] = (
        field(
            default=None,
            metadata={
                "name": "IntrmyAgt1",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            },
        )
    )
    intrmy_agt1_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "IntrmyAgt1Acct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    intrmy_agt2: Optional[BranchAndFinancialInstitutionIdentification5] = (
        field(
            default=None,
            metadata={
                "name": "IntrmyAgt2",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            },
        )
    )
    intrmy_agt2_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "IntrmyAgt2Acct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    intrmy_agt3: Optional[BranchAndFinancialInstitutionIdentification5] = (
        field(
            default=None,
            metadata={
                "name": "IntrmyAgt3",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            },
        )
    )
    intrmy_agt3_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "IntrmyAgt3Acct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    cdtr_agt: Optional[BranchAndFinancialInstitutionIdentification5] = field(
        default=None,
        metadata={
            "name": "CdtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    cdtr_agt_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "CdtrAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    cdtr: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "Cdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    cdtr_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "CdtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    ultmt_cdtr: Optional[PartyIdentification43] = field(
        default=None,
        metadata={
            "name": "UltmtCdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    purp: Optional[Purpose2Choice] = field(
        default=None,
        metadata={
            "name": "Purp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instr_for_dbtr_agt: Optional[str] = field(
        default=None,
        metadata={
            "name": "InstrForDbtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "min_length": 1,
            "max_length": 140,
        },
    )
    prvs_instg_agt: Optional[BranchAndFinancialInstitutionIdentification5] = (
        field(
            default=None,
            metadata={
                "name": "PrvsInstgAgt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            },
        )
    )
    prvs_instg_agt_acct: Optional[CashAccount24] = field(
        default=None,
        metadata={
            "name": "PrvsInstgAgtAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instr_for_nxt_agt: list[InstructionForNextAgent1] = field(
        default_factory=list,
        metadata={
            "name": "InstrForNxtAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    instr_for_cdtr_agt: list[InstructionForCreditorAgent1] = field(
        default_factory=list,
        metadata={
            "name": "InstrForCdtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )
    rmt_inf: Optional[RemittanceInformation11] = field(
        default=None,
        metadata={
            "name": "RmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class AdditionalPaymentInformationV07:
    assgnmt: Optional[CaseAssignment3] = field(
        default=None,
        metadata={
            "name": "Assgnmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    case: Optional[Case3] = field(
        default=None,
        metadata={
            "name": "Case",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    undrlyg: Optional[UnderlyingTransaction3Choice] = field(
        default=None,
        metadata={
            "name": "Undrlyg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    inf: Optional[PaymentComplementaryInformation6] = field(
        default=None,
        metadata={
            "name": "Inf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
            "required": True,
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:camt.028.001.07"

    addtl_pmt_inf: Optional[AdditionalPaymentInformationV07] = field(
        default=None,
        metadata={
            "name": "AddtlPmtInf",
            "type": "Element",
            "required": True,
        },
    )
