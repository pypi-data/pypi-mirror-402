from rdflib import Namespace
from rdflib.namespace import OWL, RDF, RDFS, XSD, ClosedNamespace

SCHEMA = Namespace("http://schema.org/")
ISDN_RES = Namespace("http://metadata.moe/isdn/res/")
ISDN_RES_PURL = Namespace("http://purl.org/isdn/")

ISDN = ClosedNamespace(
    "http://metadata.moe/ns/isdn/",
    [
        # Classes
        "ISDNIdentifier",
        "DoujinProduct",
        "ComiketGenre",
        "CCode",
        "UserOption",
        ## 形態
        "Book",
        "DoujinGoods",
        "Music",
        "Software",
        "Hardware",
        "FigurativeProduct",
        "Wearable",
        "Flyer",
        "EventCatalog",
        ## 大分類
        "OriginalWork",
        "DerivativeWork",
        # Properties
        "isdn",
        "isdnPrefix",
        "isdnRegistrationGroup",
        "isdnRegistrationGroupName",
        "isdnRegistrant",
        "isdnPublication",
        "isdnCheckDigit",
        "derivationType",
        "ratingGender",
        "ratingAge",
        "cCodeTargetAudience",
        "cCodePublicationForm",
        "cCodeContentCategory",
        "bookJanCodeSecondRow",
        "productStyle",
        "printingMethod",
        "bindingMethod",
        "carrierType",
        "carrierExtent",
    ],
)

ISDN_GRAPH = ClosedNamespace("http://metadata.moe/isdn/graph/", ["ageRestricted15", "ageRestricted18"])


__all__ = [
    "OWL",
    "RDF",
    "RDFS",
    "XSD",
    "SCHEMA",
    "ISDN",
    "ISDN_RES",
    "ISDN_RES_PURL",
    "ISDN_GRAPH",
]
