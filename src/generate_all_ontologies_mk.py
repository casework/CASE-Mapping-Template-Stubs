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

"""
This script generates a Makefile that sets up recursive calls for all
ontologies known to CASE (e.g., CASE's Investigation ontology, UCO's
Observable ontology).

The intended execution location for this script is the top-level
directory `/templates`.
"""

import argparse
import logging
from typing import Dict, Set

from case_utils.case_validate.validate_utils import get_ontology_graph
from case_utils.namespace import NS_OWL, NS_RDF
from case_utils.ontology.version_info import (
    CURRENT_CASE_VERSION,
    built_version_choices_list,
)
from rdflib import Graph, URIRef


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--built-version",
        choices=tuple(built_version_choices_list),
        default="case-" + CURRENT_CASE_VERSION,
        help="Monolithic aggregation of CASE ontology files at certain versions.  Does not require networking to use.  Default is most recent CASE release.  Passing 'none' will mean no pre-built CASE ontology versions accompanying case-utils will be included in the analysis.",
    )
    parser.add_argument("out_mk")
    args = parser.parse_args()

    graph: Graph = get_ontology_graph(args.built_version)
    logging.debug("len(graph) = %d.", len(graph))

    n_classes: Set[URIRef] = set()
    for n_subject in graph.subjects(NS_RDF.type, NS_OWL.Class):
        if not isinstance(n_subject, URIRef):
            continue
        n_classes.add(n_subject)

    n_ontologies: Set[URIRef] = set()
    for n_subject in graph.subjects(NS_RDF.type, NS_OWL.Ontology):
        if not isinstance(n_subject, URIRef):
            continue
        if not str(n_subject).startswith("https://ontology."):
            continue
        n_ontologies.add(n_subject)
    n_prefixes_from_ontologies = {URIRef(str(x) + "/") for x in n_ontologies}

    n_prefixes_from_classes: Set[URIRef] = set()
    for n_class in n_classes:
        prefix, n_prefix, local_name = graph.namespace_manager.compute_qname(
            n_class, False
        )
        n_prefixes_from_classes.add(n_prefix)

    n_prefixes_with_classes = n_prefixes_from_ontologies & n_prefixes_from_classes

    n_prefix_to_prefix_name: Dict[URIRef, str] = dict()
    for n_prefix in n_prefixes_with_classes:
        prefix_iri_parts = str(n_prefix).split("/")
        # E.g.:
        # "https://ontology.caseontology.org/case/investigation/"
        #                                    ^-3  ^-2           ^-1
        n_prefix_to_prefix_name[n_prefix] = "-".join(
            [prefix_iri_parts[-3], prefix_iri_parts[-2]]
        )

    target_to_recipe: Dict[str, str] = dict()
    for n_prefix in n_prefix_to_prefix_name:
        prefix_name = n_prefix_to_prefix_name[n_prefix]
        target_to_recipe["all-" + n_prefix_to_prefix_name[n_prefix]] = """\

all-%s:
\t$(MAKE) \\
\t  PREFIX_IRI="%s" \\
\t  --directory %s
""" % (prefix_name, str(n_prefix), prefix_name)

    with open(args.out_mk, "w") as out_fh:
        targets_formatted = " \\\n  ".join(sorted(target_to_recipe.keys()))
        out_fh.write("""\
#!/usr/bin/make -f

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

# THIS FILE IS GENERATED.

SHELL := /bin/bash

top_srcdir := ../..

all: \\
  %s

.PHONY: \\
  %s

check: \\
  all

clean:
""" % (targets_formatted, targets_formatted))

        for target in sorted(target_to_recipe):
            out_fh.write(target_to_recipe[target])


if __name__ == "__main__":
    main()
