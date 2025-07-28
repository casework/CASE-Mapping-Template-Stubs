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

__version__ = "0.0.1"

import argparse
import hashlib
import importlib.resources
import logging
from typing import cast

import case_utils.ontology
from case_utils.namespace import (
    NS_CASE_INVESTIGATION,
    NS_CASE_VOCABULARY,
    NS_CO,
    NS_OWL,
    NS_RDF,
    NS_RDFS,
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
from rdflib import SH, Graph, Namespace, URIRef
from rdflib.query import ResultRow
from rdflib.term import IdentifiedNode

CDO_CONTEXT: dict[str, Namespace] = {
    "case-investigation": NS_CASE_INVESTIGATION,
    "case-vocabulary": NS_CASE_VOCABULARY,
    "co": NS_CO,
    "owl": cast(Namespace, NS_OWL),
    "rdf": cast(Namespace, NS_RDF),
    "rdfs": cast(Namespace, NS_RDFS),
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
    "xsd": cast(Namespace, NS_XSD),
}

# A shortcut predicate to flatten some OWL syntax.
N_HAS_FACET_AT_CLASS_LEVEL = URIRef("urn:example:hasFacetAtClassLevel")

NS_SH = SH


def iri_to_gv_node_id(n_thing: IdentifiedNode) -> str:
    """
    This function returns a string safe to use as a Dot node identifier.  The main concern addressed is Dot syntax errors caused by use of colons in IRIs.

    >>> import rdflib
    >>> x = rdflib.URIRef("urn:example:kb:x")
    >>> iri_to_gv_node_id(x)
    '_b42f80365d50f29359b0a4d682366646248b4939a2b291e821a0f8bdaae4cd2a'
    """
    hasher = hashlib.sha256()
    hasher.update(str(n_thing).encode())
    return "_" + hasher.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("out_dot")
    parser.add_argument("class_iri")
    parser.add_argument("supplemental_graph", nargs="*")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    graph = Graph()
    ttl_data = importlib.resources.read_text(case_utils.ontology, "case-1.4.0.ttl")
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

    for construct_query in [
        """\
# 'Expand' syntax of OWL unions to get entailed direct-subclass relationships.
# For OWL syntax notes on union forms, see tables 16 and 18 here:
# https://www.w3.org/TR/2012/REC-owl2-mapping-to-rdf-20121211/
CONSTRUCT {
  ?nClass rdfs:subClassOf ?nSuperclass .
} WHERE {
  ?nSuperclass
    (owl:disjointUnionOf|owl:unionOf)/rdf:rest*/rdf:first ?nClass ;
    .
  FILTER (isIRI(?nClass))
  FILTER (isIRI(?nSuperclass))
}
""",
        """\
# 'Expand' model to add quick-link for Facet classes.
PREFIX uco-core: <https://ontology.unifiedcyberontology.org/uco/core/>
CONSTRUCT {
  ?nClass <urn:example:hasFacetAtClassLevel> ?nFacetClass .
} WHERE {
  ?nClass rdfs:subClassOf ?nRestriction .
  ?nRestriction
    a owl:Restriction ;
    owl:onProperty uco-core:hasFacet ;
    owl:onClass ?nFacetClass ;
    .
  ?nFacetClass
    rdfs:subClassOf+ uco-core:Facet ;
    .
}
""",
    ]:
        new_triples: set[tuple[URIRef, URIRef, URIRef]] = set()
        for construct_result in graph.query(construct_query):
            assert isinstance(construct_result, tuple)
            assert isinstance(construct_result[0], URIRef)
            assert isinstance(construct_result[1], URIRef)
            assert isinstance(construct_result[2], URIRef)
            new_triples.add(
                (
                    construct_result[0],
                    construct_result[1],
                    construct_result[2],
                )
            )
        for new_triple in new_triples:
            graph.add(new_triple)

    n_classes_to_display: set[URIRef] = {n_subject_class}
    query = """\
SELECT ?nRelatedClass
WHERE {
  {
    # Get subclass hierarchy.
    ?nClass
      rdfs:subClassOf* ?nRelatedClass ;
      .
  } UNION {
    # Get metaclasses and metaclass hierarchy.
    ?nClass
      rdfs:subClassOf*/a/rdfs:subClassOf* ?nRelatedClass ;
      .
  } UNION {
    # Get Facet classes and metaclass hierarchy.
    ?nClass
      rdfs:subClassOf*/<urn:example:hasFacetAtClassLevel>/rdfs:subClassOf* ?nRelatedClass ;
      .
  }
  FILTER (isIRI(?nRelatedClass))
}
"""
    for result in graph.query(query, initBindings={"nClass": n_subject_class}):
        assert isinstance(result, ResultRow)
        assert isinstance(result[0], URIRef)
        n_classes_to_display.add(result[0])

    triples_to_display: set[tuple[URIRef, URIRef, URIRef]] = set()
    for n_class in n_classes_to_display:
        for n_linking_predicate in [
            N_HAS_FACET_AT_CLASS_LEVEL,
            NS_RDF.type,
            NS_RDFS.subClassOf,
        ]:
            for n_object in graph.objects(n_class, n_linking_predicate):
                if isinstance(n_object, URIRef):
                    triples_to_display.add((n_class, n_linking_predicate, n_object))

    # Reduce display-sets: Cut modeling classes.
    classes_to_not_display = {NS_OWL.Class, NS_OWL.Restriction, NS_SH.NodeShape}
    filtered_classes = [
        x for x in n_classes_to_display if x not in classes_to_not_display
    ]
    filtered_triples = [
        x
        for x in triples_to_display
        if x[0] not in classes_to_not_display and x[2] not in classes_to_not_display
    ]

    with open(args.out_dot, "w") as out_fh:
        out_fh.write(
            """\
digraph "hierarchy" {
\trankdir="BT";
\t//Nodes
"""
        )
        for n_class in sorted(filtered_classes):
            out_fh.write(
                """\
\t%s [label="%s" tooltip="%s"];
"""
                % (
                    iri_to_gv_node_id(n_class),
                    graph.namespace_manager.qname(n_class),
                    str(n_class),
                )
            )
        out_fh.write(
            """\
\t//Edges
"""
        )
        for triple in sorted(filtered_triples):
            edge_label = {
                N_HAS_FACET_AT_CLASS_LEVEL: "",
                NS_RDF.type: "∈",
                NS_RDFS.subClassOf: "⊂",
            }[triple[1]]
            head_arrow = {
                N_HAS_FACET_AT_CLASS_LEVEL: "dot",
            }.get(triple[1], "normal")
            head_label = {
                N_HAS_FACET_AT_CLASS_LEVEL: "0..1",
            }.get(triple[1], "")
            out_fh.write(
                """\
\t%s -> %s [arrowhead="%s" headlabel="%s" label="%s"];
"""
                % (
                    iri_to_gv_node_id(triple[0]),
                    iri_to_gv_node_id(triple[2]),
                    head_arrow,
                    head_label,
                    edge_label,
                )
            )

        for triple in sorted(
            [x for x in filtered_triples if x[1] == N_HAS_FACET_AT_CLASS_LEVEL]
        ):
            out_fh.write(
                """\
\tsubgraph ranker%s%s {
\t\trank="same"
\t\t%s
\t\t%s
\t}
"""
                % (
                    iri_to_gv_node_id(triple[0]),
                    iri_to_gv_node_id(triple[2]),
                    iri_to_gv_node_id(triple[0]),
                    iri_to_gv_node_id(triple[2]),
                )
            )
        out_fh.write(
            """\
}
"""
        )


if __name__ == "__main__":
    main()
