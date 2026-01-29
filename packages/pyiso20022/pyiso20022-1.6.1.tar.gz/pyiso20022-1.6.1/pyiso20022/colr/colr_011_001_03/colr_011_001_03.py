from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03"


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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )


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
class GenericIdentification29:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class PostalAddress2:
    strt_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "StrtNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pst_cd_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCdId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


class RejectionReasonV021Code(Enum):
    DSEC = "DSEC"
    EVNM = "EVNM"
    UKWN = "UKWN"
    ICOL = "ICOL"
    CONL = "CONL"
    ELIG = "ELIG"
    INID = "INID"
    OTHR = "OTHR"


class Status4Code(Enum):
    REJT = "REJT"
    PACK = "PACK"


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
class AgreementFramework1Choice:
    agrmt_frmwk: Optional[AgreementFramework1Code] = field(
        default=None,
        metadata={
            "name": "AgrmtFrmwk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    prtry_id: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )


@dataclass
class CollateralAccountIdentificationType1Choice:
    tp: Optional[CollateralAccountType1Code] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    prtry: Optional[GenericIdentification29] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )


@dataclass
class CollateralSubstitutionResponse1:
    coll_sbstitn_req_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CollSbstitnReqId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    accptd_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "AccptdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )


@dataclass
class CollateralSubstitutionResponse2:
    coll_sbstitn_req_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "CollSbstitnReqId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    rjctd_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "RjctdAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )
    rjctn_rsn: Optional[RejectionReasonV021Code] = field(
        default=None,
        metadata={
            "name": "RjctnRsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )
    rjctn_rsn_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "RjctnRsnInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class NameAndAddress6:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )


@dataclass
class SupplementaryData1:
    plc_and_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlcAndNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )


@dataclass
class Agreement2:
    agrmt_dtls: Optional[str] = field(
        default=None,
        metadata={
            "name": "AgrmtDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "min_length": 1,
            "max_length": 140,
        },
    )
    agrmt_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "AgrmtDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )
    base_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "BaseCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    agrmt_frmwk: Optional[AgreementFramework1Choice] = field(
        default=None,
        metadata={
            "name": "AgrmtFrmwk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )


@dataclass
class CollateralAccount1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    tp: Optional[CollateralAccountIdentificationType1Choice] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class PartyIdentification33Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification29] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    nm_and_adr: Optional[NameAndAddress6] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )


@dataclass
class SubstitutionResponse1:
    rspn_tp: Optional[Status4Code] = field(
        default=None,
        metadata={
            "name": "RspnTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )
    coll_sbstitn_accptnc_dtls: Optional[CollateralSubstitutionResponse1] = (
        field(
            default=None,
            metadata={
                "name": "CollSbstitnAccptncDtls",
                "type": "Element",
                "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            },
        )
    )
    coll_sbstitn_rjctn_dtls: Optional[CollateralSubstitutionResponse2] = field(
        default=None,
        metadata={
            "name": "CollSbstitnRjctnDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )


@dataclass
class Obligation3:
    pty_a: Optional[PartyIdentification33Choice] = field(
        default=None,
        metadata={
            "name": "PtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )
    svcg_pty_a: Optional[PartyIdentification33Choice] = field(
        default=None,
        metadata={
            "name": "SvcgPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    pty_b: Optional[PartyIdentification33Choice] = field(
        default=None,
        metadata={
            "name": "PtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )
    svcg_pty_b: Optional[PartyIdentification33Choice] = field(
        default=None,
        metadata={
            "name": "SvcgPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    coll_acct_id: Optional[CollateralAccount1] = field(
        default=None,
        metadata={
            "name": "CollAcctId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    xpsr_tp: Optional[ExposureType5Code] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    valtn_dt: Optional[DateAndDateTimeChoice] = field(
        default=None,
        metadata={
            "name": "ValtnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )


@dataclass
class CollateralSubstitutionResponseV03:
    tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    oblgtn: Optional[Obligation3] = field(
        default=None,
        metadata={
            "name": "Oblgtn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )
    agrmt: Optional[Agreement2] = field(
        default=None,
        metadata={
            "name": "Agrmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )
    sbstitn_rspn: Optional[SubstitutionResponse1] = field(
        default=None,
        metadata={
            "name": "SbstitnRspn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
            "required": True,
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:colr.011.001.03"

    coll_sbstitn_rspn: Optional[CollateralSubstitutionResponseV03] = field(
        default=None,
        metadata={
            "name": "CollSbstitnRspn",
            "type": "Element",
            "required": True,
        },
    )
