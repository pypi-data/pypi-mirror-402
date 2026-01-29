import logging
import os
from glob import glob
from pathlib import Path
from typing import Iterator

from isdn.model import ISDNRecord, ISDNRoot
from pydantic import HttpUrl, ValidationError
from rdflib import URIRef

from ..namespace import *
from . import Literal, RDFMapper, _TripleMapType, bpo

logger = logging.getLogger(__name__)

DERIVATION_TYPE_MAP = {
    "オリジナル": ISDN.OriginalWork,
    "パロディ": ISDN.DerivativeWork,
}

PRODUCT_TYPE_MAP = {
    "同人誌": ISDN.Book,
    "同人グッズ": ISDN.DoujinGoods,
    "同人音楽": ISDN.Music,
    "同人ソフト": ISDN.Software,
    "同人ハード": ISDN.Hardware,
    "フィギュア・ドール": ISDN.FigurativeProduct,
    "衣装・アクセサリ": ISDN.Wearable,
    "フライヤー（ペーパー）": ISDN.Flyer,
    "イベントカタログ": ISDN.EventCatalog,
}

PRINTING_METHOD = {"オフセット印刷", "オンデマンド印刷", "コピー印刷"}
BINDING_METHOD = {"平綴じ", "中綴じ", "無線綴じ"}
CARRIER_TYPE = {"プレスCD", "プレスDVD", "CD-R", "DVD-R", "フロッピー"}


class ISDNXML2RDFMapper(RDFMapper):
    def __init__(self, xml_dir: str | os.PathLike):
        self.xml_dir = xml_dir

    def iterator(self) -> Iterator[ISDNRecord]:
        for file in glob(os.path.join(self.xml_dir, "*.xml")):
            yield ISDNRoot.from_xml_first(Path(file).read_bytes())

    @staticmethod
    def map_to_triples(row: ISDNRecord) -> tuple[URIRef, list[_TripleMapType]]:
        graph = None
        if row.rating_age == "15禁":
            graph = ISDN_GRAPH.ageRestricted15
        elif row.rating_age == "18禁":
            graph = ISDN_GRAPH.ageRestricted18

        s = ISDN_RES[row.isdn.code]

        triples = [
            (s, OWL.sameAs, ISDN_RES_PURL[row.isdn.code]),
            (s, RDF.type, ISDN.DoujinProduct),
            (s, RDF.type, PRODUCT_TYPE_MAP[row.type]),
            (s, ISDN.isdn, row.isdn.code),
            (
                s,
                SCHEMA.identifier,
                bpo(
                    [
                        (RDF.type, SCHEMA.PropertyValue),
                        (RDF.type, ISDN.ISDNIdentifier),
                        (SCHEMA.propertyID, "ISDN"),
                        (SCHEMA.value, Literal(row.isdn.code)),
                        (SCHEMA.alternateName, row.disp_isdn),
                        (ISDN.isdnPrefix, row.isdn.prefix),
                        (ISDN.isdnRegistrationGroup, row.isdn.group),
                        (ISDN.isdnRegistrationGroupName, row.region),
                        (ISDN.isdnRegistrant, row.isdn.registrant),
                        (ISDN.isdnPublication, row.isdn.publication),
                        (ISDN.isdnCheckDigit, row.isdn.check_digit),
                    ]
                ),
            ),
            (s, ISDN.derivationType, DERIVATION_TYPE_MAP[row.class_]),
            (s, SCHEMA.category, row.type),
            (s, ISDN.ratingGender, row.rating_gender),
            (s, ISDN.ratingAge, row.rating_age),
            (s, SCHEMA.name, row.product_name),
            (s, RDFS.label, Literal(row.product_name, lang="ja")),
            (s, RDFS.label, Literal(row.product_yomi, lang="ja-Hira")),
            (
                s,
                SCHEMA.publisher,
                bpo(
                    [
                        (RDF.type, SCHEMA.Organization),
                        (SCHEMA.name, row.publisher_name),
                        (RDFS.label, Literal(row.publisher_name, lang="ja")),
                        (RDFS.label, Literal(row.publisher_yomi, lang="ja-Hira")),
                        (ISDN.isdnRegistrant, row.publisher_code),
                    ]
                ),
            ),
            (s, SCHEMA.datePublished, Literal(row.issue_date, datatype=XSD.date)),
            (
                s,
                SCHEMA.genre,
                bpo(
                    [
                        (RDF.type, ISDN.ComiketGenre),
                        (SCHEMA.name, row.genre_name),
                        (SCHEMA.identifier, row.genre_code),
                        (SCHEMA.description, row.genre_user),
                    ]
                ),
            ),
            (
                s,
                SCHEMA.genre,
                bpo(
                    [
                        (RDF.type, ISDN.CCode),
                        (SCHEMA.identifier, row.c_code),
                        (ISDN.cCodeTargetAudience, row.author),
                        (ISDN.cCodePublicationForm, row.shape),
                        (ISDN.cCodeContentCategory, row.contents),
                    ]
                ),
            ),
            (
                s,
                SCHEMA.offers,
                bpo(
                    [
                        (RDF.type, SCHEMA.Offer),
                        (SCHEMA.price, Literal(row.price, datatype=XSD.decimal)),
                        (SCHEMA.priceCurrency, row.price_unit),
                    ]
                ),
            ),
            (s, ISDN.bookJanCodeSecondRow, row.barcode2),
            (s, SCHEMA.description, row.product_comment),
            (s, ISDN.productStyle, row.product_style),
            (s, SCHEMA.size, row.product_size),
            (
                s,
                ISDN.carrierExtent,
                bpo(
                    [
                        (RDF.type, SCHEMA.QuantitativeValue),
                        (SCHEMA.value, Literal(row.product_capacity, datatype=XSD.decimal)),
                        (SCHEMA.unitText, row.product_capacity_unit),
                    ]
                ),
            ),
            (s, SCHEMA.thumbnailUrl, URIRef(str(row.sample_image_uri)) if row.sample_image_uri else None),
        ]

        if row.product_style:
            for part in row.product_style.split("・"):
                if part in PRINTING_METHOD:
                    triples.append((s, ISDN.printingMethod, part))
                elif part in BINDING_METHOD:
                    triples.append((s, ISDN.bindingMethod, part))
                elif part in CARRIER_TYPE:
                    triples.append((s, ISDN.carrierType, part))

        if row.product_capacity_unit == "ページ":
            triples.append((s, SCHEMA.numberOfPages, Literal(row.product_capacity, datatype=XSD.decimal)))

        for option in row.useroptions:
            triples.append(
                (
                    s,
                    SCHEMA.additionalProperty,
                    bpo(
                        [
                            (RDF.type, SCHEMA.PropertyValue),
                            (RDF.type, ISDN.UserOption),
                            (SCHEMA.name, option.property),
                            (SCHEMA.value, option.value),
                        ]
                    ),
                )
            )

        for link in row.external_links:
            try:
                link_url = HttpUrl(link.uri.strip())
            except ValidationError:
                logger.warning(f"Invalid external link: {link.uri} (ISDN: {row.isdn.code})")
                continue
            triples.append(
                (
                    s,
                    SCHEMA.relatedLink,
                    bpo(
                        [
                            (RDF.type, SCHEMA.WebPage),
                            (SCHEMA.name, link.title),
                            (SCHEMA.url, URIRef(str(link_url))),
                        ]
                    ),
                )
            )

        return graph, triples


__all__ = ["ISDNXML2RDFMapper"]
