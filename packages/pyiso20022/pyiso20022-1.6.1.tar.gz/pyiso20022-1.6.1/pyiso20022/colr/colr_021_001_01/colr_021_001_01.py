from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01"


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


class CalculationMethod1Code(Enum):
    SIMP = "SIMP"
    COMP = "COMP"


class CollateralEntryType1Code(Enum):
    DELI = "DELI"
    RECE = "RECE"


class CollateralRole1Code(Enum):
    GIVE = "GIVE"
    TAKE = "TAKE"


class CollateralTransactionType1Code(Enum):
    AADJ = "AADJ"
    CDTA = "CDTA"
    CADJ = "CADJ"
    DADJ = "DADJ"
    DBVT = "DBVT"
    INIT = "INIT"
    MADJ = "MADJ"
    PADJ = "PADJ"
    RATA = "RATA"
    TERM = "TERM"


class CreditDebitCode(Enum):
    CRDT = "CRDT"
    DBIT = "DBIT"


@dataclass
class CrystallisationDay1:
    day: Optional[bool] = field(
        default=None,
        metadata={
            "name": "Day",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    prd: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


class DateType2Code(Enum):
    OPEN = "OPEN"


class DeliveryReceiptType2Code(Enum):
    FREE = "FREE"
    APMT = "APMT"


class EventFrequency12Code(Enum):
    ADHO = "ADHO"
    YEAR = "YEAR"
    DAIL = "DAIL"
    TOMN = "TOMN"
    TOWK = "TOWK"
    INDA = "INDA"
    MNTH = "MNTH"
    QUTR = "QUTR"
    SEMI = "SEMI"
    TWMN = "TWMN"
    WEEK = "WEEK"
    ONDE = "ONDE"


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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    face_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "total_digits": 30,
            "fraction_digits": 29,
        },
    )


class FrequencyRateFixing1Code(Enum):
    NONE = "NONE"
    OVNG = "OVNG"
    PRDC = "PRDC"


@dataclass
class GenericIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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


class OptionType1Code(Enum):
    CALL = "CALL"
    PUTO = "PUTO"


@dataclass
class Pagination1:
    pg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "PgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "pattern": r"[0-9]{1,5}",
        },
    )
    last_pg_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "LastPgInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )


class RepoTerminationOption1Code(Enum):
    EGRN = "EGRN"
    ETSB = "ETSB"


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


@dataclass
class TransactionIdentifications44:
    trpty_agt_svc_prvdr_coll_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrCollInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    trpty_agt_svc_prvdr_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    clnt_coll_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntCollInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    clnt_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctr_pty_coll_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrPtyCollInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctr_pty_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrPtyCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cmon_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CmonTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 52,
        },
    )


class TypeOfIdentification1Code(Enum):
    ARNU = "ARNU"
    CCPT = "CCPT"
    CHTY = "CHTY"
    CORP = "CORP"
    DRLC = "DRLC"
    FIIN = "FIIN"
    TXID = "TXID"


@dataclass
class BenchmarkCurveName13Choice:
    cd: Optional[BenchmarkCurveName7Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class BlockChainAddressWallet3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class CashMovement5:
    csh_mvmnt: Optional[CollateralEntryType1Code] = field(
        default=None,
        metadata={
            "name": "CshMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    csh_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CshAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    coll_mvmnt: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CollMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    clnt_csh_mvmnt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntCshMvmntId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    trpty_agt_svc_prvdr_csh_mvmnt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrCshMvmntId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CollateralDate2:
    trad_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "TradDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    reqd_exctn_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "ReqdExctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    sttlm_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "SttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class CollateralTransactionType1Choice:
    cd: Optional[CollateralTransactionType1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class Date3Choice:
    cd: Optional[DateType2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class ExposureType23Choice:
    cd: Optional[ExposureType14Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class ForeignExchangeTerms23:
    unit_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "UnitCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    qtd_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "QtdCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    xchg_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    rsltg_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RsltgAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )


@dataclass
class Frequency38Choice:
    cd: Optional[EventFrequency12Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class FrequencyRateFixing1Choice:
    cd: Optional[FrequencyRateFixing1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    nb_of_days: Optional[str] = field(
        default=None,
        metadata={
            "name": "NbOfDays",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[0-9]{1,3}",
        },
    )


@dataclass
class IdentificationType42Choice:
    cd: Optional[TypeOfIdentification1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class InterestComputationMethodFormat4Choice:
    cd: Optional[InterestComputationMethod2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class OptionType6Choice:
    cd: Optional[OptionType1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class OtherIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    tp: Optional[IdentificationSource3Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )


@dataclass
class PostalAddress1:
    adr_tp: Optional[AddressType2Code] = field(
        default=None,
        metadata={
            "name": "AdrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class RateOrType1Choice:
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    tp: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class SecuritiesAccount19:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )


@dataclass
class TradingPartyCapacity5Choice:
    cd: Optional[TradingCapacity7Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class AlternatePartyIdentification7:
    id_tp: Optional[IdentificationType42Choice] = field(
        default=None,
        metadata={
            "name": "IdTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )
    altrn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class AmountAndDirection49:
    amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    orgnl_ccy_and_ordrd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlCcyAndOrdrdAmt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            },
        )
    )
    fxdtls: Optional[ForeignExchangeTerms23] = field(
        default=None,
        metadata={
            "name": "FXDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class ClosingDate4Choice:
    dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    cd: Optional[Date3Choice] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class CollateralParameters11:
    coll_instr_tp: Optional[CollateralTransactionType1Choice] = field(
        default=None,
        metadata={
            "name": "CollInstrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    xpsr_tp: Optional[ExposureType23Choice] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    coll_sd: Optional[CollateralRole1Code] = field(
        default=None,
        metadata={
            "name": "CollSd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    val_sght_mrgn_rate: Optional[RateOrType1Choice] = field(
        default=None,
        metadata={
            "name": "ValSghtMrgnRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    elgblty_set_prfl: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "ElgbltySetPrfl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    trf_titl: Optional[bool] = field(
        default=None,
        metadata={
            "name": "TrfTitl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    sttlm_prc: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "SttlmPrc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class NameAndAddress5:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class RateTypeAndLookback2:
    tp: Optional[BenchmarkCurveName13Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    look_bck_days: Optional[str] = field(
        default=None,
        metadata={
            "name": "LookBckDays",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[0-9]{1,3}",
        },
    )
    crstllstn_dt: Optional[CrystallisationDay1] = field(
        default=None,
        metadata={
            "name": "CrstllstnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    tnr: Optional[InterestRateIndexTenor2Code] = field(
        default=None,
        metadata={
            "name": "Tnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[A-Z]{3,3}",
        },
    )


@dataclass
class SecurityIdentification19:
    isin: Optional[str] = field(
        default=None,
        metadata={
            "name": "ISIN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[A-Z]{2,2}[A-Z0-9]{9,9}[0-9]{1,1}",
        },
    )
    othr_id: list[OtherIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "OthrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class CollateralAmount12:
    tx: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "Tx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    termntn: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "Termntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    acrd: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "Acrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    cmpnd_smpl_acrl_clctn: Optional[CalculationMethod1Code] = field(
        default=None,
        metadata={
            "name": "CmpndSmplAcrlClctn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    pmt_frqcy: Optional[Frequency38Choice] = field(
        default=None,
        metadata={
            "name": "PmtFrqcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    intrst_pmt_dely: Optional[str] = field(
        default=None,
        metadata={
            "name": "IntrstPmtDely",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[0-9]{1,3}",
        },
    )
    val_sght: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "ValSght",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class PartyIdentification120Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    nm_and_adr: Optional[NameAndAddress5] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class RateOrName4Choice:
    rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    rate_indx_dtls: Optional[RateTypeAndLookback2] = field(
        default=None,
        metadata={
            "name": "RateIndxDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class SecuritiesMovement7:
    scties_mvmnt_tp: Optional[CollateralEntryType1Code] = field(
        default=None,
        metadata={
            "name": "SctiesMvmntTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    fin_instrm_id: Optional[SecurityIdentification19] = field(
        default=None,
        metadata={
            "name": "FinInstrmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    qty: Optional[FinancialInstrumentQuantity33Choice] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    coll_mvmnt: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CollMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    clnt_scties_mvmnt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntSctiesMvmntId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    trpty_agt_svc_prvdr_scties_mvmnt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrSctiesMvmntId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class DealTransactionDetails6:
    min_ntce_prd: Optional[str] = field(
        default=None,
        metadata={
            "name": "MinNtcePrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[0-9]{3}",
        },
    )
    clsg_dt: Optional[ClosingDate4Choice] = field(
        default=None,
        metadata={
            "name": "ClsgDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    deal_dtls_amt: Optional[CollateralAmount12] = field(
        default=None,
        metadata={
            "name": "DealDtlsAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    pricg_rate_and_indx: Optional[RateOrName4Choice] = field(
        default=None,
        metadata={
            "name": "PricgRateAndIndx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    ovrnght_frqcy_rate_fxg: Optional[FrequencyRateFixing1Choice] = field(
        default=None,
        metadata={
            "name": "OvrnghtFrqcyRateFxg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    sprd: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Sprd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    day_cnt_bsis: Optional[InterestComputationMethodFormat4Choice] = field(
        default=None,
        metadata={
            "name": "DayCntBsis",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    pmt: Optional[DeliveryReceiptType2Code] = field(
        default=None,
        metadata={
            "name": "Pmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    optn_tp: Optional[OptionType6Choice] = field(
        default=None,
        metadata={
            "name": "OptnTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    termntn_optn: Optional[RepoTerminationOption1Code] = field(
        default=None,
        metadata={
            "name": "TermntnOptn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class PartyIdentification136:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )


@dataclass
class PartyIdentificationAndAccount193:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class PartyIdentificationAndAccount203:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    pty_cpcty: Optional[TradingPartyCapacity5Choice] = field(
        default=None,
        metadata={
            "name": "PtyCpcty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class PartyIdentificationAndAccount202:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    acct_ownr: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "AcctOwnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    pty_cpcty: Optional[TradingPartyCapacity5Choice] = field(
        default=None,
        metadata={
            "name": "PtyCpcty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class CollateralParties8:
    pty_a: Optional[PartyIdentificationAndAccount202] = field(
        default=None,
        metadata={
            "name": "PtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    clnt_pty_a: Optional[PartyIdentificationAndAccount193] = field(
        default=None,
        metadata={
            "name": "ClntPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    pty_b: Optional[PartyIdentificationAndAccount203] = field(
        default=None,
        metadata={
            "name": "PtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    clnt_pty_b: Optional[PartyIdentificationAndAccount193] = field(
        default=None,
        metadata={
            "name": "ClntPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    trpty_agt: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "TrptyAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class TripartyCollateralAllegementNotificationV01:
    tx_instr_id: Optional[TransactionIdentifications44] = field(
        default=None,
        metadata={
            "name": "TxInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    pgntn: Optional[Pagination1] = field(
        default=None,
        metadata={
            "name": "Pgntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    gnl_params: Optional[CollateralParameters11] = field(
        default=None,
        metadata={
            "name": "GnlParams",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    coll_pties: Optional[CollateralParties8] = field(
        default=None,
        metadata={
            "name": "CollPties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    deal_tx_dtls: Optional[DealTransactionDetails6] = field(
        default=None,
        metadata={
            "name": "DealTxDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    deal_tx_dt: Optional[CollateralDate2] = field(
        default=None,
        metadata={
            "name": "DealTxDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
            "required": True,
        },
    )
    scties_mvmnt: list[SecuritiesMovement7] = field(
        default_factory=list,
        metadata={
            "name": "SctiesMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    csh_mvmnt: list[CashMovement5] = field(
        default_factory=list,
        metadata={
            "name": "CshMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:colr.021.001.01"

    trpty_coll_allgmt_ntfctn: Optional[
        TripartyCollateralAllegementNotificationV01
    ] = field(
        default=None,
        metadata={
            "name": "TrptyCollAllgmtNtfctn",
            "type": "Element",
            "required": True,
        },
    )
