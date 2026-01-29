import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import IO, Any, Iterator, Tuple, Union

from joblib import Parallel, delayed
from rdflib import BNode, URIRef
from rdflib import Literal as LiteralRdflib
from rdflib.graph import _ObjectType, _PredicateType, _SubjectType, _TripleType
from rdflib.namespace import RDF
from rdflib.plugins.serializers.nquads import _nq_row
from rdflib.plugins.serializers.nt import _nt_row

_TripleMapType = Tuple[_SubjectType, _PredicateType, Union[str, _ObjectType, "BlankPredicateObjectMap"]]
_PredicateObjectType = Tuple[_PredicateType, Union[str, _ObjectType, "BlankPredicateObjectMap"]]


class RDFFormatType(Enum):
    nt = "nt"
    nq = "nq"


class Literal:
    def __new__(cls, value, *args, **kwargs) -> LiteralRdflib | None:
        if value is None:
            return None
        return LiteralRdflib(value, *args, **kwargs)


class BlankPredicateObjectMap:
    def __init__(self, predicate_objects: list[_PredicateObjectType]):
        self.subject = BNode()
        self.predicate_objects = predicate_objects


def bpo(predicate_objects: list[_PredicateObjectType]) -> BlankPredicateObjectMap:
    return BlankPredicateObjectMap(predicate_objects)


def normalize_triple(triple: _TripleType) -> _TripleMapType | None:
    if triple[2] is None:
        return None
    if isinstance(triple[2], Literal) and triple[2] is None:
        return None
    if type(triple[2]) is str:
        triple = (triple[0], triple[1], Literal(triple[2]))
    return triple


def flatten_triple_map(triple_map: _TripleMapType) -> list[_TripleType]:
    triples = []

    if isinstance(triple_map[2], BlankPredicateObjectMap):
        bnode = triple_map[2].subject
        b_triples = []
        for po in triple_map[2].predicate_objects:
            b_triples.extend(flatten_triple_map((bnode, po[0], po[1])))

        # Ignore statements if rdf:type only
        if len([t for t in b_triples if t[1] != RDF.type]) > 0:
            triples.append((triple_map[0], triple_map[1], bnode))
            triples.extend(b_triples)
    else:
        t = normalize_triple(triple_map)
        if t:
            triples.append(t)

    return triples


def serialize_triple(triple: _TripleMapType, graph: URIRef | None = None) -> str:
    return _nq_row(triple, graph) if graph else _nt_row(triple)


class RDFMapper(ABC):
    @abstractmethod
    def iterator(self) -> Iterator:
        pass

    def run(
        self,
        n_jobs: int = -1,
        output: IO[str] = sys.stdout,
        format_type: RDFFormatType = RDFFormatType.nq,
    ):
        def job(row: Any) -> str:
            graph_uri, triple_maps = self.map_to_triples(row)
            return "".join(
                [
                    serialize_triple(
                        triple,
                        graph=graph_uri if format_type == RDFFormatType.nq else None,
                    )
                    for triple_map in triple_maps
                    for triple in flatten_triple_map(triple_map)
                ]
            )

        res = Parallel(n_jobs=n_jobs, return_as="generator_unordered", verbose=1)(
            delayed(job)(row) for row in self.iterator()
        )
        for lines in res:
            output.write(lines)

    @staticmethod
    @abstractmethod
    def map_to_triples(row: Any) -> tuple[URIRef, list[_TripleMapType]]:
        """
        :param row: Object provided by the iterator
        :return: ({Graph URI}, [(subject, predicate, object) ...])
        """
        raise NotImplementedError


__all__ = ["RDFFormatType", "RDFMapper"]
