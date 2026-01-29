from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01"


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
class DateAndDateTime2Choice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


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
class GenericIdentification1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    clnt_coll_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntCollInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    clnt_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ClntCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctr_pty_coll_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrPtyCollInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctr_pty_coll_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrPtyCollTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    cmon_tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CmonTxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
class BlockChainAddressWallet3:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class CollateralTransactionType1Choice:
    cd: Optional[CollateralTransactionType1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class ExposureType23Choice:
    cd: Optional[ExposureType14Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class ForeignExchangeTerms23:
    unit_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "UnitCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    qtd_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "QtdCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    xchg_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "XchgRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class PostalAddress1:
    adr_tp: Optional[AddressType2Code] = field(
        default=None,
        metadata={
            "name": "AdrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class SecuritiesAccount19:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class AlternatePartyIdentification7:
    id_tp: Optional[IdentificationType42Choice] = field(
        default=None,
        metadata={
            "name": "IdTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )
    altrn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    cdt_dbt_ind: Optional[CreditDebitCode] = field(
        default=None,
        metadata={
            "name": "CdtDbtInd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    orgnl_ccy_and_ordrd_amt: Optional[ActiveOrHistoricCurrencyAndAmount] = (
        field(
            default=None,
            metadata={
                "name": "OrgnlCcyAndOrdrdAmt",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            },
        )
    )
    fxdtls: Optional[ForeignExchangeTerms23] = field(
        default=None,
        metadata={
            "name": "FXDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class NameAndAddress5:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class PartyIdentification120Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    nm_and_adr: Optional[NameAndAddress5] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class PartyIdentification136:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class PartyIdentificationAndAccount203:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    pty_cpcty: Optional[TradingPartyCapacity5Choice] = field(
        default=None,
        metadata={
            "name": "PtyCpcty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class PartyIdentificationAndAccount202:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )
    altrn_id: Optional[AlternatePartyIdentification7] = field(
        default=None,
        metadata={
            "name": "AltrnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    sfkpg_acct: Optional[SecuritiesAccount19] = field(
        default=None,
        metadata={
            "name": "SfkpgAcct",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    blck_chain_adr_or_wllt: Optional[BlockChainAddressWallet3] = field(
        default=None,
        metadata={
            "name": "BlckChainAdrOrWllt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    acct_ownr: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "AcctOwnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    pty_cpcty: Optional[TradingPartyCapacity5Choice] = field(
        default=None,
        metadata={
            "name": "PtyCpcty",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class CollateralParties8:
    pty_a: Optional[PartyIdentificationAndAccount202] = field(
        default=None,
        metadata={
            "name": "PtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    clnt_pty_a: Optional[PartyIdentificationAndAccount193] = field(
        default=None,
        metadata={
            "name": "ClntPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    pty_b: Optional[PartyIdentificationAndAccount203] = field(
        default=None,
        metadata={
            "name": "PtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    clnt_pty_b: Optional[PartyIdentificationAndAccount193] = field(
        default=None,
        metadata={
            "name": "ClntPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    trpty_agt: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "TrptyAgt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class TripartyCollateralAllegementNotificationCancellationAdviceV01:
    tx_instr_id: Optional[TransactionIdentifications44] = field(
        default=None,
        metadata={
            "name": "TxInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    coll_tx_tp: Optional[CollateralTransactionType1Choice] = field(
        default=None,
        metadata={
            "name": "CollTxTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    xpsr_tp: Optional[ExposureType23Choice] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    coll_sd: Optional[CollateralRole1Code] = field(
        default=None,
        metadata={
            "name": "CollSd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    elgblty_set_prfl: Optional[GenericIdentification1] = field(
        default=None,
        metadata={
            "name": "ElgbltySetPrfl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    coll_pties: Optional[CollateralParties8] = field(
        default=None,
        metadata={
            "name": "CollPties",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
            "required": True,
        },
    )
    tx_amt: Optional[AmountAndDirection49] = field(
        default=None,
        metadata={
            "name": "TxAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    reqd_exctn_dt: Optional[DateAndDateTime2Choice] = field(
        default=None,
        metadata={
            "name": "ReqdExctnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )
    splmtry_data: Optional[SupplementaryData1] = field(
        default=None,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:colr.024.001.01"

    trpty_coll_allgmt_ntfctn_cxl_advc: Optional[
        TripartyCollateralAllegementNotificationCancellationAdviceV01
    ] = field(
        default=None,
        metadata={
            "name": "TrptyCollAllgmtNtfctnCxlAdvc",
            "type": "Element",
            "required": True,
        },
    )
