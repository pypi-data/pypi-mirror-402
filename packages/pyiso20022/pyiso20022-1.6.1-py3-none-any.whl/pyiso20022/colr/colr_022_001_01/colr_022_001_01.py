from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01"


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


class BenchmarkCurveName7Code(Enum):
    BBSW = "BBSW"
    BUBO = "BUBO"
    BCOL = "BCOL"
    CDOR = "CDOR"
    CIBO = "CIBO"
    CORA = "CORA"
    CZNA = "CZNA"
    EONA = "EONA"
    EONS = "EONS"
    ESTR = "ESTR"
    EURI = "EURI"
    EUUS = "EUUS"
    EUCH = "EUCH"
    EFFR = "EFFR"
    FUSW = "FUSW"
    GCFR = "GCFR"
    HKIO = "HKIO"
    ISDA = "ISDA"
    ETIO = "ETIO"
    JIBA = "JIBA"
    LIBI = "LIBI"
    LIBO = "LIBO"
    MOSP = "MOSP"
    MAAA = "MAAA"
    BJUO = "BJUO"
    NIBO = "NIBO"
    OBFR = "OBFR"
    PFAN = "PFAN"
    PRBO = "PRBO"
    RCTR = "RCTR"
    SOFR = "SOFR"
    SONA = "SONA"
    STBO = "STBO"
    SWAP = "SWAP"
    TLBO = "TLBO"
    TIBO = "TIBO"
    TOAR = "TOAR"
    TREA = "TREA"
    WIBO = "WIBO"


@dataclass
class CashAccountIdentification5Choice:
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 34,
        },
    )


class CollateralRole1Code(Enum):
    GIVE = "GIVE"
    TAKE = "TAKE"


class CollateralStatus1Code(Enum):
    EXCS = "EXCS"
    DEFI = "DEFI"
    FLAT = "FLAT"


@dataclass
class CrystallisationDay1:
    day: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Day",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    prd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[0-9]{1,3}",
        },
    )


@dataclass
class DateAndDateTime2Choice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


class DateType2Code(Enum):
    OPEN = "OPEN"


class EventFrequency7Code(Enum):
    YEAR = "YEAR"
    ADHO = "ADHO"
    MNTH = "MNTH"
    DAIL = "DAIL"
    INDA = "INDA"
    WEEK = "WEEK"
    SEMI = "SEMI"
    QUTR = "QUTR"
    TOMN = "TOMN"
    TOWK = "TOWK"
    TWMN = "TWMN"
    OVNG = "OVNG"
    ONDE = "ONDE"


class ExecutionStatus1Code(Enum):
    INTD = "INTD"
    PINT = "PINT"


class ExposureType14Code(Enum):
    BFWD = "BFWD"
    PAYM = "PAYM"
    CBCO = "CBCO"
    COMM = "COMM"
    CRDS = "CRDS"
    CRTL = "CRTL"
    CRSP = "CRSP"
    CCIR = "CCIR"
    CRPR = "CRPR"
    EQPT = "EQPT"
    EQUS = "EQUS"
    EXTD = "EXTD"
    EXPT = "EXPT"
    FIXI = "FIXI"
    FORX = "FORX"
    FORW = "FORW"
    FUTR = "FUTR"
    OPTN = "OPTN"
    LIQU = "LIQU"
    OTCD = "OTCD"
    RVPO = "RVPO"
    SLOA = "SLOA"
    SBSC = "SBSC"
    SCRP = "SCRP"
    SLEB = "SLEB"
    SCIR = "SCIR"
    SCIE = "SCIE"
    SWPT = "SWPT"
    TBAS = "TBAS"
    TRCP = "TRCP"
    UDMS = "UDMS"
    CCPC = "CCPC"
    EQUI = "EQUI"
    TRBD = "TRBD"
    REPO = "REPO"
    SHSL = "SHSL"
    MGLD = "MGLD"


@dataclass
class FinancialInstrumentQuantity33Choice:
    unit: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Unit",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    face_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )
    dgtl_tkn_unit: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "DgtlTknUnit",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 30,
            "fraction_digits": 29,
        },
    )


@dataclass
class ForeignExchangeTerms19:
    unit_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "UnitCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    qtd_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "QtdCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    xchg_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )


@dataclass
class GenericIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericIdentification178:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericIdentification36:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class GenericIdentification56:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    bal: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Bal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )


@dataclass
class IdentificationSource3Choice:
    cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


class InterestComputationMethod2Code(Enum):
    A001 = "A001"
    A002 = "A002"
    A003 = "A003"
    A004 = "A004"
    A005 = "A005"
    A006 = "A006"
    A007 = "A007"
    A008 = "A008"
    A009 = "A009"
    A010 = "A010"
    A011 = "A011"
    A012 = "A012"
    A013 = "A013"
    A014 = "A014"
    NARR = "NARR"


class InterestRateIndexTenor2Code(Enum):
    INDA = "INDA"
    MNTH = "MNTH"
    YEAR = "YEAR"
    TOMN = "TOMN"
    QUTR = "QUTR"
    FOMN = "FOMN"
    SEMI = "SEMI"
    OVNG = "OVNG"
    WEEK = "WEEK"
    TOWK = "TOWK"


@dataclass
class MarketIdentification1Choice:
    mkt_idr_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "MktIdrCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z0-9]{4,4}",
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


class MarketType4Code(Enum):
    FUND = "FUND"
    LMAR = "LMAR"
    THEO = "THEO"
    VEND = "VEND"


@dataclass
class Number3Choice:
    shrt: Optional[str] = field(
        default=None,
        metadata={
            "name": "Shrt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[0-9]{3}",
        },
    )
    lng: Optional[str] = field(
        default=None,
        metadata={
            "name": "Lng",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[0-9]{5}",
        },
    )


class OptionType1Code(Enum):
    CALL = "CALL"
    PUTO = "PUTO"


@dataclass
class OriginalAndCurrentQuantities1:
    face_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )


@dataclass
class Pagination1:
    pg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "pattern": r"[0-9]{1,5}",
        },
    )
    last_pg_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "LastPgInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )


@dataclass
class Period2:
    fr_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FrDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    to_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )


class PriceValueType1Code(Enum):
    DISC = "DISC"
    PREM = "PREM"
    PARV = "PARV"


class RepoTerminationOption1Code(Enum):
    EGRN = "EGRN"
    ETSB = "ETSB"


class SafekeepingPlace1Code(Enum):
    CUST = "CUST"
    ICSD = "ICSD"
    NCSD = "NCSD"
    SHHE = "SHHE"


class SafekeepingPlace3Code(Enum):
    SHHE = "SHHE"


class SecuritiesSettlementStatus3Code(Enum):
    PEND = "PEND"
    SETT = "SETT"


class StatementBasis3Code(Enum):
    EOSP = "EOSP"
    FUTM = "FUTM"


class StatementStatusType1Code(Enum):
    CONF = "CONF"
    PEND = "PEND"


class StatementUpdateType1Code(Enum):
    COMP = "COMP"
    DELT = "DELT"


@dataclass
class SupplementaryDataEnvelope1:
    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )


class TradingCapacity7Code(Enum):
    AGEN = "AGEN"
    PRIN = "PRIN"


class TypeOfIdentification1Code(Enum):
    ARNU = "ARNU"
    CCPT = "CCPT"
    CHTY = "CHTY"
    CORP = "CORP"
    DRLC = "DRLC"
    FIIN = "FIIN"
    TXID = "TXID"


@dataclass
class ValuationFactorBreakdown1:
    valtn_fctr: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "ValtnFctr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    infltn_fctr: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "InfltnFctr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    hrcut: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Hrcut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    pool_fctr: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "PoolFctr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )


@dataclass
class AmountAndDirection53:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    sgn: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Sgn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class BasketIdentificationAndEligibilitySetProfile1:
    prfrntl_bskt_id_nb: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "PrfrntlBsktIdNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    fllbck_startg_bskt_id: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "FllbckStartgBsktId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    exclsn_bskt_id: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "ExclsnBsktId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    elgblty_set_prfl: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "ElgbltySetPrfl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class BenchmarkCurveName13Choice:
    cd: Optional[BenchmarkCurveName7Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class BlockChainAddressWallet3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 140,
        },
    )
    tp: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class CollateralAmount4:
    actl_mkt_val_pst_valtn_fctr: Optional[
        ActiveOrHistoricCurrencyAndAmount
    ] = field(
        default=None,
        metadata={
            "name": "ActlMktValPstValtnFctr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    actl_mkt_val_bfr_valtn_fctr: Optional[
        ActiveOrHistoricCurrencyAndAmount
    ] = field(
        default=None,
        metadata={
            "name": "ActlMktValBfrValtnFctr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    xpsr_coll_in_tx_ccy: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "XpsrCollInTxCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    xpsr_coll_in_rptg_ccy: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "XpsrCollInRptgCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    mkt_val_amt_pst_valtn_fctr: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "MktValAmtPstValtnFctr",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            },
        )
    )
    mkt_val_amt_bfr_valtn_fctr: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "MktValAmtBfrValtnFctr",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            },
        )
    )
    ttl_val_of_own_coll: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfOwnColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_val_of_reusd_coll: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfReusdColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CollateralAmount9:
    actl_mkt_val_pst_hrcut: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "ActlMktValPstHrcut",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
                "required": True,
            },
        )
    )
    actl_mkt_val_bfr_hrcut: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "ActlMktValBfrHrcut",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            },
        )
    )
    xpsr_coll_in_tx_ccy: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "XpsrCollInTxCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    xpsr_coll_in_rptg_ccy: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "XpsrCollInRptgCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    mkt_val_amt_pst_hrcut: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "MktValAmtPstHrcut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    mkt_val_amt_bfr_hrcut: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "MktValAmtBfrHrcut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CollateralStatus2Choice:
    cd: Optional[ExecutionStatus1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class Date3Choice:
    cd: Optional[DateType2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class ExposureType23Choice:
    cd: Optional[ExposureType14Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class Frequency22Choice:
    cd: Optional[EventFrequency7Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class GenericIdentification78:
    tp: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class IdentificationType42Choice:
    cd: Optional[TypeOfIdentification1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class InterestComputationMethodFormat4Choice:
    cd: Optional[InterestComputationMethod2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class MarketType15Choice:
    cd: Optional[MarketType4Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class OptionType6Choice:
    cd: Optional[OptionType1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class OtherIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    tp: Optional[IdentificationSource3Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )


@dataclass
class Period4Choice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    fr_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FrDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    to_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    fr_dt_to_dt: Optional[Period2] = field(
        default=None,
        metadata={
            "name": "FrDtToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class PostalAddress1:
    adr_tp: Optional[AddressType2Code] = field(
        default=None,
        metadata={
            "name": "AdrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class PriceRateOrAmount3Choice:
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAnd13DecimalAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class Quantity51Choice:
    qty: Optional[FinancialInstrumentQuantity33Choice] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    orgnl_and_cur_face: Optional[OriginalAndCurrentQuantities1] = field(
        default=None,
        metadata={
            "name": "OrgnlAndCurFace",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class SafekeepingPlaceTypeAndIdentification1:
    sfkpg_plc_tp: Optional[SafekeepingPlace1Code] = field(
        default=None,
        metadata={
            "name": "SfkpgPlcTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )


@dataclass
class SafekeepingPlaceTypeAndText8:
    sfkpg_plc_tp: Optional[SafekeepingPlace3Code] = field(
        default=None,
        metadata={
            "name": "SfkpgPlcTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class SecuritiesAccount19:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class StatementBasis14Choice:
    cd: Optional[StatementBasis3Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class SupplementaryData1:
    plc_and_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlcAndNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )


@dataclass
class TotalValueInPageAndStatement5:
    ttl_xpsr_val_of_pg: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlXpsrValOfPg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_coll_held_val_of_pg: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "TtlCollHeldValOfPg",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            },
        )
    )


@dataclass
class TradingPartyCapacity5Choice:
    cd: Optional[TradingCapacity7Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class UpdateType15Choice:
    cd: Optional[StatementUpdateType1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class YieldedOrValueType1Choice:
    yldd: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Yldd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    val_tp: Optional[PriceValueType1Code] = field(
        default=None,
        metadata={
            "name": "ValTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class AlternatePartyIdentification7:
    id_tp: Optional[IdentificationType42Choice] = field(
        default=None,
        metadata={
            "name": "IdTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )
    altrn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class BalanceQuantity13Choice:
    qty: Optional[Quantity51Choice] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification56] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class ClosingDate4Choice:
    dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    cd: Optional[Date3Choice] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CollateralAmount15:
    val_of_coll_held: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "ValOfCollHeld",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    ttl_xpsr: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlXpsr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    mrgn: Optional[AmountAndDirection53] = field(
        default=None,
        metadata={
            "name": "Mrgn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_coll_reqrd: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlCollReqrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_acrd_intrst: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlAcrdIntrst",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_fees_comssns: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlFeesComssns",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_of_prncpls: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlOfPrncpls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_pdg_coll_in: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlPdgCollIn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_pdg_coll_out: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlPdgCollOut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_val_of_own_coll: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfOwnColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_val_of_reusd_coll: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfReusdColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_csh_faild: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlCshFaild",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CollateralAmount16:
    val_of_coll_held: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "ValOfCollHeld",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    ttl_xpsr: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlXpsr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    mrgn: Optional[AmountAndDirection53] = field(
        default=None,
        metadata={
            "name": "Mrgn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_coll_reqrd: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlCollReqrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_acrd_intrst: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlAcrdIntrst",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_val_of_own_coll: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfOwnColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_val_of_reusd_coll: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfReusdColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_of_prncpls: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlOfPrncpls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_pdg_coll_in: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlPdgCollIn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_pdg_coll_out: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlPdgCollOut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_csh_faild: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlCshFaild",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CollateralTransactionAmountBreakdown2:
    lot_nb: Optional[GenericIdentification178] = field(
        default=None,
        metadata={
            "name": "LotNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    tx_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prd: Optional[Period4Choice] = field(
        default=None,
        metadata={
            "name": "Prd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class MarketIdentification89:
    id: Optional[MarketIdentification1Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    tp: Optional[MarketType15Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )


@dataclass
class NameAndAddress5:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 350,
        },
    )
    adr: Optional[PostalAddress1] = field(
        default=None,
        metadata={
            "name": "Adr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class Price7:
    tp: Optional[YieldedOrValueType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    val: Optional[PriceRateOrAmount3Choice] = field(
        default=None,
        metadata={
            "name": "Val",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )


@dataclass
class RateTypeAndLookback2:
    tp: Optional[BenchmarkCurveName13Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    look_bck_days: Optional[str] = field(
        default=None,
        metadata={
            "name": "LookBckDays",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[0-9]{1,3}",
        },
    )
    crstllstn_dt: Optional[CrystallisationDay1] = field(
        default=None,
        metadata={
            "name": "CrstllstnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    tnr: Optional[InterestRateIndexTenor2Code] = field(
        default=None,
        metadata={
            "name": "Tnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z]{3,3}",
        },
    )


@dataclass
class SafekeepingPlaceFormat29Choice:
    id: Optional[SafekeepingPlaceTypeAndText8] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z]{2,2}",
        },
    )
    tp_and_id: Optional[SafekeepingPlaceTypeAndIdentification1] = field(
        default=None,
        metadata={
            "name": "TpAndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    prtry: Optional[GenericIdentification78] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class SecurityIdentification19:
    isin: Optional[str] = field(
        default=None,
        metadata={
            "name": "ISIN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z]{2,2}[A-Z0-9]{9,9}[0-9]{1,1}",
        },
    )
    othr_id: list[OtherIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "OthrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class Statement78:
    stmt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "StmtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    rpt_nb: Optional[Number3Choice] = field(
        default=None,
        metadata={
            "name": "RptNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    qry_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "QryRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    stmt_dt_tm: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "StmtDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    frqcy: Optional[Frequency22Choice] = field(
        default=None,
        metadata={
            "name": "Frqcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    upd_tp: Optional[UpdateType15Choice] = field(
        default=None,
        metadata={
            "name": "UpdTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    coll_sd: Optional[CollateralRole1Code] = field(
        default=None,
        metadata={
            "name": "CollSd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    stmt_bsis: Optional[StatementBasis14Choice] = field(
        default=None,
        metadata={
            "name": "StmtBsis",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    sts_tp: Optional[StatementStatusType1Code] = field(
        default=None,
        metadata={
            "name": "StsTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    summry_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "SummryInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    actvty_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "ActvtyInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )


@dataclass
class TransactionStatus6:
    cvrg_sts: Optional[CollateralStatus1Code] = field(
        default=None,
        metadata={
            "name": "CvrgSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    exctn_sts: Optional[CollateralStatus2Choice] = field(
        default=None,
        metadata={
            "name": "ExctnSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class ValuationsDetails2:
    valtn_dtls_amt: list[CollateralAmount9] = field(
        default_factory=list,
        metadata={
            "name": "ValtnDtlsAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_occurs": 1,
        },
    )
    hrcut: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Hrcut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )


@dataclass
class CashBalance15:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    fxdtls: Optional[ForeignExchangeTerms19] = field(
        default=None,
        metadata={
            "name": "FXDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    csh_acct: Optional[CashAccountIdentification5Choice] = field(
        default=None,
        metadata={
            "name": "CshAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    valtn_dtls: Optional[ValuationsDetails2] = field(
        default=None,
        metadata={
            "name": "ValtnDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    tx_lot_nb: list[GenericIdentification178] = field(
        default_factory=list,
        metadata={
            "name": "TxLotNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CollateralAmount17:
    val_of_coll_held: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "ValOfCollHeld",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    ttl_xpsr: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlXpsr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    tx_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    tx_amt_brkdwn: list[CollateralTransactionAmountBreakdown2] = field(
        default_factory=list,
        metadata={
            "name": "TxAmtBrkdwn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    mrgn: Optional[AmountAndDirection53] = field(
        default=None,
        metadata={
            "name": "Mrgn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_acrd_intrst: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlAcrdIntrst",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_coll_reqrd: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlCollReqrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_val_of_own_coll: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfOwnColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_val_of_reusd_coll: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfReusdColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_pdg_coll_in: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlPdgCollIn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_pdg_coll_out: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlPdgCollOut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_of_prncpls: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlOfPrncpls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    termntn_tx_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TermntnTxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ttl_csh_faild: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlCshFaild",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class ExposureTypeAggregation3:
    xpsr_tp: Optional[ExposureType23Choice] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    sttlm_prc: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "SttlmPrc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    valtn_amts: list[CollateralAmount16] = field(
        default_factory=list,
        metadata={
            "name": "ValtnAmts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_occurs": 1,
        },
    )
    mrgn_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "MrgnRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    gbl_xpsr_tp_sts: Optional[CollateralStatus1Code] = field(
        default=None,
        metadata={
            "name": "GblXpsrTpSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class OverallCollateralDetails2:
    valtn_amts: Optional[CollateralAmount15] = field(
        default=None,
        metadata={
            "name": "ValtnAmts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    mrgn_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "MrgnRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    gbl_coll_sts: Optional[CollateralStatus1Code] = field(
        default=None,
        metadata={
            "name": "GblCollSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    valtn_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "ValtnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    coll_addtl_dtls: Optional[str] = field(
        default=None,
        metadata={
            "name": "CollAddtlDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 350,
        },
    )


@dataclass
class PartyIdentification120Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    nm_and_adr: Optional[NameAndAddress5] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class RateOrName4Choice:
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    rate_indx_dtls: Optional[RateTypeAndLookback2] = field(
        default=None,
        metadata={
            "name": "RateIndxDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class Rating2:
    ratg: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ratg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 10,
        },
    )
    src_of_ratg: Optional[MarketIdentification89] = field(
        default=None,
        metadata={
            "name": "SrcOfRatg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )


@dataclass
class SafeKeepingPlace3:
    sfkpg_plc_frmt: Optional[SafekeepingPlaceFormat29Choice] = field(
        default=None,
        metadata={
            "name": "SfkpgPlcFrmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )


@dataclass
class ValuationsDetails1:
    mkt_pric: Optional[Price7] = field(
        default=None,
        metadata={
            "name": "MktPric",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    src_of_pric: Optional[MarketIdentification89] = field(
        default=None,
        metadata={
            "name": "SrcOfPric",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    sttlm_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "SttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    valtn_dtls_amt: Optional[CollateralAmount4] = field(
        default=None,
        metadata={
            "name": "ValtnDtlsAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    acrd_intrst: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "AcrdIntrst",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    clean_pric: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CleanPric",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    valtn_fctr_brkdwn: Optional[ValuationFactorBreakdown1] = field(
        default=None,
        metadata={
            "name": "ValtnFctrBrkdwn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    nb_of_days_acrd: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "NbOfDaysAcrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )
    qtn_age: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "QtnAge",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )


@dataclass
class PartyIdentification136:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )


@dataclass
class PartyIdentification232:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CollateralParties11:
    pty_b: Optional[PartyIdentification232] = field(
        default=None,
        metadata={
            "name": "PtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    clnt_pty_b: Optional[PartyIdentification232] = field(
        default=None,
        metadata={
            "name": "ClntPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    trpty_agt: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "TrptyAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    coll_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "CollAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class PartyIdentificationAndAccount202:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    acct_ownr: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "AcctOwnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    pty_cpcty: Optional[TradingPartyCapacity5Choice] = field(
        default=None,
        metadata={
            "name": "PtyCpcty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class SecuritiesBalance3:
    fin_instrm_id: Optional[SecurityIdentification19] = field(
        default=None,
        metadata={
            "name": "FinInstrmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    qty: Optional[BalanceQuantity13Choice] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    coll_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CollInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    sfkpg_plc: Optional[SafeKeepingPlace3] = field(
        default=None,
        metadata={
            "name": "SfkpgPlc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    acct_ownr: Optional[PartyIdentification232] = field(
        default=None,
        metadata={
            "name": "AcctOwnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    sttlm_sts: Optional[SecuritiesSettlementStatus3Code] = field(
        default=None,
        metadata={
            "name": "SttlmSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    dnmtn_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "DnmtnCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "pattern": r"[A-Z]{3,3}",
        },
    )
    ratg_dtls: list[Rating2] = field(
        default_factory=list,
        metadata={
            "name": "RatgDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    fxdtls: Optional[ForeignExchangeTerms19] = field(
        default=None,
        metadata={
            "name": "FXDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    valtn_dtls: Optional[ValuationsDetails1] = field(
        default=None,
        metadata={
            "name": "ValtnDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    tx_lot_nb: list[GenericIdentification178] = field(
        default_factory=list,
        metadata={
            "name": "TxLotNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CollateralParties9:
    pty_a: Optional[PartyIdentificationAndAccount202] = field(
        default=None,
        metadata={
            "name": "PtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    clnt_pty_a: Optional[PartyIdentificationAndAccount202] = field(
        default=None,
        metadata={
            "name": "ClntPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    trpty_agt: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "TrptyAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class CounterpartyAggregation3:
    optn_tp: Optional[OptionType6Choice] = field(
        default=None,
        metadata={
            "name": "OptnTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    termntn_optn: Optional[RepoTerminationOption1Code] = field(
        default=None,
        metadata={
            "name": "TermntnOptn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    bskt_id_and_elgblty_set_prfl: Optional[
        BasketIdentificationAndEligibilitySetProfile1
    ] = field(
        default=None,
        metadata={
            "name": "BsktIdAndElgbltySetPrfl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    coll_pties: Optional[CollateralParties11] = field(
        default=None,
        metadata={
            "name": "CollPties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    valtn_amts: list[CollateralAmount16] = field(
        default_factory=list,
        metadata={
            "name": "ValtnAmts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_occurs": 1,
        },
    )
    mrgn_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "MrgnRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    gbl_ctr_pty_sts: Optional[CollateralStatus1Code] = field(
        default=None,
        metadata={
            "name": "GblCtrPtySts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class Transaction124:
    clnt_trpty_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntTrptyCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    trpty_agt_svc_prvdr_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctr_pty_coll_tx_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrPtyCollTxRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cmon_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CmonTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "min_length": 1,
            "max_length": 52,
        },
    )
    xpsr_tp: Optional[ExposureType23Choice] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    optn_tp: Optional[OptionType6Choice] = field(
        default=None,
        metadata={
            "name": "OptnTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    termntn_optn: Optional[RepoTerminationOption1Code] = field(
        default=None,
        metadata={
            "name": "TermntnOptn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    bskt_id_and_elgblty_set_prfl: Optional[
        BasketIdentificationAndEligibilitySetProfile1
    ] = field(
        default=None,
        metadata={
            "name": "BsktIdAndElgbltySetPrfl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    coll_pties: Optional[CollateralParties11] = field(
        default=None,
        metadata={
            "name": "CollPties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    exctn_reqd_dt: Optional[ClosingDate4Choice] = field(
        default=None,
        metadata={
            "name": "ExctnReqdDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    clsg_dt: Optional[ClosingDate4Choice] = field(
        default=None,
        metadata={
            "name": "ClsgDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    valtn_amts: Optional[CollateralAmount17] = field(
        default=None,
        metadata={
            "name": "ValtnAmts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    pricg_rate: Optional[RateOrName4Choice] = field(
        default=None,
        metadata={
            "name": "PricgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    mrgn_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "MrgnRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    sprd_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "SprdRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    day_cnt_bsis: Optional[InterestComputationMethodFormat4Choice] = field(
        default=None,
        metadata={
            "name": "DayCntBsis",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    automtc_allcn: Optional[bool] = field(
        default=None,
        metadata={
            "name": "AutomtcAllcn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    tx_sts: list[TransactionStatus6] = field(
        default_factory=list,
        metadata={
            "name": "TxSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "max_occurs": 2,
        },
    )
    scties_bal: list[SecuritiesBalance3] = field(
        default_factory=list,
        metadata={
            "name": "SctiesBal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    csh_bal: list[CashBalance15] = field(
        default_factory=list,
        metadata={
            "name": "CshBal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class TripartyCollateralAndExposureReportV01:
    pgntn: Optional[Pagination1] = field(
        default=None,
        metadata={
            "name": "Pgntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    stmt_gnl_dtls: Optional[Statement78] = field(
        default=None,
        metadata={
            "name": "StmtGnlDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    coll_pties: Optional[CollateralParties9] = field(
        default=None,
        metadata={
            "name": "CollPties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
            "required": True,
        },
    )
    ovrll_coll_aggtn: Optional[OverallCollateralDetails2] = field(
        default=None,
        metadata={
            "name": "OvrllCollAggtn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    xpsr_tp_aggtn: list[ExposureTypeAggregation3] = field(
        default_factory=list,
        metadata={
            "name": "XpsrTpAggtn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    ctr_pty_aggtn: list[CounterpartyAggregation3] = field(
        default_factory=list,
        metadata={
            "name": "CtrPtyAggtn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    txs: list[Transaction124] = field(
        default_factory=list,
        metadata={
            "name": "Txs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    acct_base_ccy_ttl_amts: Optional[TotalValueInPageAndStatement5] = field(
        default=None,
        metadata={
            "name": "AcctBaseCcyTtlAmts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:colr.022.001.01"

    trpty_coll_and_xpsr_rpt: Optional[
        TripartyCollateralAndExposureReportV01
    ] = field(
        default=None,
        metadata={
            "name": "TrptyCollAndXpsrRpt",
            "type": "Element",
            "required": True,
        },
    )
