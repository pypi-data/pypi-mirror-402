from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime, XmlPeriod

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12"


@dataclass
class AccountSchemeName1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ActiveCurrencyAndAmount:
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
class ActiveOrHistoricCurrencyAnd13DecimalAmount:
    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "required": True,
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 13,
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
class AmountRangeBoundary1:
    bdry_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "BdryAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )
    incl: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Incl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


class AttendanceContext1Code(Enum):
    ATTD = "ATTD"
    SATT = "SATT"
    UATT = "UATT"


class AuthenticationEntity1Code(Enum):
    ICCD = "ICCD"
    AGNT = "AGNT"
    MERC = "MERC"


class AuthenticationMethod1Code(Enum):
    UKNW = "UKNW"
    BYPS = "BYPS"
    NPIN = "NPIN"
    FPIN = "FPIN"
    CPSG = "CPSG"
    PPSG = "PPSG"
    MANU = "MANU"
    MERC = "MERC"
    SCRT = "SCRT"
    SNCT = "SNCT"
    SCNL = "SCNL"


@dataclass
class BankTransactionCodeStructure6:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 4,
        },
    )
    sub_fmly_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "SubFmlyCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 4,
        },
    )


class Cscmanagement1Code(Enum):
    PRST = "PRST"
    BYPS = "BYPS"
    UNRD = "UNRD"
    NCSC = "NCSC"


class CardDataReading1Code(Enum):
    TAGC = "TAGC"
    PHYS = "PHYS"
    BRCD = "BRCD"
    MGST = "MGST"
    CICC = "CICC"
    DFLE = "DFLE"
    CTLS = "CTLS"
    ECTL = "ECTL"


class CardPaymentServiceType2Code(Enum):
    AGGR = "AGGR"
    DCCV = "DCCV"
    GRTT = "GRTT"
    INSP = "INSP"
    LOYT = "LOYT"
    NRES = "NRES"
    PUCO = "PUCO"
    RECP = "RECP"
    SOAF = "SOAF"
    UNAF = "UNAF"
    VCAU = "VCAU"


@dataclass
class CardSequenceNumberRange1:
    frst_tx: Optional[str] = field(
        default=None,
        metadata={
            "name": "FrstTx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    last_tx: Optional[str] = field(
        default=None,
        metadata={
            "name": "LastTx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


class CardholderVerificationCapability1Code(Enum):
    MNSG = "MNSG"
    NPIN = "NPIN"
    FCPN = "FCPN"
    FEPN = "FEPN"
    FDSG = "FDSG"
    FBIO = "FBIO"
    MNVR = "MNVR"
    FBIG = "FBIG"
    APKI = "APKI"
    PKIS = "PKIS"
    CHDT = "CHDT"
    SCEC = "SCEC"


@dataclass
class CashAccountType2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CashAvailabilityDate1Choice:
    nb_of_days: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfDays",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[\+]{0,1}[0-9]{1,15}",
        },
    )
    actl_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ActlDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CategoryPurpose1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 5,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


class CopyDuplicate1Code(Enum):
    CODU = "CODU"
    COPY = "COPY"
    DUPL = "DUPL"


@dataclass
class CorporateAction9:
    evt_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "EvtTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    evt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "EvtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


class CreditDebitCode(Enum):
    CRDT = "CRDT"
    DBIT = "DBIT"


@dataclass
class CreditorReferenceType2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CurrencyExchange24:
    src_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "SrcCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    trgt_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrgtCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    unit_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "UnitCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    xchg_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    ctrct_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrctId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    qtn_dt: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "QtnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    xchg_rate_base: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRateBase",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_inclusive": Decimal("1"),
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )


@dataclass
class DateAndDateTime2Choice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class DateAndPlaceOfBirth1:
    birth_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "BirthDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    prvc_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "PrvcOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    city_of_birth: Optional[str] = field(
        default=None,
        metadata={
            "name": "CityOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class DatePeriod2:
    fr_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FrDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    to_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class DateTimePeriod1:
    fr_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "FrDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    to_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "ToDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class DateType2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DocumentAmountType1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DocumentType2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class EntryStatus1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class FinancialIdentificationSchemeName1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class FinancialInstrumentQuantity1Choice:
    unit: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Unit",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    face_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )
    amtsd_val: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "AmtsdVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )


@dataclass
class GarnishmentType1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    schme_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "SchmeNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericIdentification3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericIdentification30:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    schme_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "SchmeNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class IdentificationSource3Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


class InterestType1Code(Enum):
    INDY = "INDY"
    OVRN = "OVRN"


@dataclass
class LocalInstrument2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class MessageIdentification2:
    msg_nm_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgNmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


class NamePrefix2Code(Enum):
    DOCT = "DOCT"
    MADM = "MADM"
    MISS = "MISS"
    MIST = "MIST"
    MIKS = "MIKS"


@dataclass
class NumberAndSumOfTransactions1:
    nb_of_ntries: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfNtries",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{1,15}",
        },
    )
    sum: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Sum",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )


class OnLineCapability1Code(Enum):
    OFLN = "OFLN"
    ONLN = "ONLN"
    SMON = "SMON"


@dataclass
class OrganisationIdentificationSchemeName1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class OriginalAndCurrentQuantities1:
    face_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )
    amtsd_val: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "AmtsdVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )


@dataclass
class OriginalBusinessQuery1:
    msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    msg_nm_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgNmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cre_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "CreDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class OtherContact1:
    chanl_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "ChanlTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 4,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 128,
        },
    )


class PoicomponentType1Code(Enum):
    SOFT = "SOFT"
    EMVK = "EMVK"
    EMVO = "EMVO"
    MRIT = "MRIT"
    CHIT = "CHIT"
    SECM = "SECM"
    PEDV = "PEDV"


@dataclass
class Pagination1:
    pg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[0-9]{1,5}",
        },
    )
    last_pg_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "LastPgInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


class PartyType3Code(Enum):
    OPOI = "OPOI"
    MERC = "MERC"
    ACCP = "ACCP"
    ITAG = "ITAG"
    ACQR = "ACQR"
    CISS = "CISS"
    DLIS = "DLIS"


class PartyType4Code(Enum):
    MERC = "MERC"
    ACCP = "ACCP"
    ITAG = "ITAG"
    ACQR = "ACQR"
    CISS = "CISS"
    TAXH = "TAXH"


@dataclass
class PersonIdentificationSchemeName1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


class PreferredContactMethod2Code(Enum):
    MAIL = "MAIL"
    FAXX = "FAXX"
    LETT = "LETT"
    CELL = "CELL"
    ONLI = "ONLI"
    PHON = "PHON"


class PriceValueType1Code(Enum):
    DISC = "DISC"
    PREM = "PREM"
    PARV = "PARV"


class Priority2Code(Enum):
    HIGH = "HIGH"
    NORM = "NORM"


@dataclass
class ProprietaryBankTransactionCodeStructure1:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ProprietaryQuantity1:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    qty: Optional[str] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ProprietaryReference1:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ref",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ProxyAccountType1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class Purpose2Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class RateType4Choice:
    pctg: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Pctg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    othr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


class RemittanceLocationMethod2Code(Enum):
    FAXI = "FAXI"
    EDIC = "EDIC"
    URID = "URID"
    EMAL = "EMAL"
    POST = "POST"
    SMSM = "SMSM"


@dataclass
class ReportingSource1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ReturnReason5Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class SequenceRange1:
    fr_seq: Optional[str] = field(
        default=None,
        metadata={
            "name": "FrSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    to_seq: Optional[str] = field(
        default=None,
        metadata={
            "name": "ToSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


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
class TaxAuthorisation1:
    titl: Optional[str] = field(
        default=None,
        metadata={
            "name": "Titl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    regn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "RegnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
class TechnicalInputChannel1Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class TrackData1:
    trck_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrckNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]",
        },
    )
    trck_val: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrckVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 140,
        },
    )


class TransactionChannel1Code(Enum):
    MAIL = "MAIL"
    TLPH = "TLPH"
    ECOM = "ECOM"
    TVPY = "TVPY"


class TransactionEnvironment1Code(Enum):
    MERC = "MERC"
    PRIV = "PRIV"
    PUBL = "PUBL"


@dataclass
class TransactionIdentifier1:
    tx_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "TxDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    tx_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "TxRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


class UnitOfMeasure1Code(Enum):
    PIEC = "PIEC"
    TONS = "TONS"
    FOOT = "FOOT"
    GBGA = "GBGA"
    USGA = "USGA"
    GRAM = "GRAM"
    INCH = "INCH"
    KILO = "KILO"
    PUND = "PUND"
    METR = "METR"
    CMET = "CMET"
    MMET = "MMET"
    LITR = "LITR"
    CELI = "CELI"
    MILI = "MILI"
    GBOU = "GBOU"
    USOU = "USOU"
    GBQA = "GBQA"
    USQA = "USQA"
    GBPI = "GBPI"
    USPI = "USPI"
    MILE = "MILE"
    KMET = "KMET"
    YARD = "YARD"
    SQKI = "SQKI"
    HECT = "HECT"
    ARES = "ARES"
    SMET = "SMET"
    SCMT = "SCMT"
    SMIL = "SMIL"
    SQMI = "SQMI"
    SQYA = "SQYA"
    SQFO = "SQFO"
    SQIN = "SQIN"
    ACRE = "ACRE"


class UserInterface2Code(Enum):
    MDSP = "MDSP"
    CDSP = "CDSP"


@dataclass
class AddressType3Choice:
    cd: Optional[AddressType2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class AmountAndCurrencyExchangeDetails5:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    ccy_xchg: Optional[CurrencyExchange24] = field(
        default=None,
        metadata={
            "name": "CcyXchg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class AmountAndCurrencyExchangeDetails6:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    ccy_xchg: Optional[CurrencyExchange24] = field(
        default=None,
        metadata={
            "name": "CcyXchg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class AmountAndDirection35:
    amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class BankTransactionCodeStructure5:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 4,
        },
    )
    fmly: Optional[BankTransactionCodeStructure6] = field(
        default=None,
        metadata={
            "name": "Fmly",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class BatchInformation2:
    msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pmt_inf_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PmtInfId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    nb_of_txs: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfTxs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{1,15}",
        },
    )
    ttl_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CardSecurityInformation1:
    cscmgmt: Optional[Cscmanagement1Code] = field(
        default=None,
        metadata={
            "name": "CSCMgmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    cscval: Optional[str] = field(
        default=None,
        metadata={
            "name": "CSCVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{3,4}",
        },
    )


@dataclass
class CardholderAuthentication2:
    authntcn_mtd: Optional[AuthenticationMethod1Code] = field(
        default=None,
        metadata={
            "name": "AuthntcnMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    authntcn_ntty: Optional[AuthenticationEntity1Code] = field(
        default=None,
        metadata={
            "name": "AuthntcnNtty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class CashAvailability1:
    dt: Optional[CashAvailabilityDate1Choice] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class CashDeposit1:
    note_dnmtn: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "NoteDnmtn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    nb_of_notes: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfNotes",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[0-9]{1,15}",
        },
    )
    amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class ChargeType3Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[GenericIdentification3] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class ClearingSystemMemberIdentification2:
    clr_sys_id: Optional[ClearingSystemIdentification2Choice] = field(
        default=None,
        metadata={
            "name": "ClrSysId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    mmb_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MmbId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class Contact13:
    nm_prfx: Optional[NamePrefix2Code] = field(
        default=None,
        metadata={
            "name": "NmPrfx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    phne_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PhneNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"\+[0-9]{1,3}-[0-9()+\-]{1,30}",
        },
    )
    mob_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "MobNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"\+[0-9]{1,3}-[0-9()+\-]{1,30}",
        },
    )
    fax_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "FaxNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"\+[0-9]{1,3}-[0-9()+\-]{1,30}",
        },
    )
    urladr: Optional[str] = field(
        default=None,
        metadata={
            "name": "URLAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 2048,
        },
    )
    email_adr: Optional[str] = field(
        default=None,
        metadata={
            "name": "EmailAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 256,
        },
    )
    email_purp: Optional[str] = field(
        default=None,
        metadata={
            "name": "EmailPurp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    job_titl: Optional[str] = field(
        default=None,
        metadata={
            "name": "JobTitl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rspnsblty: Optional[str] = field(
        default=None,
        metadata={
            "name": "Rspnsblty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dept: Optional[str] = field(
        default=None,
        metadata={
            "name": "Dept",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )
    othr: list[OtherContact1] = field(
        default_factory=list,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prefrd_mtd: Optional[PreferredContactMethod2Code] = field(
        default=None,
        metadata={
            "name": "PrefrdMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CreditorReferenceType3:
    cd_or_prtry: Optional[CreditorReferenceType2Choice] = field(
        default=None,
        metadata={
            "name": "CdOrPrtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DateAndType1:
    tp: Optional[DateType2Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class DateOrDateTimePeriod1Choice:
    dt: Optional[DatePeriod2] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dt_tm: Optional[DateTimePeriod1] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class DisplayCapabilities1:
    disp_tp: Optional[UserInterface2Code] = field(
        default=None,
        metadata={
            "name": "DispTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    nb_of_lines: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfLines",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[0-9]{1,3}",
        },
    )
    line_width: Optional[str] = field(
        default=None,
        metadata={
            "name": "LineWidth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[0-9]{1,3}",
        },
    )


@dataclass
class DocumentAdjustment1:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    addtl_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class DocumentAmount1:
    tp: Optional[DocumentAmountType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class DocumentLineType1:
    cd_or_prtry: Optional[DocumentLineType1Choice] = field(
        default=None,
        metadata={
            "name": "CdOrPrtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DocumentType1:
    cd_or_prtry: Optional[DocumentType2Choice] = field(
        default=None,
        metadata={
            "name": "CdOrPrtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class FromToAmountRange1:
    fr_amt: Optional[AmountRangeBoundary1] = field(
        default=None,
        metadata={
            "name": "FrAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    to_amt: Optional[AmountRangeBoundary1] = field(
        default=None,
        metadata={
            "name": "ToAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class GarnishmentType1:
    cd_or_prtry: Optional[GarnishmentType1Choice] = field(
        default=None,
        metadata={
            "name": "CdOrPrtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericIdentification32:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    tp: Optional[PartyType3Code] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    issr: Optional[PartyType4Code] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    shrt_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "ShrtNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericOrganisationIdentification3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        },
    )
    schme_nm: Optional[OrganisationIdentificationSchemeName1Choice] = field(
        default=None,
        metadata={
            "name": "SchmeNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericPersonIdentification2:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 256,
        },
    )
    schme_nm: Optional[PersonIdentificationSchemeName1Choice] = field(
        default=None,
        metadata={
            "name": "SchmeNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class InterestType1Choice:
    cd: Optional[InterestType1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class OtherIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    sfx: Optional[str] = field(
        default=None,
        metadata={
            "name": "Sfx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 16,
        },
    )
    tp: Optional[IdentificationSource3Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class PaymentTypeInformation27:
    instr_prty: Optional[Priority2Code] = field(
        default=None,
        metadata={
            "name": "InstrPrty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    clr_chanl: Optional[ClearingChannel2Code] = field(
        default=None,
        metadata={
            "name": "ClrChanl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    svc_lvl: list[ServiceLevel8Choice] = field(
        default_factory=list,
        metadata={
            "name": "SvcLvl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    lcl_instrm: Optional[LocalInstrument2Choice] = field(
        default=None,
        metadata={
            "name": "LclInstrm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    seq_tp: Optional[SequenceType3Code] = field(
        default=None,
        metadata={
            "name": "SeqTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ctgy_purp: Optional[CategoryPurpose1Choice] = field(
        default=None,
        metadata={
            "name": "CtgyPurp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class PointOfInteractionComponent1:
    poicmpnt_tp: Optional[PoicomponentType1Code] = field(
        default=None,
        metadata={
            "name": "POICmpntTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    manfctr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ManfctrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    mdl: Optional[str] = field(
        default=None,
        metadata={
            "name": "Mdl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    vrsn_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "VrsnNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 16,
        },
    )
    srl_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "SrlNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    apprvl_nb: list[str] = field(
        default_factory=list,
        metadata={
            "name": "ApprvlNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class PriceRateOrAmount3Choice:
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAnd13DecimalAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class Product2:
    pdct_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PdctCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 70,
        },
    )
    unit_of_measr: Optional[UnitOfMeasure1Code] = field(
        default=None,
        metadata={
            "name": "UnitOfMeasr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    pdct_qty: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "PdctQty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    unit_pric: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "UnitPric",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )
    pdct_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "PdctAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )
    tax_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    addtl_pdct_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlPdctInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class ProprietaryDate3:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class ProprietaryPrice2:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    pric: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Pric",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class ProxyAccountIdentification1:
    tp: Optional[ProxyAccountType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 2048,
        },
    )


@dataclass
class SecuritiesAccount19:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    tp: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class SequenceRange1Choice:
    fr_seq: Optional[str] = field(
        default=None,
        metadata={
            "name": "FrSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    to_seq: Optional[str] = field(
        default=None,
        metadata={
            "name": "ToSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    fr_to_seq: list[SequenceRange1] = field(
        default_factory=list,
        metadata={
            "name": "FrToSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    eqseq: list[str] = field(
        default_factory=list,
        metadata={
            "name": "EQSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    neqseq: list[str] = field(
        default_factory=list,
        metadata={
            "name": "NEQSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class TaxCharges2:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TaxParty2:
    tax_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    regn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "RegnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax_tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "TaxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    authstn: Optional[TaxAuthorisation1] = field(
        default=None,
        metadata={
            "name": "Authstn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TaxPeriod3:
    yr: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "Yr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tp: Optional[TaxRecordPeriod1Code] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    fr_to_dt: Optional[DatePeriod2] = field(
        default=None,
        metadata={
            "name": "FrToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TransactionQuantities3Choice:
    qty: Optional[FinancialInstrumentQuantity1Choice] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    orgnl_and_cur_face_amt: Optional[OriginalAndCurrentQuantities1] = field(
        default=None,
        metadata={
            "name": "OrgnlAndCurFaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry: Optional[ProprietaryQuantity1] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TransactionReferences6:
    msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    acct_svcr_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "AcctSvcrRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pmt_inf_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PmtInfId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "InstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    end_to_end_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "EndToEndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    uetr: Optional[str] = field(
        default=None,
        metadata={
            "name": "UETR",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}",
        },
    )
    tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    mndt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MndtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    chq_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "ChqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    clr_sys_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClrSysRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    acct_ownr_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AcctOwnrTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    acct_svcr_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AcctSvcrTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    mkt_infrstrctr_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MktInfrstrctrTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prcg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PrcgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prtry: list[ProprietaryReference1] = field(
        default_factory=list,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class YieldedOrValueType1Choice:
    yldd: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Yldd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    val_tp: Optional[PriceValueType1Code] = field(
        default=None,
        metadata={
            "name": "ValTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class AccountIdentification4Choice:
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    othr: Optional[GenericAccountIdentification1] = field(
        default=None,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class AmountAndCurrencyExchange4:
    instd_amt: Optional[AmountAndCurrencyExchangeDetails5] = field(
        default=None,
        metadata={
            "name": "InstdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx_amt: Optional[AmountAndCurrencyExchangeDetails5] = field(
        default=None,
        metadata={
            "name": "TxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cntr_val_amt: Optional[AmountAndCurrencyExchangeDetails5] = field(
        default=None,
        metadata={
            "name": "CntrValAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    anncd_pstng_amt: Optional[AmountAndCurrencyExchangeDetails5] = field(
        default=None,
        metadata={
            "name": "AnncdPstngAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry_amt: list[AmountAndCurrencyExchangeDetails6] = field(
        default_factory=list,
        metadata={
            "name": "PrtryAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class BankTransactionCodeStructure4:
    domn: Optional[BankTransactionCodeStructure5] = field(
        default=None,
        metadata={
            "name": "Domn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry: Optional[ProprietaryBankTransactionCodeStructure1] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CardAggregated2:
    addtl_svc: Optional[CardPaymentServiceType2Code] = field(
        default=None,
        metadata={
            "name": "AddtlSvc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx_ctgy: Optional[str] = field(
        default=None,
        metadata={
            "name": "TxCtgy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    sale_rcncltn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SaleRcncltnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    seq_nb_rg: Optional[CardSequenceNumberRange1] = field(
        default=None,
        metadata={
            "name": "SeqNbRg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx_dt_rg: Optional[DateOrDateTimePeriod1Choice] = field(
        default=None,
        metadata={
            "name": "TxDtRg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CreditorReferenceInformation3:
    tp: Optional[CreditorReferenceType3] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ref",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rltd_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "RltdDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class ImpliedCurrencyAmountRange1Choice:
    fr_amt: Optional[AmountRangeBoundary1] = field(
        default=None,
        metadata={
            "name": "FrAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    to_amt: Optional[AmountRangeBoundary1] = field(
        default=None,
        metadata={
            "name": "ToAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    fr_to_amt: Optional[FromToAmountRange1] = field(
        default=None,
        metadata={
            "name": "FrToAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    eqamt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "EQAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )
    neqamt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "NEQAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )


@dataclass
class NumberAndSumOfTransactions4:
    nb_of_ntries: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfNtries",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{1,15}",
        },
    )
    sum: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Sum",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    ttl_net_ntry: Optional[AmountAndDirection35] = field(
        default=None,
        metadata={
            "name": "TtlNetNtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class OrganisationIdentification39:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    othr: list[GenericOrganisationIdentification3] = field(
        default_factory=list,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class PaymentContext3:
    card_pres: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CardPres",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    crdhldr_pres: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CrdhldrPres",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    on_line_cntxt: Optional[bool] = field(
        default=None,
        metadata={
            "name": "OnLineCntxt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    attndnc_cntxt: Optional[AttendanceContext1Code] = field(
        default=None,
        metadata={
            "name": "AttndncCntxt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx_envt: Optional[TransactionEnvironment1Code] = field(
        default=None,
        metadata={
            "name": "TxEnvt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx_chanl: Optional[TransactionChannel1Code] = field(
        default=None,
        metadata={
            "name": "TxChanl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    attndnt_msg_cpbl: Optional[bool] = field(
        default=None,
        metadata={
            "name": "AttndntMsgCpbl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    attndnt_lang: Optional[str] = field(
        default=None,
        metadata={
            "name": "AttndntLang",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[a-z]{2,2}",
        },
    )
    card_data_ntry_md: Optional[CardDataReading1Code] = field(
        default=None,
        metadata={
            "name": "CardDataNtryMd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    fllbck_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "FllbckInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    authntcn_mtd: Optional[CardholderAuthentication2] = field(
        default=None,
        metadata={
            "name": "AuthntcnMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class PersonIdentification18:
    dt_and_plc_of_birth: Optional[DateAndPlaceOfBirth1] = field(
        default=None,
        metadata={
            "name": "DtAndPlcOfBirth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    othr: list[GenericPersonIdentification2] = field(
        default_factory=list,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class PlainCardData1:
    pan: Optional[str] = field(
        default=None,
        metadata={
            "name": "PAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[0-9]{8,28}",
        },
    )
    card_seq_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "CardSeqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{2,3}",
        },
    )
    fctv_dt: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "FctvDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    xpry_dt: Optional[XmlPeriod] = field(
        default=None,
        metadata={
            "name": "XpryDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    svc_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "SvcCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{3}",
        },
    )
    trck_data: list[TrackData1] = field(
        default_factory=list,
        metadata={
            "name": "TrckData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    card_scty_cd: Optional[CardSecurityInformation1] = field(
        default=None,
        metadata={
            "name": "CardSctyCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class PointOfInteractionCapabilities1:
    card_rdng_cpblties: list[CardDataReading1Code] = field(
        default_factory=list,
        metadata={
            "name": "CardRdngCpblties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    crdhldr_vrfctn_cpblties: list[CardholderVerificationCapability1Code] = (
        field(
            default_factory=list,
            metadata={
                "name": "CrdhldrVrfctnCpblties",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            },
        )
    )
    on_line_cpblties: Optional[OnLineCapability1Code] = field(
        default=None,
        metadata={
            "name": "OnLineCpblties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    disp_cpblties: list[DisplayCapabilities1] = field(
        default_factory=list,
        metadata={
            "name": "DispCpblties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prt_line_width: Optional[str] = field(
        default=None,
        metadata={
            "name": "PrtLineWidth",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{1,3}",
        },
    )


@dataclass
class PostalAddress27:
    adr_tp: Optional[AddressType3Choice] = field(
        default=None,
        metadata={
            "name": "AdrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    care_of: Optional[str] = field(
        default=None,
        metadata={
            "name": "CareOf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    dept: Optional[str] = field(
        default=None,
        metadata={
            "name": "Dept",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )
    sub_dept: Optional[str] = field(
        default=None,
        metadata={
            "name": "SubDept",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )
    strt_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "StrtNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 16,
        },
    )
    bldg_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    flr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Flr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )
    unit_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "UnitNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_bx: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstBx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 16,
        },
    )
    room: Optional[str] = field(
        default=None,
        metadata={
            "name": "Room",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    twn_lctn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnLctnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    dstrct_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "DstrctNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z]{2,2}",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "max_occurs": 7,
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class Price7:
    tp: Optional[YieldedOrValueType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    val: Optional[PriceRateOrAmount3Choice] = field(
        default=None,
        metadata={
            "name": "Val",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class RemittanceAmount4:
    rmt_amt_and_tp: list[DocumentAmount1] = field(
        default_factory=list,
        metadata={
            "name": "RmtAmtAndTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    adjstmnt_amt_and_rsn: list[DocumentAdjustment1] = field(
        default_factory=list,
        metadata={
            "name": "AdjstmntAmtAndRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class SecurityIdentification19:
    isin: Optional[str] = field(
        default=None,
        metadata={
            "name": "ISIN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z]{2,2}[A-Z0-9]{9,9}[0-9]{1,1}",
        },
    )
    othr_id: list[OtherIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "OthrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class TaxRecordDetails3:
    prd: Optional[TaxPeriod3] = field(
        default=None,
        metadata={
            "name": "Prd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class TransactionDates3:
    accptnc_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "AccptncDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    trad_actvty_ctrctl_sttlm_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "TradActvtyCtrctlSttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    trad_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "TradDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    intr_bk_sttlm_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "IntrBkSttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    start_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "StartDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    end_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "EndDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "TxDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry: list[ProprietaryDate3] = field(
        default_factory=list,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class ActiveOrHistoricCurrencyAndAmountRange2:
    amt: Optional[ImpliedCurrencyAmountRange1Choice] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )


@dataclass
class BranchData5:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    pstl_adr: Optional[PostalAddress27] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CardIndividualTransaction2:
    iccrltd_data: Optional[str] = field(
        default=None,
        metadata={
            "name": "ICCRltdData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 1025,
        },
    )
    pmt_cntxt: Optional[PaymentContext3] = field(
        default=None,
        metadata={
            "name": "PmtCntxt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_svc: Optional[CardPaymentServiceType2Code] = field(
        default=None,
        metadata={
            "name": "AddtlSvc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx_ctgy: Optional[str] = field(
        default=None,
        metadata={
            "name": "TxCtgy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    sale_rcncltn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SaleRcncltnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    sale_ref_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "SaleRefNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    re_presntmnt_rsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "RePresntmntRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 4,
        },
    )
    seq_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "SeqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tx_id: Optional[TransactionIdentifier1] = field(
        default=None,
        metadata={
            "name": "TxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    pdct: Optional[Product2] = field(
        default=None,
        metadata={
            "name": "Pdct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    vldtn_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "VldtnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    vldtn_seq_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "VldtnSeqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CashAccount40:
    id: Optional[AccountIdentification4Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tp: Optional[CashAccountType2Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )
    prxy: Optional[ProxyAccountIdentification1] = field(
        default=None,
        metadata={
            "name": "Prxy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class DocumentLineInformation2:
    id: list[DocumentLineIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_occurs": 1,
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 2048,
        },
    )
    amt: Optional[RemittanceAmount4] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class FinancialInstitutionIdentification23:
    bicfi: Optional[str] = field(
        default=None,
        metadata={
            "name": "BICFI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )
    clr_sys_mmb_id: Optional[ClearingSystemMemberIdentification2] = field(
        default=None,
        metadata={
            "name": "ClrSysMmbId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    pstl_adr: Optional[PostalAddress27] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    othr: Optional[GenericFinancialIdentification1] = field(
        default=None,
        metadata={
            "name": "Othr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class NameAndAddress18:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 140,
        },
    )
    adr: Optional[PostalAddress27] = field(
        default=None,
        metadata={
            "name": "Adr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class Party52Choice:
    org_id: Optional[OrganisationIdentification39] = field(
        default=None,
        metadata={
            "name": "OrgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prvt_id: Optional[PersonIdentification18] = field(
        default=None,
        metadata={
            "name": "PrvtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class PaymentCard4:
    plain_card_data: Optional[PlainCardData1] = field(
        default=None,
        metadata={
            "name": "PlainCardData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    card_ctry_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "CardCtryCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{3}",
        },
    )
    card_brnd: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "CardBrnd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_card_data: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlCardData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class PointOfInteraction1:
    id: Optional[GenericIdentification32] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    sys_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "SysNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )
    grp_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "GrpId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cpblties: Optional[PointOfInteractionCapabilities1] = field(
        default=None,
        metadata={
            "name": "Cpblties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cmpnt: list[PointOfInteractionComponent1] = field(
        default_factory=list,
        metadata={
            "name": "Cmpnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TaxAmount3:
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    taxbl_base_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TaxblBaseAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ttl_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dtls: list[TaxRecordDetails3] = field(
        default_factory=list,
        metadata={
            "name": "Dtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TotalsPerBankTransactionCode5:
    nb_of_ntries: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfNtries",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[0-9]{1,15}",
        },
    )
    sum: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Sum",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    ttl_net_ntry: Optional[AmountAndDirection35] = field(
        default=None,
        metadata={
            "name": "TtlNetNtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cdt_ntries: Optional[NumberAndSumOfTransactions1] = field(
        default=None,
        metadata={
            "name": "CdtNtries",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dbt_ntries: Optional[NumberAndSumOfTransactions1] = field(
        default=None,
        metadata={
            "name": "DbtNtries",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    fcst_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "FcstInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    bk_tx_cd: Optional[BankTransactionCodeStructure4] = field(
        default=None,
        metadata={
            "name": "BkTxCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    avlbty: list[CashAvailability1] = field(
        default_factory=list,
        metadata={
            "name": "Avlbty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TransactionPrice4Choice:
    deal_pric: Optional[Price7] = field(
        default=None,
        metadata={
            "name": "DealPric",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry: list[ProprietaryPrice2] = field(
        default_factory=list,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class BranchAndFinancialInstitutionIdentification8:
    fin_instn_id: Optional[FinancialInstitutionIdentification23] = field(
        default=None,
        metadata={
            "name": "FinInstnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    brnch_id: Optional[BranchData5] = field(
        default=None,
        metadata={
            "name": "BrnchId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CardEntry5:
    card: Optional[PaymentCard4] = field(
        default=None,
        metadata={
            "name": "Card",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    poi: Optional[PointOfInteraction1] = field(
        default=None,
        metadata={
            "name": "POI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    aggtd_ntry: Optional[CardAggregated2] = field(
        default=None,
        metadata={
            "name": "AggtdNtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    pre_pd_acct: Optional[CashAccount40] = field(
        default=None,
        metadata={
            "name": "PrePdAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CardTransaction3Choice:
    aggtd: Optional[CardAggregated2] = field(
        default=None,
        metadata={
            "name": "Aggtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    indv: Optional[CardIndividualTransaction2] = field(
        default=None,
        metadata={
            "name": "Indv",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class PartyIdentification272:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    pstl_adr: Optional[PostalAddress27] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    id: Optional[Party52Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ctry_of_res: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtryOfRes",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z]{2,2}",
        },
    )
    ctct_dtls: Optional[Contact13] = field(
        default=None,
        metadata={
            "name": "CtctDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class Rate4:
    tp: Optional[RateType4Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    vldty_rg: Optional[ActiveOrHistoricCurrencyAndAmountRange2] = field(
        default=None,
        metadata={
            "name": "VldtyRg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class ReferredDocumentInformation8:
    tp: Optional[DocumentType1] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rltd_dt: Optional[DateAndType1] = field(
        default=None,
        metadata={
            "name": "RltdDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    line_dtls: list[DocumentLineInformation2] = field(
        default_factory=list,
        metadata={
            "name": "LineDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class RemittanceLocationData2:
    mtd: Optional[RemittanceLocationMethod2Code] = field(
        default=None,
        metadata={
            "name": "Mtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    elctrnc_adr: Optional[str] = field(
        default=None,
        metadata={
            "name": "ElctrncAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 2048,
        },
    )
    pstl_adr: Optional[NameAndAddress18] = field(
        default=None,
        metadata={
            "name": "PstlAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TaxRecord3:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctgy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctgy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctgy_dtls: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtgyDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dbtr_sts: Optional[str] = field(
        default=None,
        metadata={
            "name": "DbtrSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cert_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CertId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    frms_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "FrmsCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    prd: Optional[TaxPeriod3] = field(
        default=None,
        metadata={
            "name": "Prd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tax_amt: Optional[TaxAmount3] = field(
        default=None,
        metadata={
            "name": "TaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class TotalTransactions6:
    ttl_ntries: Optional[NumberAndSumOfTransactions4] = field(
        default=None,
        metadata={
            "name": "TtlNtries",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ttl_cdt_ntries: Optional[NumberAndSumOfTransactions1] = field(
        default=None,
        metadata={
            "name": "TtlCdtNtries",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ttl_dbt_ntries: Optional[NumberAndSumOfTransactions1] = field(
        default=None,
        metadata={
            "name": "TtlDbtNtries",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ttl_ntries_per_bk_tx_cd: list[TotalsPerBankTransactionCode5] = field(
        default_factory=list,
        metadata={
            "name": "TtlNtriesPerBkTxCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class AccountInterest4:
    tp: Optional[InterestType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rate: list[Rate4] = field(
        default_factory=list,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    fr_to_dt: Optional[DateTimePeriod1] = field(
        default=None,
        metadata={
            "name": "FrToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax: Optional[TaxCharges2] = field(
        default=None,
        metadata={
            "name": "Tax",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CardTransaction18:
    card: Optional[PaymentCard4] = field(
        default=None,
        metadata={
            "name": "Card",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    poi: Optional[PointOfInteraction1] = field(
        default=None,
        metadata={
            "name": "POI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx: Optional[CardTransaction3Choice] = field(
        default=None,
        metadata={
            "name": "Tx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    pre_pd_acct: Optional[CashAccount40] = field(
        default=None,
        metadata={
            "name": "PrePdAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class CashAccount43:
    id: Optional[AccountIdentification4Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tp: Optional[CashAccountType2Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 70,
        },
    )
    prxy: Optional[ProxyAccountIdentification1] = field(
        default=None,
        metadata={
            "name": "Prxy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ownr: Optional[PartyIdentification272] = field(
        default=None,
        metadata={
            "name": "Ownr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    svcr: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "Svcr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class ChargesRecord8:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    chrg_incl_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "ChrgInclInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tp: Optional[ChargeType3Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    br: Optional[ChargeBearerType1Code] = field(
        default=None,
        metadata={
            "name": "Br",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "Agt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tax: Optional[TaxCharges2] = field(
        default=None,
        metadata={
            "name": "Tax",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class Garnishment4:
    tp: Optional[GarnishmentType1] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    grnshee: Optional[PartyIdentification272] = field(
        default=None,
        metadata={
            "name": "Grnshee",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    grnshmt_admstr: Optional[PartyIdentification272] = field(
        default=None,
        metadata={
            "name": "GrnshmtAdmstr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ref_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "RefNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rmtd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RmtdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    fmly_mdcl_insrnc_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "FmlyMdclInsrncInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    mplyee_termntn_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "MplyeeTermntnInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class GroupHeader116:
    msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    msg_rcpt: Optional[PartyIdentification272] = field(
        default=None,
        metadata={
            "name": "MsgRcpt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    msg_pgntn: Optional[Pagination1] = field(
        default=None,
        metadata={
            "name": "MsgPgntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    orgnl_biz_qry: Optional[OriginalBusinessQuery1] = field(
        default=None,
        metadata={
            "name": "OrgnlBizQry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 500,
        },
    )


@dataclass
class InterestRecord2:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    tp: Optional[InterestType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rate: Optional[Rate4] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    fr_to_dt: Optional[DateTimePeriod1] = field(
        default=None,
        metadata={
            "name": "FrToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    tax: Optional[TaxCharges2] = field(
        default=None,
        metadata={
            "name": "Tax",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class Party50Choice:
    pty: Optional[PartyIdentification272] = field(
        default=None,
        metadata={
            "name": "Pty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "Agt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class PaymentReturnReason8:
    orgnl_bk_tx_cd: Optional[BankTransactionCodeStructure4] = field(
        default=None,
        metadata={
            "name": "OrgnlBkTxCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    orgtr: Optional[PartyIdentification272] = field(
        default=None,
        metadata={
            "name": "Orgtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rsn: Optional[ReturnReason5Choice] = field(
        default=None,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_inf: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AddtlInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 105,
        },
    )


@dataclass
class ProprietaryAgent5:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "Agt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class RemittanceLocation8:
    rmt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "RmtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    rmt_lctn_dtls: list[RemittanceLocationData2] = field(
        default_factory=list,
        metadata={
            "name": "RmtLctnDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TaxData1:
    cdtr: Optional[TaxParty1] = field(
        default=None,
        metadata={
            "name": "Cdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dbtr: Optional[TaxParty2] = field(
        default=None,
        metadata={
            "name": "Dbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ultmt_dbtr: Optional[TaxParty2] = field(
        default=None,
        metadata={
            "name": "UltmtDbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    admstn_zone: Optional[str] = field(
        default=None,
        metadata={
            "name": "AdmstnZone",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ref_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "RefNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    mtd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Mtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ttl_taxbl_base_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlTaxblBaseAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ttl_tax_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlTaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    seq_nb: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "SeqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )
    rcrd: list[TaxRecord3] = field(
        default_factory=list,
        metadata={
            "name": "Rcrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class Charges15:
    ttl_chrgs_and_tax_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlChrgsAndTaxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rcrd: list[ChargesRecord8] = field(
        default_factory=list,
        metadata={
            "name": "Rcrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class ProprietaryParty6:
    tp: Optional[str] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    pty: Optional[Party50Choice] = field(
        default=None,
        metadata={
            "name": "Pty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )


@dataclass
class StructuredRemittanceInformation18:
    rfrd_doc_inf: list[ReferredDocumentInformation8] = field(
        default_factory=list,
        metadata={
            "name": "RfrdDocInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rfrd_doc_amt: Optional[RemittanceAmount4] = field(
        default=None,
        metadata={
            "name": "RfrdDocAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cdtr_ref_inf: Optional[CreditorReferenceInformation3] = field(
        default=None,
        metadata={
            "name": "CdtrRefInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    invcr: Optional[PartyIdentification272] = field(
        default=None,
        metadata={
            "name": "Invcr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    invcee: Optional[PartyIdentification272] = field(
        default=None,
        metadata={
            "name": "Invcee",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tax_rmt: Optional[TaxData1] = field(
        default=None,
        metadata={
            "name": "TaxRmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    grnshmt_rmt: Optional[Garnishment4] = field(
        default=None,
        metadata={
            "name": "GrnshmtRmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_rmt_inf: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AddtlRmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "max_occurs": 3,
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class TransactionAgents6:
    instg_agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "InstgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    instd_agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "InstdAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dbtr_agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "DbtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cdtr_agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "CdtrAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    intrmy_agt1: Optional[BranchAndFinancialInstitutionIdentification8] = (
        field(
            default=None,
            metadata={
                "name": "IntrmyAgt1",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            },
        )
    )
    intrmy_agt2: Optional[BranchAndFinancialInstitutionIdentification8] = (
        field(
            default=None,
            metadata={
                "name": "IntrmyAgt2",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            },
        )
    )
    intrmy_agt3: Optional[BranchAndFinancialInstitutionIdentification8] = (
        field(
            default=None,
            metadata={
                "name": "IntrmyAgt3",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            },
        )
    )
    rcvg_agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "RcvgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dlvrg_agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "DlvrgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    issg_agt: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "IssgAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    sttlm_plc: Optional[BranchAndFinancialInstitutionIdentification8] = field(
        default=None,
        metadata={
            "name": "SttlmPlc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry: list[ProprietaryAgent5] = field(
        default_factory=list,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TransactionInterest4:
    ttl_intrst_and_tax_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "TtlIntrstAndTaxAmt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            },
        )
    )
    rcrd: list[InterestRecord2] = field(
        default_factory=list,
        metadata={
            "name": "Rcrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class RemittanceInformation22:
    ustrd: list[str] = field(
        default_factory=list,
        metadata={
            "name": "Ustrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 140,
        },
    )
    strd: list[StructuredRemittanceInformation18] = field(
        default_factory=list,
        metadata={
            "name": "Strd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class TransactionParties12:
    initg_pty: Optional[Party50Choice] = field(
        default=None,
        metadata={
            "name": "InitgPty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dbtr: Optional[Party50Choice] = field(
        default=None,
        metadata={
            "name": "Dbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    dbtr_acct: Optional[CashAccount40] = field(
        default=None,
        metadata={
            "name": "DbtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ultmt_dbtr: Optional[Party50Choice] = field(
        default=None,
        metadata={
            "name": "UltmtDbtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cdtr: Optional[Party50Choice] = field(
        default=None,
        metadata={
            "name": "Cdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cdtr_acct: Optional[CashAccount40] = field(
        default=None,
        metadata={
            "name": "CdtrAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ultmt_cdtr: Optional[Party50Choice] = field(
        default=None,
        metadata={
            "name": "UltmtCdtr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tradg_pty: Optional[Party50Choice] = field(
        default=None,
        metadata={
            "name": "TradgPty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    prtry: list[ProprietaryParty6] = field(
        default_factory=list,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class EntryTransaction14:
    refs: Optional[TransactionReferences6] = field(
        default=None,
        metadata={
            "name": "Refs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    amt_dtls: Optional[AmountAndCurrencyExchange4] = field(
        default=None,
        metadata={
            "name": "AmtDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    avlbty: list[CashAvailability1] = field(
        default_factory=list,
        metadata={
            "name": "Avlbty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    bk_tx_cd: Optional[BankTransactionCodeStructure4] = field(
        default=None,
        metadata={
            "name": "BkTxCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    chrgs: Optional[Charges15] = field(
        default=None,
        metadata={
            "name": "Chrgs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    intrst: Optional[TransactionInterest4] = field(
        default=None,
        metadata={
            "name": "Intrst",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rltd_pties: Optional[TransactionParties12] = field(
        default=None,
        metadata={
            "name": "RltdPties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rltd_agts: Optional[TransactionAgents6] = field(
        default=None,
        metadata={
            "name": "RltdAgts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    lcl_instrm: Optional[LocalInstrument2Choice] = field(
        default=None,
        metadata={
            "name": "LclInstrm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    pmt_tp_inf: Optional[PaymentTypeInformation27] = field(
        default=None,
        metadata={
            "name": "PmtTpInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    purp: Optional[Purpose2Choice] = field(
        default=None,
        metadata={
            "name": "Purp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rltd_rmt_inf: list[RemittanceLocation8] = field(
        default_factory=list,
        metadata={
            "name": "RltdRmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "max_occurs": 10,
        },
    )
    rmt_inf: Optional[RemittanceInformation22] = field(
        default=None,
        metadata={
            "name": "RmtInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rltd_dts: Optional[TransactionDates3] = field(
        default=None,
        metadata={
            "name": "RltdDts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rltd_pric: Optional[TransactionPrice4Choice] = field(
        default=None,
        metadata={
            "name": "RltdPric",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rltd_qties: list[TransactionQuantities3Choice] = field(
        default_factory=list,
        metadata={
            "name": "RltdQties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    fin_instrm_id: Optional[SecurityIdentification19] = field(
        default=None,
        metadata={
            "name": "FinInstrmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tax: Optional[TaxData1] = field(
        default=None,
        metadata={
            "name": "Tax",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rtr_inf: Optional[PaymentReturnReason8] = field(
        default=None,
        metadata={
            "name": "RtrInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    corp_actn: Optional[CorporateAction9] = field(
        default=None,
        metadata={
            "name": "CorpActn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    csh_dpst: list[CashDeposit1] = field(
        default_factory=list,
        metadata={
            "name": "CshDpst",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    card_tx: Optional[CardTransaction18] = field(
        default=None,
        metadata={
            "name": "CardTx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_tx_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlTxInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 500,
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class EntryDetails13:
    btch: Optional[BatchInformation2] = field(
        default=None,
        metadata={
            "name": "Btch",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tx_dtls: list[EntryTransaction14] = field(
        default_factory=list,
        metadata={
            "name": "TxDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class ReportEntry14:
    ntry_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "NtryRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    rvsl_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "RvslInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    sts: Optional[EntryStatus1Choice] = field(
        default=None,
        metadata={
            "name": "Sts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    bookg_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "BookgDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    val_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "ValDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    acct_svcr_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "AcctSvcrRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 35,
        },
    )
    avlbty: list[CashAvailability1] = field(
        default_factory=list,
        metadata={
            "name": "Avlbty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    bk_tx_cd: Optional[BankTransactionCodeStructure4] = field(
        default=None,
        metadata={
            "name": "BkTxCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    comssn_wvr_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "ComssnWvrInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_inf_ind: Optional[MessageIdentification2] = field(
        default=None,
        metadata={
            "name": "AddtlInfInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    amt_dtls: Optional[AmountAndCurrencyExchange4] = field(
        default=None,
        metadata={
            "name": "AmtDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    chrgs: Optional[Charges15] = field(
        default=None,
        metadata={
            "name": "Chrgs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    tech_inpt_chanl: Optional[TechnicalInputChannel1Choice] = field(
        default=None,
        metadata={
            "name": "TechInptChanl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    intrst: Optional[TransactionInterest4] = field(
        default=None,
        metadata={
            "name": "Intrst",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    card_tx: Optional[CardEntry5] = field(
        default=None,
        metadata={
            "name": "CardTx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ntry_dtls: list[EntryDetails13] = field(
        default_factory=list,
        metadata={
            "name": "NtryDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_ntry_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlNtryInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 500,
        },
    )


@dataclass
class AccountNotification22:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    ntfctn_pgntn: Optional[Pagination1] = field(
        default=None,
        metadata={
            "name": "NtfctnPgntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    elctrnc_seq_nb: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "ElctrncSeqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )
    rptg_seq: Optional[SequenceRange1Choice] = field(
        default=None,
        metadata={
            "name": "RptgSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    lgl_seq_nb: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "LglSeqNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )
    cre_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "CreDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    fr_to_dt: Optional[DateTimePeriod1] = field(
        default=None,
        metadata={
            "name": "FrToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    cpy_dplct_ind: Optional[CopyDuplicate1Code] = field(
        default=None,
        metadata={
            "name": "CpyDplctInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    rptg_src: Optional[ReportingSource1Choice] = field(
        default=None,
        metadata={
            "name": "RptgSrc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    acct: Optional[CashAccount43] = field(
        default=None,
        metadata={
            "name": "Acct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    rltd_acct: Optional[CashAccount40] = field(
        default=None,
        metadata={
            "name": "RltdAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    intrst: list[AccountInterest4] = field(
        default_factory=list,
        metadata={
            "name": "Intrst",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    txs_summry: Optional[TotalTransactions6] = field(
        default=None,
        metadata={
            "name": "TxsSummry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    ntry: list[ReportEntry14] = field(
        default_factory=list,
        metadata={
            "name": "Ntry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )
    addtl_ntfctn_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlNtfctnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_length": 1,
            "max_length": 500,
        },
    )


@dataclass
class BankToCustomerDebitCreditNotificationV12:
    grp_hdr: Optional[GroupHeader116] = field(
        default=None,
        metadata={
            "name": "GrpHdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "required": True,
        },
    )
    ntfctn: list[AccountNotification22] = field(
        default_factory=list,
        metadata={
            "name": "Ntfctn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
            "min_occurs": 1,
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:camt.054.001.12"

    bk_to_cstmr_dbt_cdt_ntfctn: Optional[
        BankToCustomerDebitCreditNotificationV12
    ] = field(
        default=None,
        metadata={
            "name": "BkToCstmrDbtCdtNtfctn",
            "type": "Element",
            "required": True,
        },
    )
