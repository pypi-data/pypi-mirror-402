from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01"


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


class CancelledStatusReason17Code(Enum):
    CANI = "CANI"
    OTHR = "OTHR"
    CSUB = "CSUB"
    CANS = "CANS"


@dataclass
class CashAccountIdentification5Choice:
    iban: Optional[str] = field(
        default=None,
        metadata={
            "name": "IBAN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "pattern": r"[A-Z]{2,2}[0-9]{2,2}[a-zA-Z0-9]{1,30}",
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 34,
        },
    )


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


class CreditDebit3Code(Enum):
    CRDT = "CRDT"
    DBIT = "DBIT"


class CreditDebitCode(Enum):
    CRDT = "CRDT"
    DBIT = "DBIT"


@dataclass
class DateAndDateTime2Choice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


class DateType2Code(Enum):
    OPEN = "OPEN"


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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "total_digits": 18,
            "fraction_digits": 17,
        },
    )
    face_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "total_digits": 30,
            "fraction_digits": 29,
        },
    )


@dataclass
class GenericIdentification30:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 4,
        },
    )
    prtry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


class NoReasonCode(Enum):
    NORE = "NORE"


@dataclass
class OriginalAndCurrentQuantities1:
    face_amt: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FaceAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
            "pattern": r"[0-9]{1,5}",
        },
    )
    last_pg_ind: Optional[bool] = field(
        default=None,
        metadata={
            "name": "LastPgInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )


class PendingReason17Code(Enum):
    CONF = "CONF"


class ReceiveDelivery1Code(Enum):
    DELI = "DELI"
    RECE = "RECE"


class RejectionReason62Code(Enum):
    REFE = "REFE"
    ADEA = "ADEA"
    CCIX = "CCIX"
    CCTI = "CCTI"
    IIND = "IIND"
    PTYA = "PTYA"
    PTYB = "PTYB"
    ITPA = "ITPA"
    LATE = "LATE"
    SAFA = "SAFA"
    SAFB = "SAFB"
    REDT = "REDT"
    SEPR = "SEPR"
    LBDR = "LBDR"
    DCBR = "DCBR"
    CSAC = "CSAC"
    TERM = "TERM"
    DTRD = "DTRD"
    DDAT = "DDAT"
    NCRR = "NCRR"
    IESP = "IESP"
    IEXT = "IEXT"
    IPBI = "IPBI"
    IRIT = "IRIT"
    TMAC = "TMAC"
    REPA = "REPA"
    TXAC = "TXAC"
    NRGM = "NRGM"
    TABC = "TABC"
    ICTT = "ICTT"
    NRJN = "NRJN"
    NFCA = "NFCA"
    CTRA = "CTRA"


class RejectionReason63Code(Enum):
    REFE = "REFE"
    ADEA = "ADEA"
    CCIX = "CCIX"
    CCTI = "CCTI"
    IIND = "IIND"
    PTYA = "PTYA"
    PTYB = "PTYB"
    LATE = "LATE"
    ITPA = "ITPA"
    SAFA = "SAFA"
    SAFB = "SAFB"
    REDT = "REDT"
    DCAN = "DCAN"
    DPRG = "DPRG"
    RSET = "RSET"
    RREP = "RREP"
    NRJN = "NRJN"


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
class TransactionIdentifications46:
    clnt_coll_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntCollInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    clnt_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    trpty_agt_svc_prvdr_coll_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrCollInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    trpty_agt_svc_prvdr_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctr_pty_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrPtyCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cmon_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CmonTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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


class UnmatchedReason15Code(Enum):
    CPCA = "CPCA"
    DCBS = "DCBS"
    TMOP = "TMOP"
    OPTP = "OPTP"
    OFRF = "OFRF"
    SPRD = "SPRD"
    RITP = "RITP"
    RATE = "RATE"
    TMCY = "TMCY"
    TXCY = "TXCY"
    TXAM = "TXAM"
    MNTP = "MNTP"
    EGSP = "EGSP"
    EXPO = "EXPO"
    DTRD = "DTRD"
    REDT = "REDT"
    CMIS = "CMIS"
    TFRT = "TFRT"
    TERM = "TERM"
    INPD = "INPD"
    PYFQ = "PYFQ"
    CSAC = "CSAC"
    LBKD = "LBKD"
    CRYD = "CRYD"
    TENO = "TENO"
    SEPR = "SEPR"


@dataclass
class BlockChainAddressWallet3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class CancellationReason38Choice:
    cd: Optional[CancelledStatusReason17Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class CollateralDate2:
    trad_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "TradDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    reqd_exctn_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "ReqdExctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    sttlm_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "SttlmDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class CollateralTransactionType1Choice:
    cd: Optional[CollateralTransactionType1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class Date3Choice:
    cd: Optional[DateType2Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class ExposureType23Choice:
    cd: Optional[ExposureType14Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class ForeignExchangeTerms23:
    unit_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "UnitCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    qtd_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "QtdCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    xchg_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )


@dataclass
class IdentificationType42Choice:
    cd: Optional[TypeOfIdentification1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class OtherIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    tp: Optional[IdentificationSource3Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )


@dataclass
class PendingReason52Choice:
    cd: Optional[PendingReason17Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class PostalAddress1:
    adr_tp: Optional[AddressType2Code] = field(
        default=None,
        metadata={
            "name": "AdrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class ProprietaryReason4:
    rsn: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    addtl_rsn_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 210,
        },
    )


@dataclass
class Quantity51Choice:
    qty: Optional[FinancialInstrumentQuantity33Choice] = field(
        default=None,
        metadata={
            "name": "Qty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    orgnl_and_cur_face: Optional[OriginalAndCurrentQuantities1] = field(
        default=None,
        metadata={
            "name": "OrgnlAndCurFace",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class RejectionReason39Choice:
    cd: Optional[RejectionReason62Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class RejectionReason40Choice:
    cd: Optional[RejectionReason63Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class SecuritiesAccount19:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class UnmatchedReason30Choice:
    cd: Optional[UnmatchedReason15Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class AlternatePartyIdentification7:
    id_tp: Optional[IdentificationType42Choice] = field(
        default=None,
        metadata={
            "name": "IdTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )
    altrn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class AmountAndDirection44:
    amt: Optional[ActiveOrHistoricCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    orgnl_ccy_and_ordrd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlCcyAndOrdrdAmt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            },
        )
    )
    fxdtls: Optional[ForeignExchangeTerms23] = field(
        default=None,
        metadata={
            "name": "FXDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class AmountAndDirection49:
    amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    orgnl_ccy_and_ordrd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlCcyAndOrdrdAmt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            },
        )
    )
    fxdtls: Optional[ForeignExchangeTerms23] = field(
        default=None,
        metadata={
            "name": "FXDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class CancellationReason29:
    cd: Optional[CancellationReason38Choice] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    addtl_rsn_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 210,
        },
    )


@dataclass
class ClosingDate4Choice:
    dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    cd: Optional[Date3Choice] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class CollateralParameters12:
    coll_instr_tp: Optional[CollateralTransactionType1Choice] = field(
        default=None,
        metadata={
            "name": "CollInstrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    xpsr_tp: Optional[ExposureType23Choice] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    coll_sd: Optional[CollateralRole1Code] = field(
        default=None,
        metadata={
            "name": "CollSd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    sttlm_prc: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "SttlmPrc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prty: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    automtc_allcn: Optional[bool] = field(
        default=None,
        metadata={
            "name": "AutomtcAllcn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    coll_apprvd: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CollApprvd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    sttlm_apprvd: Optional[bool] = field(
        default=None,
        metadata={
            "name": "SttlmApprvd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class NameAndAddress5:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class PendingReason27:
    cd: Optional[PendingReason52Choice] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    addtl_rsn_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 210,
        },
    )


@dataclass
class ProprietaryStatusAndReason6:
    prtry_sts: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "PrtrySts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    prtry_rsn: list[ProprietaryReason4] = field(
        default_factory=list,
        metadata={
            "name": "PrtryRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class RejectionReason54:
    cd: Optional[RejectionReason39Choice] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    addtl_rsn_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 210,
        },
    )


@dataclass
class RejectionReason55:
    cd: Optional[RejectionReason40Choice] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    addtl_rsn_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 210,
        },
    )


@dataclass
class SecuritiesMovementStatus1Choice:
    amt: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    csh: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Csh",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    ccy: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Ccy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    excld: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Excld",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    futr: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Futr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    pdg: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Pdg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    mnly_accptd: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "MnlyAccptd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    elgblty: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Elgblty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    tax: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Tax",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    wait: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Wait",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class SecurityIdentification19:
    isin: Optional[str] = field(
        default=None,
        metadata={
            "name": "ISIN",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "pattern": r"[A-Z]{2,2}[A-Z0-9]{9,9}[0-9]{1,1}",
        },
    )
    othr_id: list[OtherIdentification1] = field(
        default_factory=list,
        metadata={
            "name": "OthrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class UnmatchedReason21:
    cd: Optional[UnmatchedReason30Choice] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    addtl_rsn_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 210,
        },
    )


@dataclass
class CancellationStatus29Choice:
    no_spcfd_rsn: Optional[NoReasonCode] = field(
        default=None,
        metadata={
            "name": "NoSpcfdRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    rsn: list[CancellationReason29] = field(
        default_factory=list,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class CashMovement7:
    csh_mvmnt: Optional[CreditDebit3Code] = field(
        default=None,
        metadata={
            "name": "CshMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    csh_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CshAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    csh_acct: Optional[CashAccountIdentification5Choice] = field(
        default=None,
        metadata={
            "name": "CshAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    mvmnt_sts: Optional[ProprietaryStatusAndReason6] = field(
        default=None,
        metadata={
            "name": "MvmntSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    coll_mvmnt: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CollMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    csh_mvmnt_apprvd: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CshMvmntApprvd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    pos_tp: Optional[bool] = field(
        default=None,
        metadata={
            "name": "PosTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    clnt_csh_mvmnt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntCshMvmntId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    trpty_agt_svc_prvdr_csh_mvmnt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrCshMvmntId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class CollateralAmount14:
    tx: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "Tx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    termntn: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "Termntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    acrd: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "Acrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    val_sght: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "ValSght",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    udsptd_tx: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "UdsptdTx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class PartyIdentification120Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    nm_and_adr: Optional[NameAndAddress5] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class PendingStatus56Choice:
    no_spcfd_rsn: Optional[NoReasonCode] = field(
        default=None,
        metadata={
            "name": "NoSpcfdRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    rsn: Optional[PendingReason27] = field(
        default=None,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class RejectionStatus33Choice:
    no_spcfd_rsn: Optional[NoReasonCode] = field(
        default=None,
        metadata={
            "name": "NoSpcfdRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    rsn: list[RejectionReason54] = field(
        default_factory=list,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class RejectionStatus34Choice:
    no_spcfd_rsn: Optional[NoReasonCode] = field(
        default=None,
        metadata={
            "name": "NoSpcfdRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    rsn: list[RejectionReason55] = field(
        default_factory=list,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class SecuritiesMovement8:
    scties_mvmnt_tp: Optional[ReceiveDelivery1Code] = field(
        default=None,
        metadata={
            "name": "SctiesMvmntTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    fin_instrm_id: Optional[SecurityIdentification19] = field(
        default=None,
        metadata={
            "name": "FinInstrmId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    scties_qty: Optional[Quantity51Choice] = field(
        default=None,
        metadata={
            "name": "SctiesQty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    mvmnt_sts: Optional[SecuritiesMovementStatus1Choice] = field(
        default=None,
        metadata={
            "name": "MvmntSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    coll_mvmnt: Optional[bool] = field(
        default=None,
        metadata={
            "name": "CollMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    scties_mvmnts_apprvd: Optional[bool] = field(
        default=None,
        metadata={
            "name": "SctiesMvmntsApprvd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    pos_tp: Optional[bool] = field(
        default=None,
        metadata={
            "name": "PosTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    clnt_scties_mvmnt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntSctiesMvmntId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    trpty_agt_svc_prvdr_scties_mvmnt_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TrptyAgtSvcPrvdrSctiesMvmntId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    mrgnd_val: Optional[AmountAndDirection44] = field(
        default=None,
        metadata={
            "name": "MrgndVal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class UnmatchedStatus22Choice:
    no_spcfd_rsn: Optional[NoReasonCode] = field(
        default=None,
        metadata={
            "name": "NoSpcfdRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    rsn: list[UnmatchedReason21] = field(
        default_factory=list,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class CancellationStatus30Choice:
    canc: Optional[CancellationStatus29Choice] = field(
        default=None,
        metadata={
            "name": "Canc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prcd: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Prcd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    pdg: Optional[PendingStatus56Choice] = field(
        default=None,
        metadata={
            "name": "Pdg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    rjctd: Optional[RejectionStatus34Choice] = field(
        default=None,
        metadata={
            "name": "Rjctd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[ProprietaryStatusAndReason6] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class DealTransactionDetails7:
    clsg_dt: Optional[ClosingDate4Choice] = field(
        default=None,
        metadata={
            "name": "ClsgDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    deal_dtls_amt: Optional[CollateralAmount14] = field(
        default=None,
        metadata={
            "name": "DealDtlsAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class MatchingStatus33Choice:
    mtchd: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Mtchd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    umtchd: Optional[UnmatchedStatus22Choice] = field(
        default=None,
        metadata={
            "name": "Umtchd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[ProprietaryStatusAndReason6] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class PartyIdentification136:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class PartyIdentificationAndAccount203:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    pty_cpcty: Optional[TradingPartyCapacity5Choice] = field(
        default=None,
        metadata={
            "name": "PtyCpcty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class ProcessingStatus82Choice:
    prcd: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Prcd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    futr: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "Futr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    rjctd: Optional[RejectionStatus33Choice] = field(
        default=None,
        metadata={
            "name": "Rjctd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    canc: Optional[CancellationStatus29Choice] = field(
        default=None,
        metadata={
            "name": "Canc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    pdg_cxl: Optional[PendingStatus56Choice] = field(
        default=None,
        metadata={
            "name": "PdgCxl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    cxl_req: Optional[ProprietaryReason4] = field(
        default=None,
        metadata={
            "name": "CxlReq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    prtry: Optional[ProprietaryStatusAndReason6] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class PartyIdentificationAndAccount202:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    acct_ownr: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "AcctOwnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    pty_cpcty: Optional[TradingPartyCapacity5Choice] = field(
        default=None,
        metadata={
            "name": "PtyCpcty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class CollateralParties8:
    pty_a: Optional[PartyIdentificationAndAccount202] = field(
        default=None,
        metadata={
            "name": "PtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    clnt_pty_a: Optional[PartyIdentificationAndAccount193] = field(
        default=None,
        metadata={
            "name": "ClntPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    pty_b: Optional[PartyIdentificationAndAccount203] = field(
        default=None,
        metadata={
            "name": "PtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    clnt_pty_b: Optional[PartyIdentificationAndAccount193] = field(
        default=None,
        metadata={
            "name": "ClntPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    trpty_agt: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "TrptyAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class TripartyCollateralTransactionInstructionProcessingStatusAdviceV01:
    tx_instr_id: Optional[TransactionIdentifications46] = field(
        default=None,
        metadata={
            "name": "TxInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    cxl_req_ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "CxlReqRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    pgntn: Optional[Pagination1] = field(
        default=None,
        metadata={
            "name": "Pgntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    instr_prcg_sts: Optional[ProcessingStatus82Choice] = field(
        default=None,
        metadata={
            "name": "InstrPrcgSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    mtchg_sts: Optional[MatchingStatus33Choice] = field(
        default=None,
        metadata={
            "name": "MtchgSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    cxl_prcg_sts: Optional[CancellationStatus30Choice] = field(
        default=None,
        metadata={
            "name": "CxlPrcgSts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    gnl_params: Optional[CollateralParameters12] = field(
        default=None,
        metadata={
            "name": "GnlParams",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    coll_pties: Optional[CollateralParties8] = field(
        default=None,
        metadata={
            "name": "CollPties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    deal_tx_dtls: Optional[DealTransactionDetails7] = field(
        default=None,
        metadata={
            "name": "DealTxDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    deal_tx_dt: Optional[CollateralDate2] = field(
        default=None,
        metadata={
            "name": "DealTxDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
            "required": True,
        },
    )
    scties_mvmnt: list[SecuritiesMovement8] = field(
        default_factory=list,
        metadata={
            "name": "SctiesMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    csh_mvmnt: list[CashMovement7] = field(
        default_factory=list,
        metadata={
            "name": "CshMvmnt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:colr.020.001.01"

    trpty_coll_tx_instr_prcg_sts_advc: Optional[
        TripartyCollateralTransactionInstructionProcessingStatusAdviceV01
    ] = field(
        default=None,
        metadata={
            "name": "TrptyCollTxInstrPrcgStsAdvc",
            "type": "Element",
            "required": True,
        },
    )
