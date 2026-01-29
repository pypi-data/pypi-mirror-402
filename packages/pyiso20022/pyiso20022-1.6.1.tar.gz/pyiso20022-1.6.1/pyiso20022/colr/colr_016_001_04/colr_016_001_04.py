from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04"


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


class AgreementFramework1Code(Enum):
    FBAA = "FBAA"
    BBAA = "BBAA"
    DERV = "DERV"
    ISDA = "ISDA"
    NONR = "NONR"


class CcpmemberType1Code(Enum):
    ACMB = "ACMB"
    CCPX = "CCPX"
    DCMB = "DCMB"
    FCMC = "FCMC"
    GCMB = "GCMB"
    SCMB = "SCMB"


class CollateralAccountType1Code(Enum):
    HOUS = "HOUS"
    CLIE = "CLIE"
    LIPR = "LIPR"
    MGIN = "MGIN"
    DFLT = "DFLT"


class CollateralAppliedExcess1Code(Enum):
    APLD = "APLD"
    EXCS = "EXCS"


class CollateralDirection1Code(Enum):
    CDPA = "CDPA"
    CDPB = "CDPB"


class CollateralType8Code(Enum):
    COMO = "COMO"
    CCCL = "CCCL"
    CEMC = "CEMC"
    CXCC = "CXCC"
    CFTD = "CFTD"
    CFTI = "CFTI"
    CTRC = "CTRC"
    CASH = "CASH"
    LCRE = "LCRE"
    OTHR = "OTHR"
    SECU = "SECU"
    CTCO = "CTCO"
    CCVR = "CCVR"


@dataclass
class DateAndDateTime2Choice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


class DateType2Code(Enum):
    OPEN = "OPEN"


class DepositType1Code(Enum):
    FITE = "FITE"
    CALL = "CALL"


class EventFrequency6Code(Enum):
    DAIL = "DAIL"
    INDA = "INDA"
    ONDE = "ONDE"


class ExposureType5Code(Enum):
    BFWD = "BFWD"
    PAYM = "PAYM"
    CCPC = "CCPC"
    COMM = "COMM"
    CRDS = "CRDS"
    CRTL = "CRTL"
    CRSP = "CRSP"
    CCIR = "CCIR"
    CRPR = "CRPR"
    EQUI = "EQUI"
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
    REPO = "REPO"
    RVPO = "RVPO"
    SLOA = "SLOA"
    SBSC = "SBSC"
    SCRP = "SCRP"
    SLEB = "SLEB"
    SHSL = "SHSL"
    SCIR = "SCIR"
    SCIE = "SCIE"
    SWPT = "SWPT"
    TBAS = "TBAS"
    TRBD = "TRBD"
    TRCP = "TRCP"


class ExposureType8Code(Enum):
    CCIR = "CCIR"
    CRPR = "CRPR"
    EQUI = "EQUI"
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
    MGLD = "MGLD"
    OTCD = "OTCD"
    REPO = "REPO"
    RVPO = "RVPO"
    SLOA = "SLOA"
    SBSC = "SBSC"
    SCRP = "SCRP"
    SLEB = "SLEB"
    SHSL = "SHSL"
    SCIR = "SCIR"
    SCIE = "SCIE"
    ESCL = "ESCL"
    SWPT = "SWPT"
    TBAS = "TBAS"
    ECRT = "ECRT"
    ECFR = "ECFR"
    EMLO = "EMLO"
    EMLI = "EMLI"
    EOIM = "EOIM"
    EOMI = "EOMI"
    TRCP = "TRCP"
    TRBD = "TRBD"
    BFWD = "BFWD"
    PAYM = "PAYM"
    CCPC = "CCPC"
    COMM = "COMM"
    CRDS = "CRDS"
    CRTL = "CRTL"
    CRSP = "CRSP"
    EOMO = "EOMO"


@dataclass
class FinancialInstrumentQuantity1Choice:
    unit: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Unit",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    face_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_inclusive": Decimal("0"),
            "total_digits": 18,
            "fraction_digits": 5,
        },
    )


@dataclass
class GenericIdentification30:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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


@dataclass
class Pagination1:
    pg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "pattern": r"[0-9]{1,5}",
        },
    )
    last_pg_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "LastPgInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )


@dataclass
class PostalAddress2:
    strt_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "StrtNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pst_cd_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCdId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


class PriceValueType1Code(Enum):
    DISC = "DISC"
    PREM = "PREM"
    PARV = "PARV"


class ReturnExcessCash1Code(Enum):
    RTND = "RTND"
    RTDN = "RTDN"
    SSPD = "SSPD"


class SafekeepingPlace1Code(Enum):
    CUST = "CUST"
    ICSD = "ICSD"
    NCSD = "NCSD"
    SHHE = "SHHE"


class SafekeepingPlace3Code(Enum):
    SHHE = "SHHE"


class SettlementStatus3Code(Enum):
    ASTL = "ASTL"
    AAUT = "AAUT"
    ACCF = "ACCF"
    ARCF = "ARCF"
    MTCH = "MTCH"
    PSTL = "PSTL"
    RJCT = "RJCT"
    STLD = "STLD"
    STCR = "STCR"
    SPLT = "SPLT"
    NMAT = "NMAT"


class ShortLong1Code(Enum):
    SHOR = "SHOR"
    LONG = "LONG"


@dataclass
class SupplementaryDataEnvelope1:
    any_element: Optional[object] = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )


class ThresholdType1Code(Enum):
    SECU = "SECU"
    UNSE = "UNSE"


@dataclass
class AgreementFramework1Choice:
    agrmt_frmwk: Optional[AgreementFramework1Code] = field(
        default=None,
        metadata={
            "name": "AgrmtFrmwk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    prtry_id: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class CashCollateral4:
    asst_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "AsstNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )
    dpst_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "DpstAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    dpst_tp: Optional[DepositType1Code] = field(
        default=None,
        metadata={
            "name": "DpstTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    blckd_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "BlckdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    mtrty_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "MtrtyDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    val_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ValDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    xchg_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    coll_val: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CollVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    hrcut: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Hrcut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )


@dataclass
class CollateralAccountIdentificationType3Choice:
    tp: Optional[CollateralAccountType1Code] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    prtry: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class CollateralAmount1:
    coll_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CollAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    rptd_ccy_and_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RptdCcyAndAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    mkt_val_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "MktValAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    acrd_intrst_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "AcrdIntrstAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    fees_and_comssns: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "FeesAndComssns",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class DateCode9Choice:
    cd: Optional[DateType2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class GenericIdentification78:
    tp: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class NameAndAddress6:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 70,
        },
    )
    adr: Optional[PostalAddress2] = field(
        default=None,
        metadata={
            "name": "Adr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )


@dataclass
class OtherIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 16,
        },
    )
    tp: Optional[IdentificationSource3Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )


@dataclass
class OtherTypeOfCollateral2:
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 140,
        },
    )
    qty: Optional[FinancialInstrumentQuantity1Choice] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class PriceRateOrAmount3Choice:
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    amt: Optional[ActiveOrHistoricCurrencyAnd13DecimalAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class ReportParameters6:
    rpt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "RptId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    rpt_dt_and_tm: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "RptDtAndTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    frqcy: Optional[EventFrequency6Code] = field(
        default=None,
        metadata={
            "name": "Frqcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    rpt_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "RptCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    clctn_dt: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "ClctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class ReturnExcessCash1Choice:
    cd: Optional[ReturnExcessCash1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class SafekeepingPlaceTypeAndIdentification1:
    sfkpg_plc_tp: Optional[SafekeepingPlace1Code] = field(
        default=None,
        metadata={
            "name": "SfkpgPlcTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class SupplementaryData1:
    plc_and_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlcAndNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )


@dataclass
class YieldedOrValueType1Choice:
    yldd: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Yldd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    val_tp: Optional[PriceValueType1Code] = field(
        default=None,
        metadata={
            "name": "ValTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class Agreement4:
    agrmt_dtls: Optional[str] = field(
        default=None,
        metadata={
            "name": "AgrmtDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 140,
        },
    )
    agrmt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AgrmtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 140,
        },
    )
    agrmt_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "AgrmtDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    base_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "BaseCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    agrmt_frmwk: Optional[AgreementFramework1Choice] = field(
        default=None,
        metadata={
            "name": "AgrmtFrmwk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class CollateralAccount3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    tp: Optional[CollateralAccountIdentificationType3Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class DateFormat14Choice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    dt_cd: Optional[DateCode9Choice] = field(
        default=None,
        metadata={
            "name": "DtCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class PartyIdentification178Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    nm_and_adr: Optional[NameAndAddress6] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class Price7:
    tp: Optional[YieldedOrValueType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    val: Optional[PriceRateOrAmount3Choice] = field(
        default=None,
        metadata={
            "name": "Val",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )


@dataclass
class ReturnExcessCash1:
    rtr_xcss_csh_tp: Optional[ReturnExcessCash1Choice] = field(
        default=None,
        metadata={
            "name": "RtrXcssCshTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    csh_coll_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "CshCollCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "pattern": r"[A-Z]{2,2}",
        },
    )
    tp_and_id: Optional[SafekeepingPlaceTypeAndIdentification1] = field(
        default=None,
        metadata={
            "name": "TpAndId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    prtry: Optional[GenericIdentification78] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class SecurityIdentification19:
    isin: Optional[str] = field(
        default=None,
        metadata={
            "name": "ISIN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "pattern": r"[A-Z]{2,2}[A-Z0-9]{9,9}[0-9]{1,1}",
        },
    )
    othr_id: list[OtherIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "OthrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class CollateralOwnership3:
    prtry: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    clnt_nm: Optional[PartyIdentification178Choice] = field(
        default=None,
        metadata={
            "name": "ClntNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class PartyIdentification242:
    id: Optional[PartyIdentification178Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    ccpmmb_tp: Optional[CcpmemberType1Code] = field(
        default=None,
        metadata={
            "name": "CCPMmbTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class SummaryAmounts2:
    thrshld_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "ThrshldAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    thrshld_tp: Optional[ThresholdType1Code] = field(
        default=None,
        metadata={
            "name": "ThrshldTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    pre_hrcut_coll_val: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "PreHrcutCollVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    adjstd_xpsr: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "AdjstdXpsr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    coll_reqrd: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CollReqrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    rtr_xcss_csh_and_coll_ccy: list[ReturnExcessCash1] = field(
        default_factory=list,
        metadata={
            "name": "RtrXcssCshAndCollCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    min_trf_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "MinTrfAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    rndg_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RndgAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    prvs_xpsr_val: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "PrvsXpsrVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    prvs_coll_val: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "PrvsCollVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    ttl_pdg_incmg_coll: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlPdgIncmgColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    ttl_pdg_outgng_coll: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlPdgOutgngColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    ttl_acrd_intrst_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlAcrdIntrstAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    ttl_fees: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlFees",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class Obligation6:
    pty_a: Optional[PartyIdentification242] = field(
        default=None,
        metadata={
            "name": "PtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    svcg_pty_a: Optional[PartyIdentification178Choice] = field(
        default=None,
        metadata={
            "name": "SvcgPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    pty_b: Optional[PartyIdentification242] = field(
        default=None,
        metadata={
            "name": "PtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    svcg_pty_b: Optional[PartyIdentification178Choice] = field(
        default=None,
        metadata={
            "name": "SvcgPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    coll_acct_id: Optional[CollateralAccount3] = field(
        default=None,
        metadata={
            "name": "CollAcctId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    xpsr_tp: Optional[ExposureType5Code] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    valtn_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "ValtnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )


@dataclass
class OtherCollateral8:
    asst_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "AsstNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )
    lttr_of_cdt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "LttrOfCdtId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )
    lttr_of_cdt_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "LttrOfCdtAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    grnt_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "GrntAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    othr_tp_of_coll: Optional[OtherTypeOfCollateral2] = field(
        default=None,
        metadata={
            "name": "OthrTpOfColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    coll_ownrsh: Optional[CollateralOwnership3] = field(
        default=None,
        metadata={
            "name": "CollOwnrsh",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    isse_dt: Optional[DateFormat14Choice] = field(
        default=None,
        metadata={
            "name": "IsseDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    xpry_dt: Optional[DateFormat14Choice] = field(
        default=None,
        metadata={
            "name": "XpryDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    ltd_cvrg_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "LtdCvrgInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    issr: Optional[PartyIdentification178Choice] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    blckd_qty: Optional[FinancialInstrumentQuantity1Choice] = field(
        default=None,
        metadata={
            "name": "BlckdQty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    val_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ValDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    xchg_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    mkt_val: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "MktVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    hrcut: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Hrcut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    coll_val: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CollVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    sfkpg_plc: Optional[SafekeepingPlaceFormat29Choice] = field(
        default=None,
        metadata={
            "name": "SfkpgPlc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class SecuritiesCollateral9:
    asst_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "AsstNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )
    scty_id: Optional[SecurityIdentification19] = field(
        default=None,
        metadata={
            "name": "SctyId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    mtrty_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "MtrtyDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    coll_ownrsh: Optional[CollateralOwnership3] = field(
        default=None,
        metadata={
            "name": "CollOwnrsh",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    ltd_cvrg_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "LtdCvrgInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    qty: Optional[FinancialInstrumentQuantity1Choice] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    blckd_qty: Optional[FinancialInstrumentQuantity1Choice] = field(
        default=None,
        metadata={
            "name": "BlckdQty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    pric: Optional[Price7] = field(
        default=None,
        metadata={
            "name": "Pric",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    mkt_val: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "MktVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    hrcut: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Hrcut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    coll_val: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CollVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    val_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ValDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    sfkpg_plc: Optional[SafekeepingPlaceFormat29Choice] = field(
        default=None,
        metadata={
            "name": "SfkpgPlc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )


@dataclass
class Summary2:
    xpsd_amt_pty_a: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "XpsdAmtPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    xpsd_amt_pty_b: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "XpsdAmtPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    xpsr_tp: Optional[ExposureType8Code] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    ttl_val_of_coll: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlValOfColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    net_xcss_dfcit: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "NetXcssDfcit",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    net_xcss_dfcit_ind: Optional[ShortLong1Code] = field(
        default=None,
        metadata={
            "name": "NetXcssDfcitInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    valtn_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "ValtnDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    reqd_sttlm_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ReqdSttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    summry_dtls: Optional[SummaryAmounts2] = field(
        default=None,
        metadata={
            "name": "SummryDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class CollateralValuation12:
    coll_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CollId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )
    coll_tp: Optional[CollateralType8Code] = field(
        default=None,
        metadata={
            "name": "CollTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    coll_drctn: Optional[CollateralDirection1Code] = field(
        default=None,
        metadata={
            "name": "CollDrctn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    sttlm_sts: Optional[SettlementStatus3Code] = field(
        default=None,
        metadata={
            "name": "SttlmSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    apld_xcss_ind: Optional[CollateralAppliedExcess1Code] = field(
        default=None,
        metadata={
            "name": "ApldXcssInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    nb_of_days_acrd: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "NbOfDaysAcrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )
    valtn_amts: Optional[CollateralAmount1] = field(
        default=None,
        metadata={
            "name": "ValtnAmts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    day_cnt_bsis: Optional[InterestComputationMethod2Code] = field(
        default=None,
        metadata={
            "name": "DayCntBsis",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    xchg_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    ccy_hrcut: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "CcyHrcut",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    adjstd_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "AdjstdRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    scties_coll: Optional[SecuritiesCollateral9] = field(
        default=None,
        metadata={
            "name": "SctiesColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    csh_coll: Optional[CashCollateral4] = field(
        default=None,
        metadata={
            "name": "CshColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    othr_coll: Optional[OtherCollateral8] = field(
        default=None,
        metadata={
            "name": "OthrColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class Collateral43:
    acct_id: Optional[CollateralAccount3] = field(
        default=None,
        metadata={
            "name": "AcctId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    rpt_summry: Optional[Summary2] = field(
        default=None,
        metadata={
            "name": "RptSummry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    coll_valtn: list[CollateralValuation12] = field(
        default_factory=list,
        metadata={
            "name": "CollValtn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class CollateralAndExposureReportV04:
    rpt_params: Optional[ReportParameters6] = field(
        default=None,
        metadata={
            "name": "RptParams",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    pgntn: Optional[Pagination1] = field(
        default=None,
        metadata={
            "name": "Pgntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    oblgtn: Optional[Obligation6] = field(
        default=None,
        metadata={
            "name": "Oblgtn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "required": True,
        },
    )
    agrmt: Optional[Agreement4] = field(
        default=None,
        metadata={
            "name": "Agrmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )
    coll_rpt: list[Collateral43] = field(
        default_factory=list,
        metadata={
            "name": "CollRpt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
            "min_occurs": 1,
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:colr.016.001.04"

    coll_and_xpsr_rpt: Optional[CollateralAndExposureReportV04] = field(
        default=None,
        metadata={
            "name": "CollAndXpsrRpt",
            "type": "Element",
            "required": True,
        },
    )
