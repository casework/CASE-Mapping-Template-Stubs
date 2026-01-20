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
classes directly defined within an ontology within CDO (e.g., the
classes in CASE's Investigation ontology).

The intended execution location for this script is any 2nd-level
directory `/templates/X`, where X is the prefix name for the ontology
(e.g., `templates/case-investigation`).
"""

import argparse
import importlib.resources

import case_utils.ontology
from case_utils.namespace import NS_OWL, NS_RDF
from rdflib import Graph, URIRef


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out_mk")
    parser.add_argument("prefix_iri")
    args = parser.parse_args()

    graph = Graph()
    ttl_data = importlib.resources.read_text(case_utils.ontology, "case-1.4.0.ttl")
    graph.parse(data=ttl_data)

    n_classes: set[URIRef] = set()
    for n_subject in graph.subjects(NS_RDF.type, NS_OWL.Class):
        if not isinstance(n_subject, URIRef):
            continue
        if str(n_subject).startswith(args.prefix_iri):
            n_classes.add(n_subject)

    local_names: set[str] = set()
    for n_class in n_classes:
        prefix, n_namespace, local_name = graph.namespace_manager.compute_qname(
            n_class, False
        )
        if local_name in local_names:
            raise ValueError("Encountered same local name twice: %r." % local_name)
        local_names.add(local_name)

    target_to_recipe: dict[str, str] = dict()
    for local_name in local_names:
        target_to_recipe[local_name + "/Makefile"] = """\

%s/Makefile: \\
  $(top_srcdir_abspath)/src/class-copy-template.mk.in
\tmkdir \\
\t  -p \\
\t  %s
\tsed \\
\t  -e 's!@PREFIX_IRI@!%s!g' \\
\t  $< \\
\t  > $@_
\tmv $@_ $@
""" % (local_name, local_name, args.prefix_iri)
        target_to_recipe["all-" + local_name] = """\

all-%s: \\
  %s/Makefile
\t$(MAKE) \\
\t  --directory %s
""" % (local_name, local_name, local_name)

    targets_as_dependencies: str = "".join(
        [" \\\n  " + x for x in sorted(target_to_recipe.keys()) if x.startswith("all-")]
    )

    with open(args.out_mk, "w") as out_fh:
        out_fh.write(r"""#!/usr/bin/make -f

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

top_srcdir_relpath := ../..

top_srcdir_abspath := $(shell cd $(top_srcdir_relpath) ; pwd)

all:%s

.PHONY:%s
""" % (targets_as_dependencies, targets_as_dependencies))

        out_fh.write("""\

check: \\
  all

clean:
\t@rm -f \\
\t  */*.{dot,json,svg}
""")

        for target in sorted(target_to_recipe):
            out_fh.write(target_to_recipe[target])


if __name__ == "__main__":
    main()
