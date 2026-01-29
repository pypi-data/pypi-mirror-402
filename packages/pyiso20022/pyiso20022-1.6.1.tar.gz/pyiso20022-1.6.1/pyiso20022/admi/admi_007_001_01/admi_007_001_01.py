from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01"


class AddressType2Code(Enum):
    ADDR = "ADDR"
    PBOX = "PBOX"
    HOME = "HOME"
    BIZZ = "BIZZ"
    MLTO = "MLTO"
    DLVY = "DLVY"


@dataclass
class GenericIdentification36:
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class MessageHeader10:
    msg_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    cre_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "CreDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
        },
    )
    qry_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "QryNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )


@dataclass
class RequestHandling2:
    sts_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "StsCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 4,
            "pattern": r"[a-zA-Z0-9]{1,4}",
        },
    )
    sts_dt_tm: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "StsDtTm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
        },
    )
    desc: Optional[str] = field(
        default=None,
        metadata={
            "name": "Desc",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 140,
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
class PostalAddress1:
    adr_tp: Optional[AddressType2Code] = field(
        default=None,
        metadata={
            "name": "AdrTp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
        },
    )
    adr_line: list[str] = field(
        default_factory=list,
        metadata={
            "name": "AdrLine",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 70,
        },
    )
    bldg_nb: Optional[str] = field(
        default=None,
        metadata={
            "name": "BldgNb",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    pst_cd: Optional[str] = field(
        default=None,
        metadata={
            "name": "PstCd",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 16,
        },
    )
    twn_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "TwnNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry_sub_dvsn: Optional[str] = field(
        default=None,
        metadata={
            "name": "CtrySubDvsn",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ctry: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ctry",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "required": True,
            "pattern": r"[A-Z]{2,2}",
        },
    )


@dataclass
class SupplementaryData1:
    plc_and_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlcAndNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 350,
        },
    )
    envlp: Optional[SupplementaryDataEnvelope1] = field(
        default=None,
        metadata={
            "name": "Envlp",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
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
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
        },
    )


@dataclass
class PartyIdentification120Choice:
    any_bic: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnyBIC",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "pattern": r"[A-Z0-9]{4,4}[A-Z]{2,2}[A-Z0-9]{2,2}([A-Z0-9]{3,3}){0,1}",
        },
    )
    prtry_id: Optional[GenericIdentification36] = field(
        default=None,
        metadata={
            "name": "PrtryId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
        },
    )
    nm_and_adr: Optional[NameAndAddress5] = field(
        default=None,
        metadata={
            "name": "NmAndAdr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
        },
    )


@dataclass
class PartyIdentification136:
    id: Optional[PartyIdentification120Choice] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "required": True,
        },
    )
    lei: Optional[str] = field(
        default=None,
        metadata={
            "name": "LEI",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "pattern": r"[A-Z0-9]{18,18}[0-9]{2,2}",
        },
    )


@dataclass
class MessageReference1:
    ref: Optional[str] = field(
        default=None,
        metadata={
            "name": "Ref",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "required": True,
            "min_length": 1,
            "max_length": 35,
        },
    )
    msg_nm: Optional[str] = field(
        default=None,
        metadata={
            "name": "MsgNm",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_length": 1,
            "max_length": 35,
        },
    )
    ref_issr: Optional[PartyIdentification136] = field(
        default=None,
        metadata={
            "name": "RefIssr",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
        },
    )


@dataclass
class ReceiptAcknowledgementReport2:
    rltd_ref: Optional[MessageReference1] = field(
        default=None,
        metadata={
            "name": "RltdRef",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "required": True,
        },
    )
    req_hdlg: Optional[RequestHandling2] = field(
        default=None,
        metadata={
            "name": "ReqHdlg",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "required": True,
        },
    )


@dataclass
class ReceiptAcknowledgementV01:
    msg_id: Optional[MessageHeader10] = field(
        default=None,
        metadata={
            "name": "MsgId",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "required": True,
        },
    )
    rpt: list[ReceiptAcknowledgementReport2] = field(
        default_factory=list,
        metadata={
            "name": "Rpt",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
            "min_occurs": 1,
        },
    )
    splmtry_data: list[SupplementaryData1] = field(
        default_factory=list,
        metadata={
            "name": "SplmtryData",
            "type": "Element",
            "namespace": "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01",
        },
    )


@dataclass
class Document:
    class Meta:
        namespace = "urn:iso:std:iso:20022:tech:xsd:admi.007.001.01"

    rct_ack: Optional[ReceiptAcknowledgementV01] = field(
        default=None,
        metadata={
            "name": "RctAck",
            "type": "Element",
            "required": True,
        },
    )
