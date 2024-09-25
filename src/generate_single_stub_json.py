#!/usr/bin/env python3

# Portions of this file contributed by NIST are governed by the
# following statement:
#
# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to Title 17 Section 105 of the
# United States Code, this software is not subject to copyright
# protection within the United States. NIST assumes no responsibility
# whatsoever for its use by other parties, and makes no guarantees,
# expressed or implied, about its quality, reliability, or any other
# characteristic.
#
# We would appreciate acknowledgement if the software is used.

import argparse
import importlib.resources
import json
import logging
from typing import Dict, List, Optional, Set, Union

import case_utils.ontology
import pyld  # type: ignore
from case_utils.namespace import (
    NS_CASE_INVESTIGATION,
    NS_CASE_VOCABULARY,
    NS_CO,
    NS_OWL,
    NS_RDF,
    NS_UCO_ACTION,
    NS_UCO_ANALYSIS,
    NS_UCO_CONFIGURATION,
    NS_UCO_CORE,
    NS_UCO_IDENTITY,
    NS_UCO_LOCATION,
    NS_UCO_MARKING,
    NS_UCO_OBSERVABLE,
    NS_UCO_PATTERN,
    NS_UCO_ROLE,
    NS_UCO_TOOL,
    NS_UCO_TYPES,
    NS_UCO_VICTIM,
    NS_UCO_VOCABULARY,
    NS_XSD,
)
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.query import ResultRow

# JSON type via:
# https://github.com/python/typing/issues/182#issuecomment-1320974824
# Union is needed instead of '|' operator before Python 3.10.
JSON = Union[Dict[str, "JSON"], List["JSON"], str, int, float, bool, None]

NS_KB = Namespace("http://example.org/kb/")

CDO_CONTEXT: Dict[str, Namespace] = {
    "case-investigation": NS_CASE_INVESTIGATION,
    "case-vocabulary": NS_CASE_VOCABULARY,
    "co": NS_CO,
    "uco-action": NS_UCO_ACTION,
    "uco-analysis": NS_UCO_ANALYSIS,
    "uco-configuration": NS_UCO_CONFIGURATION,
    "uco-core": NS_UCO_CORE,
    "uco-identity": NS_UCO_IDENTITY,
    "uco-location": NS_UCO_LOCATION,
    "uco-marking": NS_UCO_MARKING,
    "uco-observable": NS_UCO_OBSERVABLE,
    "uco-pattern": NS_UCO_PATTERN,
    "uco-role": NS_UCO_ROLE,
    "uco-tool": NS_UCO_TOOL,
    "uco-types": NS_UCO_TYPES,
    "uco-victim": NS_UCO_VICTIM,
    "uco-vocabulary": NS_UCO_VOCABULARY,
}


def resolve_max_cardinality(
    graph: Graph, n_class: URIRef, n_property: URIRef
) -> Optional[int]:
    """
    Give the maximum cardinality for a property on a specific class.
    Returns None for unbounded, otherwise an int for ceiling.
    Precondition: Assumes (i.e., does not check that) property is associated with n_class.

    >>> import rdflib
    >>> g = rdflib.Graph()
    >>> data = '''\
@prefix ex: <http://example.org/ontology/> .\
@prefix owl: <http://www.w3.org/2002/07/owl#> .\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\
@prefix sh: <http://www.w3.org/ns/shacl#> .\
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\
\
ex:A\
  a owl:Class , sh:NodeShape ;\
  sh:property [\
    sh:maxCount 4 ;\
    sh:path ex:foo ;\
  ] ;\
  .\
\
ex:B\
  a owl:Class , sh:NodeShape ;\
  rdfs:subClassOf ex:A ;\
  sh:property [\
    sh:maxCount 3 ;\
    sh:path ex:foo ;\
  ] ;\
  .\
\
ex:C\
  a owl:Class ;\
  rdfs:subClassOf\
    ex:B ,\
    [\
      a owl:Restriction ;\
      owl:onProperty ex:foo ;\
      owl:maxCardinality "2"^^xsd:nonNegativeInteger ;\
    ]\
    ;\
  .\
\
ex:D\
  a owl:Class ;\
  rdfs:subClassOf\
    ex:B ,\
    [\
      a owl:Restriction ;\
      owl:onProperty ex:foo ;\
      owl:cardinality "1"^^xsd:nonNegativeInteger ;\
    ]\
    ;\
  .\
\
ex:foo\
  a owl:AnnotationProperty ;\
  .\
'''
    >>> _ = g.parse(data=data, format="turtle")
    >>> ns_ex = rdflib.Namespace("http://example.org/ontology/")
    >>> resolve_max_cardinality(g, ns_ex["A"], ns_ex["foo"])
    4
    >>> resolve_max_cardinality(g, ns_ex["B"], ns_ex["foo"])
    3
    >>> resolve_max_cardinality(g, ns_ex["C"], ns_ex["foo"])
    2
    >>> resolve_max_cardinality(g, ns_ex["D"], ns_ex["foo"])
    1
    """
    max_counts: Set[int] = set()
    query = """\
SELECT ?lMaxCount
WHERE {
  ?nClass rdfs:subClassOf* ?nSuperClass .
  {
    ?nSuperClass sh:property ?nPropertyShape .
    ?nPropertyShape
      sh:maxCount ?lMaxCount ;
      sh:path ?nProperty ;
      .
  }
  UNION
  {
    ?nSuperClass rdfs:subClassOf ?nRestriction .
    ?nRestriction
      a owl:Restriction ;
      owl:onProperty ?nProperty ;
      .
    {
      ?nRestriction
        owl:cardinality ?lMaxCount ;
        .
    }
    UNION
    {
      ?nRestriction
        owl:maxCardinality ?lMaxCount ;
        .
    }
  }
}
"""
    for result in graph.query(
        query, initBindings={"nClass": n_class, "nProperty": n_property}
    ):
        assert isinstance(result, ResultRow)
        if not isinstance(result[0], Literal):
            continue
        max_counts.add(int(result[0]))
    if len(max_counts) == 0:
        return None
    else:
        return min(max_counts)


def get_properties(graph: Graph, n_class: URIRef) -> Set[URIRef]:
    """
    >>> import rdflib
    >>> g = rdflib.Graph()
    >>> data = '''\
@prefix ex: <http://example.org/ontology/> .\
@prefix owl: <http://www.w3.org/2002/07/owl#> .\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\
@prefix sh: <http://www.w3.org/ns/shacl#> .\
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\
\
ex:A\
  a owl:Class , sh:NodeShape ;\
  sh:property [\
    sh:maxCount 4 ;\
    sh:path ex:foo ;\
  ] ;\
  .\
\
ex:B\
  a owl:Class , sh:NodeShape ;\
  rdfs:subClassOf ex:A ;\
  sh:property [\
    sh:maxCount 3 ;\
    sh:path ex:bar ;\
  ] ;\
  .\
\
ex:C\
  a owl:Class , sh:NodeShape ;\
  rdfs:subClassOf\
    ex:A ,\
    [\
      a owl:Restriction ;\
      owl:onProperty ex:baz ;\
      owl:maxCardinality "2"^^xsd:nonNegativeInteger ;\
    ]\
    ;\
  .\
\
ex:D\
  a owl:Class ;\
  .\
\
ex:bar\
  a owl:AnnotationProperty ;\
  .\
\
ex:baz\
  a owl:AnnotationProperty ;\
  .\
\
ex:foo\
  a owl:AnnotationProperty ;\
  .\
\
ex:cname\
  a owl:DatatypeProperty ;\
  rdfs:domain [\
    a owl:Class ;\
    owl:unionOf (\
      ex:C\
      ex:D\
    );\
  ];\
  .\
'''
    >>> _ = g.parse(data=data, format="turtle")
    >>> ns_ex = rdflib.Namespace("http://example.org/ontology/")
    >>> [str(x) for x in sorted(get_properties(g, ns_ex["A"]))]
    ['http://example.org/ontology/foo']
    >>> [str(x) for x in sorted(get_properties(g, ns_ex["B"]))]
    ['http://example.org/ontology/bar', 'http://example.org/ontology/foo']
    >>> [str(x) for x in sorted(get_properties(g, ns_ex["C"]))]
    ['http://example.org/ontology/baz', 'http://example.org/ontology/cname', 'http://example.org/ontology/foo']
    >>> [str(x) for x in sorted(get_properties(g, ns_ex["D"]))]
    ['http://example.org/ontology/cname']
    """
    n_properties: Set[URIRef] = set()
    query = """\
SELECT ?nProperty
WHERE {
  ?nClass rdfs:subClassOf* ?nSuperClass .
  {
    ?nSuperClass sh:property ?nPropertyShape .
    ?nPropertyShape
      sh:path ?nProperty ;
      .
  }
  UNION
  {
    ?nSuperClass rdfs:subClassOf ?nRestriction .
    ?nRestriction
      a owl:Restriction ;
      owl:onProperty ?nProperty ;
      .
  }
  UNION
  {
    ?nProperty rdfs:domain/(owl:unionOf/rdf:rest*/rdf:first)? ?nSuperClass .
  }
}
"""
    for result in graph.query(query, initBindings={"nClass": n_class}):
        assert isinstance(result, ResultRow)
        if not isinstance(result[0], URIRef):
            continue
        n_properties.add(result[0])
    return n_properties


def get_facet_classes(graph: Graph, n_class: URIRef) -> Set[URIRef]:
    logging.debug("get_facet_classes(graph, %r) ...", n_class)
    n_facet_classes: Set[URIRef] = set()
    query = """\
PREFIX uco-core: <https://ontology.unifiedcyberontology.org/uco/core/>
SELECT ?nFacetClass
WHERE {
  ?nClass rdfs:subClassOf+ ?nRestriction .
  ?nRestriction
    a owl:Restriction ;
    owl:onProperty uco-core:hasFacet ;
    owl:onClass ?nFacetClass ;
    .
  ?nFacetClass
    rdfs:subClassOf+ uco-core:Facet ;
    .
}

"""
    for result in graph.query(query, initBindings={"nClass": n_class}):
        assert isinstance(result, ResultRow)
        if not isinstance(result[0], URIRef):
            continue
        n_facet_classes.add(result[0])
    return n_facet_classes


def generate_expanded_stub(graph: Graph, n_subject_class: URIRef) -> Dict[str, JSON]:
    subject_prefix, n_namespace, local_name = graph.namespace_manager.compute_qname(
        n_subject_class, False
    )

    expanded_individual: Dict[str, JSON] = {
        "@id": str(NS_KB[local_name + "-1"]),
        "@type": str(n_subject_class),
    }

    for n_property in get_properties(graph, n_subject_class):
        max_cardinality = resolve_max_cardinality(graph, n_subject_class, n_property)
        stub_value: JSON
        if max_cardinality == 0:
            continue
        elif max_cardinality == 1:
            stub_value = None
        else:
            stub_value = []
        expanded_individual[str(n_property)] = stub_value

    logging.debug(expanded_individual.get(str(NS_UCO_CORE.hasFacet)))

    if expanded_individual.get(str(NS_UCO_CORE.hasFacet)) is not None:
        facet_stubs_list = expanded_individual[str(NS_UCO_CORE.hasFacet)]
        assert isinstance(facet_stubs_list, list)
        for n_facet_class in sorted(get_facet_classes(graph, n_subject_class)):
            logging.debug("n_facet_class = %r.", n_facet_class)
            expanded_facet_individual = generate_expanded_stub(graph, n_facet_class)
            facet_stubs_list.append(expanded_facet_individual)

    return expanded_individual


def get_concept_iris(document: JSON) -> Set[URIRef]:
    retval: Set[URIRef] = set()
    assert isinstance(document, dict)
    for key in document:
        if key == "@id":
            continue
        elif key == "@type":
            if isinstance(document[key], str):
                type_iri = document[key]
                assert isinstance(type_iri, str)
                retval.add(URIRef(type_iri))
            elif isinstance(document[key], list):
                child_things = document[key]
                assert isinstance(child_things, list)
                for child_thing in child_things:
                    assert isinstance(child_thing, str)
                    retval.add(URIRef(child_thing))
        else:
            retval.add(URIRef(key))
            if isinstance(document[key], dict):
                retval |= get_concept_iris(document[key])
            if isinstance(document[key], list):
                child_things = document[key]
                assert isinstance(child_things, list)
                for child_thing in child_things:
                    if isinstance(child_thing, dict):
                        retval |= get_concept_iris(child_thing)
    return retval


def swap_values(
    document: JSON, from_value: Optional[int], to_value: Optional[int]
) -> None:
    """
    This is a hack to place a sentinel value in place of nulls.  The JSON-LD compaction algorithm does not necessarily preserve a key if its object is a null, so this function swaps in something that will be preserved.
    >>> d = {"foo": None, "bar": 9}
    >>> swap_values(d, None, 8)
    >>> d
    {'foo': 8, 'bar': 9}
    >>> swap_values(d, 9, None)
    >>> d
    {'foo': 8, 'bar': None}
    """
    assert isinstance(document, dict)
    for key in document:
        if isinstance(document[key], dict):
            swap_values(document[key], from_value, to_value)
        if isinstance(document[key], list):
            child_things = document[key]
            assert isinstance(child_things, list)
            for child_thing in child_things:
                if isinstance(child_thing, dict):
                    swap_values(child_thing, from_value, to_value)
        elif isinstance(document[key], int):
            if isinstance(from_value, int):
                if document[key] == from_value:
                    document[key] = to_value
        elif document[key] is None:
            if from_value is None:
                document[key] = to_value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("out_json")
    parser.add_argument("class_iri")
    parser.add_argument("supplemental_graph", nargs="*")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    graph = Graph()
    ttl_data = importlib.resources.read_text(case_utils.ontology, "case-1.3.0.ttl")
    graph.parse(data=ttl_data)
    logging.debug("len(graph) = %d.", len(graph))

    if args.supplemental_graph:
        for supplemental_graph_filename in args.supplemental_graph:
            logging.debug("Loading %r.", supplemental_graph_filename)
            graph.parse(supplemental_graph_filename)
            logging.debug("len(graph) = %d.", len(graph))

    for key in CDO_CONTEXT:
        graph.bind(key, CDO_CONTEXT[key])

    n_subject_class = URIRef(args.class_iri)
    if (n_subject_class, NS_RDF.type, NS_OWL.Class) not in graph:
        raise ValueError(
            "Requested class IRI not found in CASE graph: %r." % args.class_iri
        )

    expanded_stub = generate_expanded_stub(graph, n_subject_class)

    all_concept_iris = get_concept_iris(expanded_stub)
    all_used_prefixes: Set[str] = set()
    for concept_iri in all_concept_iris:
        prefix, _1, _2 = graph.namespace_manager.compute_qname(concept_iri, False)
        all_used_prefixes.add(prefix)

    # Build context dictionary that only uses prefixes for concepts that appear in the expanded document.
    context: Dict[str, str] = {
        "kb": str(NS_KB),
        "xsd": str(NS_XSD),
    }
    for prefix in all_used_prefixes:
        context[prefix] = str(CDO_CONTEXT[prefix])

    swap_values(expanded_stub, None, 9)
    # logging.debug("expanded_stub = %r.", expanded_stub)
    compacted_graph = pyld.jsonld.compact(expanded_stub, context)
    swap_values(compacted_graph, 9, None)

    # Guarantee "@graph" key is used and list-valued.
    if "@graph" not in compacted_graph.keys():
        new_graph: Dict[str, JSON] = dict()
        new_graph["@context"] = compacted_graph["@context"]
        del compacted_graph["@context"]
        new_graph["@graph"] = [compacted_graph]
        compacted_graph = new_graph

    with open(args.out_json, "w") as out_fh:
        json.dump(compacted_graph, out_fh, indent=4, sort_keys=True)
        out_fh.write("\n")


if __name__ == "__main__":
    main()
