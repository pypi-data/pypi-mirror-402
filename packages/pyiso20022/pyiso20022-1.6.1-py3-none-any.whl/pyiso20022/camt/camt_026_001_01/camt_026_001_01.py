from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01"


@dataclass
class Case:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "required": True,
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    reop_case_indctn: Optional[bool] = field(
        default=None,
        metadata={
            "name": "ReopCaseIndctn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
        },
    )


@dataclass
class CaseAssignment:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "required": True,
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    assgne: Optional[str] = field(
        default=None,
        metadata={
            "name": "Assgne",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "required": True,
            "pattern": r"[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3,3}){0,1}",
        },
    )
    cre_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "CreDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
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


class UnableToApplyIncorrectInfo1Code(Enum):
    IN01 = "IN01"
    IN02 = "IN02"
    IN03 = "IN03"
    IN04 = "IN04"
    IN05 = "IN05"
    IN06 = "IN06"
    IN07 = "IN07"
    IN08 = "IN08"
    IN09 = "IN09"
    IN10 = "IN10"
    IN11 = "IN11"
    IN12 = "IN12"
    IN13 = "IN13"
    IN14 = "IN14"
    IN15 = "IN15"
    IN16 = "IN16"
    IN17 = "IN17"
    IN18 = "IN18"
    IN19 = "IN19"
    MM20 = "MM20"
    MM21 = "MM21"
    MM22 = "MM22"


class UnableToApplyMissingInfo1Code(Enum):
    MS01 = "MS01"
    MS02 = "MS02"
    MS03 = "MS03"
    MS04 = "MS04"
    MS05 = "MS05"
    MS06 = "MS06"
    MS07 = "MS07"
    MS08 = "MS08"
    MS09 = "MS09"
    MS10 = "MS10"
    MS11 = "MS11"
    MS12 = "MS12"
    MS13 = "MS13"
    MS14 = "MS14"


@dataclass
class MissingOrIncorrectInformation:
    mssng_inf: list[UnableToApplyMissingInfo1Code] = field(
        default_factory=list,
        metadata={
            "name": "MssngInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "max_occurs": 10,
        },
    )
    incrrct_inf: list[UnableToApplyIncorrectInfo1Code] = field(
        default_factory=list,
        metadata={
            "name": "IncrrctInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "max_occurs": 10,
        },
    )


@dataclass
class PaymentInstructionExtract:
    assgnr_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AssgnrInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    assgne_instr_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AssgneInstrId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ccy_amt: Optional[CurrencyAndAmount] = field(
        default=None,
        metadata={
            "name": "CcyAmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
        },
    )
    val_dt: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "ValDt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
        },
    )


@dataclass
class UnableToApplyJustificationChoice:
    any_inf: Optional[bool] = field(
        default=None,
        metadata={
            "name": "AnyInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
        },
    )
    mssng_or_incrrct_inf: Optional[MissingOrIncorrectInformation] = field(
        default=None,
        metadata={
            "name": "MssngOrIncrrctInf",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
        },
    )


@dataclass
class Camt02600101:
    class Meta:
        name = "camt.026.001.01"

    assgnmt: Optional[CaseAssignment] = field(
        default=None,
        metadata={
            "name": "Assgnmt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "required": True,
        },
    )
    case: Optional[Case] = field(
        default=None,
        metadata={
            "name": "Case",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "required": True,
        },
    )
    undrlyg: Optional[PaymentInstructionExtract] = field(
        default=None,
        metadata={
            "name": "Undrlyg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "required": True,
        },
    )
    justfn: Optional[UnableToApplyJustificationChoice] = field(
        default=None,
        metadata={
            "name": "Justfn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01",
            "required": True,
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:camt.026.001.01"

    camt_026_001_01: Optional[Camt02600101] = field(
        default=None,
        metadata={
            "name": "camt.026.001.01",
            "type": "Element",
            "required": True,
        },
    )
