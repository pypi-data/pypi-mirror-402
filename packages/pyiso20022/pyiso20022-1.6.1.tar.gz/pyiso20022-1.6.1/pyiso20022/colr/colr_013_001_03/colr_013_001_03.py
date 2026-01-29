from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate, XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03"


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


class CalculationMethod1Code(Enum):
    SIMP = "SIMP"
    COMP = "COMP"


class CollateralAccountType1Code(Enum):
    HOUS = "HOUS"
    CLIE = "CLIE"
    LIPR = "LIPR"
    MGIN = "MGIN"
    DFLT = "DFLT"


class CollateralPurpose1Code(Enum):
    VAMA = "VAMA"
    SINA = "SINA"


@dataclass
class DateAndDateTimeChoice:
    dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "Dt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class DatePeriodDetails:
    fr_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "FrDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    to_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ToDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
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
class GenericIdentification29:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
            "pattern": r"[a-zA-Z0-9]{4}",
        },
    )
    issr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Issr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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


class InterestMethod1Code(Enum):
    PHYS = "PHYS"
    ROLL = "ROLL"


class InterestRequestSequence1Code(Enum):
    INIT = "INIT"
    UPDA = "UPDA"


@dataclass
class PostalAddress2:
    strt_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "StrtNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "min_length": 1,
            "max_length": 70,
        },
    )
    pst_cd_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCdId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class Reference20:
    intrst_pmt_req_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "IntrstPmtReqId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    intrst_pmt_rspn_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "IntrstPmtRspnId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
class VariableInterest1Rate:
    indx: Optional[str] = field(
        default=None,
        metadata={
            "name": "Indx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    bsis_pt_sprd: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "BsisPtSprd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "total_digits": 18,
            "fraction_digits": 0,
        },
    )


@dataclass
class AgreementFramework1Choice:
    agrmt_frmwk: Optional[AgreementFramework1Code] = field(
        default=None,
        metadata={
            "name": "AgrmtFrmwk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    prtry_id: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class CollateralAccountIdentificationType1Choice:
    tp: Optional[CollateralAccountType1Code] = field(
        default=None,
        metadata={
            "name": "Tp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    prtry: Optional[GenericIdentification29] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class CollateralBalance1:
    held_by_pty_a: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "HeldByPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    held_by_pty_b: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "HeldByPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )


@dataclass
class CollateralPurpose1Choice:
    cd: Optional[CollateralPurpose1Code] = field(
        default=None,
        metadata={
            "name": "Cd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    prtry: Optional[GenericIdentification30] = field(
        default=None,
        metadata={
            "name": "Prtry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class InterestRate1Choice:
    fxd_intrst_rate: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "FxdIntrstRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "total_digits": 11,
            "fraction_digits": 10,
        },
    )
    varbl_intrst_rate: Optional[VariableInterest1Rate] = field(
        default=None,
        metadata={
            "name": "VarblIntrstRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class NameAndAddress6:
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "min_length": 1,
            "max_length": 140,
        },
    )
    agrmt_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "AgrmtDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    base_ccy: Optional[str] = field(
        default=None,
        metadata={
            "name": "BaseCcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
            "pattern": r"[A-Z]{3,3}",
        },
    )
    agrmt_frmwk: Optional[AgreementFramework1Choice] = field(
        default=None,
        metadata={
            "name": "AgrmtFrmwk",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class CollateralAccount1:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Nm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "min_length": 1,
            "max_length": 70,
        },
    )


@dataclass
class InterestAmount1:
    intrst_req_seq: Optional[InterestRequestSequence1Code] = field(
        default=None,
        metadata={
            "name": "IntrstReqSeq",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    intrst_prd: Optional[DatePeriodDetails] = field(
        default=None,
        metadata={
            "name": "IntrstPrd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    acrd_intrst_amt: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "AcrdIntrstAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    val_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ValDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    intrst_mtd: Optional[InterestMethod1Code] = field(
        default=None,
        metadata={
            "name": "IntrstMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    intrst_rate: Optional[InterestRate1Choice] = field(
        default=None,
        metadata={
            "name": "IntrstRate",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    day_cnt_bsis: Optional[InterestComputationMethod2Code] = field(
        default=None,
        metadata={
            "name": "DayCntBsis",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    apld_whldg_tax: Optional[bool] = field(
        default=None,
        metadata={
            "name": "ApldWhldgTax",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    clctn_mtd: Optional[CalculationMethod1Code] = field(
        default=None,
        metadata={
            "name": "ClctnMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    clctn_frqcy: Optional[Frequency1Code] = field(
        default=None,
        metadata={
            "name": "ClctnFrqcy",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    coll_purp: Optional[CollateralPurpose1Choice] = field(
        default=None,
        metadata={
            "name": "CollPurp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    opng_coll_bal: Optional[CollateralBalance1] = field(
        default=None,
        metadata={
            "name": "OpngCollBal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    clsg_coll_bal: Optional[CollateralBalance1] = field(
        default=None,
        metadata={
            "name": "ClsgCollBal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    std_sttlm_instrs: Optional[str] = field(
        default=None,
        metadata={
            "name": "StdSttlmInstrs",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "min_length": 1,
            "max_length": 140,
        },
    )
    addtl_inf: Optional[str] = field(
        default=None,
        metadata={
            "name": "AddtlInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "min_length": 1,
            "max_length": 210,
        },
    )
    ref_dtls: Optional[Reference20] = field(
        default=None,
        metadata={
            "name": "RefDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class InterestResult1:
    intrst_due_to_a: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "IntrstDueToA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    intrst_due_to_b: Optional[ActiveCurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "IntrstDueToB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    val_dt: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ValDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    intrst_mtd: Optional[InterestMethod1Code] = field(
        default=None,
        metadata={
            "name": "IntrstMtd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    opng_coll_bal: Optional[CollateralBalance1] = field(
        default=None,
        metadata={
            "name": "OpngCollBal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    clsg_coll_bal: Optional[CollateralBalance1] = field(
        default=None,
        metadata={
            "name": "ClsgCollBal",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )


@dataclass
class PartyIdentification33Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification29] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    nm_and_adr: Optional[NameAndAddress6] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class Obligation3:
    pty_a: Optional[PartyIdentification33Choice] = field(
        default=None,
        metadata={
            "name": "PtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    svcg_pty_a: Optional[PartyIdentification33Choice] = field(
        default=None,
        metadata={
            "name": "SvcgPtyA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    pty_b: Optional[PartyIdentification33Choice] = field(
        default=None,
        metadata={
            "name": "PtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    svcg_pty_b: Optional[PartyIdentification33Choice] = field(
        default=None,
        metadata={
            "name": "SvcgPtyB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    coll_acct_id: Optional[CollateralAccount1] = field(
        default=None,
        metadata={
            "name": "CollAcctId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    xpsr_tp: Optional[ExposureType5Code] = field(
        default=None,
        metadata={
            "name": "XpsrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    valtn_dt: Optional[DateAndDateTimeChoice] = field(
        default=None,
        metadata={
            "name": "ValtnDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )


@dataclass
class InterestPaymentRequestV03:
    tx_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "TxId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    agrmt: Optional[Agreement2] = field(
        default=None,
        metadata={
            "name": "Agrmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
            "required": True,
        },
    )
    intrst_due_to_a: Optional[InterestAmount1] = field(
        default=None,
        metadata={
            "name": "IntrstDueToA",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    intrst_due_to_b: Optional[InterestAmount1] = field(
        default=None,
        metadata={
            "name": "IntrstDueToB",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    net_amt_dtls: Optional[InterestResult1] = field(
        default=None,
        metadata={
            "name": "NetAmtDtls",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:colr.013.001.03"

    intrst_pmt_req: Optional[InterestPaymentRequestV03] = field(
        default=None,
        metadata={
            "name": "IntrstPmtReq",
            "type": "Element",
            "required": True,
        },
    )
