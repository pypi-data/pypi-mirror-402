from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04"


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


class AgreementFramework1Code(Enum):
    FBAA = "FBAA"
    BBAA = "BBAA"
    DERV = "DERV"
    ISDA = "ISDA"
    NONR = "NONR"


class CollateralAccountType1Code(Enum):
    HOUS = "HOUS"
    CLIE = "CLIE"
    LIPR = "LIPR"
    MGIN = "MGIN"
    DFLT = "DFLT"


@dataclass
class DateAndDateTimeChoice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


class ExposureConventionType1Code(Enum):
    GROS = "GROS"
    NET1 = "NET1"


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


@dataclass
class GenericIdentification30:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )


class IndependentAmountConventionType1Code(Enum):
    NBTR = "NBTR"
    NATR = "NATR"
    SEGR = "SEGR"


class MarginCallResponse1Code(Enum):
    NVDA = "NVDA"
    RANT = "RANT"


@dataclass
class PostalAddress2:
    strt_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "StrtNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pst_cd_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCdId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


class RoundingMethod1Code(Enum):
    DRDW = "DRDW"
    DRUP = "DRUP"
    NONE = "NONE"
    CLSR = "CLSR"


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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    prtry_id: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class Amount1:
    agrd_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "AgrdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    mrgn_call_req_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MrgnCallReqId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    addtl_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 210,
        },
    )


@dataclass
class CollateralAccountIdentificationType2Choice:
    tp: Optional[CollateralAccountType1Code] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    prtry: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class IndependentAmount1:
    amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    cnvntn: Optional[IndependentAmountConventionType1Code] = field(
        default=None,
        metadata={
            "name": "Cnvntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )


@dataclass
class IndependentAmount2:
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 140,
        },
    )
    amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "Amt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    cnvntn: Optional[IndependentAmountConventionType1Code] = field(
        default=None,
        metadata={
            "name": "Cnvntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )


@dataclass
class MarginCollateral1:
    held_by_pty_a: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "HeldByPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    held_by_pty_b: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "HeldByPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    prr_agrd_to_pty_a: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "PrrAgrdToPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    prr_agrd_to_pty_b: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "PrrAgrdToPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    in_trnst_to_pty_a: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "InTrnstToPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    in_trnst_to_pty_b: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "InTrnstToPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class NameAndAddress6:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )


@dataclass
class ResponseType1Choice:
    cd: Optional[MarginCallResponse1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class SegregatedIndependentAmountMargin1:
    min_trf_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "MinTrfAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    rndg_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RndgAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    rndg_mtd: Optional[RoundingMethod1Code] = field(
        default=None,
        metadata={
            "name": "RndgMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class SupplementaryData1:
    plc_and_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlcAndNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )


@dataclass
class VariationMargin1:
    thrshld_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "ThrshldAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    thrshld_tp: Optional[ThresholdType1Code] = field(
        default=None,
        metadata={
            "name": "ThrshldTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    min_trf_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "MinTrfAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    rndg_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RndgAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    rndg_mtd: Optional[RoundingMethod1Code] = field(
        default=None,
        metadata={
            "name": "RndgMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )


@dataclass
class AggregatedIndependentAmount1:
    trad: Optional[IndependentAmount1] = field(
        default=None,
        metadata={
            "name": "Trad",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    val_at_rsk: Optional[IndependentAmount1] = field(
        default=None,
        metadata={
            "name": "ValAtRsk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    net_opn_pos: Optional[IndependentAmount1] = field(
        default=None,
        metadata={
            "name": "NetOpnPos",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    othr_amt: list[IndependentAmount2] = field(
        default_factory=list,
        metadata={
            "name": "OthrAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class AgreedAmount1:
    vartn_mrgn_amt: Optional[Amount1] = field(
        default=None,
        metadata={
            "name": "VartnMrgnAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    sgrtd_indpdnt_amt: Optional[Amount1] = field(
        default=None,
        metadata={
            "name": "SgrtdIndpdntAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class Agreement4:
    agrmt_dtls: Optional[str] = field(
        default=None,
        metadata={
            "name": "AgrmtDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 140,
        },
    )
    agrmt_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "AgrmtDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    base_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "BaseCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    agrmt_frmwk: Optional[AgreementFramework1Choice] = field(
        default=None,
        metadata={
            "name": "AgrmtFrmwk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class Collateral1:
    vartn_mrgn: Optional[MarginCollateral1] = field(
        default=None,
        metadata={
            "name": "VartnMrgn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    sgrtd_indpdnt_amt: Optional[MarginCollateral1] = field(
        default=None,
        metadata={
            "name": "SgrtdIndpdntAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class CollateralAccount2:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    tp: Optional[CollateralAccountIdentificationType2Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class Margin1:
    vartn_mrgn: Optional[VariationMargin1] = field(
        default=None,
        metadata={
            "name": "VartnMrgn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    sgrtd_indpdnt_amt_mrgn: Optional[SegregatedIndependentAmountMargin1] = (
        field(
            default=None,
            metadata={
                "name": "SgrtdIndpdntAmtMrgn",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            },
        )
    )


@dataclass
class PartyIdentification100Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    nm_and_adr: Optional[NameAndAddress6] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class Response1:
    rspn_tp_dtls: list[ResponseType1Choice] = field(
        default_factory=list,
        metadata={
            "name": "RspnTpDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_occurs": 1,
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class AgreedAmount1Choice:
    agrd_amt_dtls: Optional[AgreedAmount1] = field(
        default=None,
        metadata={
            "name": "AgrdAmtDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    sgrtd_indpdnt_amt: Optional[Amount1] = field(
        default=None,
        metadata={
            "name": "SgrtdIndpdntAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class CollateralBalance1Choice:
    ttl_coll: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "TtlColl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    coll_dtls: Optional[Collateral1] = field(
        default=None,
        metadata={
            "name": "CollDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    sgrtd_indpdnt_amt: Optional[MarginCollateral1] = field(
        default=None,
        metadata={
            "name": "SgrtdIndpdntAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class MarginTerms1Choice:
    mrgn_dtls: Optional[Margin1] = field(
        default=None,
        metadata={
            "name": "MrgnDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    sgrtd_indpdnt_amt_mrgn: Optional[SegregatedIndependentAmountMargin1] = (
        field(
            default=None,
            metadata={
                "name": "SgrtdIndpdntAmtMrgn",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            },
        )
    )


@dataclass
class Obligation4:
    pty_a: Optional[PartyIdentification100Choice] = field(
        default=None,
        metadata={
            "name": "PtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    svcg_pty_a: Optional[PartyIdentification100Choice] = field(
        default=None,
        metadata={
            "name": "SvcgPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    pty_b: Optional[PartyIdentification100Choice] = field(
        default=None,
        metadata={
            "name": "PtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    svcg_pty_b: Optional[PartyIdentification100Choice] = field(
        default=None,
        metadata={
            "name": "SvcgPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    coll_acct_id: Optional[CollateralAccount2] = field(
        default=None,
        metadata={
            "name": "CollAcctId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    xpsr_tp: Optional[ExposureType5Code] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    valtn_dt: Optional[DateAndDateTimeChoice] = field(
        default=None,
        metadata={
            "name": "ValtnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )


@dataclass
class MarginCall1:
    xpsd_amt_pty_a: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "XpsdAmtPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    xpsd_amt_pty_b: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "XpsdAmtPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    xpsr_cnvntn: Optional[ExposureConventionType1Code] = field(
        default=None,
        metadata={
            "name": "XpsrCnvntn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    indpdnt_amt_pty_a: Optional[AggregatedIndependentAmount1] = field(
        default=None,
        metadata={
            "name": "IndpdntAmtPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    indpdnt_amt_pty_b: Optional[AggregatedIndependentAmount1] = field(
        default=None,
        metadata={
            "name": "IndpdntAmtPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    mrgn_terms: Optional[MarginTerms1Choice] = field(
        default=None,
        metadata={
            "name": "MrgnTerms",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    coll_bal: Optional[CollateralBalance1Choice] = field(
        default=None,
        metadata={
            "name": "CollBal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class MarginCallResponseV04:
    tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    oblgtn: Optional[Obligation4] = field(
        default=None,
        metadata={
            "name": "Oblgtn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
            "required": True,
        },
    )
    agrmt: Optional[Agreement4] = field(
        default=None,
        metadata={
            "name": "Agrmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    mrgn_dtls_due_to_a: Optional[MarginCall1] = field(
        default=None,
        metadata={
            "name": "MrgnDtlsDueToA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    mrgn_dtls_due_to_b: Optional[MarginCall1] = field(
        default=None,
        metadata={
            "name": "MrgnDtlsDueToB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    agrd_amt_due_to_a: Optional[AgreedAmount1Choice] = field(
        default=None,
        metadata={
            "name": "AgrdAmtDueToA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    agrd_amt_due_to_b: Optional[AgreedAmount1Choice] = field(
        default=None,
        metadata={
            "name": "AgrdAmtDueToB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    rspn_dtls: Optional[Response1] = field(
        default=None,
        metadata={
            "name": "RspnDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:colr.004.001.04"

    mrgn_call_rspn: Optional[MarginCallResponseV04] = field(
        default=None,
        metadata={
            "name": "MrgnCallRspn",
            "type": "Element",
            "required": True,
        },
    )
