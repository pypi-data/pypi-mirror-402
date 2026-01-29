from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01"


@dataclass
class Case:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    cretr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Cretr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    reop_case_indctn: Optional[bool] = field(
        default=None,
        metadata={
            "name": "ReopCaseIndctn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )


@dataclass
class CaseAssignment:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    assgnr: Optional[str] = field(
        default=None,
        metadata={
            "name": "Assgnr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    assgne: Optional[str] = field(
        default=None,
        metadata={
            "name": "Assgne",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    cre_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "CreDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
        },
    )


@dataclass
class CurrencyAndAmount:
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


class InvestigationExecutionConfirmation1Code(Enum):
    CNCL = "CNCL"
    MODI = "MODI"
    ACDA = "ACDA"
    IPAY = "IPAY"
    ICOV = "ICOV"
    MCOV = "MCOV"
    IPYI = "IPYI"
    INFO = "INFO"
    CONF = "CONF"
    CWFW = "CWFW"


class PaymentCancellationRejection1Code(Enum):
    LEGL = "LEGL"
    AGNT = "AGNT"
    CUST = "CUST"


class PaymentModificationRejection1Code(Enum):
    UM01 = "UM01"
    UM02 = "UM02"
    UM03 = "UM03"
    UM04 = "UM04"
    UM05 = "UM05"
    UM06 = "UM06"
    UM07 = "UM07"
    UM08 = "UM08"
    UM09 = "UM09"
    UM10 = "UM10"
    UM11 = "UM11"
    UM12 = "UM12"
    UM13 = "UM13"
    UM14 = "UM14"
    UM15 = "UM15"
    UM16 = "UM16"
    UM17 = "UM17"
    UM18 = "UM18"
    UM19 = "UM19"
    UM20 = "UM20"
    UM21 = "UM21"


@dataclass
class PaymentInstructionExtract:
    assgnr_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AssgnrInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    assgne_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AssgneInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ccy_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CcyAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )
    val_dt: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "ValDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )


@dataclass
class RejectedCancellationJustification:
    rsn_cd: Optional[PaymentCancellationRejection1Code] = field(
        default=None,
        metadata={
            "name": "RsnCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
        },
    )
    rsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "Rsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "min_length": 1,
            "max_length": 140,
        },
    )


@dataclass
class InvestigationStatusChoice:
    conf: Optional[InvestigationExecutionConfirmation1Code] = field(
        default=None,
        metadata={
            "name": "Conf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )
    rjctd_mod: list[PaymentModificationRejection1Code] = field(
        default_factory=list,
        metadata={
            "name": "RjctdMod",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "max_occurs": 14,
        },
    )
    rjctd_cxl: Optional[RejectedCancellationJustification] = field(
        default=None,
        metadata={
            "name": "RjctdCxl",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )
    dplct_of: Optional[Case] = field(
        default=None,
        metadata={
            "name": "DplctOf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )
    assgnmt_cxl_conf: Optional[bool] = field(
        default=None,
        metadata={
            "name": "AssgnmtCxlConf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )


@dataclass
class Camt02900101:
    class Meta:
        name = "camt.029.001.01"

    assgnmt: Optional[CaseAssignment] = field(
        default=None,
        metadata={
            "name": "Assgnmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
        },
    )
    rslvd_case: Optional[Case] = field(
        default=None,
        metadata={
            "name": "RslvdCase",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
            "required": True,
        },
    )
    sts: Optional[InvestigationStatusChoice] = field(
        default=None,
        metadata={
            "name": "Sts",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )
    crrctn_tx: Optional[PaymentInstructionExtract] = field(
        default=None,
        metadata={
            "name": "CrrctnTx",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:camt.029.001.01"

    camt_029_001_01: Optional[Camt02900101] = field(
        default=None,
        metadata={
            "name": "camt.029.001.01",
            "type": "Element",
            "required": True,
        },
    )
