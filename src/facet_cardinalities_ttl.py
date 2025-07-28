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
import logging
from typing import Set

import case_utils.ontology
from case_utils.namespace import NS_OWL, NS_RDF, NS_RDFS, NS_UCO_CORE, NS_XSD
from rdflib import BNode, Graph, Literal, URIRef
from rdflib.query import ResultRow


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out_graph")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    in_graph = Graph()
    out_graph = Graph()
    ttl_data = importlib.resources.read_text(case_utils.ontology, "case-1.4.0.ttl")
    in_graph.parse(data=ttl_data)
    case_utils.ontology.load_subclass_hierarchy(in_graph)

    n_leaf_facet_classes: Set[URIRef] = set()
    leaf_facet_query = """\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX uco-core: <https://ontology.unifiedcyberontology.org/uco/core/>
SELECT ?nClass
WHERE {
  ?nClass
    a owl:Class ;
    rdfs:subClassOf* uco-core:Facet ;
    .
  FILTER NOT EXISTS {
    ?nSubClass
      a owl:Class ;
      rdfs:subClassOf ?nClass ;
      .
  }
}
"""
    for result in in_graph.query(leaf_facet_query):
        assert isinstance(result, ResultRow)
        assert isinstance(result[0], URIRef)
        n_leaf_facet_classes.add(result[0])

    n_uco_object_classes: Set[URIRef] = set()
    uco_object_query = """\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX uco-core: <https://ontology.unifiedcyberontology.org/uco/core/>
SELECT ?nClass
WHERE {
  ?nClass
    a owl:Class ;
    rdfs:subClassOf* uco-core:UcoObject ;
    .
}
"""
    for result in in_graph.query(uco_object_query):
        assert isinstance(result, ResultRow)
        assert isinstance(result[0], URIRef)
        n_uco_object_classes.add(result[0])

    n_leaf_facet_classes_restricted: Set[URIRef] = set()
    # Determine which Facets are named by the pattern of a corresponding UcoObject subclass, plus "Facet".
    for n_uco_object_class in n_uco_object_classes:
        uco_object_class_iri = str(n_uco_object_class)
        n_maybe_leaf_facet = URIRef(uco_object_class_iri + "Facet")
        if n_maybe_leaf_facet in n_leaf_facet_classes:
            n_restriction = BNode()
            out_graph.add((n_restriction, NS_RDF.type, NS_OWL.Restriction))
            out_graph.add((n_restriction, NS_OWL.onClass, n_maybe_leaf_facet))
            out_graph.add((n_restriction, NS_OWL.onProperty, NS_UCO_CORE.hasFacet))
            out_graph.add(
                (
                    n_restriction,
                    NS_OWL.qualifiedCardinality,
                    Literal("1", datatype=NS_XSD.nonNegativeInteger),
                )
            )
            out_graph.add((n_uco_object_class, NS_RDFS.subClassOf, n_restriction))
            n_leaf_facet_classes_restricted.add(n_maybe_leaf_facet)

    if len(n_leaf_facet_classes_restricted) < len(n_leaf_facet_classes):
        logging.info("These classes had no pattern-matched UcoObject subclasses:")
        for n_leaf_facet_class in sorted(
            n_leaf_facet_classes - n_leaf_facet_classes_restricted
        ):
            logging.info("* %s", str(n_leaf_facet_class))

    out_graph.serialize(args.out_graph)


if __name__ == "__main__":
    main()
